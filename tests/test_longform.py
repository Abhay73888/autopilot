"""
tests/test_longform.py — Tests for Long-Form Video Engine (10 to 60 Minutes)
"""

import unittest
from core.config import CONFIG, get_profile


class TestLongformProfiles(unittest.TestCase):
    def test_profiles(self):
        shorts = get_profile("shorts")
        self.assertEqual(shorts["profile_name"], "shorts")
        self.assertEqual(shorts["length_sec"], 32)
        self.assertEqual(shorts["video_length_sec"], 32)
        self.assertEqual(shorts["aspect"], "9:16")
        self.assertEqual(shorts["subtitles"], "kinetic")
        self.assertFalse(shorts["chapters"])

        longform = get_profile("longform")
        self.assertEqual(longform["profile_name"], "longform")
        self.assertEqual(longform["length_sec"], 600)
        self.assertEqual(longform["video_length_sec"], 600)
        self.assertEqual(longform["aspect"], "16:9")
        self.assertEqual(longform["resolution"], "1920x1080")
        self.assertEqual(longform["subtitles"], "clean")
        self.assertTrue(longform["chapters"])
        self.assertEqual(longform["max_length_sec"], 3600)

        # Legacy top-level keys in CONFIG still work
        self.assertIn("video_length_sec", CONFIG)
        self.assertIn("resolution", CONFIG)


class TestWriterLongform(unittest.TestCase):
    def test_writer_longform(self):
        from core.db import DB
        from core.llm import LLM
        from agents.writer import Writer

        db = DB()
        llm = LLM(force_mock=True)
        writer = Writer(db=db, llm=llm)

        script = writer.write_longform("The Mystery of Room 404", total_sec=600)

        # Assertions
        chapters = script.get("chapters", [])
        self.assertGreaterEqual(len(chapters), 6, f"Expected >= 6 chapters, got {len(chapters)}")

        # Verify cumulative monotonic start_sec
        self.assertEqual(chapters[0]["start_sec"], 0.0)
        for i in range(1, len(chapters)):
            self.assertGreater(chapters[i]["start_sec"], chapters[i-1]["start_sec"])

        # Verify word count within +/- 15% of 600 * 2.6 = 1560
        target = 600 * 2.6
        wc = script.get("word_count", 0)
        self.assertGreaterEqual(wc, target * 0.85, f"Word count {wc} below 85% of {target}")
        self.assertLessEqual(wc, target * 1.15, f"Word count {wc} above 115% of {target}")

        # Verify script dict shape
        self.assertTrue(script.get("title"))
        self.assertTrue(script.get("hook_line"))
        self.assertTrue(script.get("hook_text_overlay"))
        self.assertTrue(script.get("comment_bait"))
        self.assertTrue(len(script.get("lines", [])) > 0)
        self.assertEqual(script["lines"][0]["role"], "hook")
        self.assertEqual(script["lines"][-1]["role"], "ending")


class TestArtDirectorScaling(unittest.TestCase):
    def test_artdirector_scaling(self):
        from core.db import DB
        from core.llm import LLM
        from agents.artdirector import ArtDirector

        db = DB()
        llm = LLM(force_mock=True)
        art = ArtDirector(db=db, llm=llm)

        script_600 = {
            "target_length_sec": 600,
            "profile": "longform",
            "lines": [{"speaker": "narrator", "text": f"Line {i} of longform narration."} for i in range(150)],
            "hook_line": "Opening hook line.",
            "ending": "Closing ending line."
        }

        plan_res = art.plan(script_600)
        n_scenes = plan_res.get("n_scenes") or len(plan_res.get("scenes", []))

        # Assertions: 600s with 6.0 sec/scene -> 100 scenes, definitely not clamped at 8!
        self.assertGreater(n_scenes, 20, f"Expected >20 scenes for 600s, got {n_scenes} (was clamped!)")
        self.assertAlmostEqual(n_scenes, 100, delta=10)
        self.assertTrue(plan_res.get("character"))
        self.assertTrue(plan_res.get("scenes"))


class TestStockFootageProvider(unittest.TestCase):
    def test_stock_footage_fallback(self):
        from agents.stockfootage import StockFootageProvider
        provider = StockFootageProvider(pexels_key="", pixabay_key="")
        self.assertFalse(provider.has_keys)

        # Keyword extraction check
        kw = provider.extract_keywords("Cinematic wide shot of an ancient abandoned temple in dense dark misty forest, vertical 9:16, no text")
        self.assertTrue(len(kw) > 0)
        self.assertNotIn("vertical", kw.lower())
        self.assertNotIn("text", kw.lower())

        # Graceful fallback: without keys, get_b_roll returns None
        b_roll = provider.get_b_roll({"beat": "ancient temple discover", "image_prompt": "temple in woods"})
        self.assertIsNone(b_roll)

        # Manifest assignment marks eligible scenes as type="image" when no keys are available
        scenes = [{"n": 1, "beat": "hook"}, {"n": 2, "beat": "b-roll nature"}, {"n": 3, "beat": "climax"}]
        updated = provider.assign_manifest_scenes(scenes)
        self.assertEqual(len(updated), 3)
        self.assertTrue(all(sc["type"] == "image" for sc in updated))


