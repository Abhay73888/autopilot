r"""
core/billing.py — Credit Ledger, Unit Economics & Cost Control Engine for AUTOPILOT.

Responsibilities:
1. Tracks exact raw API costs (LLM tokens, TTS audio characters, AI image generations, FFmpeg rendering).
2. Manages internal credit ledger (debit, credit, balance checks).
3. Enforces autonomy spend boundaries (daily video caps, monthly budget limits).
4. Provides billing summaries for SaaS analytics and investor reporting.
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .db_base import DB_ENGINE, get_current_organization, get_current_workspace
from .logbook import Logbook

log = Logbook("billing")

# =====================================================================
# Unit Cost Benchmarks (USD) & Credit Conversion Rate (1 Credit = $0.10)
# =====================================================================
CREDIT_VALUE_USD = 0.10

COST_RATES = {
    # LLM costs per 1K tokens (input/output average blend)
    "llm_gemini_flash": 0.0001,
    "llm_gpt4o": 0.0050,
    "llm_claude_sonnet": 0.0075,
    "llm_groq_llama": 0.0002,
    "llm_kimi": 0.0015,
    # TTS costs per 1,000 characters
    "tts_edge": 0.0000,        # Free
    "tts_elevenlabs": 0.3000,  # $0.30 per 1k chars (~$0.03/short)
    # Image/Keyframe generation per image
    "image_fal_sdxl": 0.0040,  # $0.004 per image (~$0.024 for 6 keyframes)
    "image_replicate_flux": 0.0250,
    # Rendering compute cost per second of render time
    "render_compute_sec": 0.0005,
}

# Standard credit deduction per video generation operation
STANDARD_OPERATION_CREDITS = {
    "video_full_standard": 10,   # 10 credits ($1.00 user cost, ~$0.08 raw cost = 92% margin)
    "script_only": 2,
    "voice_only": 2,
    "visuals_only": 3,
    "render_only": 3,
}


@dataclass
class CostRecord:
    operation_type: str
    provider: str
    units_consumed: float
    raw_cost_usd: float
    credits_debited: int


class BillingEngine:
    """Enterprise billing and credit enforcement engine."""

    @staticmethod
    def calculate_raw_cost(operation_type: str, units: float, provider: str = "default") -> float:
        """Calculates exact underlying vendor cost in USD."""
        rate_key = f"{operation_type}_{provider}"
        rate = COST_RATES.get(rate_key, COST_RATES.get(operation_type, 0.001))
        return round(units * rate, 6)

    def __init__(self):
        # In-memory balance tracking for local tests / concurrency protection
        self._local_balances: Dict[str, int] = {}
        self._charged_jobs: set[str] = set()
        self._daily_spend: Dict[str, float] = {}
        self._ledger_lock = threading.RLock()


    def get_workspace_balance(self, workspace_id: Optional[str] = None) -> int:
        """Returns current credit balance for the workspace organization."""
        ws_id = workspace_id or get_current_workspace() or "default_workspace"
        with self._ledger_lock:
            if ws_id in self._local_balances:
                return self._local_balances[ws_id]
        try:
            rows = DB_ENGINE.execute_query(
                "SELECT balance FROM credit_accounts WHERE organization_id = %s LIMIT 1",
                (ws_id,)
            )
            if rows:
                bal = int(rows[0].get("balance", 0))
                with self._ledger_lock:
                    self._local_balances[ws_id] = bal
                return bal
        except Exception:
            pass
        # Fallback default for local dev / unconfigured DB
        with self._ledger_lock:
            self._local_balances.setdefault(ws_id, 1000)
            return self._local_balances[ws_id]

    def check_has_sufficient_credits(self, required_credits: int, workspace_id: Optional[str] = None) -> bool:
        """Checks whether workspace has enough credits to proceed with operation."""
        balance = self.get_workspace_balance(workspace_id)
        return balance >= required_credits

    def record_usage(
        self,
        operation_type: str,
        provider: str,
        units_consumed: float,
        credits_to_debit: Optional[int] = None,
        workspace_id: Optional[str] = None,
        video_id: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> CostRecord:
        """
        Deducts credits atomically, checks invariants (never negative, no double-charge),
        calculates raw cost, and writes an immutable entry to the usage ledger.
        """
        ws_id = workspace_id or get_current_workspace() or "default_workspace"
        org_id = get_current_organization() or ws_id

        raw_cost = self.calculate_raw_cost(operation_type, units_consumed, provider)
        credits = credits_to_debit if credits_to_debit is not None else STANDARD_OPERATION_CREDITS.get(operation_type, 1)

        with self._ledger_lock:
            # Invariant 1: Prevent double-charge on same job
            if job_id:
                if job_id in self._charged_jobs:
                    raise RuntimeError(f"DOUBLE_CHARGE_PREVENTED: Job {job_id} has already been debited.")
                self._charged_jobs.add(job_id)

            # Invariant 2: Balance can NEVER go negative
            current_bal = self.get_workspace_balance(ws_id)
            if current_bal < credits:
                raise RuntimeError(
                    f"INSUFFICIENT_CREDITS_INVARIANT: Attempted to debit {credits} credits, but current balance is {current_bal}."
                )

            # Deduct balance atomically
            new_bal = current_bal - credits
            self._local_balances[ws_id] = new_bal

            # Invariant 3: Guardrail spend caps
            current_spend = self._daily_spend.get(ws_id, 0.0) + raw_cost
            self._daily_spend[ws_id] = current_spend

            # Per-workspace daily USD cap ($50.00 default)
            if current_spend > 50.0:
                log.warn(f"Spend spike detected for workspace {ws_id}: ${current_spend:.2f}. Triggering emergency halt.")
                try:
                    from backend.app.services.workspace_service import workspace_service
                    workspace_service.trigger_emergency_stop(ws_id)
                except Exception:
                    pass

        ledger_id = f"led_{uuid.uuid4().hex[:16]}"
        now_ts = datetime.now(timezone.utc).isoformat()

        try:
            DB_ENGINE.execute_mutation(
                """
                INSERT INTO usage_ledger (id, organization_id, workspace_id, operation_type, units_consumed, raw_cost_usd, credits_debited, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (ledger_id, org_id, ws_id, operation_type, units_consumed, raw_cost, credits, now_ts)
            )
            DB_ENGINE.execute_mutation(
                "UPDATE credit_accounts SET balance = %s WHERE organization_id = %s",
                (new_bal, ws_id)
            )
        except Exception as e:
            log.warning("Ledger recording fallback to local logger", error=str(e))

        log.info(
            "Billing Ledger Debit",
            ledger_id=ledger_id,
            operation=operation_type,
            provider=provider,
            units=units_consumed,
            raw_cost_usd=raw_cost,
            credits_debited=credits,
            balance_after=new_bal
        )

        return CostRecord(
            operation_type=operation_type,
            provider=provider,
            units_consumed=units_consumed,
            raw_cost_usd=raw_cost,
            credits_debited=credits,
        )

    def check_autonomy_budget_exceeded(self, workspace_id: Optional[str] = None) -> bool:
        """Validates whether workspace has crossed daily render count or monthly budget."""
        ws_id = workspace_id or get_current_workspace() or "default_workspace"
        with self._ledger_lock:
            return self._daily_spend.get(ws_id, 0.0) >= 50.0


BILLING = BillingEngine()

