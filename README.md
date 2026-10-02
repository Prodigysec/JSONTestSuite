# JSON Parsing Test Suite

A corpus of valid, invalid, and implementation-dependent JSON inputs, with
adapters and a runner for comparing parser behavior against
[RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html).

This is the [Prodigysec fork](https://github.com/Prodigysec/JSONTestSuite) of
[nst/JSONTestSuite](https://github.com/nst/JSONTestSuite), originally created by
Nicolas Seriot as an appendix to
[Parsing JSON is a Minefield 💣](https://seriot.ch/software/parsing_json.html).
The fork's goal is to expand coverage, address upstream issues, and integrate
reviewed contributions across JSON parsers, versions, and platforms. Universal
parser coverage is a goal, not a property of the current checkout.

At the initial assessment, the repository contains **318 parsing fixtures**
(95 `y_`, 188 `n_`, 35 `i_`), **22 transformation fixtures**, and **94 registered
parser configurations**. Configurations include different versions and modes of
the same library; registration does not mean a parser is installed or runnable.
See the [project assessment and upstream review queue](docs/project-assessment.md)
for the baseline, known limitations, and planned work.

The current parsing corpus has **327 fixtures** (94 `y_`, 194 `n_`, 39 `i_`),
including trailing nonbreaking-space, octal-escape, and leading-zero cases
reviewed from upstream PRs #146, #137, and #105, plus an escaped-NUL scalar
reviewed from [issue #94](docs/review-batch-92-94-93.md). Four large or
underflowing number cases were reclassified under `i_` for
[issue #149](docs/review-batch-149-119-118.md), and a modest fraction-exponent
case was added under `y_`. A lowercase-`u` scalar escape companion to an
existing uppercase-`U` rejection was added for
[issue #112](docs/review-batch-112-91-85.md).

## Start with one parser

The corpus can be used directly in your own tests without installing the bundled
parsers. To try the supplied Python wrapper, clone this fork and use Python 3:

```sh
git clone https://github.com/Prodigysec/JSONTestSuite.git
cd JSONTestSuite
python3 parsers/test_json.py test_parsing/y_structure_lonely_null.json
echo $?  # expected: 0 (accepted)
python3 parsers/test_json.py test_parsing/n_array_extra_comma.json
echo $?  # expected: 1 (rejected)
```

These POSIX-shell examples test the locally installed Python standard-library
parser. They do not generate reports or establish that Python passes the whole
suite. In particular, the wrapper uses Python's default JSON options and reads
text using the environment's encoding; it is not a strict reference validator.

The runner itself uses Python 3's standard library. Each selected adapter has
its own runtime, library, and build requirements. There is no repository-wide
dependency installer or universal build command. Many entries target historical
versions, absolute executable paths, or platform-specific binaries. Check the
`programs` dictionary in [run_tests.py](run_tests.py) and the relevant files in
`parsers/` before running an adapter.

Four checked-in C adapters can be rebuilt with `make c-parsers` using make and
a C99 compiler. The executables go into ignored `parsers/.build/`. CCAN now
uses its rebuilt executable through the runner after a whole-input wrapper fix;
the other three retain their historical registry entries pending adapter
review. See the [build and distribution review](docs/review-batch-140-87-81.md)
and [CCAN follow-up](docs/review-batch-149-119-118.md).

To use the fixtures without parser binaries, run `make corpus-archive` for a
small archive of the committed fixture trees and `LICENSE`, or use a partial
clone with sparse checkout. The [corpus-only instructions](docs/corpus-only.md)
give both commands and their limits.

## Run the corpus and generate reports

Run these commands from the repository root. **CLI runs overwrite the tracked
`results/logs.txt`, `results/parsing.html`, and `results/parsing_pruned.html`.**
Use a disposable copy if you want to preserve the historical reports.

For a small setup, Perl with `JSON::PP` provides an existing registry entry:

```sh
# Check the runtime and module first; this entry expects /usr/bin/perl.
/usr/bin/perl -MJSON::PP -e 'print "$^V JSON::PP $JSON::PP::VERSION\n"'

# The filter contains exact registry names, not executable paths.
filter_file=$(mktemp)
printf '%s\n' '["Perl JSON::PP"]' > "$filter_file"
python3 run_tests.py --filter="$filter_file"

# Select one fixture already in test_parsing/.
python3 run_tests.py test_parsing/y_array_empty.json --filter="$filter_file"
rm "$filter_file"
```

Each invocation replaces the preceding run's log and reports. If Perl or its
module is unavailable, select another adapter after installing/building its
dependencies. To list the exact registered names without executing parsers:

```sh
python3 -B -c 'import run_tests; print("\n".join(sorted(run_tests.programs)))'
python3 run_tests.py --help
```

For the Ruby adapter's dependencies, tested version, invocation, and default
parser behavior, see [Ruby adapter notes](docs/ruby-adapter.md).
The source builds and validation status for JSONpp, opack, and Newtonsoft.Json
are recorded in the [parser review batch](docs/review-batch-128-147-143.md).
The next [adapter review batch](docs/review-batch-142-133-124.md) covers
fastjson2, jsoncgx's two comment modes, and two clojure.data.json versions.
The [rl_json, libfyaml, and parallel-runner review](docs/review-batch-107-103-141.md)
records pinned source builds and their validation.

To attempt all registered parsers, after preparing their dependencies:

```sh
python3 run_tests.py
```

To run independent parsers concurrently, add `--jobs N` (a positive integer).
For example, `python3 run_tests.py --jobs 2` runs up to two registered parsers
at a time after their dependencies are prepared. A parser's fixtures still run
sequentially, and setup commands finish one at a time before parallel testing
starts. Logs and reports retain parser-name order. The default is `--jobs 1`.

Current CLI details:

- The optional positional argument selects fixtures in `test_parsing/`. A bare
  filename matches every fixture with that basename; a relative path such as
  `test_parsing/subdir/case.json` or `subdir/case.json`, or an absolute path
  inside the corpus, selects exactly one fixture. External paths and unmatched
  selectors are errors; this option does not parse an arbitrary external file.
- `--filter` requires a non-empty JSON array of exact registry names. Invalid
  JSON, other value types, non-string entries, and unknown names are errors.
  Repeated names select a parser once. Omit `--filter` to select all parsers.
- Invalid selections, an empty parser registry, or an empty corpus exit with
  status `2` before setup commands execute or logs/reports are overwritten.
- `--jobs` accepts a positive integer; invalid values exit with status `2`
  before the log is replaced.
- The registry's `Python 2.7.10` and `Python 3.5.2` entries are historical. The
  latter invokes `python3.5`, not whichever `python3` is installed. For a newer
  runtime, add/update an entry with an accurate label and executable.
- A parser process has a fixed five-second timeout per fixture. Some entries
  run a setup/build command before testing; that command has no such timeout.
- The script attempts to open reports when `/usr/bin/open` exists. Otherwise,
  open the HTML files manually, keeping `style.css` alongside them.

## Understand the fixtures and results

| Prefix | Suite expectation |
| --- | --- |
| `y_` | Accept the input. |
| `n_` | Reject the input. |
| `i_` | Acceptance or rejection is implementation-dependent; record either. |

These are the corpus's expectations for parsing a single JSON text. They are
not a complete compliance certification: RFC 8259 permits extensions and
implementation limits. Record parser modes and limits when interpreting a
disagreement. Acceptance alone also says nothing about numeric precision,
duplicate-key handling, or preservation of string values.

**Preserve fixture bytes.** Some inputs intentionally contain invalid UTF-8,
literal NUL bytes, incomplete structures, or unusual whitespace. Do not run a
formatter, encoding conversion, or newline normalization over the corpus.

`y_number_minus_zero.json` and `y_number_negative_zero.json` intentionally retain
identical bytes for filename compatibility. They count as two cases; see the
[duplicate review](docs/review-batch-105-113-126.md#duplicate-minus-zero).

The non-exhaustive [extension-candidate metadata](metadata/extension-candidates.json)
labels six nonfinite-number rejection fixtures from upstream issue #93 without
changing their `n_` expectations. It is not yet displayed by the runner; see
the [CCAN and extension review](docs/review-batch-92-94-93.md) for scope.

The [streaming-candidate metadata](metadata/streaming-candidates.json) marks two
root `n_` fixtures that contain two complete JSON texts; a streaming parser may
accept them, while the runner still expects one text. The
[escape, stream, and encoding review](docs/review-batch-112-91-85.md) also
explains why malformed UTF-8 and alternate-encoding fixtures retain their
original bytes.

Adapters receive a file path as the final argument, or raw bytes on stdin when
their registry entry sets `use_stdin: True`. The runner interprets outcomes as:

| Process outcome | Runner meaning |
| --- | --- |
| Exit `0` | Parser accepted the input. |
| Exit `1` | Parser rejected the input. |
| Any other return code, including signal termination | `CRASH`; investigate parser, wrapper, and environment. |
| Exceeds five seconds | `TIMEOUT`. |

Parser stdout/stderr are discarded during normal runner execution. Invoke an
adapter directly to see its diagnostics. A missing or unstartable executable
causes its remaining selected cases to be recorded as skipped. A setup command
that fails causes all selected cases for that parser to be recorded as skipped;
a missing dependency reported by a launched interpreter can instead appear as
rejection or a crash, so inspect the environment before drawing conclusions.

`results/logs.txt` contains tab-separated parser name, status, and fixture name:

| Logged status | Interpretation |
| --- | --- |
| `EXPECTED_RESULT` | A `y_` input was accepted or an `n_` input was rejected. |
| `SHOULD_HAVE_PASSED` | A `y_` input was rejected. |
| `SHOULD_HAVE_FAILED` | An `n_` input was accepted. |
| `IMPLEMENTATION_PASS` / `IMPLEMENTATION_FAIL` | An `i_` input was accepted / rejected. |
| `CRASH` / `TIMEOUT` | Execution failed or exceeded the time limit. |
| `SKIPPED_UNAVAILABLE` | The parser process could not start; this case was not executed. |
| `SKIPPED_SETUP_FAILED` | Parser setup failed; this case was not executed. |

Completed runs record one row per selected parser/fixture pair, including
expected results and skips. Fixture identifiers are paths relative to
`test_parsing/` (the existing root fixtures keep their original names).
Report generation reads **only `results/logs.txt`**, avoiding accidental mixing
with other `.txt` files. To report on an archived log using the Python report
functions, put it in a separate results directory as `logs.txt` and point
`LOGS_DIR_PATH` at that directory; do not invoke the CLI, which starts a new run.

`parsing.html` shows every recorded case; `parsing_pruned.html` keeps one
representative from each group with identical outcomes in its comparison table.
Both reports include the same per-parser counts of recorded executions, skips,
and missing records. Crashes and timeouts count as executions, not successes.
Parser detail tables retain all recorded cases even in the pruned report.

Historical three-column logs remain readable. They omitted successful `y_`/`n_`
outcomes and skips, so absent entries now appear as **`NOT_RECORDED` (`?`)**,
never inferred success. Missing-record counts cover only cases appearing
somewhere in that log; completely omitted cases or parsers cannot be recovered.
Counts from old or interrupted runs are therefore recorded counts, not proof of
complete execution. New statuses extend the format; external log consumers that
validate status names must recognize them. Invalid records raise an error.
The runner's exit status is not an aggregate pass/fail status suitable for CI.

The checked-in reports are historical examples, not measurements of your
machine or current parser releases. Known runner defects and reporting gaps
are tracked in the [assessment](docs/project-assessment.md).

## Repository guide

| Path | Purpose |
| --- | --- |
| [test_parsing/](test_parsing/) | Acceptance/rejection fixtures consumed by the runner. |
| [test_transform/](test_transform/) | 26 inputs exploring huge numbers, signed zero, similar keys, NULs, and string transformations. |
| [parsers/](parsers/) | Wrappers, library sources, project files, and historical binaries. |
| [run_tests.py](run_tests.py) | Parser registry, subprocess runner, log reader, and HTML generator. |
| [results/](results/) | Historical logs/reports and report assets. |
| [article/parsing_json.md](article/parsing_json.md) | Source of the original article. |
| [AGENTS.md](AGENTS.md) | Repository guidance for coding agents. |
| [docs/project-assessment.md](docs/project-assessment.md) | Architecture, initial findings, and upstream triage. |

The transformation fixtures were used for `results/transform.html`.
`run_tests.py` does **not** run that corpus or regenerate that report; an automated
transformation comparison remains future work.
Four new examples compare signed zero and case-distinct object keys; see the
[RFC and transformation review](docs/review-batch-77-76-71.md) for their exact
bytes and direct Python/Perl observations.

## Contribute a fixture or parser

Run the runner's regression tests with Python 3 (no third-party dependencies):

```sh
python3 -B -m unittest discover -s tests -v
```

These tests use temporary fixtures and controlled adapters to exercise exit
codes, timeouts, skips, raw stdin bytes, resource cleanup, and report accounting
for both current and historical logs, plus selection validation and preservation
of existing outputs on selection errors. Ruby adapter tests also run when
`ruby` or `ruby3.2` is available on PATH, and otherwise explicitly skip.
They do not overwrite
the checked-in reports. For runner changes, also check a known available parser
against the full corpus in a disposable copy.

For fixtures, check existing byte-level coverage, choose a descriptive prefixed
filename, and explain the expectation with an RFC section and the relevant
upstream issue or PR. Keep deliberately malformed bytes intact. Avoid removing
or renaming existing fixtures without considering downstream consumers.

For parsers, add a small adapter under `parsers/` and register its command in
`run_tests.py`. Document the library source/version, dependencies, build steps,
platforms, and parser mode. Consume the entire input, distinguish `null`/`false`/
`0` from failure, and implement the exit-code contract above. Validate both
acceptance and rejection, scalar inputs, trailing garbage, and malformed bytes.

Upstream [issues](https://github.com/nst/JSONTestSuite/issues) and
[pull requests](https://github.com/nst/JSONTestSuite/pulls) inform this fork's
work. Review each change, preserve attribution, and record local integration
and validation separately from its upstream status. The
[review queue](docs/project-assessment.md#upstream-review-queue) describes the
initial priorities.

## License

The suite is [MIT licensed](LICENSE), copyright Nicolas Seriot. Bundled parser
implementations may carry their own licenses; preserve their notices when
redistributing them.