class TestVoiceChunkedTTS(unittest.TestCase):
    def test_voice_chunking(self):
        from agents.voice import split_sentences, chunk_text, chunk_lines

        long_sample = (
            "Yeh pehla hissa hai kahani ka jo bahut gehra hai. "
            "Kya aapne kabhi socha tha ki aisi jagah bhi ho sakti hai? "
            "Raat ke 3 baje darwaze apne aap khul gaye! "
            "Aur fir ek aisi aawaz aayi jisne sabko khauf mein daal diya।"
        )
        sentences = split_sentences(long_sample)
        self.assertGreaterEqual(len(sentences), 4)

        # Chunk with a small max_chars to verify splitting
        chunks = chunk_text(long_sample, max_chars=80)
        self.assertGreater(len(chunks), 1)
        for ch in chunks:
            self.assertLessEqual(len(ch), 80)

        # Test chunk_lines
        lines_input = [
            {"speaker": "narrator", "text": "Short line 1."},
            {"speaker": "narrator", "text": "Very long text. " * 30},
        ]
        result_chunks = chunk_lines(lines_input, max_chars=120)
        self.assertGreater(len(result_chunks), 2)
        for r in result_chunks:
            self.assertLessEqual(len(r["text"]), 120)

    def test_voice_narrate_chunked_mock(self):
        import os
        import tempfile
        import shutil
        from agents.voice import Voice

        os.environ["AUTOPILOT_MOCK_MODE"] = "true"
        td = tempfile.mkdtemp(prefix="test_voice_chunked_")
        try:
            v = Voice()
            lines = [
                {"speaker": "narrator", "text": f"Chapter narration line {i}. A strange phenomenon occurred here."}
                for i in range(15)
            ]
            res = v.narrate_chunked(lines, td)
            self.assertTrue(os.path.exists(res["audio_path"]))
            self.assertGreater(res["duration_sec"], 0)
            self.assertGreater(len(res["lines"]), 0)
            self.assertGreater(len(res["words"]), 0)
            # Verify cumulative word timing is monotonic
            words = res["words"]
            for i in range(len(words) - 1):
                self.assertLessEqual(words[i]["start"], words[i]["end"])
                self.assertLessEqual(words[i]["start"], words[i + 1]["start"])
        finally:
            shutil.rmtree(td, ignore_errors=True)


class TestRenderBatching(unittest.TestCase):
    def test_render_batching(self):
        from unittest.mock import patch, MagicMock
        from pathlib import Path
        import tempfile
        import shutil
        from pipeline.render import Renderer

        td = Path(tempfile.mkdtemp(prefix="test_batch_render_"))
        try:
            fake_manifest = {
                "render_spec": {"resolution": "1920x1080", "fps": 30, "crf": 21},
                "scenes": [{"n": i + 1, "dur": 6.0, "motion": "pan_left", "path": str(td / f"dummy_{i}.jpg")} for i in range(40)]
            }
            renderer = Renderer(fake_manifest)

            # Create 40 fake clip files
            fake_clips = []
            for i in range(40):
                c_path = td / f"clip_{i:04d}.mp4"
                c_path.write_bytes(b"dummy clip content")
                fake_clips.append(c_path)

            scenes = fake_manifest["scenes"]
            out_file = td / "video_silent.mp4"

            run_calls = []
            def fake_run(cmd, **kw):
                run_calls.append(cmd)
                target = cmd[-1]
                Path(target).write_bytes(b"dummy output mp4")
                return MagicMock(returncode=0)

            with patch("pipeline.render.run", side_effect=fake_run):
                renderer._concat_xfade_batched(fake_clips, scenes, out_file, preset="ultrafast", checkpoint_dir=td, resume=False)

            # 40 clips / batch size 8 = 5 segments
            segment_xfade_calls = [c for c in run_calls if "-filter_complex" in c]
            self.assertEqual(len(segment_xfade_calls), 5, f"Expected 5 segment xfades, got {len(segment_xfade_calls)}")
            for call in segment_xfade_calls:
                input_count = sum(1 for arg in call if arg == "-i")
                self.assertLessEqual(input_count, 8, f"Segment xfade exceeded batch limit of 8: had {input_count} inputs")

            # Final call must use concat DEMUXER (-f concat -safe 0 ... -c copy)
            final_calls = [c for c in run_calls if "-f" in c and "concat" in c and "-c" in c and "copy" in c]
            self.assertTrue(len(final_calls) >= 1, "Final join did not use concat demuxer (-c copy)!")
            self.assertIn(str(out_file), final_calls[-1])
        finally:
            shutil.rmtree(td, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
