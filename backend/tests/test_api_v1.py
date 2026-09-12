r"""
backend/tests/test_api_v1.py — Automated Integration & Endpoint Test Suite
"""

import unittest
from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


class TestAutopilotApiV1(unittest.TestCase):
    def test_health_endpoints(self):
        res_live = client.get("/health/live")
        self.assertEqual(res_live.status_code, 200)
        self.assertEqual(res_live.json()["status"], "ok")

        res_ready = client.get("/health/ready")
        self.assertEqual(res_ready.status_code, 200)
        self.assertEqual(res_ready.json()["status"], "ready")

    def test_auth_and_session(self):
        res = client.post("/api/v1/auth/login", json={"email": "test@autopilot.ai", "password": "password123"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("accessToken", data["data"])

    def test_workspace_and_emergency_stop(self):
        res = client.get("/api/v1/workspaces/current")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

        stop_res = client.post("/api/v1/workspaces/current/emergency-stop")
        self.assertEqual(stop_res.status_code, 200)
        self.assertTrue(stop_res.json()["success"])

    def test_projects_crud(self):
        res = client.get("/api/v1/projects")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertGreaterEqual(len(res.json()["data"]), 1)

    def test_ideas_generation(self):
        res = client.post("/api/v1/ideas/generate", json={"count": 3, "focusKeywords": ["ai", "coding"]})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertEqual(len(res.json()["data"]), 3)

    def test_scripts_generation(self):
        res = client.post("/api/v1/scripts/generate", json={"topic": "The Offline AI Tool", "targetSeconds": 30})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertIn("hook", res.json()["data"])
        self.assertGreaterEqual(len(res.json()["data"]["scenesBreakdown"]), 1)

    def test_video_queue_and_qa(self):
        res = client.post("/api/v1/videos/generate", json={"projectId": "proj_test", "scriptId": "scp_test"})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        job_id = res.json()["data"]["jobId"]
        video_id = res.json()["data"]["videoId"]

        # Check QA report
        qa_res = client.get(f"/api/v1/videos/{video_id}/qa")
        self.assertEqual(qa_res.status_code, 200)
        self.assertTrue(qa_res.json()["success"])

    def test_copilot_command(self):
        res = client.post("/api/v1/copilot/execute", json={"command": "Show me top hook retention"})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertEqual(res.json()["data"]["intent"], "SHOW_ANALYTICS")

    def test_billing_and_credits(self):
        plans_res = client.get("/api/v1/billing/plans")
        self.assertEqual(plans_res.status_code, 200)
        self.assertEqual(len(plans_res.json()["data"]), 3)

        cred_res = client.get("/api/v1/billing/credits")
        self.assertEqual(cred_res.status_code, 200)
        self.assertIn("balance", cred_res.json()["data"])

    def test_pipeline_adapter_and_sse(self):
        from backend.app.workers.pipeline_adapter import emit_job_progress, get_job_state, register_job_listener

        test_job_id = "test_job_sse_01"
        test_video_id = "test_vid_sse_01"
        q = register_job_listener(test_job_id)

        emit_job_progress(
            test_job_id,
            test_video_id,
            status="completed",
            step="completed",
            progress=100,
            message="Completed test event"
        )

        state = get_job_state(test_job_id)
        self.assertIsNotNone(state)
        self.assertEqual(state["status"], "completed")
        self.assertEqual(state["progress"], 100)

        # Test SSE stream endpoint returns text/event-stream
        res = client.get(f"/api/v1/jobs/{test_job_id}/stream")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/event-stream", res.headers.get("content-type", ""))



if __name__ == "__main__":
    unittest.main()

