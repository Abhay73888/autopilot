"""
tests/test_copilot_reference_video.py — Integration Tests for AI Copilot Dual-Reference Video Generation
"""

import asyncio
import os
import unittest
from backend.app.schemas.copilot import CopilotChatRequest, CopilotExecuteRequest
from backend.app.services.copilot_service import copilot_service
from pipeline.reference_video_engine import reference_video_engine


from unittest.mock import patch, MagicMock
from pathlib import Path


class TestCopilotReferenceVideo(unittest.TestCase):
    def setUp(self):
        self.workspace_id = "ws_admin_abhay"
        self.render_patcher = patch(
            "pipeline.reference_video_engine.ReferenceVideoEngine.render_half_body_cinematic_video",
            return_value=Path(r"output/reference_renders/mock_test_video.mp4")
        )
        self.mock_render = self.render_patcher.start()

    def tearDown(self):
        self.render_patcher.stop()

    def test_01_generate_model_prompt_constraints(self):
        """Verify model prompt generation enforces half-body, character scale, and role separation."""
        prompt_data = reference_video_engine.generate_model_prompt(
            character_name="Muzan Kibutsuji",
            composition="half_body",
            character_scale_cm=1.75,
            aspect_ratio="16:9"
        )
        
        # 1. Role Separation
        self.assertIn("media_1790011617379.png", prompt_data["character_identity_reference"])
        self.assertIn("GOD_LEVEL_MUZAN_D_ANIME_REFER.mp4", prompt_data["motion_camera_reference_video"])
        
        # 2. Positive prompt constraints
        pos = prompt_data["positive_prompt"].lower()
        self.assertIn("chest and waist upward", pos)
        self.assertIn("only his upper half body is visible", pos)
        self.assertIn("1.75cm", pos)
        self.assertIn("push-in", pos)
        self.assertIn("dark crimson and obsidian aura", pos)
        
        # 3. Negative prompt constraints (Legs, feet, full body must be strictly excluded)
        neg = prompt_data["negative_prompt"].lower()
        self.assertIn("full body", neg)
        self.assertIn("legs", neg)
        self.assertIn("feet", neg)
        self.assertIn("lower body", neg)

    def test_02_copilot_process_command_dual_reference(self):
        """Verify process_command detects dual reference intent and produces action plan."""
        cmd = "Use this Muzan image and this video as reference. Make only half body visible."
        req = CopilotExecuteRequest(command=cmd)
        plan = copilot_service.process_command(self.workspace_id, req)
        
        self.assertEqual(plan.intent, "DUAL_REFERENCE_VIDEO_GENERATION")
        self.assertEqual(plan.tool, "generate_reference_video")
        self.assertIsNotNone(plan.video_model_instruction)
        self.assertIn("Muzan Kibutsuji", plan.summary)
        
        res = plan.result or {}
        self.assertTrue(res.get("videoId", "").startswith("vid_muzan_"))
        self.assertIsNotNone(res.get("videoUrl"))

    def test_03_copilot_chat_natural_language_dispatch(self):
        """Verify copilot chat natural language command returns formatted model prompt and instruction."""
        async def run_chat():
            req = CopilotChatRequest(
                message="Keep the camera movement and effects from reference video with chest upward framing for Muzan.",
                language="en",
                generate_speech=False
            )
            return await copilot_service.chat(self.workspace_id, req, user_id="admin_abhay", role="admin")

        res = asyncio.run(run_chat())
        self.assertEqual(res.intent, "DUAL_REFERENCE_VIDEO_GENERATION")
        self.assertEqual(res.tool, "generate_reference_video")
        self.assertIsNotNone(res.video_model_instruction)
        self.assertIn("Half-Body Only", res.reply)
        self.assertIn("Production Video Model Prompt", res.reply)


    def test_04_character_swap_workflow(self):
        """Verify character swap detection and prompt synthesis for generate_the_again_and_i_want.mp4."""
        cmd = "us baddhe se character ko hata kr is type character ko integrate kr do yrr"
        req = CopilotExecuteRequest(command=cmd)
        plan = copilot_service.process_command(self.workspace_id, req)
        
        self.assertEqual(plan.intent, "CHARACTER_IDENTITY_SWAP")
        self.assertEqual(plan.tool, "generate_character_swap")
        self.assertIsNotNone(plan.video_model_instruction)
        self.assertEqual(plan.video_model_instruction["workflow"], "CHARACTER_IDENTITY_SWAP")
        self.assertIn("generate_the_again_and_i_want.mp4", plan.video_model_instruction["motion_camera_reference_video"])
        self.assertIn("Muzan Kibutsuji", plan.video_model_instruction["positive_prompt"])
        self.assertIn("Replace the existing character", plan.video_model_instruction["positive_prompt"])
        
        res = plan.result or {}
        self.assertTrue(res.get("swapWorkflow"))
        self.assertTrue(res.get("sourceCharacterRemoved"))
        self.assertEqual(res.get("targetCharacter"), "Muzan Kibutsuji")


    def test_05_copilot_chat_character_swap_natural_language(self):
        """Verify chat natural language triggers character swap workflow and returns Hindi reply."""
        async def run_chat():
            req = CopilotChatRequest(
                message="us baddhe se character ko hata kr is type character ko integrate kr do yrr",
                language="hi",
                generate_speech=False
            )
            return await copilot_service.chat(self.workspace_id, req, user_id="admin_abhay", role="admin")

        res = asyncio.run(run_chat())
        self.assertEqual(res.intent, "CHARACTER_IDENTITY_SWAP")
        self.assertEqual(res.tool, "generate_character_swap")
        self.assertIsNotNone(res.video_model_instruction)
        self.assertIn("मुज़ान", res.reply)
        self.assertIn("हाफ-बॉडी", res.reply)


if __name__ == "__main__":
    unittest.main()


