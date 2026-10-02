"""Runner regressions using temporary fixtures and controlled adapters."""

import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_tests


class RunnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.corpus = self.root / "corpus"
        self.corpus.mkdir()
        self.log = self.root / "logs.txt"
        self.output = io.StringIO()
        self.registry = {}
        for name, value in (
            ("programs", self.registry),
            ("TEST_CASES_DIR_PATH", str(self.corpus)),
            ("LOG_FILE_PATH", str(self.log)),
        ):
            patcher = patch.object(run_tests, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def fixture(self, name, content=b"null"):
        (self.corpus / name).write_bytes(content)

    def adapter(self, name, code="pass", use_stdin=False):
        self.registry[name] = {
            "url": "",
            "commands": [sys.executable, "-c", code],
            "use_stdin": use_stdin,
        }

    def run_runner(self):
        with contextlib.redirect_stdout(self.output):
            run_tests.run_tests()
        return self.log.read_text().splitlines()

    def test_exit_codes_keep_existing_log_contract(self):
        for prefix in ("y", "n", "i"):
            self.fixture(prefix + "_case.json")
        self.adapter("accept", "raise SystemExit(0)")
        self.adapter("reject", "raise SystemExit(1)")
        self.adapter("crash", "raise SystemExit(2)")
        self.assertCountEqual(self.run_runner(), [
            "accept\tSHOULD_HAVE_FAILED\tn_case.json",
            "accept\tIMPLEMENTATION_PASS\ti_case.json",
            "reject\tSHOULD_HAVE_PASSED\ty_case.json",
            "reject\tIMPLEMENTATION_FAIL\ti_case.json",
            "crash\tCRASH\ty_case.json",
            "crash\tCRASH\tn_case.json",
            "crash\tCRASH\ti_case.json",
        ])

    def test_first_timeout_is_logged_and_next_parser_runs(self):
        self.fixture("i_case.json")
        self.adapter("a_timeout")
        self.adapter("b_reject")
        with patch.object(run_tests.subprocess, "call", side_effect=[
            subprocess.TimeoutExpired(["controlled-adapter"], 5), 1,
        ]) as call:
            rows = self.run_runner()
        self.assertEqual(rows, [
            "a_timeout\tTIMEOUT\ti_case.json",
            "b_reject\tIMPLEMENTATION_FAIL\ti_case.json",
        ])
        self.assertEqual(call.call_count, 2)
        self.assertIn("RESULT: TIMEOUT", self.output.getvalue())
        for invocation in call.call_args_list:
            self.assertEqual(invocation.kwargs["timeout"], 5)

    def test_timeout_does_not_print_previous_result(self):
        self.fixture("y_case.json")
        self.adapter("a_accept")
        self.adapter("b_timeout")
        with patch.object(run_tests.subprocess, "call", side_effect=[
            0, subprocess.TimeoutExpired(["controlled-adapter"], 5),
        ]):
            self.assertEqual(self.run_runner(), ["b_timeout\tTIMEOUT\ty_case.json"])
        self.assertIn("RESULT: TIMEOUT", self.output.getvalue())
        self.assertNotIn("RESULT: PASS", self.output.getvalue())

    def test_stdin_preserves_raw_bytes(self):
        content = b"\xff\x00\r\n"
        self.fixture("i_bytes.json", content)
        self.adapter("stdin", "import sys; raise SystemExit(0 if "
                     "sys.stdin.buffer.read() == %r else 1)" % content,
                     use_stdin=True)
        self.assertEqual(self.run_runner(), ["stdin\tIMPLEMENTATION_PASS\ti_bytes.json"])

    def test_stdin_closed_on_every_subprocess_outcome(self):
        self.fixture("i_case.json")
        self.adapter("stdin", use_stdin=True)
        outcomes = [0, 1, 2,
                    subprocess.TimeoutExpired(["controlled-adapter"], 5),
                    FileNotFoundError(2, "missing", "controlled-adapter"),
                    OSError(run_tests.INVALID_BINARY_FORMAT, "invalid binary"),
                    PermissionError(13, "permission denied")]
        for outcome in outcomes:
            with self.subTest(outcome=repr(outcome)):
                streams = []

                def invoke(*args, **kwargs):
                    streams.extend([kwargs["stdin"], kwargs["stdout"]])
                    if isinstance(outcome, Exception):
                        raise outcome
                    return outcome

                with patch.object(run_tests.subprocess, "call", side_effect=invoke):
                    if isinstance(outcome, PermissionError):
                        with self.assertRaises(PermissionError):
                            self.run_runner()
                    else:
                        self.run_runner()
                self.assertEqual(len(streams), 2)
                self.assertTrue(all(stream.closed for stream in streams))

    @unittest.skipUnless(os.name == "posix", "signal exit codes require POSIX")
    def test_signal_termination_is_a_crash(self):
        self.fixture("i_case.json")
        self.adapter("signal", "import os, signal; os.kill(os.getpid(), signal.SIGTERM)")
        self.assertEqual(self.run_runner(), ["signal\tCRASH\ti_case.json"])


if __name__ == "__main__":
    unittest.main()
