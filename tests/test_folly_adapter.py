"""Folly wrapper preserves parser verdicts and surfaces runtime failures."""

import subprocess
import unittest
from unittest.mock import patch

from parsers import test_folly


class FollyAdapterTests(unittest.TestCase):
    @patch("parsers.test_folly.subprocess.run")
    def test_exit_codes_and_runtime_failures(self, run):
        path = str(test_folly.ROOT / "test_parsing" / "y_structure_lonely_null.json")
        for code in (0, 1, 2, -11, 124, 125):
            with self.subTest(code=code):
                run.return_value = subprocess.CompletedProcess([], code)
                self.assertEqual(test_folly.main(["adapter", path]), code if code in (0, 1) else 2)
        run.side_effect = FileNotFoundError("docker")
        self.assertEqual(test_folly.main(["adapter", path]), 2)
        run.side_effect = subprocess.TimeoutExpired([], 5)
        self.assertEqual(test_folly.main(["adapter", path]), 2)

    @patch("parsers.test_folly.subprocess.run")
    def test_missing_input_does_not_invoke_parser(self, run):
        self.assertEqual(test_folly.main(["adapter", str(test_folly.ROOT / "missing-folly.json")]), 2)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
