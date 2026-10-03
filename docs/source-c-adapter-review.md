# Source-built C adapters: issue #140 follow-up

Reviewed on 2026-10-03 against local parent `caa8222`. Upstream
[issue #140](https://github.com/nst/JSONTestSuite/issues/140) was refreshed:
it remains open, has no comments, and requests source builds rather than
platform-specific binaries. There is no contribution revision to integrate.
The earlier [build review](review-batch-140-87-81.md) added build targets;
this local follow-up repairs and registers the remaining three wrappers.
Local integration commit: `4303a068fdf4a796b21a280af4d0e406a61c68f2`.

## Sources, build, and invocation

The existing registry names are retained so filter files continue to work.
Their commands now use ignored native builds rather than the historical
checked-in binaries. Each mode runs its individual Makefile target as setup;
setup failure is recorded as an explicit skip by the runner. Historical
binaries are preserved. Existing source copyright and license notices are
preserved, including cJSON's MIT notice and JSON Checker's JSON.org notice.

| Registry mode | Vendored source identity and native mode | Makefile target |
| --- | --- | --- |
| `C jsmn` | Untagged checked-in source; `jsmn.c` Git blob `e7765eb1d100164cd1a165b640f8113f4761eb6d`, `jsmn.h` blob `1a952fd36ce8c532ddb3ddd47d3f6e6eb50b797e`; non-strict tokenizer | `parsers/.build/test_jsmn` |
| `C JSON Checker` | Source dated 2007-08-24; original library blob `50f054fc8ad105b9c17dfa7911f3dfd97f6dad92`; container-only mode with stack size 20 | `parsers/.build/jsonChecker` |
| `C cJSON 1.7.3` | Header version 1.7.3; `cJSON.c` blob `3dcde3d274f3649f1bd3fcd312c9c81efa58f1cb`; native parsing with complete-string option, double numbers, default nesting limit 1000 | `parsers/.build/test_cJSON_1_7_3` |

Build on a POSIX system with make, a C99 compiler, the platform C library, and
libm for cJSON:

```sh
make c-parsers
parsers/.build/test_jsmn test_parsing/y_structure_lonely_null.json
parsers/.build/jsonChecker test_parsing/y_array_empty.json
parsers/.build/test_cJSON_1_7_3 test_parsing/y_structure_lonely_null.json
python3 -m unittest discover -s tests -p test_source_c_adapters.py -v
```

The executable's final argument is the fixture path; these modes do not use
stdin. Setup uses `make` and honors the Makefile's compiler overrides and
standard environment variables. Validation was on Linux x86-64; other POSIX
platforms were not separately tested. Vendored source is fixed by this Git
checkout, but the host compiler and C library are not pinned by the build.

## Reproductions and repairs

Previously compiled original wrappers reproduced these defects before edits:
jsmn rejected a valid 201-number array because of its hard-coded 100-byte input
length and 50-token budget, and accepted `{} []` as multiple texts. cJSON
accepted `31 32 33 00 74 72 75 65` (`123`, literal NUL, `true`) because its string
API stopped at NUL. JSON Checker rejected `5b 22 c3 a9 22 5d` (`["é"]`) because
the wrapper passed signed `char` values to its nonnegative-character API.
All three returned rejection for a missing file instead of an adapter error.

The shared binary reader checks seeking, length, allocation, read completion,
and close errors, returning 2 for failures. Buffers are released on every
wrapper exit after a successful read. Argument errors also return 2. The
wrappers return 0 for acceptance and 1 for parser rejection, so runtime errors
remain distinct from rejection in the runner.

jsmn now receives the actual file length and sufficient token storage for at
most one token per input byte. It checks that the first root token occupies
all non-whitespace input, accounting for string tokens excluding their quotes.
Literal NUL is rejected before tokenization. Inputs of `INT_MAX` bytes or more
are rejected because token positions use signed `int`; token-allocation errors
return 2. The old wrapper's `JSMN_STRICT` definition was confined to its own
translation unit and never affected the separately compiled library. The new
wrapper explicitly retains the default non-strict library mode. It does not
add a second JSON grammar validator or claim that tokenization proves syntax.

JSON Checker receives each original byte as `unsigned char`, feeds the whole
file, and uses its completion check. Its constructor now checks both allocation
results; the wrapper reports failure as 2. This is the only change to its
vendored library, and does not alter its grammar. Stack size 20 includes the
initial sentinel, allowing 19 nested containers; a 20-container smoke case was
rejected. Top-level scalars remain unsupported by this legacy parser, rather
than being wrapped or treated as falsey results.

cJSON rejects literal NUL before invoking its NUL-terminated API, requests
complete-input parsing, and checks the returned end pointer against the actual
file length. It accepts successfully parsed scalar values without printing
or serializing them. Allocator hooks report parser allocation failures as 2.
Native BOM handling, permissive whitespace, string behavior, and numeric
parsing remain observable; the adapter does not strip or replace bytes.

RFC 8259 §§2 and 7 exclude literal NUL anywhere in a JSON text, while the
escaped bytes `5c 75 30 30 30 30` (`\u0000`) are allowed in a string.
Sections 2–3 allow scalar texts, so JSON Checker's scalar rejection is recorded
as an unexpected rejection. Implementation depth and size limits are permitted
by §9. No fixture bytes or classifications were changed for these modes.

## Validation and results

Linux x86-64 validation used GCC 13.3.0 (Ubuntu
`13.3.0-6ubuntu2~24.04.1`), GNU make 4.3, glibc 2.39, and Python 3.12.3.
The compiler, binutils, and make were extracted under `/tmp` without changing
system packages. Builds with `-O2 -Wall -Wextra` produced no warnings.
Corpus revision was `caa8222`, containing 327 parsing fixtures.

The actual registered commands and Makefile setup ran through the runner's
five-second per-case budget. Both temporary HTML reports were generated. Log
audits found exactly 327 distinct rows per C mode, no missing or extra
fixtures, and no duplicate outcomes:

| Mode | Expected `y_`/`n_` | Unexpected acceptance | Unexpected rejection | `i_` accept / reject | Crash / timeout / skip |
| --- | ---: | ---: | ---: | ---: | ---: |
| jsmn | 190 | 98 | 0 | 35 / 4 | 0 / 0 / 0 |
| JSON Checker | 270 | 6 | 12 | 34 / 5 | 0 / 0 / 0 |
| cJSON 1.7.3 | 270 | 18 | 0 | 24 / 15 | 0 / 0 / 0 |

All three accepted `i_string_invalid_utf-8.json` in their native byte-oriented
modes. JSON Checker and jsmn rejected the UTF-8 BOM fixture; cJSON accepted it
through its native BOM handling. These observations are recorded under `i_`,
without adding a UTF-8 decoder or removing the BOM in the wrappers.

These are native parser observations, not full RFC compliance. In particular:

- jsmn's tokenizer accepts malformed primitives, numbers, containers, and
  unescaped string controls. For example, it accepts `[1,]` (`5b 31 2c 5d`),
  which is excluded by §5, and `[NaN]` (`5b 4e 61 4e 5d`), excluded by §6.
- JSON Checker accepts six numbers missing required fraction digits, including
  `[-2.]` (`5b 2d 32 2e 5d`), excluded by §6. Its 12 unexpected rejections are
  all valid scalar texts, consistent with its container-only grammar.
- cJSON accepts seven leading-zero numbers, six numbers missing fraction
  digits, and `[-.123]` (`5b 2d 2e 31 32 33 5d`), all excluded by §6. It also
  accepts `\uqqqq` inside a string, two unescaped newline/tab strings, and
  `[\x0c]` (literal formfeed, `5b 0c 5d`), excluded by §§7 and 2 respectively.

The C batch's opt-in CI verdict is 1 because of these native discrepancies.
A historical Python 2.7 registry mode selected as an initial control was
unavailable and explicitly logged 327 skips. A separate available SQLite JSON1
control (Python sqlite3, SQLite 3.45.1) logged all 327 fixtures: 288 expected
results and 35/4 implementation-dependent results, without discrepancies,
crashes, timeouts, or skips.

Focused native regressions cover long files, token capacity, trailing input,
literal versus escaped NUL, scalars, UTF-8 bytes, missing paths, directories,
and bad argument counts. GNU linker fault injection verifies reader allocation,
jsmn token allocation, JSON Checker object/stack allocation, and cJSON parser
allocation all return 2. The full regression suite passed 102 tests with 19
optional dependency skips. `git diff --check` passed.

Temporary C logs, reports, and full discrepancy lists are at
`/tmp/jsonsuite-source-c-run-ebvs44dc`; the SQLite control is at
`/tmp/jsonsuite-source-c-control-jzjqn4j9`. These paths are ephemeral. Fixture
bytes and tracked historical reports were preserved. This advances the local
source-build integration for #140; the upstream issue remains open, and
universal builds across all historical parsers remain outside this batch.
