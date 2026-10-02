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
            ("LOGS_DIR_PATH", str(self.root)),
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

    def run_runner(self, jobs=1):
        with contextlib.redirect_stdout(self.output):
            run_tests.run_tests(jobs=jobs)
        return self.log.read_text().splitlines()

    def test_parallel_parsers_overlap_and_log_in_registry_order(self):
        self.fixture('y_case.json')
        for name, peer in (('a', 'b'), ('b', 'a')):
            marker = self.root / (name + '.started')
            peer_marker = self.root / (peer + '.started')
            code = ('import pathlib, sys, time\n'
                    f'pathlib.Path({str(marker)!r}).touch()\n'
                    'deadline = time.monotonic() + 2\n'
                    f'while not pathlib.Path({str(peer_marker)!r}).exists() and time.monotonic() < deadline:\n'
                    '    time.sleep(0.01)\n'
                    f'time.sleep({0.15 if name == "a" else 0})\n'
                    f'raise SystemExit(0 if pathlib.Path({str(peer_marker)!r}).exists() else 2)')
            self.adapter(name, code)
        self.assertEqual(self.run_runner(jobs=2), [
            'a\tEXPECTED_RESULT\ty_case.json',
            'b\tEXPECTED_RESULT\ty_case.json',
        ])
        self.assertIn('<TD>a</TD><TD>1</TD><TD>0</TD><TD>0</TD>', self.report())

    def test_parallel_timeout_and_unavailable_have_one_record_each(self):
        for name in ('y_first.json', 'n_second.json'):
            self.fixture(name)
        for name in ('a_timeout', 'b_missing', 'c_accept'):
            self.registry[name] = {'url': '', 'commands': [name]}

        def invoke(command, **_kwargs):
            if command[0] == 'a_timeout':
                raise subprocess.TimeoutExpired(command, 5)
            if command[0] == 'b_missing':
                raise FileNotFoundError(2, 'missing', command[0])
            return 0

        with patch.object(run_tests.subprocess, 'call', side_effect=invoke):
            self.assertEqual(self.run_runner(jobs=3), [
                'a_timeout\tTIMEOUT\tn_second.json',
                'a_timeout\tTIMEOUT\ty_first.json',
                'b_missing\tSKIPPED_UNAVAILABLE\tn_second.json',
                'b_missing\tSKIPPED_UNAVAILABLE\ty_first.json',
                'c_accept\tSHOULD_HAVE_FAILED\tn_second.json',
                'c_accept\tEXPECTED_RESULT\ty_first.json',
            ])

    def test_invalid_job_count_preserves_existing_log(self):
        self.fixture('y_case.json')
        self.adapter('selected')
        self.log.write_bytes(b'previous\x00\xff')
        for jobs in (0, -1, True, '2'):
            with self.subTest(jobs=jobs):
                with self.assertRaisesRegex(run_tests.SelectionError, 'positive integer'):
                    run_tests.run_tests(jobs=jobs)
                self.assertEqual(self.log.read_bytes(), b'previous\x00\xff')

    def test_exit_codes_record_every_outcome(self):
        for prefix in ("y", "n", "i"):
            self.fixture(prefix + "_case.json")
        self.adapter("accept", "raise SystemExit(0)")
        self.adapter("reject", "raise SystemExit(1)")
        self.adapter("crash", "raise SystemExit(2)")
        self.assertCountEqual(self.run_runner(), [
            "accept\tEXPECTED_RESULT\ty_case.json",
            "accept\tSHOULD_HAVE_FAILED\tn_case.json",
            "accept\tIMPLEMENTATION_PASS\ti_case.json",
            "reject\tSHOULD_HAVE_PASSED\ty_case.json",
            "reject\tIMPLEMENTATION_FAIL\ti_case.json",
            "reject\tEXPECTED_RESULT\tn_case.json",
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
            self.assertEqual(self.run_runner(), [
                "a_accept\tEXPECTED_RESULT\ty_case.json",
                "b_timeout\tTIMEOUT\ty_case.json",
            ])
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
                    self.run_runner()
                self.assertEqual(len(streams), 2)
                self.assertTrue(all(stream.closed for stream in streams))

    @unittest.skipUnless(os.name == "posix", "signal exit codes require POSIX")
    def test_signal_termination_is_a_crash(self):
        self.fixture("i_case.json")
        self.adapter("signal", "import os, signal; os.kill(os.getpid(), signal.SIGTERM)")
        self.assertEqual(self.run_runner(), ["signal\tCRASH\ti_case.json"])

    def report(self, pruned=False):
        path = self.root / 'report.html'
        with patch.object(run_tests.os, 'system'):
            run_tests.generate_report(str(path), pruned)
        return path.read_text()

    def test_successful_cases_appear_in_report_and_summary(self):
        self.fixture('y_one.json')
        self.fixture('y_two.json')
        self.adapter('accept')
        self.run_runner()
        html = self.report()
        self.assertIn('y_one.json', html)
        self.assertIn('y_two.json', html)
        self.assertIn('<TD>accept</TD><TD>2</TD><TD>0</TD><TD>0</TD>', html)
        self.assertIn('class="EXPECTED_RESULT" title="expected result"', html)
        pruned = self.report(pruned=True)
        self.assertIn('<TD>accept</TD><TD>2</TD><TD>0</TD><TD>0</TD>', pruned)
        matrix = pruned.split('<A NAME="all_results"></A>')[1].split('</TABLE>')[0]
        self.assertIn('y_one.json', matrix)
        self.assertNotIn('y_two.json', matrix)

    def test_missing_executable_skips_all_selected_cases_once(self):
        self.fixture('y_one.json')
        self.fixture('n_two.json')
        self.adapter('missing')
        self.registry['missing']['commands'] = [str(self.root / 'missing-binary')]
        with patch.object(run_tests.subprocess, 'call', wraps=subprocess.call) as call:
            rows = self.run_runner()
        self.assertEqual(call.call_count, 1)
        self.assertCountEqual(rows, [
            'missing\tSKIPPED_UNAVAILABLE\ty_one.json',
            'missing\tSKIPPED_UNAVAILABLE\tn_two.json',
        ])
        html = self.report()
        self.assertIn('<TD>missing</TD><TD>0</TD><TD>2</TD><TD>0</TD>', html)
        self.assertNotIn('class="EXPECTED_RESULT" title=', html)

    def test_setup_failure_skips_cases_without_running_parser(self):
        self.fixture('y_case.json')
        self.adapter('build')
        self.registry['build']['setup'] = [sys.executable, '-c', 'raise SystemExit(7)']
        for failure in (7, FileNotFoundError(2, 'missing', 'build')):
            with self.subTest(failure=failure):
                with patch.object(run_tests.subprocess, 'call', side_effect=[failure]) as call:
                    self.assertEqual(self.run_runner(), [
                        'build\tSKIPPED_SETUP_FAILED\ty_case.json',
                    ])
                self.assertEqual(call.call_count, 1)

    def test_late_unavailability_preserves_execution_and_skips_remaining(self):
        for name in ('y_a.json', 'y_b.json', 'y_c.json'):
            self.fixture(name)
        self.adapter('parser')
        with patch.object(run_tests.subprocess, 'call', side_effect=[
            0, PermissionError(13, 'not executable'),
        ]) as call:
            self.assertEqual(self.run_runner(), [
                'parser\tEXPECTED_RESULT\ty_a.json',
                'parser\tSKIPPED_UNAVAILABLE\ty_b.json',
                'parser\tSKIPPED_UNAVAILABLE\ty_c.json',
            ])
        self.assertEqual(call.call_count, 2)
        self.assertIn('<TD>parser</TD><TD>1</TD><TD>2</TD><TD>0</TD>', self.report())

    def test_filtered_run_only_records_selected_pairs(self):
        self.fixture('y_one.json')
        self.fixture('y_two.json')
        self.adapter('selected')
        self.adapter('unselected')
        with contextlib.redirect_stdout(self.output):
            run_tests.run_tests('y_two.json', io.StringIO('["selected"]'))
        self.assertEqual(self.log.read_text(), 'selected\tEXPECTED_RESULT\ty_two.json\n')
        html = self.report()
        self.assertNotIn('unselected', html)
        self.assertNotIn('y_one.json', html)

    def test_path_selector_targets_one_nested_fixture_but_basename_keeps_both(self):
        self.fixture('y_case.json')
        nested = self.corpus / 'nested'
        nested.mkdir()
        (nested / 'y_case.json').write_bytes(b'null')
        self.adapter('parser')

        for selector in ('nested/y_case.json', 'test_parsing/nested/y_case.json',
                         str(nested / 'y_case.json')):
            with self.subTest(selector=selector):
                with contextlib.redirect_stdout(self.output):
                    run_tests.run_tests(selector, ['parser'])
                self.assertEqual(self.log.read_text().splitlines(), [
                    'parser\tEXPECTED_RESULT\tnested/y_case.json',
                ])

        with contextlib.redirect_stdout(self.output):
            run_tests.run_tests('y_case.json', ['parser'])
        self.assertEqual(self.log.read_text().splitlines(), [
            'parser\tEXPECTED_RESULT\ty_case.json',
            'parser\tEXPECTED_RESULT\tnested/y_case.json',
        ])

    def test_external_path_with_matching_basename_preserves_log(self):
        self.fixture('y_case.json')
        outside = self.root / 'outside'
        outside.mkdir()
        external = outside / 'y_case.json'
        external.write_bytes(b'not JSON')
        self.adapter('parser')
        self.log.write_bytes(b'previous\x00\xff')
        with patch.object(run_tests.subprocess, 'call') as call:
            for selector in (str(external), 'test_parsing/../outside/y_case.json'):
                with self.subTest(selector=selector):
                    with self.assertRaisesRegex(run_tests.SelectionError, 'outside test_parsing'):
                        run_tests.run_tests(selector, ['parser'])
        call.assert_not_called()
        self.assertEqual(self.log.read_bytes(), b'previous\x00\xff')

    def test_cli_runs_one_selected_fixture_and_reports_expected_result(self):
        self.fixture('y_one.json')
        self.fixture('y_two.json')
        self.adapter('parser')
        reports = self.root / 'results'
        reports.mkdir()
        filter_path = self.root / 'filter.json'
        filter_path.write_text('["parser"]')
        with patch.object(run_tests, 'BASE_DIR', str(self.root)), \
                patch.object(run_tests.os, 'system'), \
                contextlib.redirect_stdout(self.output):
            run_tests.main(['test_parsing/y_two.json', '--filter', str(filter_path)])
        self.assertEqual(self.log.read_text(),
                         'parser\tEXPECTED_RESULT\ty_two.json\n')
        full = (reports / 'parsing.html').read_text()
        self.assertIn('y_two.json', full)
        self.assertNotIn('y_one.json', full)
        self.assertIn('class="EXPECTED_RESULT" title="expected result"', full)

    def test_invalid_cli_selection_preserves_outputs_and_never_starts_setup(self):
        self.fixture('y_case.json')
        self.adapter('selected')
        self.registry['selected']['setup'] = ['controlled-setup']
        filter_path = self.root / 'filter.json'
        results = self.root / 'results'
        results.mkdir()
        outputs = [self.log, results / 'parsing.html', results / 'parsing_pruned.html']
        for path in outputs:
            path.write_bytes(b'previous results\x00\xff')
        invalid_selections = [
            ('[]', [], 'non-empty JSON array'),
            ('null', [], 'non-empty JSON array'),
            ('"selected"', [], 'non-empty JSON array'),
            ('{"selected": true}', [], 'non-empty JSON array'),
            ('[1]', [], 'non-empty JSON array'),
            ('["selected", null]', [], 'non-empty JSON array'),
            ('[', [], 'Invalid JSON filter'),
            ('["missing"]', [], "Unknown parser name(s): 'missing'"),
            ('["selected", "missing"]', [], "Unknown parser name(s): 'missing'"),
            ('["selected"]', ['y_missing.json'], 'No corpus fixture matches'),
            ('["selected"]', [''], 'No corpus fixture matches'),
        ]
        for content, selectors, message in invalid_selections:
            with self.subTest(content=content, selectors=selectors):
                filter_path.write_text(content)
                stderr = io.StringIO()
                with patch.object(run_tests, 'BASE_DIR', str(self.root)), \
                        patch.object(run_tests.subprocess, 'call') as call, \
                        patch.object(run_tests, 'generate_report') as report, \
                        contextlib.redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as raised:
                        run_tests.main(selectors + ['--filter', str(filter_path)])
                self.assertEqual(raised.exception.code, 2)
                self.assertIn(message, stderr.getvalue())
                self.assertNotIn('Traceback', stderr.getvalue())
                call.assert_not_called()
                report.assert_not_called()
                for path in outputs:
                    self.assertEqual(path.read_bytes(), b'previous results\x00\xff')

    def test_empty_corpus_or_registry_preserves_log(self):
        self.log.write_text('previous results')
        self.adapter('selected')
        with patch.object(run_tests.subprocess, 'call') as call:
            with self.assertRaisesRegex(run_tests.SelectionError, 'No JSON fixtures'):
                run_tests.run_tests()
            self.fixture('y_case.json')
            self.registry.clear()
            with self.assertRaisesRegex(run_tests.SelectionError, 'No parsers selected'):
                run_tests.run_tests()
        call.assert_not_called()
        self.assertEqual(self.log.read_text(), 'previous results')

    def test_direct_empty_filter_is_rejected_before_creating_log(self):
        self.fixture('y_case.json')
        self.adapter('selected')
        with self.assertRaisesRegex(run_tests.SelectionError, 'non-empty JSON array'):
            run_tests.run_tests(restrict_to_program=[])
        self.assertFalse(self.log.exists())

    def test_valid_filter_keeps_basename_selection_and_deduplicates_parsers(self):
        self.fixture('y_case.json')
        self.fixture('y_other.json')
        self.adapter('selected')
        self.adapter('unselected')
        with contextlib.redirect_stdout(self.output):
            run_tests.run_tests('test_parsing/y_case.json', ['selected', 'selected'])
        self.assertEqual(self.log.read_text(), 'selected\tEXPECTED_RESULT\ty_case.json\n')

    def test_nested_fixtures_have_distinct_log_identifiers(self):
        for folder in ('one', 'two'):
            (self.corpus / folder).mkdir()
            self.fixture(folder + '/y_case.json')
        self.adapter('parser')
        self.assertEqual(len(self.run_runner()), 2)
        by_file, _ = run_tests.f_status_for_lib_for_file(str(self.corpus), str(self.root))
        self.assertEqual(set(by_file), {
            str(self.corpus / 'one/y_case.json'), str(self.corpus / 'two/y_case.json'),
        })
        html = self.report()
        for folder in ('one', 'two'):
            self.assertIn(os.path.join(folder, 'y_case.json'), html)

    def test_legacy_missing_entries_are_unknown_not_success(self):
        self.fixture('y_case.json')
        self.fixture('i_case.json')
        self.log.write_text('old parser\tSHOULD_HAVE_PASSED\ty_case.json\n'
                            'another parser\tIMPLEMENTATION_PASS\ti_case.json\n')
        html = self.report()
        self.assertIn('old parser', html)  # No current registry entry required.
        self.assertIn('class="NOT_RECORDED"', html)
        self.assertNotIn('class="EXPECTED_RESULT" title=', html)
        self.assertIn('<TD>old parser</TD><TD>1</TD><TD>0</TD><TD>1</TD>', html)
        self.assertIn('Historical logs omit successful tests', html)

    def test_report_ignores_other_text_files(self):
        self.fixture('y_case.json')
        self.log.write_text('current\tEXPECTED_RESULT\ty_case.json\n')
        (self.root / 'stale.txt').write_text('stale\tCRASH\ty_case.json\n')
        self.assertNotIn('stale', self.report())

    def test_missing_fixture_keeps_its_recorded_outcome(self):
        self.log.write_text('historic\tCRASH\tn_removed.json\n')
        html = self.report()
        matrix = html.split('<A NAME="all_results"></A>')[1].split('</TABLE>')[0]
        self.assertIn('n_removed.json', matrix)
        self.assertIn('(MISSING FILE)', matrix)

    def test_report_escapes_fixture_and_parser_text(self):
        self.fixture('y_case.json', b'"<script>&"')
        self.adapter('<parser>')
        self.run_runner()
        html = self.report()
        self.assertIn('&lt;parser&gt;', html)
        self.assertIn('&lt;script&gt;&amp;', html)
        self.assertNotIn('<script>', html)

    def test_readers_use_supplied_corpus_directory(self):
        self.log.write_text('parser\tEXPECTED_RESULT\ty_case.json\n')
        alternate = self.root / 'alternate'
        expected_path = str(alternate / 'y_case.json')
        by_file, libs = run_tests.f_status_for_lib_for_file(str(alternate), str(self.root))
        by_parser = run_tests.f_status_for_path_for_lib(str(alternate), str(self.root))
        self.assertEqual(libs, ['parser'])
        self.assertEqual(by_file, {expected_path: {'parser': 'EXPECTED_RESULT'}})
        self.assertEqual(by_parser, {'parser': {expected_path: 'EXPECTED_RESULT'}})


if __name__ == "__main__":
    unittest.main()
