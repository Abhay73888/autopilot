"""
PHASE 5 - DEPLOYABILITY, OBSERVABILITY & ADMIN TESTS
Tests:
- GET /metrics returns jobs queued/running/failed, spend today, quota remaining.
- X-Request-ID correlation header is returned on every HTTP response.
- GET /api/v1/admin/overview returns system metrics and healthy providers.
- GET /api/v1/admin/dlq and POST /api/v1/admin/dlq/replay requeue dead-letter jobs.
"""

import unittest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.video_service import video_service


class TestObservabilityAdmin(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_request_id_correlation_header(self):
        """Responses must echo X-Request-ID and X-Response-Time headers."""
        custom_id = "req_custom_tracer_9999"
        res = self.client.get("/health", headers={"X-Request-ID": custom_id})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("X-Request-ID"), custom_id)
        self.assertIn("X-Response-Time", res.headers)

    def test_prometheus_metrics_endpoint(self):
        """Metrics endpoint returns live counters for jobs, billing, and YouTube API quota."""
        res = self.client.get("/metrics")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("jobs", data)
        self.assertIn("billing", data)
        self.assertIn("quota", data)

        self.assertIn("queued", data["jobs"])
        self.assertIn("running", data["jobs"])
        self.assertIn("failed", data["jobs"])
        self.assertIn("spendTodayUsd", data["billing"])
        self.assertIn("youtubeApiUnitsRemaining", data["quota"])

    def test_admin_overview(self):
        res = self.client.get("/api/v1/admin/overview")
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertIn("totalUsers", data)
        self.assertIn("activeWorkspaces", data)
        self.assertIn("providerStatus", data)

    def test_admin_dlq_and_replay(self):
        # 1. Create a simulated failed job in video_service
        failed_job_id = "job_failed_for_dlq_test"
        video_service._jobs[failed_job_id] = {
            "jobId": failed_job_id,
            "workspaceId": "ws_test",
            "status": "failed",
            "error": "Simulated render timeout"
        }

        # 2. Check DLQ
        dlq_res = self.client.get("/api/v1/admin/dlq")
        self.assertEqual(dlq_res.status_code, 200)
        dlq_jobs = dlq_res.json()["data"]
        self.assertTrue(any(j["jobId"] == failed_job_id for j in dlq_jobs))

        # 3. Replay from DLQ
        replay_res = self.client.post(f"/api/v1/admin/dlq/replay?job_id={failed_job_id}")
        self.assertEqual(replay_res.status_code, 200)
        replay_data = replay_res.json()["data"]
        self.assertEqual(replay_data["status"], "replayed")
        self.assertIn(failed_job_id, replay_data["replayedJobIds"])

        # 4. Verify job status was restored to queued
        self.assertEqual(video_service._jobs[failed_job_id]["status"], "queued")


if __name__ == "__main__":
    unittest.main()
