import unittest
from unittest.mock import MagicMock, patch
import json

# Define the logic to test (extracted from settings.py)
def is_newer(v_latest, v_current):
    try:
        l_parts = [int(p) for p in v_latest.split('.')]
        c_parts = [int(p) for p in v_current.split('.')]
        max_len = max(len(l_parts), len(c_parts))
        l_parts += [0] * (max_len - len(l_parts))
        c_parts += [0] * (max_len - len(c_parts))
        return l_parts > c_parts
    except:
        return v_latest > v_current

def find_exe_asset(data):
    assets = data.get("assets", [])
    exe_download_url = data.get("html_url", "")
    for asset in assets:
        if asset.get("name", "").lower().endswith(".exe"):
            exe_download_url = asset.get("browser_download_url", exe_download_url)
            break
    return exe_download_url

class TestUpdateLogic(unittest.TestCase):
    def test_version_comparison(self):
        self.assertTrue(is_newer("0.1.0", "0.0.9"))
        self.assertTrue(is_newer("1.0.0", "0.9.9"))
        self.assertTrue(is_newer("0.1.10", "0.1.9"))
        self.assertFalse(is_newer("0.1.9", "0.1.10"))
        self.assertFalse(is_newer("0.1.3", "0.1.3"))
        self.assertTrue(is_newer("0.2", "0.1.9"))

    def test_asset_discovery(self):
        mock_data = {
            "html_url": "https://github.com/release-page",
            "assets": [
                {"name": "readme.txt", "browser_download_url": "https://github.com/readme"},
                {"name": "QLX-App.exe", "browser_download_url": "https://github.com/app.exe"},
                {"name": "source.zip", "browser_download_url": "https://github.com/source"}
            ]
        }
        url = find_exe_asset(mock_data)
        self.assertEqual(url, "https://github.com/app.exe")

    def test_asset_discovery_fallback(self):
        mock_data = {
            "html_url": "https://github.com/release-page",
            "assets": [
                {"name": "source.zip", "browser_download_url": "https://github.com/source"}
            ]
        }
        url = find_exe_asset(mock_data)
        self.assertEqual(url, "https://github.com/release-page")

if __name__ == "__main__":
    unittest.main()
