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


if __name__ == "__main__":
    unittest.main()
