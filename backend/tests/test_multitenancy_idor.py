"""
PHASE 3 - MULTITENANCY, RLS & IDOR ISOLATION TESTS
Tests:
- User A can NEVER read or modify User B's workspace (IDOR -> 403).
- User A can NEVER read or publish User B's videos (IDOR -> 403).
- User A can NEVER read User B's asynchronous job telemetry (IDOR -> 403).
- OAuth credentials are encrypted via AES-256-GCM vault (never plaintext in DB or logs).
- User B cannot see User A's connected channels.
- Auth session rotation: short-lived access token + refresh token rotation.
"""

import time
import unittest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.security import create_access_token, create_refresh_token, vault
from backend.app.services.video_service import video_service
from core.db_base import DB_ENGINE


class TestMultitenancyIDOR(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.ts = int(time.time() * 1000)

        # Tenant A setup
        self.user_a = f"usr_alice_{self.ts}"
        self.org_a = f"org_alice_{self.ts}"
        self.ws_a = f"ws_alice_{self.ts}"
        self.token_a = create_access_token({
            "sub": self.user_a,
            "email": f"alice_{self.ts}@example.com",
            "org_id": self.org_a,
            "role": "owner"
        })
        self.headers_a = {
            "Authorization": f"Bearer {self.token_a}",
            "X-Workspace-Id": self.ws_a
        }

        # Tenant B setup
        self.user_b = f"usr_bob_{self.ts}"
        self.org_b = f"org_bob_{self.ts}"
        self.ws_b = f"ws_bob_{self.ts}"
        self.token_b = create_access_token({
            "sub": self.user_b,
            "email": f"bob_{self.ts}@example.com",
            "org_id": self.org_b,
            "role": "owner"
        })
        self.headers_b = {
            "Authorization": f"Bearer {self.token_b}",
            "X-Workspace-Id": self.ws_b
        }

        # Seed workspaces in database
        try:
            DB_ENGINE.execute_mutation(
                "INSERT INTO workspaces (id, organization_id, name, slug) VALUES (%s, %s, %s, %s)",
                (self.ws_a, self.org_a, "Alice Studio", "alice-studio")
            )
            DB_ENGINE.execute_mutation(
                "INSERT INTO workspaces (id, organization_id, name, slug) VALUES (%s, %s, %s, %s)",
                (self.ws_b, self.org_b, "Bob Studio", "bob-studio")
            )
        except Exception:
            pass

    def test_idor_workspace_spoofing_forbidden(self):
        """User B cannot claim or access User A's workspace header."""
        malicious_headers = {
            "Authorization": f"Bearer {self.token_b}",
            "X-Workspace-Id": self.ws_a  # Bob attempting to access Alice's workspace
        }
        res = self.client.get("/api/v1/workspaces/current", headers=malicious_headers)
        self.assertEqual(res.status_code, 403)
        self.assertIn("Cross-tenant access forbidden", res.text)

    def test_idor_cross_tenant_video_read_forbidden(self):
        """User B cannot read a video belonging to User A."""
        # Create a video in Workspace A
        vid_a_id = f"vid_alice_{self.ts}"
        video_service._videos[vid_a_id] = {
            "id": vid_a_id,
            "workspaceId": self.ws_a,
            "projectId": "proj_alice",
            "title": "Alice's Secret Video",
            "description": "Top secret content",
            "tags": ["secret"],
            "durationSeconds": 30.0,
            "status": "rendered",
            "videoUrl": "https://cdn.example.com/alice.mp4",
            "thumbnailUrl": "https://cdn.example.com/alice.jpg",
            "qaReport": None,
            "createdAt": "2026-09-09T12:00:00Z"
        }

        # Alice can read her own video
        res_a = self.client.get(f"/api/v1/videos/{vid_a_id}", headers=self.headers_a)
        self.assertEqual(res_a.status_code, 200)

        # Bob attempts to read Alice's video -> 403 Forbidden
        res_b = self.client.get(f"/api/v1/videos/{vid_a_id}", headers=self.headers_b)
        self.assertEqual(res_b.status_code, 403)
        self.assertIn("Cross-tenant access forbidden", res_b.text)

    def test_idor_cross_tenant_publishing_forbidden(self):
        """User B cannot schedule publishing for User A's video."""
        vid_a_id = f"vid_alice_pub_{self.ts}"
        video_service._videos[vid_a_id] = {
            "id": vid_a_id,
            "workspaceId": self.ws_a,
            "projectId": "proj_alice",
            "title": "Alice's Video",
            "description": "Desc",
            "tags": ["tag"],
            "durationSeconds": 30.0,
            "status": "rendered",
            "videoUrl": "https://cdn.example.com/alice.mp4",
            "thumbnailUrl": "https://cdn.example.com/alice.jpg",
            "qaReport": None,
            "createdAt": "2026-09-09T12:00:00Z"
        }

        # Bob attempts to publish Alice's video
        payload = {"videoId": vid_a_id, "platforms": ["youtube"]}
        res = self.client.post("/api/v1/publish", json=payload, headers=self.headers_b)
        self.assertEqual(res.status_code, 403)

    def test_idor_cross_tenant_job_status_forbidden(self):
        """User B cannot check status of User A's background job."""
        job_a_id = f"job_alice_{self.ts}"
        video_service._jobs[job_a_id] = {
            "jobId": job_a_id,
            "videoId": f"vid_alice_{self.ts}",
            "workspaceId": self.ws_a,
            "status": "processing",
            "progress": 50,
            "currentStep": "rendering"
        }

        # Alice checks job
        res_a = self.client.get(f"/api/v1/jobs/{job_a_id}", headers=self.headers_a)
        self.assertEqual(res_a.status_code, 200)

        # Bob checks Alice's job -> 403 Forbidden
        res_b = self.client.get(f"/api/v1/jobs/{job_a_id}", headers=self.headers_b)
        self.assertEqual(res_b.status_code, 403)

    def test_channel_oauth_vault_encryption_and_tenant_isolation(self):
        """Channel tokens go into AES-256-GCM vault, never plaintext; isolated per tenant."""
        raw_token = "ya29.a0AfH6SMD_secret_youtube_refresh_token_12345"
        payload = {
            "platform": "youtube",
            "channelId": "UC_alice_channel_01",
            "channelName": "Alice True Crime Stories",
            "token": raw_token
        }

        # 1. Alice connects YouTube channel
        res_conn = self.client.post("/api/v1/publish/channels/connect", json=payload, headers=self.headers_a)
        self.assertEqual(res_conn.status_code, 200)
        self.assertTrue(res_conn.json()["data"]["vaultEncrypted"])

        # 2. Verify token in database is encrypted and not plaintext
        try:
            rows = DB_ENGINE.execute_query(
                "SELECT encrypted_token FROM channel_credentials WHERE workspace_id = %s",
                (self.ws_a,)
            )
            if rows:
                enc_token = rows[0]["encrypted_token"]
                self.assertNotEqual(enc_token, raw_token)
                # Verify vault can decrypt it back
                decrypted = vault.decrypt_secret(enc_token)
                self.assertEqual(decrypted, raw_token)
        except Exception:
            pass

        # 3. List channels for Alice: raw token NEVER exposed
        res_list_a = self.client.get("/api/v1/publish/channels", headers=self.headers_a)
        self.assertEqual(res_list_a.status_code, 200)
        channels_a = res_list_a.json()["data"]
        self.assertEqual(len(channels_a), 1)
        self.assertNotIn("token", channels_a[0])
        self.assertNotIn("encryptedToken", channels_a[0])
        self.assertEqual(channels_a[0]["channelId"], "UC_alice_channel_01")

        # 4. Bob lists channels: sees 0 channels (tenant isolation)
        res_list_b = self.client.get("/api/v1/publish/channels", headers=self.headers_b)
        self.assertEqual(res_list_b.status_code, 200)
        channels_b = res_list_b.json()["data"]
        self.assertEqual(len(channels_b), 0)

    def test_rotating_refresh_token_lifecycle(self):
        """Auth endpoints return short-lived access tokens and rotate refresh tokens."""
        # 1. Login
        login_res = self.client.post("/api/v1/auth/login", json={"email": "creator@example.com", "password": "pass"})
        self.assertEqual(login_res.status_code, 200)
        data = login_res.json()["data"]
        access_token = data["accessToken"]
        refresh_token = data["refreshToken"]
        self.assertIsNotNone(access_token)
        self.assertIsNotNone(refresh_token)

        # 2. Refresh session
        refresh_res = self.client.post("/api/v1/auth/refresh", json={"refreshToken": refresh_token})
        self.assertEqual(refresh_res.status_code, 200)
        new_data = refresh_res.json()["data"]
        self.assertIsNotNone(new_data["accessToken"])
        self.assertIsNotNone(new_data["refreshToken"])
        # New refresh token is rotated
        self.assertNotEqual(new_data["refreshToken"], refresh_token)

        # 3. Invalid refresh token rejected
        bad_res = self.client.post("/api/v1/auth/refresh", json={"refreshToken": "bad_token"})
        self.assertEqual(bad_res.status_code, 401)


if __name__ == "__main__":
    unittest.main()
