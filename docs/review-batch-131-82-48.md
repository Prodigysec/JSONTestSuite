# Runner issue review: #131, #82, and #48

Reviewed on 2026-10-03 against local parent `4697fc9`. All three upstream
issues remain open. They had no comments when refreshed; local dispositions
do not change their upstream status. Fixture bytes and tracked historical
reports were not changed.

## Expected results in reports: issue #131

[Issue #131](https://github.com/nst/JSONTestSuite/issues/131) reports that
successful tests were omitted from HTML output. Its last upstream update was
2024-02-29. The local runner already addressed this in the earlier
[explicit-outcomes work](project-assessment.md#2026-10-02-explicit-outcomes-and-issue-131):
each selected parser/fixture pair gets a log row, including `EXPECTED_RESULT`
and explicit skips, and both reports render those records. A fresh 324-fixture
run here confirmed 289 expected outcomes, 15 implementation-dependent
acceptances, and 20 implementation-dependent rejections, all visible in the
temporary full report. No new report change was needed. Historical logs still
cannot reveal cases or parsers omitted entirely from the log; absent cells are
unknown, never inferred successes.

## CLI execution: issue #82

[Issue #82](https://github.com/nst/JSONTestSuite/issues/82) says the call to
`run_tests()` was commented out. Its last upstream update was 2018-05-04.
The current local `main()` calls `run_tests()` unconditionally after parsing
arguments, and then generates reports. The temporary full and single-fixture
CLI runs below both launched Perl and wrote outcomes. This reported condition
is absent locally; no runner activation edit was needed.

## Selecting one file: issue #48

[Issue #48](https://github.com/nst/JSONTestSuite/issues/48) says a single-file
argument stopped working. Its last upstream update was 2016-10-30. The
current runner already accepted a bare corpus filename, but discarded directory
components from any selector. A path to `nested/y_case.json` could therefore
select both it and a root `y_case.json`; an external path with that basename
could silently select the corpus case. The local change keeps the bare-name
shorthand, while paths relative to `test_parsing/`, paths relative to the
corpus root, and absolute paths inside the corpus select one exact fixture.
Absolute paths outside the corpus and relative paths that traverse upward
fail validation before the log or reports are replaced. Arbitrary
external-file parsing remains outside this runner's
corpus-based expectation contract.

Focused regressions cover duplicate basenames in nested directories, exact
relative and absolute paths, outside-path rejection without side effects,
and an actual `main()` call that logs and reports an expected result. The
temporary CLI used Linux x86_64, Python 3.12.3, and Perl 5.38.2 / JSON::PP
4.16. Its full run logged all 324 fixtures exactly once; a second invocation
selected only `test_parsing/y_array_empty.json` and logged one expected result.
An external file of the same basename exited `2` and preserved all three
temporary output files byte-for-byte. The per-fixture timeout stayed at five
seconds. The full Python suite passed 63 tests, with 19 optional adapter tests
skipped for unrelated missing dependencies. No other historical toolchains
were needed for this runner change.
