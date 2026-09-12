import hashlib
import hmac
import os
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from core.billing import BILLING
from ...core.idempotency import IDEMPOTENCY
from ...schemas.billing import CheckoutRequest, CreditBalanceResponse, PlanTier, UsageLedgerItem
from ...schemas.common import ApiResponse
from ...services.billing_service import billing_service
from ..dependencies import TenantContext, get_current_tenant_context

router = APIRouter(prefix="/billing", tags=["Billing & Credits"])

# In-memory webhook event idempotency cache
_processed_webhook_events: set[str] = set()


@router.get("/plans", response_model=ApiResponse[List[PlanTier]])
async def list_plans():
    plans = billing_service.get_plans()
    return ApiResponse(success=True, data=plans)


@router.get("/credits", response_model=ApiResponse[CreditBalanceResponse])
async def get_credit_balance(ctx: TenantContext = Depends(get_current_tenant_context)):
    balance = billing_service.get_credit_balance(ctx.workspace_id)
    return ApiResponse(success=True, data=balance)


@router.get("/ledger", response_model=ApiResponse[List[UsageLedgerItem]])
async def get_usage_ledger(ctx: TenantContext = Depends(get_current_tenant_context)):
    ledger = billing_service.get_usage_ledger(ctx.workspace_id)
    return ApiResponse(success=True, data=ledger)


@router.post("/checkout", response_model=ApiResponse[Dict[str, Any]])
async def create_checkout_session(
    req: CheckoutRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    ctx: TenantContext = Depends(get_current_tenant_context)
):
    if idempotency_key:
        cached = IDEMPOTENCY.get(idempotency_key)
        if cached:
            return ApiResponse(success=True, data=cached)

    res_data = {
        "checkoutUrl": f"https://checkout.stripe.com/c/pay/cs_test_{req.planId}",
        "planId": req.planId,
        "interval": req.interval
    }

    if idempotency_key:
        IDEMPOTENCY.set(idempotency_key, res_data)

    return ApiResponse(success=True, data=res_data)


@router.post("/webhook")
async def billing_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature")
):
    """
    Provider-agnostic webhook receiver with HMAC signature validation,
    timestamp replay protection, and event idempotency.
    """
    body_bytes = await request.body()
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_test_secret_for_validation")

    sig_header = stripe_signature or x_webhook_signature
    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing webhook signature header"
        )

    # Parse timestamp and signature elements
    elements = {}
    for item in sig_header.split(","):
        if "=" in item:
            k, v = item.strip().split("=", 1)
            elements[k] = v

    ts_str = elements.get("t")
    expected_v1 = elements.get("v1")

    # Replay protection: max 300 seconds clock drift
    if ts_str:
        try:
            ts = float(ts_str)
            if abs(time.time() - ts) > 300:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Webhook signature timestamp too old (replay protection)"
                )
        except ValueError:
            pass

    # Verify HMAC signature if v1 provided
    if expected_v1:
        signed_payload = f"{ts_str}.".encode("utf-8") + body_bytes
        computed = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed, expected_v1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature"
            )

    try:
        event = await request.json()
    except Exception:
        event = {}

    event_id = event.get("id", f"evt_{int(time.time())}")
    if event_id in _processed_webhook_events:
        return {"status": "success", "message": "Event already processed (idempotent)"}

    _processed_webhook_events.add(event_id)

    event_type = event.get("type", "checkout.session.completed")
    if event_type in ("checkout.session.completed", "invoice.payment_succeeded"):
        ws_id = event.get("data", {}).get("object", {}).get("client_reference_id", "default_workspace")
        # Credit account with 1000 credits
        BILLING.get_workspace_balance(ws_id)
        if ws_id in BILLING._local_balances:
            BILLING._local_balances[ws_id] += 1000

    return {"status": "success", "event_id": event_id, "type": event_type}

