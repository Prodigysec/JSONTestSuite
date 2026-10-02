# PRs #107 and #103; issue #141

Reviewed on 2026-10-03 against the current local checkout. This is a local
integration of the proposed adapters and runner feature, with substantive
changes, rather than a cherry-pick or an upstream merge. Historical reports
and fixture bytes were not changed. The implementation commit is `f6632f3`.

## Tcl rl_json: PR #107

[PR #107](https://github.com/nst/JSONTestSuite/pull/107) remains open. Its
reviewed base is `9f23c68b521dd700e8c99151d6dc1c5c52a0246e` and head is
`1a2431ed6e34f2b6ac0ce79a616ef8078b9f1688` (author `snoe925`). There
are no formal reviews. The discussion notes that rl_json's default accepts
comments. The proposed Tcl script reads standard input, calls `json parse`,
maps every Tcl error to rejection, and its shell wrapper expands `$*` without
preserving arguments. The local adapter instead uses rl_json's documented
`json valid -extensions {}` mode, which checks the complete text, rejects
comments, and accepts scalar values regardless of truthiness. It separates
missing package/runtime failures from JSON rejection.

The tested dependency is RubyLane [rl_json v0.17.6](https://github.com/RubyLane/rl_json/releases/tag/v0.17.6),
source archive SHA-256 `c00da959d85ec1895ccf375f7551138d3a53a3d8af8387513b4370e007ca8655`.
Build with `parsers/test_rl_json_0_17_6/build.sh`; it verifies the archive,
extracts it into the ignored `.build` directory, configures against Tcl, and
builds the extension without its optional Pandoc documentation target. Requires
POSIX shell, curl, sha256sum, tar, a C compiler, make, Tcl 8.6 or 9.0 and its
development headers/stub library, and Python 3 for the adapter. For a Tcl
installation outside system paths, set `TCL_CONFIG_DIR` and `TCL_INCLUDE_DIR`
to the corresponding directories before building. Invocation is the registry's
`python3 parsers/test_rl_json_0_17_6/TestJSONParsing.py` with raw fixture bytes
on stdin. `RL_JSON_PACKAGE_DIR` and `TCLSH` may override the package directory
and interpreter for isolated testing.

The Python entry point performs strict UTF-8 byte decoding before Tcl receives
the text because Tcl 8.6 silently maps malformed byte sequences to characters
when reading them. It does not strip a BOM or repair input. Invalid UTF-8
returns rejection; missing package/interpreter returns an adapter error. This
tests strict UTF-8 input to rl_json's character API, not rl_json's optional
UTF-16/UTF-32 decoder. The release archive retains RubyLane's license notice.

## libfyaml: PR #103

[PR #103](https://github.com/nst/JSONTestSuite/pull/103) remains open. Its
reviewed base is `9f23c68b521dd700e8c99151d6dc1c5c52a0246e` and head
is `d32ca1f2a071c1425553ae908c625d2ff6805696` (author `pantoniou`).
No reviews or discussion were present. Its proposed script calls
`fy-testsuite --streaming --json=force $1`, but converts a missing executable
to exit `1` and does not quote the fixture path. In v0.9.6 the equivalent
command is `fy-tool --testsuite --streaming --json=force -- FILE`. The local
wrapper quotes the path, checks that the input and build exist, and returns
`2` for invocation errors rather than reporting them as JSON rejection. The
streaming JSON mode rejects a second JSON text or trailing non-whitespace
after one text.

The tested dependency is [libfyaml v0.9.6](https://github.com/pantoniou/libfyaml/releases/tag/v0.9.6),
source archive SHA-256 `a59cc3331e2eb903ec36933ad52a45888041cac31e44f553a00511131242c483`.
Build with `parsers/test_libfyaml_0_9_6/build.sh`; it verifies the archive and
compiles `fy-tool` under the ignored `.build` directory. Requires POSIX shell,
curl, sha256sum, tar, m4, a C compiler, and make. The tested CLI is a Unix-like
build; upstream also supports other platforms, but this adapter has not been
verified there. The release source retains its MIT license notice.

Invoke it through the registry's
`sh parsers/test_libfyaml_0_9_6/run.sh FILE`; `FY_TOOL_BIN` may override the
binary path for isolated testing.

## Parallel runner: issue #141

[Issue #141](https://github.com/nst/JSONTestSuite/issues/141) remains open and
had no comments when reviewed. `--jobs N` now runs up to N independent parser
configurations concurrently. Each parser still visits fixtures sequentially,
with the existing five-second timeout for each fixture. Setup commands are
serialized before parser execution to avoid concurrent writes to shared build
output. Only the main thread writes the log, replaying completed parser events
in sorted registry order, so reports remain deterministic. The default
`--jobs 1` retains serial operation. Invalid job counts fail before replacing
the log. This addresses parser-level parallelism, not per-fixture parallelism.

## Validation

The dependency builds and corpus runs were tested on Linux x86_64, Python
3.12.3, Tcl 8.6.14, Perl 5.38.2 / JSON::PP 4.16, and the pinned libfyaml and
rl_json versions above. GCC, make, m4, binutils, and Tcl development files
unavailable on the host were extracted under `/tmp`; no system packages were
installed. Both committed build scripts succeeded with the pinned archives.
The corpus revision is the local parent commit `f8b195a` with 324 fixtures.

Direct adapter probes exercised `null`, `false`, `0`, a valid object, a valid
non-ASCII string, trailing garbage, a second JSON text, empty input, comments,
a trailing comma, BOM input, malformed UTF-8, and UTF-8 encoding of a surrogate.
Both adapters returned `0` for the valid cases and `1` for the invalid cases;
both accepted the BOM case. Missing dependencies and files were not reported
as JSON rejection (exit `2` from each wrapper). Each probe was bounded to five
seconds.

A temporary copy of the runner and corpus selected both new adapters plus the
known Perl JSON::PP control and ran `--jobs 2`. All **972** parser/fixture
commands executed, one record per fixture per parser, with no missing rows,
duplicates, skips, crashes, or timeouts. Each parser had **289** expected
results; the 35 implementation-dependent cases split as follows:

| Parser | Accepted `i_` | Rejected `i_` |
| --- | ---: | ---: |
| Tcl rl_json 0.17.6 | 22 | 13 |
| C libfyaml 0.9.6 | 12 | 23 |
| Perl JSON::PP 4.16 | 15 | 20 |

The temporary full and pruned HTML reports were generated from those logged
rows. Focused runner tests cover actual parser overlap and stable log order,
timeouts and unavailable executables during parallel work, and invalid job
counts that leave the log untouched. The command
`python3 -B -m unittest discover -s tests -v` passed 58 tests, with 19 optional
adapter tests skipped because their
separate dependencies were unavailable. The new native-adapter contract tests
ran against both pinned builds, including a fixture path containing a space.

Remaining scope: historical platform-specific parser configurations and other
toolchains were not rebuilt. Parser acceptance does not prove that values are
preserved or all RFC 8259 requirements are met. No reports were published.
