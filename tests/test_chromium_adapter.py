import pathlib
import subprocess
import unittest
from unittest.mock import patch

from parsers import chromium_browser, test_chromium


class ChromiumAdapterTests(unittest.TestCase):
    def setUp(self):
        self.fixture = pathlib.Path(__file__).resolve().parents[1] / "test_parsing" / "y_structure_lonely_null.json"

    @patch("parsers.chromium_browser.shutil.which", return_value="/usr/bin/docker")
    @patch("parsers.chromium_browser.subprocess.run")
    def test_browser_marker_controls_rejection(self, run, _which):
        run.side_effect = [
            subprocess.CompletedProcess([], 0),
            subprocess.CompletedProcess([], 0, '<pre id="result">JSONTESTSUITE:{&quot;status&quot;:&quot;reject&quot;}</pre>', ''),
        ]
        self.assertEqual(chromium_browser.observe(self.fixture), {"status": "reject"})

    @patch("parsers.chromium_browser.shutil.which", return_value="/usr/bin/docker")
    @patch("parsers.chromium_browser.subprocess.run")
    def test_missing_marker_is_adapter_error(self, run, _which):
        run.side_effect = [subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 0, '<html></html>', '')]
        self.assertEqual(chromium_browser.observe(self.fixture)["status"], "error")

    @patch("parsers.chromium_browser.shutil.which", return_value="/usr/bin/docker")
    @patch("parsers.chromium_browser.subprocess.run", return_value=subprocess.CompletedProcess([], 1))
    def test_missing_image_is_explicit(self, _run, _which):
        self.assertEqual(chromium_browser.observe(self.fixture)["status"], "unavailable")

    @patch("parsers.test_chromium.observe", return_value={"status": "reject"})
    def test_registry_adapter_maps_rejection_to_one(self, _observe):
        self.assertEqual(test_chromium.main(["test_chromium.py", str(self.fixture)]), 1)


if __name__ == "__main__":
    unittest.main()
