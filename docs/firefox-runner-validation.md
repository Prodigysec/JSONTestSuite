# Firefox per-fixture runner validation

The initial four-worker validation exposed WebDriver startup timeouts. The
first four shards recorded all 164 selected fixtures, but 25 outcomes were
`CRASH` because the adapter returned 2. Failures occurred across valid,
invalid, and implementation-dependent inputs. Serial reproduction of three
affected inputs returned their expected verdicts. A concurrent diagnostic run
reproduced `TimeoutError('timed out')` inside the probe's WebDriver request,
which had a ten-second timeout.

The probe now gives each WebDriver request 25 seconds. Its container timeout
is 40 seconds, the host subprocess timeout is 42 seconds, and the registry's
runner timeout is 45 seconds. These bounds allow browser startup under load;
adapter failures still return 2 and remain `CRASH` in the runner. The existing
fixture bytes, decoding policy, and JSON.parse invocation are unchanged.

Validation uses eight disjoint corpus shards with four concurrent worker
processes. Each worker calls the actual runner CLI entry point with the
registered Firefox adapter and `--fail-on-discrepancy`, writes its own log,
and generates both reports. Temporary corpus entries are symlinks to the
original fixtures, so the wrapper resolves and mounts the original files.
The completeness audit checks fixture names, duplicate records, skips,
errors, and all 16 generated reports.

On 2026-10-03, the corrected full run recorded exactly 327 distinct fixtures:
288 `EXPECTED_RESULT`, 25 `IMPLEMENTATION_PASS`, and 14 `IMPLEMENTATION_FAIL`.
All eight shard CLI verdicts were zero. No discrepancy, crash, timeout, skip,
missing fixture, extra fixture, or duplicate row was recorded. Both HTML
reports were generated for each shard (16 reports in total). This exercises
327 separate adapter invocations with fresh Firefox launches, under four-way
load, rather than the earlier one-session engine survey.

The run used Linux x86-64, host Python 3.12.3, Firefox ESR 153.4.0, and
geckodriver 0.36.0. The corpus revision was
`b62e2b4db25f05e90c2d75a262625e1ef4d0c1ff`, with this timeout fix applied to
the runner and adapter. The tested image ID was
`sha256:25250eb69f60d0b85394b7cf37c8b48ef6b5ddcee54b83e48b90144c2098b342`.
Logs, invocation traces, and reports are retained temporarily at
`/tmp/jsonsuite-firefox-full-mnbfxwo6`; this location is ephemeral.

The regression suite passed 92 tests with 21 optional dependency skips.
Focused probe tests check the bounded request budget and verify that a
transport timeout remains adapter error 2 and closes the driver. Existing
adapter tests verify that outer timeouts likewise remain errors.
`git diff --check` passed. Tracked fixture bytes and historical reports were
preserved. These measurements establish the tested configuration's behavior
on this corpus and host; other loads and environments may require separate
validation.
