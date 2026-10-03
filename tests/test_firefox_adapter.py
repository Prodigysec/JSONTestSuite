"""Firefox container adapter maps browser outcomes without hiding failures."""

import subprocess
import unittest
from unittest.mock import patch

from parsers import test_firefox


class FirefoxAdapterTests(unittest.TestCase):
    def setUp(self):
        self.valid = str(test_firefox.ROOT / "test_parsing" / "y_structure_lonely_null.json")

    @patch("parsers.test_firefox.subprocess.run")
    def test_exit_codes_and_timeout(self, run):
        for code in (0, 1, 2, 124):
            with self.subTest(code=code):
                run.return_value = subprocess.CompletedProcess([], code)
                self.assertEqual(test_firefox.main(["adapter", self.valid]),
                                 code if code in (0, 1) else 2)
        self.assertEqual(run.call_args.kwargs["timeout"], 16)
        run.side_effect = subprocess.TimeoutExpired([], 16)
        self.assertEqual(test_firefox.main(["adapter", self.valid]), 2)

    def test_missing_file_is_adapter_error(self):
        self.assertEqual(test_firefox.main(["adapter", self.valid + ".missing"]), 2)


if __name__ == "__main__":
    unittest.main()
