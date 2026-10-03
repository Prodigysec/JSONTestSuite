# Review batch: jq and Node.js parser modes

Reviewed on 2026-10-03 against local baseline `1f7805d`. Upstream issues
[#39](https://github.com/nst/JSONTestSuite/issues/39),
[#25](https://github.com/nst/JSONTestSuite/issues/25), and
[#83](https://github.com/nst/JSONTestSuite/issues/83) remain open. Their bodies
and discussions were refreshed; none has a proposed PR base/head revision to
integrate. #39 points to [jqlang/jq#1264](https://github.com/jqlang/jq/issues/1264),
whose six comments discuss streaming, extension modes, and historical jq 1.5
results. #25 asks to restore jq testing via a historical Python 2 script. #83
asks for more specific JavaScript engine reporting and browser engines.

## Adapter provenance and invocation

| Registry entry | Source and dependency | Build and invocation | Tested platform and mode |
| --- | --- | --- | --- |
| `jq (raw-slurp fromjson)` | [jq](https://jqlang.org/jq/), executable on `PATH`; tested `jq-1.7` | No repository build or vendored binary; use the command below. | Linux x86_64, one-text `fromjson` on jq's decoded raw-slurp string. |
| `Node.js V8 JSON.parse (strict UTF-8)` | [Node.js](https://nodejs.org/), executable on `PATH`; tested Node `v24.21.0`, V8 `13.6.233.17-node.53` | No repository build or vendored binary. `node parsers/test_node_json_utf8.js fixture.json`. Requires Node 18.14+ for [`buffer.isUtf8`](https://nodejs.org/api/buffer.html#bufferisutf8input). | Linux x86_64, one complete JSON text, strict UTF-8 bytes, `JSON.parse`. |

Other platforms with these executables on `PATH` may work but were not tested.
The registry names describe engine and mode without pretending to detect a
runtime version. The direct jq invocation and version checks are:

```sh
jq -Rs 'try (fromjson | empty) catch (halt_error(1))' fixture.json
jq --version
node -p 'JSON.stringify({node:process.version,v8:process.versions.v8})'
```

The historical `JavaScript` registry entry still points to `/usr/local/bin/node`
and the old `test_json.js`; it is left intact for report/name compatibility.
The old `parsers/test_json-jq.py` is also retained as a historical script, but
its Python 2 syntax and `/Users/nst/...` paths are unsuitable for the current
runner. The new jq entry calls jq directly.

## jq: restore execution while enforcing one text

The [jq 1.7 manual](https://jqlang.org/manual/v1.7/) says the normal `.` filter
reads a *stream* of JSON values. That behavior explains the historical
`n_structure_object_with_trailing_garbage.json` example: it contains one object
followed by one string, so a stream parser can emit two results. The runner's
contract is one complete JSON text ([RFC 8259 section 2](https://www.rfc-editor.org/rfc/rfc8259.html#section-2)),
and the root `n_` expectation remains appropriate for that contract.

`-Rs` supplies the entire file to jq as one decoded string. `fromjson` parses
that string as one JSON text; `empty` avoids printing the parsed value, including
valid `null` or `false`. A caught parse error calls `halt_error(1)`, while a
missing file or filter/runtime failure keeps its non-1 code. Thus the direct
registry command obeys exit `0`/`1`/other without spawning a child wrapper.
The mode has a material limit: jq's raw-input decoder can replace malformed
UTF-8 before `fromjson` sees it. For example, jq 1.7 accepts the five bytes
`5b 22 ff 22 5d` in `i_string_invalid_utf-8.json` in this mode. It also
accepts the BOM-prefixed `i_structure_UTF-8_BOM_empty_object.json`. These are
recorded as implementation-dependent observations, not evidence that those
original bytes are well-formed UTF-8.

## Node.js/V8: identify the engine and preserve input bytes

The old wrapper passes a `Buffer` directly to `JSON.parse`; JavaScript then
coerces it to a string, potentially replacing malformed UTF-8. The new wrapper
checks the original bytes with `buffer.isUtf8` before decoding, preserves any
BOM for `JSON.parse` to decide, and invokes `JSON.parse` once on the whole
string. It returns `0` for valid scalars including `null`, `false`, and `0`,
`1` for malformed UTF-8 or JSON syntax, and `2` for missing arguments, unreadable
files, or an unsupported Node runtime. Unexpected errors remain visible as
non-1 failures. The new registry label explicitly names Node.js/V8 and its
strict UTF-8 mode. A browser-engine matrix, WebKit/SpiderMonkey adapters, and
version-specific historical Node results are still separate work for #83.
No browser executable was available in this test environment.

## Full-corpus observations

The current `test_parsing/` tree has 327 fixtures: 94 `y_`, 194 `n_`, and 39
`i_`. A disposable copy of `run_tests.py` with symlinks to the current corpus
and parsers ran both entries with `--jobs 2`, generated full and pruned reports,
and recorded one log row for each of the 654 selected pairs. Neither parser
was skipped, crashed, or timed out. Tracked historical reports were untouched.

| Mode | Expected `y_`/`n_` | `i_` accepted | `i_` rejected | `n_` accepted |
| --- | ---: | ---: | ---: | ---: |
| Node.js/V8 strict UTF-8 | 288 | 25 | 14 | 0 |
| jq 1.7 raw-slurp `fromjson` | 264 | 28 | 11 | 24 |

jq's 24 `n_` acceptances were all number cases: leading zeros, leading plus,
missing integer/fraction digits around a decimal point, or nonfinite spellings.
They are parser-extension observations under [RFC 8259 section 9](https://www.rfc-editor.org/rfc/rfc8259.html#section-9);
the strict syntax expectations and fixture bytes were not changed. The two
multiple-text root cases were rejected in this mode. The historical jq issue's
2016/2017 results used different jq versions and default streaming behavior,
so they are not directly comparable with this 2026 jq 1.7 run.

## Validation and limits

Focused contract checks covered scalars, containers, empty input, trailing
text, malformed bytes, BOM handling, and missing files. The complete Python
suite ran 72 tests: 53 passed and 19 optional-runtime tests skipped, using
isolated GCC/make and shared libraries under `/tmp`. The final corpus run
produced both reports in a temporary directory. No browser, Rust, or PHP
runtime survey was performed in this batch. The runner exit code remains a
process-completion status; the 24 jq discrepancies are visible in the log and
report, rather than making the command fail.
