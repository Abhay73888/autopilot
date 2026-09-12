"""
PHASE 4 - ANALYTICS LOOP & SCIENTIST OPTIMIZATION TESTS
Tests:
- Scheduled poller: quota-aware YouTube Analytics poller respects 10,000 unit limit.
- Metrics feed into Scientist recommendations per workspace.
- Analytics overview endpoint returns aggregated metrics.
"""

import time
import unittest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.security import create_access_token
from backend.app.services.analytics_service import PROJECT_DAILY_QUOTA_LIMIT, analytics_service


class TestAnalyticsLoop(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.ts = int(time.time() * 1000)
        self.user_id = f"usr_test_{self.ts}"
        self.ws_id = f"ws_analytics_{self.ts}"
        self.token = create_access_token({"sub": self.user_id, "email": f"test_{self.ts}@example.com", "org_id": f"org_{self.user_id}"})
        self.headers = {"Authorization": f"Bearer {self.token}", "X-Workspace-Id": self.ws_id}

    def test_analytics_overview(self):
        res = self.client.get("/api/v1/analytics/overview?timeframe=30d", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertEqual(data["workspaceId"], self.ws_id)
        self.assertIn("totalViews", data)
        self.assertIn("avgRetentionPercent", data)
        self.assertIn("topPerformingHook", data)
        self.assertIn("projectQuotaRemaining", data)

    def test_scientist_recommendations(self):
        res = self.client.get("/api/v1/analytics/scientist/recommendations", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        recs = res.json()["data"]
        self.assertGreaterEqual(len(recs), 2)
        categories = [r["category"] for r in recs]
        self.assertIn("hook_optimization", categories)
        self.assertIn("scene_pacing", categories)

    def test_quota_aware_polling_loop(self):
        # 1. Connect a test channel
        self.client.post("/api/v1/publish/channels/connect", json={
            "platform": "youtube",
            "channelId": f"UC_poller_{self.ts}",
            "channelName": "Test Poller Channel",
            "token": "ya29.sample_oauth_token"
        }, headers=self.headers)

        # 2. Trigger poll
        res = self.client.post("/api/v1/analytics/poll", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        poll_data = res.json()["data"]
        self.assertEqual(poll_data["status"], "success")
        self.assertIn(f"UC_poller_{self.ts}", poll_data["channelsPolled"])
        self.assertLessEqual(poll_data["projectQuotaRemaining"], PROJECT_DAILY_QUOTA_LIMIT)

    def test_quota_exhaustion_backoff(self):
        # Temporarily simulate exhausted project quota
        prev = analytics_service._daily_project_quota_used
        try:
            analytics_service._daily_project_quota_used = PROJECT_DAILY_QUOTA_LIMIT
            res = self.client.post("/api/v1/analytics/poll", headers=self.headers)
            self.assertEqual(res.status_code, 200)
            data = res.json()["data"]
            self.assertEqual(data["status"], "quota_exhausted")
            self.assertIn("limit reached", data["message"].lower())
        finally:
            analytics_service._daily_project_quota_used = prev


if __name__ == "__main__":
    unittest.main()
