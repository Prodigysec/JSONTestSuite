"""Native wrapper regressions for the three newly registered source builds."""

import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "jsmn": ("parsers/test_jsmn", "test_jsmn/test_jsmn/main.c", "jsmn.c"),
    "checker": ("parsers/test_jsonChecker/jsonChecker", "jsonChecker/main.c", "JSON_checker.c"),
    "cjson": ("parsers/test_cJSON_1_7_3", "test-cJSON/main.c", "cJSON.c"),
}


class SourceCAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shlex.split(os.environ.get("CC", "cc"))
        if not compiler or not shutil.which(compiler[0]):
            raise unittest.SkipTest("A C99 compiler is required for native wrapper tests")
        cls.build = tempfile.TemporaryDirectory(prefix="jsonsuite-source-c-")
        cls.addClassCleanup(cls.build.cleanup)
        cls.binaries = {}
        cls.fault_binaries = {}
        fault_source = Path(cls.build.name) / "allocation_fault.c"
        fault_source.write_text("""
#include <stdlib.h>
static unsigned calls;
void *__real_malloc(size_t);
void *__real_calloc(size_t, size_t);
static int fail(void) {
    const char *value = getenv("JSONSUITE_FAIL_ALLOCATION");
    return value != NULL && ++calls == strtoul(value, NULL, 10);
}
void *__wrap_malloc(size_t size) { return fail() ? NULL : __real_malloc(size); }
void *__wrap_calloc(size_t n, size_t size) { return fail() ? NULL : __real_calloc(n, size); }
""")
        for name, (directory, main, library) in SOURCES.items():
            source = ROOT / directory
            binary = Path(cls.build.name) / name
            command = compiler + ["-std=c99", "-O2", "-I" + str(source),
                                  str(source / main), str(source / library)]
            libraries = ["-lm"] if name == "cjson" else []
            subprocess.run(command + ["-o", str(binary)] + libraries,
                           check=True, capture_output=True, timeout=30)
            cls.binaries[name] = binary
            if sys.platform.startswith("linux"):
                fault_binary = Path(cls.build.name) / (name + "-fault")
                subprocess.run(command + [str(fault_source), "-Wl,--wrap=malloc,--wrap=calloc",
                                          "-o", str(fault_binary)] + libraries,
                               check=True, capture_output=True, timeout=30)
                cls.fault_binaries[name] = fault_binary

    def run_case(self, name, data, fail_allocation=None):
        path = Path(self.build.name) / "case.json"
        path.write_bytes(data)
        environment = os.environ.copy()
        binary = self.binaries[name]
        if fail_allocation is not None:
            binary = self.fault_binaries[name]
            environment["JSONSUITE_FAIL_ALLOCATION"] = str(fail_allocation)
        return subprocess.run([str(binary), str(path)], env=environment,
                              capture_output=True, timeout=5).returncode

    def test_complete_file_and_token_budget(self):
        for name in self.binaries:
            for data in (b"[" + b"0," * 200 + b"0]", b"[" + b" " * 110 + b"1]"):
                with self.subTest(name=name, size=len(data)):
                    self.assertEqual(self.run_case(name, data), 0)
            self.assertEqual(self.run_case(name, b"[" + b" " * 110 + b"1]junk"), 1)

    def test_whole_text_and_literal_nul(self):
        for name in self.binaries:
            for data in (b"", b"{} []", b'"ok" true', b"[] trailing",
                         b"123\0true", b"[]\0", b'["a\0b"]'):
                with self.subTest(name=name, data=data):
                    self.assertEqual(self.run_case(name, data), 1)
            self.assertEqual(self.run_case(name, b'["\\u0000"]'), 0)

    def test_native_scalars_and_utf8_bytes(self):
        for name in self.binaries:
            for data in (b"null", b"false", b"0", b'"ok"'):
                with self.subTest(name=name, data=data):
                    self.assertEqual(self.run_case(name, data), 1 if name == "checker" else 0)
            self.assertEqual(self.run_case(name, b'["\xc3\xa9"]'), 0)

    def test_file_and_invocation_errors(self):
        for name, binary in self.binaries.items():
            for arguments in ([], [str(Path(self.build.name) / "missing")], [self.build.name]):
                with self.subTest(name=name, arguments=arguments):
                    self.assertEqual(subprocess.run([str(binary)] + arguments,
                                                    capture_output=True, timeout=5).returncode, 2)

    @unittest.skipUnless(sys.platform.startswith("linux"), "GNU linker allocation fault injection")
    def test_allocation_errors_are_not_rejections(self):
        for name in self.binaries:
            for allocation in (1, 2):
                with self.subTest(name=name, allocation=allocation):
                    self.assertEqual(self.run_case(name, b"[]", allocation), 2)
        self.assertEqual(self.run_case("checker", b"[]", 3), 2)


if __name__ == "__main__":
    unittest.main()
