# Parser coverage batch: #97, #42, and #70

Reviewed on 2026-10-03 against the open upstream requests
[#97](https://github.com/nst/JSONTestSuite/issues/97),
[#42](https://github.com/nst/JSONTestSuite/issues/42), and
[#70](https://github.com/nst/JSONTestSuite/issues/70). There are no proposed
patches to cherry-pick in these issues. #97 links to Angelo Masci's C parser,
whose repository is now named [amjson](https://github.com/amwales-888/amjson).
#42 asks for the C [YAJL](https://github.com/lloyd/yajl) library; the existing
Ruby Yajl adapter is a separate binding. #70 asks for SQLite's JSON parser;
this batch uses its in-process JSON1 extension without a server or persistent
database.

| Registry entry | Source and tested version | Build/dependency/invocation | Mode |
| --- | --- | --- | --- |
| `C amjson 1e282121` | amjson commit `1e282121c4ffa923740c9fe4477b1af8f2ef3f92` (MIT; copyright Angelo Masci) | `sh parsers/build_amjson.sh`; C99 compiler, curl, tar, sha256sum. Runs `parsers/.build/amjson/test_amjson FILE`. | Whole text, 64-level depth limit. The parser itself accepts UTF-8 BOMs and malformed UTF-8 in strings. |
| `C YAJL 2.1.0` | YAJL tag 2.1.0, commit `a0ecdde0c042b9256170f2f8890dd9451a4240aa` (ISC; copyright Lloyd Hilaiel) | `sh parsers/build_yajl_c.sh`; C99 compiler, curl, tar, sha256sum. Runs `parsers/.build/yajl-c/test_yajl_c FILE`. | Default strict flags: no comments, trailing garbage, multiple values, or disabled UTF-8 validation; `yajl_complete_parse()` checks the end. |
| `SQLite JSON1 (Python sqlite3)` | Python 3.12.3 linked to SQLite 3.45.1 in this survey | Python 3 with `sqlite3` and JSON1. Runs `python3 parsers/test_sqlite_json.py FILE`. | `json_valid(CAST(? AS TEXT))` default JSON mode in a fresh in-memory connection. Raw bytes are bound as a BLOB, then SQLite casts them; no Python text decoding. Literal NUL is rejected before the call because SQLite otherwise treats `123\x00` as `123`. |

The C build scripts pin archive SHA-256 hashes and leave the source archives,
including `LICENSE` and `COPYING`, in ignored `parsers/.build/` directories.
They compile only the parser units needed by the adapters. On this Linux x86-64
host, GCC and its linker were used from an isolated `/tmp` toolchain; no system
package or historical report was changed. The C adapters read fixture paths as
raw bytes. All three adapters use exit 0 for acceptance, 1 for rejection, and
2 for argument, file, allocation, or dependency errors.

Before integration, the registry lacked these three modes. A byte-level smoke
check confirmed that `null`, `false`, `0`, `[]`, and `{}` are accepted; `null true`,
`{`, the empty file, literal NUL in a string, and comments are rejected; and a
missing file exits 2. The input `"\xff"` is accepted by amjson and SQLite but
rejected by YAJL; `EF BB BF 7B 7D` is accepted by amjson and rejected by the
other two. These are reported parser/SQLite behaviors, not normalized by the
wrappers. RFC 8259 §8.1 requires UTF-8 for interchange and permits parsers to
ignore a BOM; §2 and §7 exclude an unescaped NUL from JSON text/string syntax.

The complete 327-file `test_parsing/` corpus was run per adapter in a temporary
copy of `run_tests.py`, using its five-second per-case timeout. Initial results
were 327 explicit outcomes for each adapter, with no skips, crashes, or timeouts:

| Adapter | Expected | Implementation-dependent pass/fail | Unexpected acceptance |
| --- | ---: | ---: | --- |
| amjson | 288 | 35 / 4 | 0 |
| YAJL | 287 | 28 / 11 | 1: `n_structure_whitespace_formfeed.json` (`5B 0C 5D`) |
| SQLite before NUL guard | 287 | 35 / 4 | 1: `n_multidigit_number_then_00.json` (`31 32 33 00`) |

YAJL's form-feed acceptance is left visible as an actual parser result. The
SQLite result showed that its text path stops at a literal NUL; the wrapper now
rejects any literal NUL to validate the complete input. This guard follows RFC
8259 §2 and §7 and does not change or decode other bytes. The final post-change
survey, using the same temporary runner copy, logged all 327 outcomes per
adapter. It found no skips, crashes, or timeouts. amjson and YAJL counts were
unchanged; SQLite recorded 288 expected results, 35 implementation-dependent
passes, four implementation-dependent failures, and no unexpected acceptances.
The generated `parsing.html` and `parsing_pruned.html` remained in the temporary
directory.

No fixture bytes or tracked historical reports are changed. This adds coverage
for the requested modes; it does not establish complete RFC compliance or imply
that other SQLite builds behave identically.
