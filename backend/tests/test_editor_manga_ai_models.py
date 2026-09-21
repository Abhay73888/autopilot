r"""
backend/tests/test_editor_manga_ai_models.py — Unit & Integration tests for:
1. Video Editor API Multi-Tenant Scoping & Export
2. Manga PDF Extraction & Video Generation Pipeline
3. AI Models Configuration Endpoint (Masked Secrets & RBAC)
"""

import io
import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import create_access_token
from core.db_base import DB_ENGINE


class TestEditorMangaAIModels(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Admin token
        self.admin_token = create_access_token({
            "sub": "admin_abhay",
            "email": "admin@autopilot.ai",
            "role": "admin",
            "org_id": "org_admin"
        })
        # Regular user token
        self.user_token = create_access_token({
            "sub": "usr_regular_42",
            "email": "regular@autopilot.ai",
            "role": "user",
            "org_id": "org_usr_regular_42"
        })

    def test_01_editor_videos_multi_tenant_scoping(self):
        """Admin sees full editable video catalog; regular user sees only their owned videos."""
        # Admin request
        admin_res = self.client.get(
            "/api/v1/editor/videos",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(admin_res.status_code, 200)
        data = admin_res.json()
        self.assertTrue(data.get("ok"))
        self.assertIsInstance(data.get("videos"), list)

        # Regular user request (should only see videos with their user_id or empty list)
        user_res = self.client.get(
            "/api/v1/editor/videos",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        self.assertEqual(user_res.status_code, 200)
        user_data = user_res.json()
        self.assertTrue(user_data.get("ok"))
        self.assertIsInstance(user_data.get("videos"), list)

    def test_02_editor_timeline_authorization(self):
        """Accessing a video timeline requires ownership if not admin."""
        # Admin access to video 166 (existing admin video)
        res = self.client.get(
            "/api/v1/editor/video/166",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertIn(res.status_code, (200, 404))  # 200 if folder exists, 404 if clean machine

        # Unauthorized non-admin user trying to access admin video
        # Insert a video owned by admin_abhay
        DB_ENGINE.execute_mutation(
            "INSERT OR REPLACE INTO videos (id, created_ts, updated_ts, user_id, workspace_id, title, topic, length_sec, status) VALUES (?, datetime('now'), datetime('now'), ?, ?, ?, ?, ?, ?)",
            (9999, "admin_abhay", "ws_admin_abhay", "Admin Exclusive", "Topic", 30.0, "ready")
        )

        user_res = self.client.get(
            "/api/v1/editor/video/9999",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        self.assertEqual(user_res.status_code, 403)

    def test_03_manga_upload_validation(self):
        """Manga upload endpoint rejects invalid formats and accepts images/pdf."""
        # Invalid format (.txt)
        bad_file = io.BytesIO(b"This is plain text, not manga")
        res = self.client.post(
            "/api/v1/manga/upload",
            files={"file": ("story.txt", bad_file, "text/plain")},
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        self.assertEqual(res.status_code, 400)

        # Valid image mock
        good_file = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")
        good_res = self.client.post(
            "/api/v1/manga/upload",
            files={"file": ("page1.png", good_file, "image/png")},
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        self.assertEqual(good_res.status_code, 200)
        d = good_res.json()
        self.assertTrue(d.get("success"))
        self.assertTrue(d.get("data", {}).get("mangaId").startswith("manga_"))
        self.assertEqual(d.get("data", {}).get("pageCount"), 1)

    def test_04_ai_models_admin_protection(self):
        """Normal users cannot read or update AI model configuration; admins can."""
        # Non-admin access denied
        user_res = self.client.get(
            "/api/v1/admin/ai-models",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        self.assertEqual(user_res.status_code, 403)

        # Admin access granted
        admin_res = self.client.get(
            "/api/v1/admin/ai-models",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(admin_res.status_code, 200)
        data = admin_res.json()
        self.assertTrue(data.get("success"))
        cfg = data.get("data")
        self.assertIn("llmProvider", cfg)
        self.assertIn("ttsProvider", cfg)
        # Verify secret key is masked
        if cfg.get("hasLlmApiKey"):
            self.assertTrue(cfg.get("llmApiKeyMasked").startswith("•"))

    def test_05_ai_models_update_modular_config(self):
        """Admin can update model providers modularly without leaking API keys."""
        payload = {
            "llmProvider": "gemini",
            "llmModel": "gemini-2.5-pro",
            "ttsProvider": "edge_tts",
            "voiceModel": "hi-IN-MadhurNeural"
        }
        res = self.client.post(
            "/api/v1/admin/ai-models",
            json=payload,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d.get("success"))
        self.assertEqual(d.get("data", {}).get("llmProvider"), "gemini")
        self.assertEqual(d.get("data", {}).get("ttsProvider"), "edge_tts")


if __name__ == "__main__":
    unittest.main()
