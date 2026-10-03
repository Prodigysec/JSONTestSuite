"""Contract and mode checks for the active-interpreter JSON adapter."""

from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from parsers import test_python_json
import run_tests


class PythonJsonAdapterTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="jsonsuite-python-json-")
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "case.json"

    def invoke(self, data, reject=False):
        self.path.write_bytes(data)
        command = [sys.executable, str(Path(test_python_json.__file__))]
        if reject:
            command.append("--reject-nonfinite")
        return subprocess.run(command + [str(self.path)], capture_output=True,
                              timeout=5).returncode

    def test_scalars_and_complete_input(self):
        for reject in (False, True):
            for data in (b"null", b"false", b"0", b'""', b"[]", b"{}",
                         b'["\\u0000"]', b'["\xc3\xa9"]', b'"NaN"'):
                with self.subTest(reject=reject, data=data):
                    self.assertEqual(self.invoke(data, reject), 0)
            for data in (b"", b"null false", b"[]#", b"123\0true", b"[1,]",
                         b'["\xff"]', b'"\xc0\xaf"', b"\xef\xbb\xbf{}",
                         b"{}".decode().encode("utf-16"), b"{}".decode().encode("utf-32")):
                with self.subTest(reject=reject, data=data):
                    self.assertEqual(self.invoke(data, reject), 1)

    def test_constant_policy_does_not_reject_numeric_overflow(self):
        for data in (b"NaN", b"Infinity", b"-Infinity", b"[NaN,Infinity,-Infinity]"):
            self.assertEqual(self.invoke(data), 0)
            self.assertEqual(self.invoke(data, True), 1)
        self.assertEqual(self.invoke(b"1e999", True), 0)
        for reject in (False, True):
            self.assertEqual(self.invoke(b'"\\uDEAD"', reject), 0)
            self.assertEqual(self.invoke(b'{"a":1,"a":2}', reject), 0)

    def test_file_and_argument_errors(self):
        for arguments in ([], ["--reject-nonfinite"], [str(self.path)],
                          [self.directory.name], ["extra", str(self.path)]):
            self.assertEqual(test_python_json.main(["adapter"] + arguments), 2)

    def test_runtime_errors_and_implementation_limits(self):
        self.path.write_bytes(b"[]")
        for error, expected in ((MemoryError(), 2), (RuntimeError(), 2),
                                (RecursionError(), 1), (ValueError(), 1)):
            with self.subTest(error=type(error).__name__):
                with patch("parsers.test_python_json.json.loads", side_effect=error):
                    self.assertEqual(test_python_json.main(["adapter", str(self.path)]), expected)
        with patch("parsers.test_python_json.Path.read_bytes", side_effect=MemoryError()):
            self.assertEqual(test_python_json.main(["adapter", str(self.path)]), 2)
        self.assertEqual(self.invoke(b"[" * 100000), 1)
        digit_limit = getattr(sys, "get_int_max_str_digits", lambda: 0)()
        if digit_limit:
            self.assertEqual(self.invoke(b"1" * (digit_limit + 1)), 1)

    def test_registry_uses_this_interpreter_and_its_version(self):
        modes = {name: entry for name, entry in run_tests.programs.items()
                 if str(Path(test_python_json.__file__)) in entry["commands"]}
        self.assertEqual(len(modes), 2)
        for name, entry in modes.items():
            self.assertIn(platform.python_version(), name)
            self.assertIn(platform.python_implementation(), name)
            self.assertEqual(entry["commands"][0], sys.executable)


if __name__ == "__main__":
    unittest.main()
