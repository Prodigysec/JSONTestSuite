"""Native V8 adapter result mapping and malformed-byte handling."""

import subprocess
import unittest
from unittest.mock import patch

from parsers import test_v8_native


class V8NativeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.valid = str(test_v8_native.ROOT / "test_parsing" / "y_structure_lonely_null.json")

    @patch("parsers.test_v8_native.subprocess.run")
    def test_parser_verdicts_are_preserved(self, run):
        for code in (0, 1, 2, 124):
            with self.subTest(code=code):
                run.return_value = subprocess.CompletedProcess([], code)
                self.assertEqual(test_v8_native.main(["adapter", self.valid]),
                                 code if code in (0, 1) else 2)

    @patch("parsers.test_v8_native.subprocess.run")
    def test_malformed_input_does_not_reach_v8(self, run):
        malformed = str(test_v8_native.ROOT / "test_parsing" / "i_string_invalid_utf-8.json")
        self.assertEqual(test_v8_native.main(["adapter", malformed]), 1)
        run.assert_not_called()

    def test_missing_file_is_adapter_error(self):
        self.assertEqual(test_v8_native.main(["adapter", self.valid + ".missing"]), 2)


if __name__ == "__main__":
    unittest.main()
