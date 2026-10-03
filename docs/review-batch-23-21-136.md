# Parser coverage and octal-escape review: #23, #21, #136

Reviewed on 2026-10-03. Upstream [#23](https://github.com/nst/JSONTestSuite/issues/23)
requests testing Patrick Lehmann's [JSON-for-VHDL](https://github.com/Paebbels/JSON-for-VHDL)
with GHDL. The author reported an external PowerShell survey in the issue's
discussion; this batch adds a runner adapter for the current local corpus.
Upstream [#21](https://github.com/nst/JSONTestSuite/issues/21) requests broader
C++ comparison. The registry already contains nlohmann/json, RapidJSON,
sajson, JSONpp, and simdjson modes, so this batch adds a distinct
[picojson](https://github.com/kazuho/picojson) mode from the issue's list.
Upstream [#136](https://github.com/nst/JSONTestSuite/issues/136) is already
locally covered by Simon McVittie's fixture from
[PR #137](https://github.com/nst/JSONTestSuite/pull/137); it was verified,
without adding a duplicate.

| Registry mode | Pinned source and license | Build, platform, invocation, and mode |
| --- | --- | --- |
| `C++ picojson 111c9be5` | picojson commit `111c9be5188f7350c2eac9ddaedd8cca3d7bf394`, BSD-2-Clause; copyright Cybozu Labs and Kazuho Oku | `sh parsers/build_picojson.sh` with a C++17 compiler, curl, tar, and sha256sum. Tested on Linux x86-64 with GCC 13.3. Runs `parsers/.build/picojson/test_picojson FILE`. Reads all bytes, calls picojson's iterator parser, then accepts only JSON whitespace through end of input. Default floating-point mode. |
| `VHDL JSON-for-VHDL 2ab1ebc2 (GHDL 4.1)` | JSON-for-VHDL commit `2ab1ebc2c788ececce152a49ffda706f84570e95`, Apache-2.0; copyright Patrick Lehmann | `sh parsers/build_vhdl_json.sh` with GHDL 4.1, curl, tar, and sha256sum. Tested with GHDL mcode 4.1.0 on Linux x86-64. Runs `python3 parsers/test_vhdl_json.py FILE` with `JSONTESTSUITE_GHDL` if GHDL is outside `PATH`. VHDL-2008, raw file bytes, `jsonParseStream` mode. |

The build scripts verify SHA-256-pinned archives and preserve their source
trees, `LICENSE`/`LICENSE.md`, and notices in ignored `parsers/.build/`.
GHDL 4.1.0 and GCC 13.3 were extracted under `/tmp` for this survey; no
system packages were installed. Missing GHDL or build output causes a runner
setup skip. The VHDL source's `jsonLoad`/`jsonReadFile` path strips line
boundaries and leading whitespace; the adapter instead reads each fixture byte
as a VHDL `character` and calls `jsonParseStream` directly. The VHDL record
uses 16-bit content indices, so files of 65,535 bytes or more reject as an
implementation size limit. A simulator failure or missing result marker exits
2, rather than being disguised as JSON rejection.

Smoke checks included `null`, `false`, `0`, objects and arrays, incomplete
input, trailing text, malformed UTF-8, BOMs, literal NUL, missing files, and
the octal-escape fixture. `null` accepts in both modes; `null true` rejects.
picojson accepts raw `22 FF 22` inside a string in its default mode and
rejects the UTF-8 BOM before `{}`. JSON-for-VHDL accepts `null` but rejects
`null` followed by LF; this confirms the adapter exposes line boundaries
instead of normalizing them away. Both adapters return 2 for missing files.

Full 327-case surveys used temporary runner copies and generated temporary
HTML reports. The final counts were:

| Mode | Expected | Implementation pass/fail | Unexpected acceptance | Unexpected rejection | Crash | Timeout/skip |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| picojson | 274 | 19 / 20 | 14 | 0 | 0 | 0 |
| JSON-for-VHDL | 219 | 33 / 5 | 55 | 3 | 12 | 0 |

All 14 picojson unexpected acceptances are malformed numbers. Examples are
`n_number_00.0.json` (`5B 30 30 2E 30 5D`) and
`n_number_-2..json` (`5B 2D 32 2E 5D`). Its `_parse_number` accumulates number
characters before calling `strtod`, which explains these observed extensions.
Its numeric overflow throws `std::overflow_error`; the wrapper maps that
documented parser limit to rejection, leaving no adapter crashes. RFC 8259 §6
requires a single zero before a fraction and at least one digit after the
decimal point.

JSON-for-VHDL's 55 unexpected acceptances include 29 numbers, 18 strings,
four arrays, and four structure cases. It accepts the incomplete array
`n_array_incomplete.json` (`5B 22 78 22`) and the invalid escape
`n_string_escape_x.json` (`5B 22 5C 78 30 30 22 5D`), for example. The three valid
texts it rejects contain LF, including `y_structure_trailing_newline.json`
(`5B 22 61 22 5D 0A`); RFC 8259 §2 permits LF as whitespace. Twelve cases
cause simulator failure, including three `y_` cases and
`i_structure_500_nested_arrays.json`. The pinned library uses VHDL
`report ... severity FAILURE` in `ST_CLOSED` for some inputs, and an incomplete
input reaches an out-of-bounds access. These are logged as `CRASH`; an `i_`
fixture never treats a crash as success. The broad acceptance and failure
patterns mean this is a survey of the current VHDL parser, not a validator
for corpus expectations.

For #136, `test_parsing/n_string_octal_escape.json` is still exactly
`5B 22 5C 30 31 32 22 5D 0A`, with Git blob
`f18a5b57695d97ff650e51f4a09b5332baf686d6`, matching reviewed PR #137
head `91df0e5a8cadcf95ae5be96eed5b2c4a4fb47218`. Issue #136 and PR #137
remain open upstream. Both new adapters rejected this fixture. RFC 8259 §7
lists allowed escapes and does not include a backslash followed by ASCII `0`;
the fixture is a syntax rejection, not a Unicode or number-limit case.

No corpus fixture or tracked historical report changed. Other parsers named
in #21, including folly and JSON Spirit, remain unreviewed here.
