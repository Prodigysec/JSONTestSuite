import subprocess
import unittest
from unittest.mock import patch

from parsers import test_jsc


class JavaScriptCoreAdapterTests(unittest.TestCase):
    def setUp(self):
        self.valid = str(test_jsc.ROOT / "test_parsing" / "y_structure_lonely_null.json")

    @patch("parsers.test_jsc.subprocess.run")
    def test_shell_marker_controls_rejection(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, "JSONTESTSUITE_REJECT\n", "")
        self.assertEqual(test_jsc.main(["test_jsc.py", self.valid]), 1)

    @patch("parsers.test_jsc.subprocess.run")
    def test_missing_marker_is_adapter_error(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, "", "")
        self.assertEqual(test_jsc.main(["test_jsc.py", self.valid]), 2)

    @patch("parsers.test_jsc.subprocess.run")
    def test_invalid_utf8_is_rejected_before_shell(self, run):
        malformed = str(test_jsc.ROOT / "test_parsing" / "n_array_invalid_utf8.json")
        self.assertEqual(test_jsc.main(["test_jsc.py", malformed]), 1)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
