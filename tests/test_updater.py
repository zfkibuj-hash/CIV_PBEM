"""Tests for GitHub self-update helpers."""
import unittest

from src.updater import (
    is_newer,
    parse_version,
    pick_exe_asset,
    release_info_from_payload,
    should_offer_update,
)


class VersionCompareTests(unittest.TestCase):
    def test_parse_strips_v(self):
        self.assertEqual(parse_version("v5.0.12"), (5, 0, 12))
        self.assertEqual(parse_version("5.0.13"), (5, 0, 13))

    def test_is_newer(self):
        self.assertTrue(is_newer("5.0.13", "5.0.12"))
        self.assertTrue(is_newer("v5.1.0", "5.0.99"))
        self.assertFalse(is_newer("5.0.12", "5.0.12"))
        self.assertFalse(is_newer("5.0.11", "5.0.12"))
        self.assertTrue(is_newer("5.0.12", "5.0"))


class AssetPickTests(unittest.TestCase):
    def test_prefers_civ4_name(self):
        assets = [
            {"name": "other.exe", "browser_download_url": "http://x/other.exe"},
            {
                "name": "Civ4PBEMManager.exe",
                "browser_download_url": "http://x/Civ4PBEMManager.exe",
                "size": 10,
            },
        ]
        picked = pick_exe_asset(assets)
        self.assertEqual(picked["name"], "Civ4PBEMManager.exe")

    def test_first_exe_fallback(self):
        assets = [
            {"name": "notes.txt", "browser_download_url": "http://x/n"},
            {"name": "App.exe", "browser_download_url": "http://x/App.exe"},
        ]
        picked = pick_exe_asset(assets)
        self.assertEqual(picked["name"], "App.exe")

    def test_none_without_exe(self):
        self.assertIsNone(pick_exe_asset([{"name": "a.zip", "browser_download_url": "u"}]))


class ShouldOfferTests(unittest.TestCase):
    def _release(self, version: str):
        return release_info_from_payload({
            "tag_name": f"v{version}",
            "name": f"v{version}",
            "body": "notes",
            "html_url": "https://example.com",
            "assets": [{
                "name": "Civ4PBEMManager.exe",
                "browser_download_url": "https://example.com/a.exe",
                "size": 1,
            }],
        })

    def test_offers_newer(self):
        rel = self._release("5.0.13")
        self.assertTrue(should_offer_update(rel, "5.0.12", ""))

    def test_skips_same_skipped_version(self):
        rel = self._release("5.0.13")
        self.assertFalse(should_offer_update(rel, "5.0.12", "5.0.13"))
        self.assertFalse(should_offer_update(rel, "5.0.12", "v5.0.13"))

    def test_offers_again_when_even_newer(self):
        rel = self._release("5.0.14")
        self.assertTrue(should_offer_update(rel, "5.0.12", "5.0.13"))

    def test_no_offer_when_current(self):
        rel = self._release("5.0.12")
        self.assertFalse(should_offer_update(rel, "5.0.12", ""))


if __name__ == "__main__":
    unittest.main()
