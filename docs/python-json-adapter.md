# Active-interpreter Python JSON modes

Reviewed on 2026-10-04 against local parent `e2cf08a`. The previous C adapter
survey selected a historical Python registry command as a control, which logged
327 unavailable skips. The existing standard-library modes require Python
2.7.10 or 3.5.2 and remain preserved with their original commands. Direct
invocation of the historical `test_json.py` using this host's Python 3.12.3
reproduced exit 1 with a traceback for both malformed UTF-8 (`5b 22 ff 22 5d`)
and a missing file: both failures occurred outside its parsing exception handler.

The new `test_python_json.py` adapter uses the same interpreter as the runner,
via `sys.executable`. Its registry labels contain the runtime version and
implementation reported by `platform`, rather than a historical fixed version.
The two tested modes are:

- `Python stdlib 3.12.3 (CPython, UTF-8, default constants)`
- `Python stdlib 3.12.3 (CPython, UTF-8, nonfinite constants rejected)`

These are current-runtime adapters, not upgrades to the old executable entries.
They use Python's bundled `json` module; the tested module was at
`/usr/lib/python3.12/json/__init__.py`. No dependency installation or source build
is required beyond an available Python 3 interpreter. Invocation works wherever
Python 3 and this checkout are available; validation was on Linux x86-64.

```sh
python3 parsers/test_python_json.py test_parsing/y_structure_lonely_null.json
python3 parsers/test_python_json.py --reject-nonfinite test_parsing/n_number_NaN.json
python3 -B -m unittest discover -s tests -p test_python_json_adapter.py -v
```

The final argument is the fixture path; these modes do not use stdin. The
adapter reads raw bytes, decodes UTF-8 without removing a BOM or replacing
malformed sequences, and calls `json.loads` on the resulting string. This is an
explicit UTF-8 input mode: it does not use the decoder's binary-input API, which
can recognize UTF-16/32 or consume a BOM. Unicode decoding errors return 1.
`json.loads` validates a complete text, and its returned value is ignored when
deciding acceptance, so `null`, `false`, zero, and empty strings are accepted.
File and argument errors return 2. Parsing errors, numeric conversion limits,
and `RecursionError` return 1; allocation and unexpected runtime errors return
2, which the runner classifies as CRASH rather than JSON rejection.

The default decoder accepts the NaN, Infinity, and -Infinity spellings. The
second mode installs `parse_constant` to reject those three spellings; it does
not change float conversion, duplicate-key handling, escaped surrogate behavior,
or other decoder options. In particular, both modes accept `1e999`, whose float
representation overflows, and quoted `"NaN"`. Python's `strict` decoder option
controls unescaped string control characters, not the nonfinite constant policy.
These API distinctions are described in the
[Python JSON documentation](https://docs.python.org/3.12/library/json.html).

Under [RFC 8259 §6](https://www.rfc-editor.org/rfc/rfc8259.html#section-6), NaN
and Infinity spellings are excluded; input such as `[NaN]` has bytes
`5b 4e 61 4e 5d`. Section 6 permits numeric representation limits, and §9 permits
parser limits. The tested interpreter retained its default recursion budget and
4,300-digit integer conversion limit; the adapter does not change them. Escaped
lone-surrogate sequences and duplicate keys remain accepted, so the second mode
is not a general Unicode/value-preservation validator. No corpus expectations
were changed to accommodate either mode.

The active-runtime registration also makes the existing scoped core image's
Python installation usable without a separate historical interpreter. The
[environment request #41](https://github.com/nst/JSONTestSuite/issues/41) and
[its program-list comment](https://github.com/nst/JSONTestSuite/issues/41#issuecomment-512833851)
were refreshed on 2026-10-04: the issue remains open, with one comment. This
local step does not provide the requested all-parser image. Host/runtime and
container APT revisions remain separate reproducibility limits; the core image
was not rebuilt for this adapter change.

## Validation

Validation used CPython 3.12.3 on Linux x86-64 and the 327-fixture corpus at
`e2cf08a`. Both actual registry commands ran under the default five-second
per-fixture budget, with temporary logs and both HTML reports. Each mode had
exactly one row per fixture, with no missing, extra, or duplicate records:

| Mode | Expected `y_`/`n_` | Unexpected acceptance / rejection | `i_` accept / reject | Crash / timeout / skip |
| --- | ---: | ---: | ---: | ---: |
| Default constants | 285 | 3 / 0 | 25 / 14 | 0 / 0 / 0 |
| Nonfinite constants rejected | 288 | 0 / 0 | 25 / 14 | 0 / 0 / 0 |

The three default-mode acceptances were `n_number_NaN.json`,
`n_number_infinity.json`, and `n_number_minus_infinity.json`. The constant-policy
mode rejected all three. The combined opt-in CI verdict was 1 because of the
native default-mode extensions; it does not indicate adapter failures. Zero
unexpected results for the other mode applies to this corpus and runtime only.

The focused subprocess tests exercised valid scalars, complete text, malformed
UTF-8, UTF-16/32 rejection, BOM preservation, literal NUL, named constants,
overflow, duplicate keys, escaped surrogates, missing paths, directories, bad
argument counts, recursion limits, and the integer-digit limit. Mocked allocation
and unexpected decoder failures returned 2. All five focused tests passed.
The full regression suite ran 107 tests successfully with 19 optional dependency
skips, using the isolated C compiler for the native adapter tests.
`git diff --check` passed; fixture bytes and tracked historical reports were
preserved. Logs, reports, and the audited summary are at
`/tmp/jsonsuite-python-json-run-mv3252ub`; that location is ephemeral.
