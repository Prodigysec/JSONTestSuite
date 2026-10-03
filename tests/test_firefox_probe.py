"""WebDriver transport failures must remain adapter errors."""

import unittest
from unittest.mock import MagicMock, patch

from parsers import firefox_probe


class FirefoxProbeTests(unittest.TestCase):
    @patch("parsers.firefox_probe.urllib.request.urlopen")
    def test_request_has_bounded_startup_budget(self, urlopen):
        response = MagicMock()
        response.read.return_value = b'{"value":true}'
        urlopen.return_value.__enter__.return_value = response
        self.assertEqual(firefox_probe.request("http://127.0.0.1:1234", "GET", "/status"),
                         {"value": True})
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 25)

    @patch("parsers.firefox_probe.subprocess.Popen")
    @patch("parsers.firefox_probe.request", side_effect=TimeoutError("startup timed out"))
    def test_startup_timeout_is_error_and_driver_is_closed(self, request, popen):
        from parsers import test_firefox
        path = str(test_firefox.ROOT / "test_parsing" / "y_structure_lonely_null.json")
        self.assertEqual(firefox_probe.main(["probe", path]), 2)
        popen.return_value.terminate.assert_called_once()
        popen.return_value.wait.assert_called_once_with(timeout=2)


if __name__ == "__main__":
    unittest.main()
