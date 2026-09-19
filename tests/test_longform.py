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


if __name__ == "__main__":
    unittest.main()
