"""
PHASE 2 - MONEY SAFETY & LEDGER INVARIANT TESTS
Tests:
- Balance can NEVER go negative under parallel workers (concurrency test).
- Same job can NEVER be charged twice (idempotent debit per job_id).
- Spend guardrails: per-workspace daily USD cap triggers emergency stop.
- Billing webhook HMAC signature verification & timestamp replay protection.
- Idempotency-Key cache consistency.
"""

import hashlib
import hmac
import os
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest import mock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.idempotency import IDEMPOTENCY
from backend.app.services.workspace_service import workspace_service
from core.billing import BILLING


class TestBillingInvariants(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_ws = f"ws_test_{int(time.time() * 1000)}"
        # Initialize test balance with 100 credits
        BILLING._local_balances[self.test_ws] = 100
        BILLING._daily_spend[self.test_ws] = 0.0

    def test_invariant_balance_never_goes_negative_under_parallel_debits(self):
        """Invariant 1: Balance must NEVER go below zero even under concurrent debit races."""
        # Initial balance is 100 credits.
        # Each debit is 15 credits (e.g. video render).
        # We fire 20 concurrent threads: total attempted = 300 credits.
        # Only at most 6 debits (90 credits) should succeed, 14 must fail with RuntimeError.
        successes = 0
        failures = 0

        def debit_worker(worker_id: int):
            try:
                BILLING.record_usage(
                    operation_type="render_seconds",
                    provider="remotion",
                    units_consumed=15,
                    credits_to_debit=15,
                    workspace_id=self.test_ws,
                    job_id=f"job_concurrent_{worker_id}"
                )
                return True
            except RuntimeError as e:
                if "INSUFFICIENT_CREDITS_INVARIANT" in str(e):
                    return False
                raise

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(debit_worker, range(20)))

        successes = sum(1 for r in results if r is True)
        failures = sum(1 for r in results if r is False)

        final_bal = BILLING.get_workspace_balance(self.test_ws)
        self.assertGreaterEqual(final_bal, 0, f"Invariant violated! Balance went negative: {final_bal}")
        self.assertEqual(final_bal, 100 - (successes * 15))
        self.assertEqual(successes + failures, 20)
        self.assertLessEqual(successes, 6)

    def test_invariant_same_job_never_charged_twice(self):
        """Invariant 2: Same job_id can NEVER be charged twice."""
        job_id = f"job_unique_{int(time.time())}"
        # First charge succeeds
        rec1 = BILLING.record_usage(
            operation_type="llm_tokens",
            provider="openai",
            units_consumed=1000,
            workspace_id=self.test_ws,
            job_id=job_id
        )
        self.assertIsNotNone(rec1)

        # Second charge with identical job_id must raise RuntimeError
        with self.assertRaises(RuntimeError) as ctx:
            BILLING.record_usage(
                operation_type="llm_tokens",
                provider="openai",
                units_consumed=1000,
                workspace_id=self.test_ws,
                job_id=job_id
            )
        self.assertIn("DOUBLE_CHARGE_PREVENTED", str(ctx.exception))

    def test_spend_guardrail_triggers_emergency_stop(self):
        """Guardrail: Workspace crossing daily USD cap triggers emergency halt."""
        self.assertFalse(workspace_service.is_emergency_stopped(self.test_ws))
        # Initial large debit of $55 (equivalent to 100,000 units of custom compute)
        # In billing.py, USD cost > $50.0 triggers workspace_service.trigger_emergency_stop
        # Give enough credits to debit
        BILLING._local_balances[self.test_ws] = 10000

        BILLING.record_usage(
            operation_type="custom_heavy_compute",
            provider="runpod",
            units_consumed=100000,  # calculates > $50 in raw cost
            workspace_id=self.test_ws,
            job_id=f"job_spike_{int(time.time())}"
        )

        self.assertTrue(workspace_service.is_emergency_stopped(self.test_ws))
        self.assertTrue(BILLING.check_autonomy_budget_exceeded(self.test_ws))

    def test_billing_webhook_hmac_and_replay_protection(self):
        """Webhook security: Valid HMAC succeeds, bad HMAC fails, stale timestamp fails."""
        secret = "whsec_test_secret_for_validation"
        now = time.time()
        body = b'{"id": "evt_test_123", "type": "checkout.session.completed", "data": {"object": {"client_reference_id": "' + self.test_ws.encode() + b'"}}}'

        # 1. Valid signature
        signed_payload = f"{now}.".encode("utf-8") + body
        valid_sig = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
        header = f"t={now},v1={valid_sig}"

        res = self.client.post("/api/v1/billing/webhook", content=body, headers={"stripe-signature": header})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "success")

        # 2. Replay of same event_id should be idempotent
        res_repeat = self.client.post("/api/v1/billing/webhook", content=body, headers={"stripe-signature": header})
        self.assertEqual(res_repeat.status_code, 200)
        self.assertIn("already processed", res_repeat.json()["message"])

        # 3. Invalid signature
        bad_header = f"t={now},v1=badbadbadbadbad"
        res_bad = self.client.post("/api/v1/billing/webhook", content=body, headers={"stripe-signature": bad_header})
        self.assertEqual(res_bad.status_code, 400)

        # 4. Expired timestamp (> 300s old)
        stale_time = now - 600
        stale_signed = f"{stale_time}.".encode("utf-8") + body
        stale_sig = hmac.new(secret.encode("utf-8"), stale_signed, hashlib.sha256).hexdigest()
        stale_header = f"t={stale_time},v1={stale_sig}"
        res_stale = self.client.post("/api/v1/billing/webhook", content=body, headers={"stripe-signature": stale_header})
        self.assertEqual(res_stale.status_code, 400)
        self.assertIn("timestamp too old", res_stale.json()["detail"])

    def test_idempotency_key_header_caching(self):
        """Idempotency-Key guarantees same result without duplicate charges."""
        key = f"idem_{time.time()}"
        headers = {"Idempotency-Key": key}
        payload = {
            "planId": "starter",
            "interval": "month",
            "successUrl": "https://autopilot.media/success",
            "cancelUrl": "https://autopilot.media/cancel"
        }

        res1 = self.client.post("/api/v1/billing/checkout", json=payload, headers=headers)
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()["data"]

        # Second request with identical key returns cached response
        res2 = self.client.post("/api/v1/billing/checkout", json=payload, headers=headers)
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()["data"]

        self.assertEqual(data1["checkoutUrl"], data2["checkoutUrl"])
        self.assertEqual(data1["planId"], data2["planId"])


if __name__ == "__main__":
    unittest.main()
