"""Check the CCAN file wrapper's exit-code and whole-input contract."""

import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CCANAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shlex.split(os.environ.get("CC", "cc"))
        if not compiler or not shutil.which(compiler[0]):
            raise unittest.SkipTest("A C99 compiler is required for CCAN wrapper tests")
        cls.build = tempfile.TemporaryDirectory(prefix="jsonsuite-ccan-")
        cls.binary = Path(cls.build.name) / "test_ccan"
        source = ROOT / "parsers/test_ccan_json"
        subprocess.run(compiler + [
            "-std=c99", "-I" + str(source / "json"),
            str(source / "test_ccan/test_ccan/main.c"),
            str(source / "json/json.c"), "-o", str(cls.binary),
        ], check=True, capture_output=True, timeout=30)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "build"):
            cls.build.cleanup()

    def run_case(self, data):
        path = Path(self.build.name) / "case.json"
        path.write_bytes(data)
        return subprocess.run([str(self.binary), str(path)],
                              capture_output=True, timeout=5).returncode

    def test_scalar_and_complete_text(self):
        for data in (b"null", b"false", b"0", b"[]", b'"ok"'):
            with self.subTest(data=data):
                self.assertEqual(self.run_case(data), 0)
        for data in (b"", b"123 true", b"[1,]", b'"\xff"'):
            with self.subTest(data=data):
                self.assertEqual(self.run_case(data), 1)

    def test_embedded_nul_cannot_hide_trailing_input(self):
        for data in (b"123\0", b"123\0true", b'["ok"]\0[]'):
            with self.subTest(data=data):
                self.assertEqual(self.run_case(data), 1)

    def test_invocation_errors_are_not_json_rejections(self):
        self.assertEqual(subprocess.run([str(self.binary)],
                                        capture_output=True, timeout=5).returncode, 2)
        self.assertEqual(subprocess.run([str(self.binary), str(Path(self.build.name) / "missing")],
                                        capture_output=True, timeout=5).returncode, 2)


if __name__ == "__main__":
    unittest.main()
