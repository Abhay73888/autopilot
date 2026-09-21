"""
Comprehensive Production Database, User Isolation, and YouTube Security Test Suite
Tests:
1. Database Integrity and Canonical Ownership Verification (Zero Fake Data)
2. Authentication & Current User Endpoint (GET /api/v1/auth/me)
3. Dashboard User-Specific Statistics (Abhay: 367 videos, 76 series vs User B: 0)
4. Multi-Tenant Video Scoping & IDOR Attack Prevention
5. Video Generation & Series Creation strictly scoped to authenticated user
6. YouTube Connection Isolation & Disconnect Protection
7. Admin Authorization & User Inspection (/api/v1/admin/users)
"""

import os
import sys
import unittest
import sqlite3
from fastapi.testclient import TestClient

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app
from backend.app.core.security import create_access_token

class TestUserIsolationAndProductionSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        
        # Verify database path
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "autopilot.db")
        cls.db_path = db_path
        assert os.path.exists(db_path), f"Production database {db_path} does not exist!"

        # Clean slate for User B in test suite
        conn = sqlite3.connect(cls.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM series WHERE user_id = 'usr_test_user_b'")
        c.execute("DELETE FROM videos WHERE user_id = 'usr_test_user_b'")
        c.execute("DELETE FROM episodes WHERE user_id = 'usr_test_user_b'")
        c.execute("DELETE FROM channel_credentials WHERE user_id = 'usr_test_user_b'")
        c.execute("DELETE FROM jobs WHERE user_id = 'usr_test_user_b'")

        # Ensure User B exists in DB for isolation tests
        c.execute("""
            INSERT OR IGNORE INTO users (user_id, email, password_hash, role, name, tier, credits, created_ts, is_onboarded)
            VALUES ('usr_test_user_b', 'user_b@autopilot.ai', '$2b$12$userbhashedpasswordplaceholder', 'creator', 'Test Creator B', 'starter', 100, '2026-03-09', 1)
        """)
        conn.commit()
        conn.close()

        # Generate tokens
        cls.token_abhay = create_access_token({
            "sub": "admin_abhay",
            "email": "shivpuran2803@gmail.com",
            "role": "admin",
            "org_id": "org_admin_abhay"
        })
        cls.token_user_b = create_access_token({
            "sub": "usr_test_user_b",
            "email": "user_b@autopilot.ai",
            "role": "creator",
            "org_id": "org_user_b"
        })

    def test_01_database_integrity_and_abhay_ownership(self):
        """Verify real production data in database has 0 orphaned records and Abhay owns all historical assets."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM videos")
        total_videos = c.fetchone()[0]
        self.assertGreaterEqual(total_videos, 367, "Must contain all 367 historical videos")

        c.execute("SELECT COUNT(*) FROM videos WHERE user_id = 'admin_abhay'")
        abhay_videos = c.fetchone()[0]
        self.assertEqual(abhay_videos, total_videos, "All videos must be owned by canonical admin_abhay")

        c.execute("SELECT COUNT(*) FROM series")
        total_series = c.fetchone()[0]
        self.assertGreaterEqual(total_series, 76, "Must contain all 76 series franchises")

        c.execute("SELECT COUNT(*) FROM episodes")
        total_episodes = c.fetchone()[0]
        self.assertGreaterEqual(total_episodes, 58, "Must contain all 58 episodes")

        c.execute("SELECT COUNT(*) FROM channel_credentials WHERE user_id = 'admin_abhay' AND platform = 'youtube'")
        abhay_yt_creds = c.fetchone()[0]
        self.assertGreaterEqual(abhay_yt_creds, 1, "Abhay must have connected YouTube credentials in database")

        conn.close()

    def test_02_auth_me_endpoint_resolves_current_user(self):
        """Verify server resolves user strictly from Authorization Bearer token."""
        # Abhay
        res_a = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {self.token_abhay}"})
        self.assertEqual(res_a.status_code, 200)
        data_a = res_a.json()["data"]
        self.assertEqual(data_a["id"], "admin_abhay")
        self.assertEqual(data_a["role"], "admin")
        self.assertEqual(data_a["email"], "shivpuran2803@gmail.com")

        # User B
        res_b = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {self.token_user_b}"})
        self.assertEqual(res_b.status_code, 200)
        data_b = res_b.json()["data"]
        self.assertEqual(data_b["id"], "usr_test_user_b")
        self.assertEqual(data_b["role"], "creator")

    def test_03_dashboard_user_isolation(self):
        """Verify Abhay sees 367 videos, 76 series, YouTube connected; User B sees 0 videos, YouTube disconnected."""
        # Abhay Dashboard
        res_a = self.client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {self.token_abhay}"})
        self.assertEqual(res_a.status_code, 200)
        d_a = res_a.json()["data"]
        stats_a = d_a["stats"]
        self.assertEqual(stats_a["total_videos"], 367)
        self.assertEqual(stats_a["total_series"], 76)
        self.assertEqual(stats_a["total_episodes"], 58)
        self.assertEqual(d_a["youtube"]["is_connected"], True)
        self.assertTrue(len(d_a["youtube"]["channel_title"]) > 0)
        self.assertGreater(len(d_a["recent_activity"]), 0)

        # User B Dashboard
        res_b = self.client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {self.token_user_b}"})
        self.assertEqual(res_b.status_code, 200)
        d_b = res_b.json()["data"]
        stats_b = d_b["stats"]
        self.assertEqual(stats_b["total_videos"], 0)
        self.assertEqual(stats_b["total_series"], 0)
        self.assertEqual(stats_b["total_episodes"], 0)
        self.assertEqual(stats_b["total_jobs"], 0)
        self.assertEqual(d_b["youtube"]["is_connected"], False)

    def test_04_idor_protection_video_access(self):
        """Verify User B cannot view or access Abhay's video records by direct ID (403 or 404)."""
        # Pick a video ID belonging to Abhay
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id FROM videos WHERE user_id = 'admin_abhay' LIMIT 1")
        abhay_video_id = c.fetchone()[0]
        conn.close()

        # Abhay can access his own video
        res_a = self.client.get(f"/api/v1/videos/{abhay_video_id}", headers={"Authorization": f"Bearer {self.token_abhay}"})
        self.assertEqual(res_a.status_code, 200)
        self.assertIn(str(res_a.json()["data"]["id"]), [str(abhay_video_id), f"vid_{abhay_video_id}"])

        # User B trying to access Abhay's video -> MUST BE 403 Forbidden or 404 Not Found
        res_b = self.client.get(f"/api/v1/videos/{abhay_video_id}", headers={"Authorization": f"Bearer {self.token_user_b}"})
        self.assertIn(res_b.status_code, [403, 404], f"IDOR Vulnerability! User B got status {res_b.status_code}")

    def test_05_series_creation_strictly_bound_to_authenticated_user(self):
        """Verify new franchise created by User B is owned by User B and invisible to Abhay's personal library."""
        # User B creates a series
        res = self.client.post("/api/v1/series", 
            headers={"Authorization": f"Bearer {self.token_user_b}"},
            json={"title": "User B Solo Anime", "description": "Independent franchise for User B"}
        )
        self.assertEqual(res.status_code, 200)
        series_id = res.json()["data"]["id"]

        # Verify in DB that series.user_id == 'usr_test_user_b'
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT user_id FROM series WHERE id = ?", (series_id,))
        owner = c.fetchone()[0]
        conn.close()
        self.assertEqual(owner, "usr_test_user_b")

        # User B lists series: contains this series
        res_b_list = self.client.get("/api/v1/series", headers={"Authorization": f"Bearer {self.token_user_b}"})
        series_ids_b = [s["id"] for s in res_b_list.json()["data"]]
        self.assertIn(series_id, series_ids_b)

        # Abhay lists series: does NOT contain User B's series
        res_a_list = self.client.get("/api/v1/series", headers={"Authorization": f"Bearer {self.token_abhay}"})
        series_ids_a = [s["id"] for s in res_a_list.json()["data"]]
        self.assertNotIn(series_id, series_ids_a)

    def test_06_youtube_isolation_and_disconnect(self):
        """Verify User B disconnecting YouTube does NOT disconnect Abhay's channel."""
        # User B checks status -> disconnected
        res_b_status = self.client.get("/api/v1/integrations/youtube/status", headers={"Authorization": f"Bearer {self.token_user_b}"})
        self.assertEqual(res_b_status.json()["data"]["isConnected"], False)

        # User B calls disconnect
        res_b_dis = self.client.post("/api/v1/integrations/youtube/disconnect", headers={"Authorization": f"Bearer {self.token_user_b}"})
        self.assertEqual(res_b_dis.status_code, 200)

        # Abhay's connection MUST REMAIN ACTIVE
        res_a_status = self.client.get("/api/v1/integrations/youtube/status", headers={"Authorization": f"Bearer {self.token_abhay}"})
        self.assertEqual(res_a_status.json()["data"]["isConnected"], True)
        self.assertTrue(len(res_a_status.json()["data"]["channelTitle"]) > 0)

    def test_07_admin_users_authorization_and_details_inspection(self):
        """Verify only Admin can access /api/v1/admin/users and inspect user details; Creator gets 403."""
        # User B (creator) -> 403 Forbidden
        res_b = self.client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {self.token_user_b}"})
        self.assertEqual(res_b.status_code, 403)

        # User B trying to inspect Abhay -> 403 Forbidden
        res_b_insp = self.client.get("/api/v1/admin/users/admin_abhay", headers={"Authorization": f"Bearer {self.token_user_b}"})
        self.assertEqual(res_b_insp.status_code, 403)

        # Abhay (admin) -> 200 OK
        res_a = self.client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {self.token_abhay}"})
        self.assertEqual(res_a.status_code, 200)
        users = res_a.json()["data"]
        self.assertGreaterEqual(len(users), 2)
        
        # Verify admin_abhay record in user list
        abhay_entry = next((u for u in users if u["id"] == "admin_abhay"), None)
        self.assertIsNotNone(abhay_entry)
        self.assertEqual(abhay_entry["video_count"], 367)
        self.assertEqual(abhay_entry["series_count"], 76)
        self.assertEqual(abhay_entry["youtube_connected"], True)

        # Abhay inspects User B details -> 200 OK
        res_a_insp = self.client.get("/api/v1/admin/users/usr_test_user_b", headers={"Authorization": f"Bearer {self.token_abhay}"})
        self.assertEqual(res_a_insp.status_code, 200)
        data_insp = res_a_insp.json()["data"]
        self.assertEqual(data_insp["profile"]["id"], "usr_test_user_b")
        self.assertEqual(data_insp["counts"]["videos"], 0)
        self.assertEqual(data_insp["youtube"]["connected"], False)

if __name__ == "__main__":
    unittest.main()
