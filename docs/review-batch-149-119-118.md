# Review batch: numeric limits, trailing NUL, and DEL

Reviewed on 2026-10-03 against local baseline `31fad4f`. The upstream issues
[#149](https://github.com/nst/JSONTestSuite/issues/149),
[#119](https://github.com/nst/JSONTestSuite/issues/119), and
[#118](https://github.com/nst/JSONTestSuite/issues/118) remain open. Their public
issue bodies and discussions were refreshed. #149, last updated 2026-05-27,
and #118, last updated 2020-11-05, had no comments. #119, last updated
2021-10-14, had one comment explaining that NUL is not JSON whitespace.
These are issues without proposed base/head revisions or PR patches.

## #149: separate number syntax from implementation limits

[RFC 8259 section 6](https://www.rfc-editor.org/rfc/rfc8259.html#section-6)
allows the syntax of all four reported numbers, while sections 6 and 9 allow
implementations to limit accepted range and precision. A binary32-only parser
may reject the three large positive exponents or the tiny negative fraction.
Such rejection is an implementation limit, not a JSON grammar error. The issue
calls `y_number.json` `j_number.json` and pluralizes the fraction-exponent
filename; the table uses paths verified in this checkout.

| Previous root path | Current root path | Exact bytes |
| --- | --- | --- |
| `y_number.json` | `i_number_123e65.json` | `[123e65]` |
| `y_number_double_close_to_zero.json` | `i_number_double_close_to_zero.json` | `[-0.` + 77 ASCII `0` bytes + `1]` + LF |
| `y_number_real_exponent.json` | `i_number_real_exponent.json` | `[123e45]` |
| `y_number_real_fraction_exponent.json` | `i_number_real_fraction_exponent.json` | `[123.456e78]` |

Each renamed file retains its exact previous bytes, including the one final
LF. The other three have no final newline. A new
`y_number_fraction_exponent_exact.json` contains the eight bytes `5b 31 32 2e
35 65 32 5d` (`[12.5e2]`), with no final newline and no byte-identical root
case. It retains a modest, exactly representable fraction-plus-exponent syntax
example under `y_`. It does not imply that RFC 8259 requires any particular
minimum numerical range. The new corpus has 326 fixtures: 93 `y_`, 194 `n_`,
and 39 `i_`.

**Compatibility impact:** the four former `y_` paths are no longer corpus
selectors, and fresh logs use their `i_` names and expectations. Tracked
historical logs and HTML still name the old paths; they remain untouched as
snapshots of earlier runs. Re-rendering an old log against the new corpus may
show a missing preview for those paths. Consumers keyed by fixture name should
use the mapping above. Acceptance of an `i_` case says nothing about exact
numeric value preservation; that needs transformation assertions.

## #119: literal NUL after a complete number

`n_multidigit_number_then_00.json` is exactly `31 32 33 00` (`123` followed by
a literal NUL), with no final newline. [RFC 8259 section 2](https://www.rfc-editor.org/rfc/rfc8259.html#section-2)
defines one JSON text as `ws value ws`, where `ws` consists only of space,
horizontal tab, LF, and CR. NUL is none of them, so the existing `n_`
expectation is correct. This differs from the valid escaped NUL inside a
quoted string reviewed in [#94](review-batch-92-94-93.md#94-escaped-nul-is-valid-json-syntax).

The checked-in CCAN wrapper did have a reproducible input-handling defect:
it read all four bytes, appended a C terminator, then passed the buffer to
`json_validate(const char *)`. That API stopped at the input NUL and accepted
the apparent `123`. The tracked historical log also records CCAN's unexpected
acceptance of this fixture. The wrapper now rejects any embedded NUL before
calling that C-string API, checks file reads and closes, and exits `2` for
invocation/I/O errors rather than reporting them as JSON rejection. It still
passes all other bytes unchanged to the vendored parser.

The `C ccan` registry entry now builds from the checked-in source with
`make -C <repo> parsers/.build/test_ccan` and invokes that executable with the
fixture path. The root `make c-parsers` target also includes it. The source is
`parsers/test_ccan_json/json/json.c` and `json.h`, with the existing license
notice intact. This unversioned vendored snapshot has `json.c` Git blob
`2f0452aebe568277f554072eff7685bdd6b33fc9`; the tested build used GCC
13.3.0 on Linux x86_64 and the platform C library. It needs make and a C99
compiler, downloads nothing, and writes only ignored `parsers/.build/` output.
No cross-platform build was run.

## #118: DEL is allowed unescaped by the JSON string grammar

`y_string_unescaped_char_delete.json` is exactly `5b 22 7f 22 5d`
(`[` + quote + DEL + quote + `]`). [RFC 8259 section 7](https://www.rfc-editor.org/rfc/rfc8259.html#section-7)
requires escaping U+0000 through U+001F and its `unescaped` production
includes U+007F. DEL's general Unicode control classification does not change
that explicit JSON grammar. Both Perl JSON::PP and CCAN accepted the existing
fixture; no corpus change is needed.

## Validation and remaining limits

The four renamed fixture bytes match their previous `HEAD` blobs. A direct
CCAN source build reproduced the old `123 00` acceptance, then rejected it
after the wrapper fix. Focused adapter checks covered valid scalars, empty and
malformed input, trailing text, embedded NUL, and missing arguments/files.
All 66 repository tests ran with isolated make/GCC 13.3.0: 47 passed and 19
optional-runtime tests were skipped.

A temporary copy of the runner and current corpus exercised both registered
`C ccan` and Perl JSON::PP 4.16 (Perl 5.38.2) across all 326 fixtures, with
no skips or missing rows. Perl recorded 287 expected results, 19
implementation-dependent acceptances, and 20 implementation-dependent
rejections, with no unexpected outcomes. CCAN recorded 282 expected results,
15 implementation-dependent acceptances, 24 implementation-dependent
rejections, three unexpected rejections of valid escaped-NUL strings, and two
segmentation faults on deeply nested malformed arrays. The latter are native
parser limitations, not wrapper rejection; their fixtures are
`n_structure_100000_opening_arrays.json` and
`n_structure_open_array_object.json`. Both reports were generated in `/tmp`;
tracked historical results were not regenerated. The runner's zero exit status
does not imply those CCAN discrepancies passed.
