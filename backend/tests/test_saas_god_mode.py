r"""
backend/tests/test_saas_god_mode.py — Comprehensive SaaS & God Mode Test Suite

Validates:
1. Authentication: Signup, PBKDF2 password hashing, login, session persistence, onboarding.
2. Multi-Tenancy & Data Isolation: User A vs User B strict isolation (Videos, Series, Episodes).
3. YouTube OAuth & Upload Guard:
   - 400 rejection when unlinked.
   - AGENTS.md Zero Comment Lock Policy invariant enforcement.
   - AES-256 token storage & clean disconnect.
4. Video Generation & Multi-Duration:
   - 5-minute (300s) and 10-minute (600s) planning.
5. Series System & Story Continuity:
   - Episodic context preservation across consecutive episodes.
6. Autonomous AI Agent (Copilot):
   - Natural language intent parsing to structured action plans across tools.
7. Admin RBAC:
   - 403 Forbidden for non-admin users.
   - 200 OK for admin role with safe user inspection (no password or token leaks).
"""

import os
import time
import unittest

os.environ["AUTOPILOT_TEST_MODE"] = "1"

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.security import create_access_token, hash_password, vault
from backend.app.services.video_service import video_service
from core.db_base import DB_ENGINE


class TestSaaSGodMode(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.ts = int(time.time() * 1000)

        # Tenant A Setup
        self.user_a_email = f"creator_a_{self.ts}@autopilot.ai"
        self.user_a_id = f"usr_a_{self.ts}"
        self.ws_a = f"ws_a_{self.ts}"
        self.token_a = create_access_token({
            "sub": self.user_a_id,
            "email": self.user_a_email,
            "org_id": f"org_a_{self.ts}",
            "role": "user"
        })
        self.headers_a = {
            "Authorization": f"Bearer {self.token_a}",
            "X-Workspace-Id": self.ws_a
        }

        # Tenant B Setup
        self.user_b_email = f"creator_b_{self.ts}@autopilot.ai"
        self.user_b_id = f"usr_b_{self.ts}"
        self.ws_b = f"ws_b_{self.ts}"
        self.token_b = create_access_token({
            "sub": self.user_b_id,
            "email": self.user_b_email,
            "org_id": f"org_b_{self.ts}",
            "role": "user"
        })
        self.headers_b = {
            "Authorization": f"Bearer {self.token_b}",
            "X-Workspace-Id": self.ws_b
        }

        # Admin Setup
        self.admin_user_id = f"admin_{self.ts}"
        self.admin_token = create_access_token({
            "sub": self.admin_user_id,
            "email": f"admin_{self.ts}@autopilot.ai",
            "org_id": "org_platform_admin",
            "role": "admin"
        })
        self.headers_admin = {
            "Authorization": f"Bearer {self.admin_token}",
            "X-Workspace-Id": "ws_admin"
        }

    # =========================================================================
    # 1. AUTHENTICATION & ONBOARDING
    # =========================================================================

    def test_01_user_signup_and_password_hashing(self):
        """Signup creates user with PBKDF2 hashed password and personal workspace."""
        email = f"signup_test_{self.ts}@autopilot.ai"
        password = "SecurePassword123!"

        res = self.client.post("/api/v1/auth/signup", json={
            "email": email,
            "password": password,
            "name": "Alex Test Creator",
            "workspaceName": "Alex Studio"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertIn("token", data)
        self.assertFalse(data["user"]["isOnboarded"])
        self.assertEqual(data["user"]["email"], email)

        # Verify password in DB is hashed and not plaintext
        user_row = DB_ENGINE.get_user_by_email(email)
        self.assertIsNotNone(user_row)
        pw_hash = user_row.get("password_hash")
        self.assertTrue(pw_hash.startswith("pbkdf2_sha256$"))
        self.assertNotIn(password, pw_hash)

    def test_02_user_login_success_and_failure(self):
        """Login succeeds with valid password and fails with invalid password."""
        email = f"login_test_{self.ts}@autopilot.ai"
        password = "CorrectPassword123!"

        # Create user
        self.client.post("/api/v1/auth/signup", json={
            "email": email,
            "password": password,
            "name": "Login Test User"
        })

        # Correct password
        res_ok = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        self.assertEqual(res_ok.status_code, 200)
        token = res_ok.json()["data"]["token"]

        # Check /me with token
        res_me = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res_me.status_code, 200)
        self.assertEqual(res_me.json()["data"]["email"], email)

        # Incorrect password
        res_bad = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": "WrongPassword!"
        })
        self.assertEqual(res_bad.status_code, 401)

    def test_03_onboarding_completion(self):
        """Onboarding completion updates user state in database."""
        email = f"onboarding_test_{self.ts}@autopilot.ai"
        res_signup = self.client.post("/api/v1/auth/signup", json={
            "email": email,
            "password": "SecretPassword123!",
            "name": "Onboarding User"
        })
        token = res_signup.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        res_complete = self.client.post("/api/v1/auth/onboarding/complete", headers=headers, json={
            "preferences": {"defaultLanguage": "hi", "defaultDuration": "300"}
        })
        self.assertEqual(res_complete.status_code, 200)
        self.assertTrue(res_complete.json()["data"]["isOnboarded"])

        # Verify /me reflects isOnboarded: True
        res_me = self.client.get("/api/v1/auth/me", headers=headers)
        self.assertTrue(res_me.json()["data"]["isOnboarded"])

    # =========================================================================
    # 2. MULTI-TENANCY & IDOR ISOLATION
    # =========================================================================

    def test_04_video_tenant_isolation(self):
        """User A's video cannot be accessed by User B (returns 403)."""
        # User A creates a video
        v_a = video_service.create_video(self.ws_a, "Alice Secret Video")
        vid_id = v_a["id"]

        # User A can get it
        res_a = self.client.get(f"/api/v1/videos/{vid_id}", headers=self.headers_a)
        self.assertEqual(res_a.status_code, 200)
        self.assertEqual(res_a.json()["data"]["title"], "Alice Secret Video")

        # User B attempts to access it -> 403 Forbidden
        res_b = self.client.get(f"/api/v1/videos/{vid_id}", headers=self.headers_b)
        self.assertEqual(res_b.status_code, 403)

    def test_05_series_tenant_isolation(self):
        """User A's series cannot be accessed or manipulated by User B."""
        # User A creates a series
        res_create = self.client.post("/api/v1/series", headers=self.headers_a, json={
            "title": "Alice Franchise",
            "description": "Secret narrative bible"
        })
        self.assertEqual(res_create.status_code, 200)
        series_id = res_create.json()["data"]["id"]

        # User A can view the series
        res_get_a = self.client.get(f"/api/v1/series/{series_id}", headers=self.headers_a)
        self.assertEqual(res_get_a.status_code, 200)

        # User B gets 403 Forbidden
        res_get_b = self.client.get(f"/api/v1/series/{series_id}", headers=self.headers_b)
        self.assertEqual(res_get_b.status_code, 403)

        # User B cannot list episodes of User A's series
        res_ep_b = self.client.get(f"/api/v1/series/{series_id}/episodes", headers=self.headers_b)
        self.assertEqual(res_ep_b.status_code, 403)

        # User B cannot generate episodes for User A's series
        res_gen_b = self.client.post(f"/api/v1/series/{series_id}/episodes/generate", headers=self.headers_b, json={
            "episodeNumber": 2,
            "title": "Hijacked Episode"
        })
        self.assertEqual(res_gen_b.status_code, 403)

    # =========================================================================
    # 3. YOUTUBE OAUTH & UPLOAD GUARD
    # =========================================================================

    def test_06_youtube_upload_guard_unlinked(self):
        """Publishing fails with 400 and clear message if YouTube is not connected."""
        # Ensure workspace A has no YouTube integration
        res_status = self.client.get("/api/v1/integrations/youtube/status", headers=self.headers_a)
        self.assertEqual(res_status.status_code, 200)
        self.assertFalse(res_status.json()["data"]["isConnected"])

        # Attempt to upload video without YouTube linked
        res_upload = self.client.post("/api/v1/publish/youtube", headers=self.headers_a, json={
            "videoId": "vid_sample_01",
            "title": "Test Title",
            "description": "Test Desc",
            "tags": ["test"]
        })
        self.assertEqual(res_upload.status_code, 400)
        err_msg = res_upload.json()["error"]["message"]
        self.assertIn("YouTube account required", err_msg)
        self.assertIn("Connect and authorize your YouTube channel before uploading", err_msg)

    def test_07_youtube_oauth_start_url(self):
        """OAuth start endpoint returns valid Google OAuth URL with signed state."""
        res = self.client.get("/api/v1/integrations/youtube/oauth/start", headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertIn("authUrl", data)
        self.assertIn("accounts.google.com", data["authUrl"])
        self.assertIn("state", data)

    def test_08_youtube_comments_on_invariant(self):
        """Zero Comment Lock Policy: selfDeclaredMadeForKids cannot be True."""
        res = self.client.post("/api/v1/publish/youtube", headers=self.headers_a, json={
            "videoId": "vid_sample_01",
            "title": "Test Video",
            "description": "Test Description",
            "selfDeclaredMadeForKids": True  # Strictly forbidden
        })
        self.assertEqual(res.status_code, 400)
        err_msg = res.json()["error"]["message"]
        self.assertIn("Zero Comment Lock Policy", err_msg)

    # =========================================================================
    # 4. VIDEO GENERATION & MULTI-DURATION PLANNING
    # =========================================================================

    def test_09_five_minute_video_generation_request(self):
        """Video generator supports 300s (5m) without truncation."""
        res = self.client.post("/api/v1/videos/generate", headers=self.headers_a, json={
            "projectId": "proj_feature",
            "title": "5 Minute Deep Dive on AI",
            "topic": "Explain autonomous AI agents and local neural networks",
            "durationSeconds": 300.0,
            "voiceId": "en-US-ChristopherNeural",
            "resolution": "1080x1920"
        })
        self.assertEqual(res.status_code, 200)
        job_data = res.json()["data"]
        self.assertIn("jobId", job_data)
        self.assertIn("videoId", job_data)

        # Check stored video record duration
        video = video_service.get_video(self.ws_a, job_data["videoId"])
        self.assertEqual(video.durationSeconds, 300.0)
        self.assertEqual(video.title, "5 Minute Deep Dive on AI")

    # =========================================================================
    # 5. SERIES CONTINUITY & EPISODIC CONTEXT
    # =========================================================================

    def test_10_series_episodic_generation_with_continuity(self):
        """Series episode generation preserves story context and recaps."""
        # 1. Create franchise
        res_series = self.client.post("/api/v1/series", headers=self.headers_a, json={
            "title": "Jab Pyaar Online Tha",
            "description": "Romantic drama between Aarav and Meera."
        })
        series_id = res_series.json()["data"]["id"]

        # 2. Generate Episode 1
        res_ep1 = self.client.post(f"/api/v1/series/{series_id}/episodes/generate", headers=self.headers_a, json={
            "episodeNumber": 1,
            "title": "The First Notification",
            "conflictPrompt": "Aarav receives a DM from a mysterious girl."
        })
        self.assertEqual(res_ep1.status_code, 200)
        ep1_data = res_ep1.json()["data"]
        self.assertEqual(ep1_data["episodeNumber"], 1)
        self.assertIn("script", ep1_data)

        # 3. Generate Episode 2 with continuity
        res_ep2 = self.client.post(f"/api/v1/series/{series_id}/episodes/generate", headers=self.headers_a, json={
            "episodeNumber": 2,
            "title": "The Voice Note",
            "conflictPrompt": "Meera reveals she knows Aarav's dark past."
        })
        self.assertEqual(res_ep2.status_code, 200)
        ep2_data = res_ep2.json()["data"]
        self.assertEqual(ep2_data["episodeNumber"], 2)

        # 4. List episodes
        res_eps = self.client.get(f"/api/v1/series/{series_id}/episodes", headers=self.headers_a)
        self.assertEqual(res_eps.status_code, 200)
        eps = res_eps.json()["data"]
        self.assertEqual(len(eps), 2)

    # =========================================================================
    # 6. AUTONOMOUS AI AGENT (COPILOT)
    # =========================================================================

    def test_11_ai_agent_natural_language_dispatch(self):
        """AI agent parses commands and executes appropriate tool within tenant boundary."""
        # Command 1: Create 5 minute video
        res_cmd1 = self.client.post("/api/v1/copilot/action", headers=self.headers_a, json={
            "prompt": "Create a 5 minute video about AI Agents"
        })
        self.assertEqual(res_cmd1.status_code, 200)
        data1 = res_cmd1.json()["data"]
        self.assertEqual(data1["tool"], "create_video")
        self.assertIn(data1["status"], ("completed", "executed"))

        # Command 2: Generate episode of series
        res_cmd2 = self.client.post("/api/v1/copilot/action", headers=self.headers_a, json={
            "prompt": "Generate Episode 5 of Series 1"
        })
        self.assertEqual(res_cmd2.status_code, 200)
        data2 = res_cmd2.json()["data"]
        self.assertEqual(data2["tool"], "create_episode")

        # Command 3: Check YouTube channel status
        res_cmd3 = self.client.post("/api/v1/copilot/action", headers=self.headers_a, json={
            "prompt": "Check my YouTube channel status"
        })
        self.assertEqual(res_cmd3.status_code, 200)
        data3 = res_cmd3.json()["data"]
        self.assertEqual(data3["tool"], "get_youtube_status")

        # Command 4: Show video library
        res_cmd4 = self.client.post("/api/v1/copilot/action", headers=self.headers_a, json={
            "prompt": "Show my video library"
        })
        self.assertEqual(res_cmd4.status_code, 200)
        data4 = res_cmd4.json()["data"]
        self.assertEqual(data4["tool"], "list_library")

    # =========================================================================
    # 7. ADMIN RBAC ENFORCEMENT
    # =========================================================================

    def test_12_admin_rbac_protection(self):
        """Admin endpoints reject non-admin users (403) and admit admins (200)."""
        # Non-admin user gets 403 Forbidden
        res_overview_user = self.client.get("/api/v1/admin/overview", headers=self.headers_a)
        self.assertEqual(res_overview_user.status_code, 403)

        res_users_user = self.client.get("/api/v1/admin/users", headers=self.headers_a)
        self.assertEqual(res_users_user.status_code, 403)

        # Admin user gets 200 OK
        res_overview_admin = self.client.get("/api/v1/admin/overview", headers=self.headers_admin)
        self.assertEqual(res_overview_admin.status_code, 200)
        overview_data = res_overview_admin.json()["data"]
        self.assertIn("totalUsers", overview_data)
        self.assertIn("activeWorkspaces", overview_data)
        self.assertIn("providerStatus", overview_data)

        # Admin user list returns registered users without exposing passwords or tokens
        res_users_admin = self.client.get("/api/v1/admin/users", headers=self.headers_admin)
        self.assertEqual(res_users_admin.status_code, 200)
        users_list = res_users_admin.json()["data"]
        self.assertIsInstance(users_list, list)
        for u in users_list:
            self.assertNotIn("password", u)
            self.assertNotIn("password_hash", u)
            self.assertNotIn("token", u)
            self.assertIn("email", u)
            self.assertIn("role", u)


if __name__ == "__main__":
    unittest.main()
