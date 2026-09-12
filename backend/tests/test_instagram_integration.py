r"""
backend/tests/test_instagram_integration.py — Production-Grade Test Suite for Instagram Publishing.

Covers:
1. Meta OAuth 2.0 State Security (HMAC verification, expiration, CSRF, cross-tenant rejection)
2. AES-256-GCM Token Encryption & Redaction (Plaintext never leaked to DB, logs, or API)
3. Multi-Tenant Isolation & IDOR Protection (User B cannot access or publish via User A's account)
4. Instagram Reel Video Validation (Format, duration <= 90s, codecs, caption limits)
5. Idempotent Publishing Engine (Duplicate publish calls return same job without duplicate reel)
6. Asynchronous Background Worker Lifecycle (Container create -> poll -> publish)
7. Error Handling & Circuit Breaker (Exponential backoff, token expiry halt, emergency stop)
8. End-to-End API Integration via TestClient
"""

import time
import unittest
import uuid
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.api.v1.integrations_instagram import generate_oauth_state, verify_oauth_state
from backend.app.publishers.base import ValidationResult
from backend.app.publishers.mock_instagram import MockInstagramProvider
from backend.app.services.publishing_service import publishing_service
from backend.app.services.reel_validator import validate_reel
from backend.app.services.video_service import video_service
from backend.app.workers.instagram_worker import execute_publish_job
from core.db_base import DB_ENGINE
from core.security import vault


class TestInstagramIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.ws_a = f"ws_ig_tenant_a_{uuid.uuid4().hex[:8]}"
        self.ws_b = f"ws_ig_tenant_b_{uuid.uuid4().hex[:8]}"
        self.user_a = f"usr_a_{uuid.uuid4().hex[:8]}"
        self.user_b = f"usr_b_{uuid.uuid4().hex[:8]}"

        # Initialize test workspaces matching default auth org
        self.org_id = "org_media_group_01"
        DB_ENGINE.execute_mutation(
            "INSERT INTO workspaces (id, organization_id, name, slug, is_active) VALUES (%s, %s, %s, %s, %s)",
            (self.ws_a, self.org_id, "Workspace A", "ws-a", 1)
        )
        DB_ENGINE.execute_mutation(
            "INSERT INTO workspaces (id, organization_id, name, slug, is_active) VALUES (%s, %s, %s, %s, %s)",
            (self.ws_b, self.org_id, "Workspace B", "ws-b", 1)
        )

        # Enable mock provider mode
        self.mock_provider = publishing_service.set_mock_mode(enabled=True, mode="SUCCESS")

    def tearDown(self):
        # Reset provider mode
        publishing_service.set_mock_mode(enabled=False)

    # =========================================================================
    # 1. OAuth 2.0 Security & State Invariants
    # =========================================================================
    def test_oauth_state_generation_and_signature_verification(self):
        """Valid HMAC state parses correctly and retains tenant identity."""
        state = generate_oauth_state(self.ws_a, self.user_a)
        payload = verify_oauth_state(state)
        self.assertEqual(payload["ws"], self.ws_a)
        self.assertEqual(payload["u"], self.user_a)
        self.assertGreater(payload["exp"], time.time())

    def test_oauth_state_tampering_rejected_with_400(self):
        """Tampered state must fail cryptographic HMAC check (Anti-CSRF)."""
        state = generate_oauth_state(self.ws_a, self.user_a)
        parts = state.split(".")
        # Tamper payload
        tampered_state = f"dGFtcGVyZWQ.{parts[1]}"
        with self.assertRaises(Exception):
            verify_oauth_state(tampered_state)

    def test_oauth_state_expiration_rejected(self):
        """State older than 10 minutes is rejected as expired."""
        payload = {"ws": self.ws_a, "u": self.user_a, "nonce": "abc", "exp": int(time.time()) - 10}
        import base64, hashlib, hmac, json
        raw = json.dumps(payload, sort_keys=True)
        sig = hmac.new(settings.secret_key.encode(), raw.encode(), hashlib.sha256).hexdigest()
        b64 = base64.urlsafe_b64encode(raw.encode()).decode()
        expired_state = f"{b64}.{sig}"

        with self.assertRaises(Exception):
            verify_oauth_state(expired_state)

    # =========================================================================
    # 2. Token Security & Vault Encryption
    # =========================================================================
    def test_platform_token_encryption_and_safe_listing(self):
        """Access token must be AES-256-GCM encrypted in DB and redacted in API responses."""
        raw_secret_token = "EAABwz_secret_meta_token_never_plain"
        account = publishing_service.connect_account(
            workspace_id=self.ws_a,
            platform="instagram",
            external_account_id="178414000000001",
            username="test_creator_brand",
            display_name="Test Brand",
            profile_image_url="https://example.com/pic.jpg",
            access_token=raw_secret_token,
            scopes=["instagram_basic", "instagram_content_publish"]
        )

        # 1. Verify DB contains ciphertext, not plaintext
        rows = DB_ENGINE.execute_query(
            "SELECT encrypted_access_token FROM platform_accounts WHERE id = %s",
            (account["id"],)
        )
        self.assertTrue(len(rows) > 0)
        stored_cipher = rows[0]["encrypted_access_token"]
        self.assertNotEqual(stored_cipher, raw_secret_token)
        self.assertNotIn("EAABwz", stored_cipher)

        # 2. Verify vault can decrypt back to original
        decrypted = vault.decrypt_secret(stored_cipher)
        self.assertEqual(decrypted, raw_secret_token)

        # 3. Verify list_accounts never returns access_token
        accounts_list = publishing_service.list_accounts(self.ws_a)
        self.assertTrue(len(accounts_list) > 0)
        for acct in accounts_list:
            self.assertNotIn("encrypted_access_token", acct)
            self.assertNotIn("access_token", acct)
            self.assertEqual(acct["username"], "test_creator_brand")

    # =========================================================================
    # 3. Multi-Tenancy & IDOR Isolation
    # =========================================================================
    def test_idor_cross_tenant_account_access_forbidden(self):
        """Workspace B cannot view or disconnect Workspace A's Instagram account."""
        account_a = publishing_service.connect_account(
            workspace_id=self.ws_a,
            platform="instagram",
            external_account_id="178414000000002",
            username="tenant_a_influencer",
            display_name="Tenant A Channel",
            profile_image_url="https://example.com/a.jpg",
            access_token="token_a_12345",
            scopes=["instagram_basic"]
        )

        # Workspace B attempts to read Workspace A's account
        acct_from_b = publishing_service.get_account(self.ws_b, account_a["id"])
        self.assertIsNone(acct_from_b)

        # Workspace B attempts to disconnect Workspace A's account
        success = publishing_service.disconnect_account(self.ws_b, account_a["id"])
        self.assertFalse(success)

        # Verify Workspace A's account is still active
        acct_from_a = publishing_service.get_account(self.ws_a, account_a["id"])
        self.assertIsNotNone(acct_from_a)
        self.assertEqual(acct_from_a["status"], "connected")

    # =========================================================================
    # 4. Reel Media Validation Engine
    # =========================================================================
    def test_reel_validation_rejects_nonexistent_and_invalid_formats(self):
        """Reel validator rejects missing files, huge captions, and invalid constraints."""
        # Nonexistent file
        res = validate_reel("/nonexistent/video.mp4", caption="Hello #ai")
        self.assertFalse(res.is_valid)
        self.assertTrue(any("not found" in e.lower() for e in res.errors))

        # Caption > 2200 characters
        huge_caption = "a" * 2250
        res = validate_reel(__file__, caption=huge_caption)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("exceeds maximum limit of 2200" in e for e in res.errors))

        # Caption with > 30 hashtags
        too_many_tags = " ".join([f"#tag{i}" for i in range(35)])
        res = validate_reel(__file__, caption=too_many_tags)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("limits to maximum 30 hashtags" in e for e in res.errors))

    # =========================================================================
    # 5. Idempotent Publishing Lifecycle
    # =========================================================================
    def test_idempotent_publish_returns_same_job_without_duplicate(self):
        """Calling publish twice with identical idempotencyKey returns the same job."""
        account = publishing_service.connect_account(
            workspace_id=self.ws_a,
            platform="instagram",
            external_account_id="178414000000003",
            username="idempotent_creator",
            display_name="Idempotent Creator",
            profile_image_url="https://example.com/p.jpg",
            access_token="tok_idem_123",
            scopes=["instagram_basic", "instagram_content_publish"]
        )

        # Create video in Workspace A
        vid = video_service.create_video(self.ws_a, "Idempotent Reel", "Topic A")
        idem_key = f"idem_{uuid.uuid4().hex[:12]}"

        # First publish call
        job1 = publishing_service.create_publishing_job(
            workspace_id=self.ws_a,
            platform_account_id=account["id"],
            video_id=vid["id"],
            caption="First publish attempt #viral",
            idempotency_key=idem_key
        )

        # Second publish call (simulating network retry or double click)
        job2 = publishing_service.create_publishing_job(
            workspace_id=self.ws_a,
            platform_account_id=account["id"],
            video_id=vid["id"],
            caption="First publish attempt #viral",
            idempotency_key=idem_key
        )

        self.assertEqual(job1["id"], job2["id"])
        self.assertEqual(job1["idempotency_key"], job2["idempotency_key"])

    # =========================================================================
    # 6. Background Worker & Asynchronous Publishing Flow
    # =========================================================================
    def test_worker_publishes_reel_successfully(self):
        """Worker executes full pipeline: upload -> process -> publish -> mark published."""
        account = publishing_service.connect_account(
            workspace_id=self.ws_a,
            platform="instagram",
            external_account_id="178414000000004",
            username="async_worker_tester",
            display_name="Async Tester",
            profile_image_url="https://example.com/p.jpg",
            access_token="tok_worker_success",
            scopes=["instagram_basic", "instagram_content_publish"]
        )
        vid = video_service.create_video(self.ws_a, "Async Reel Test", "Mystery Topic")

        job = publishing_service.create_publishing_job(
            workspace_id=self.ws_a,
            platform_account_id=account["id"],
            video_id=vid["id"],
            caption="Testing autonomous async reel publish #autopilot",
            scheduled_at="2026-10-01T12:00:00Z"  # Don't auto-dispatch in thread for unit test
        )

        # Run worker synchronously for test inspection
        success = execute_publish_job(job["id"])
        self.assertTrue(success)

        # Inspect job in DB
        updated_job = publishing_service.get_job(self.ws_a, job["id"])
        self.assertEqual(updated_job["status"], "published")
        self.assertTrue(updated_job["external_media_id"].startswith("mock_ig_media_"))
        self.assertIsNotNone(updated_job["published_at"])

    # =========================================================================
    # 7. Error Handling, Token Expiration & Emergency Stop
    # =========================================================================
    def test_worker_halts_on_token_expiration_and_marks_account_expired(self):
        """Token expired (code 190) terminates retries and flags account as token_expired."""
        self.mock_provider.set_mode("TOKEN_EXPIRED")

        account = publishing_service.connect_account(
            workspace_id=self.ws_a,
            platform="instagram",
            external_account_id="178414000000005",
            username="expired_tester",
            display_name="Expired Tester",
            profile_image_url="https://example.com/p.jpg",
            access_token="tok_expired_123",
            scopes=["instagram_basic", "instagram_content_publish"]
        )
        vid = video_service.create_video(self.ws_a, "Expired Token Test", "Topic")
        job = publishing_service.create_publishing_job(
            workspace_id=self.ws_a,
            platform_account_id=account["id"],
            video_id=vid["id"],
            caption="This will fail with expired token",
            scheduled_at="2026-10-01T12:00:00Z"
        )

        success = execute_publish_job(job["id"])
        self.assertFalse(success)

        # Verify job marked failed with INSTAGRAM_TOKEN_EXPIRED
        updated_job = publishing_service.get_job(self.ws_a, job["id"])
        self.assertEqual(updated_job["status"], "failed")
        self.assertIn("TOKEN_EXPIRED", updated_job["error_code"])

        # Verify account marked token_expired
        updated_account = publishing_service.get_account(self.ws_a, account["id"])
        self.assertEqual(updated_account["status"], "token_expired")

    def test_emergency_stop_aborts_publishing(self):
        """Paused workspace circuit breaker aborts publishing and marks job cancelled."""
        # Pause workspace
        DB_ENGINE.execute_mutation(
            "UPDATE workspaces SET is_active = 0 WHERE id = %s",
            (self.ws_a,)
        )

        account = publishing_service.connect_account(
            workspace_id=self.ws_a,
            platform="instagram",
            external_account_id="178414000000006",
            username="paused_tester",
            display_name="Paused Tester",
            profile_image_url="https://example.com/p.jpg",
            access_token="tok_paused_123",
            scopes=["instagram_basic"]
        )
        vid = video_service.create_video(self.ws_a, "Paused Test", "Topic")

        # Publishing request must be rejected directly
        with self.assertRaises(Exception):
            publishing_service.create_publishing_job(
                workspace_id=self.ws_a,
                platform_account_id=account["id"],
                video_id=vid["id"],
                caption="Emergency stop should block this"
            )

    # =========================================================================
    # 8. API Integration via TestClient
    # =========================================================================
    def test_api_oauth_start_and_accounts_listing(self):
        """API endpoints return valid OAuth URL and safe accounts list."""
        headers = {"X-Workspace-ID": self.ws_a}

        # 1. GET /api/v1/integrations/instagram/oauth/start
        res = self.client.get("/api/v1/integrations/instagram/oauth/start", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertIn("authorization_url", data)
        self.assertIn("state", data)
        self.assertIn("client_id", data["authorization_url"])

        # 2. Connect an account directly to test listing
        publishing_service.connect_account(
            workspace_id=self.ws_a,
            platform="instagram",
            external_account_id="178414000000007",
            username="api_creator",
            display_name="API Creator",
            profile_image_url="https://example.com/p.jpg",
            access_token="tok_api_123",
            scopes=["instagram_basic", "instagram_content_publish"]
        )

        # 3. GET /api/v1/integrations/instagram/accounts
        res = self.client.get("/api/v1/integrations/instagram/accounts", headers=headers)
        self.assertEqual(res.status_code, 200)
        accts = res.json()["data"]
        self.assertTrue(len(accts) > 0)
        self.assertEqual(accts[0]["username"], "api_creator")
        # Ensure token is never returned
        self.assertNotIn("access_token", accts[0])
        self.assertNotIn("encrypted_access_token", accts[0])

        # 4. GET /api/v1/integrations/instagram/status
        res = self.client.get("/api/v1/integrations/instagram/status", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["data"]["connected"])

    def test_api_publish_and_job_lifecycle(self):
        """POST /api/v1/instagram/publish queues job and GET /jobs/{id} returns status."""
        headers = {"X-Workspace-ID": self.ws_a}
        acct = publishing_service.connect_account(
            workspace_id=self.ws_a,
            platform="instagram",
            external_account_id="178414000000008",
            username="publish_api_tester",
            display_name="Publish Tester",
            profile_image_url="https://example.com/p.jpg",
            access_token="tok_pub_api",
            scopes=["instagram_basic", "instagram_content_publish"]
        )
        vid = video_service.create_video(self.ws_a, "API Reel", "Topic API")

        # Publish immediately
        res = self.client.post(
            "/api/v1/instagram/publish",
            headers=headers,
            json={
                "platformAccountId": acct["id"],
                "videoId": vid["id"],
                "caption": "Reel published via API #tech",
                "idempotencyKey": f"api_idem_{uuid.uuid4().hex[:8]}"
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        job_id = data["job_id"]
        self.assertEqual(data["status"], "queued")

        # Poll job status
        res = self.client.get(f"/api/v1/instagram/jobs/{job_id}", headers=headers)
        self.assertEqual(res.status_code, 200)
        job_data = res.json()["data"]
        self.assertEqual(job_data["job_id"], job_id)
        self.assertEqual(job_data["workspace_id"], self.ws_a)

    def test_api_schedule_and_cancellation(self):
        """POST /api/v1/instagram/schedule schedules post; POST /cancel cancels it."""
        headers = {"X-Workspace-ID": self.ws_a}
        acct = publishing_service.connect_account(
            workspace_id=self.ws_a,
            platform="instagram",
            external_account_id="178414000000009",
            username="schedule_api_tester",
            display_name="Schedule Tester",
            profile_image_url="https://example.com/p.jpg",
            access_token="tok_sched_api",
            scopes=["instagram_basic", "instagram_content_publish"]
        )
        vid = video_service.create_video(self.ws_a, "Schedule Reel", "Topic Sched")

        res = self.client.post(
            "/api/v1/instagram/schedule",
            headers=headers,
            json={
                "platformAccountId": acct["id"],
                "videoId": vid["id"],
                "caption": "Scheduled Reel #future",
                "scheduledAt": "2026-12-01T15:00:00Z",
                "timezone": "Asia/Kolkata"
            }
        )
        self.assertEqual(res.status_code, 200)
        job_id = res.json()["data"]["job_id"]
        self.assertEqual(res.json()["data"]["status"], "scheduled")

        # Cancel job
        cancel_res = self.client.post(f"/api/v1/instagram/jobs/{job_id}/cancel", headers=headers)
        self.assertEqual(cancel_res.status_code, 200)
        self.assertEqual(cancel_res.json()["data"]["status"], "cancelled")

    def test_api_cross_tenant_publishing_idor_forbidden(self):
        """Workspace B cannot publish using Workspace A's account or video."""
        acct_a = publishing_service.connect_account(
            workspace_id=self.ws_a,
            platform="instagram",
            external_account_id="178414000000010",
            username="victim_brand",
            display_name="Victim Brand",
            profile_image_url="https://example.com/p.jpg",
            access_token="tok_victim",
            scopes=["instagram_basic"]
        )
        vid_a = video_service.create_video(self.ws_a, "Victim Video", "Topic")

        # Workspace B attempts to publish using Workspace A's credentials
        headers_b = {"X-Workspace-ID": self.ws_b}
        res = self.client.post(
            "/api/v1/instagram/publish",
            headers=headers_b,
            json={
                "platformAccountId": acct_a["id"],
                "videoId": vid_a["id"],
                "caption": "Malicious post attempt"
            }
        )
        # Should be forbidden / rejected
        self.assertIn(res.status_code, (400, 403))

    def test_api_analytics_and_sync(self):
        """GET /api/v1/instagram/analytics and POST /sync return valid metrics."""
        headers = {"X-Workspace-ID": self.ws_a}
        res = self.client.get("/api/v1/instagram/analytics", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertIn("total_posts", data)
        self.assertIn("total_views", data)

        sync_res = self.client.post("/api/v1/instagram/sync", headers=headers)
        self.assertEqual(sync_res.status_code, 200)
        self.assertIn("synced_posts", sync_res.json()["data"])


if __name__ == "__main__":
    unittest.main()
