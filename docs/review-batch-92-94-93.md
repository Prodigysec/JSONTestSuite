# Review batch: nested CCAN cases and extension candidates

Reviewed on 2026-10-03 against upstream issues
[#92](https://github.com/nst/JSONTestSuite/issues/92),
[#94](https://github.com/nst/JSONTestSuite/issues/94), and
[#93](https://github.com/nst/JSONTestSuite/issues/93). All three remained open.
The public issue API showed no comments on #92 (last updated 2019-04-22), one
agreement on #94 (last updated 2019-08-26), and one comment on #93 naming six
nonfinite-number fixtures (last updated 2019-04-22). These are issues, so there
are no proposed base/head revisions to merge. The local source baseline was
`28ef54c`; this review did not run unreviewed upstream code.

## #92: two identical CCAN cases

`parsers/test_ccan_json/json/_test/nst_files/n_172.json` and `n_175.json` both
contain `5b 22 5c 22 5c 22 5c 22 5c 22 22 2c 20 2e 35 5d` (SHA-256
`c28f64ade65fab04e9ced46a826c6779188f7754c604fb3f4c3e8b80e3418148`).
They are generated from two identical `invalid` lines in CCAN's vendored
`json/_test/test-strings` by `x.py`. The root `test_parsing/` corpus has no
byte-identical case; the root runner never selects these nested files. Deleting
one generated copy would leave the duplicate source line and change a vendored
test identifier, so both remain. The issue also mentions jq's multiple-text
mode: `n_31.json` is `22 68 69 22 22 22` (`"hi"""`), which is invalid as one
JSON text under [RFC 8259 section 2](https://www.rfc-editor.org/rfc/rfc8259.html#section-2).
Stream acceptance must be interpreted in that separate mode; it does not
reclassify the fixture.

## #94: escaped NUL is valid JSON syntax

CCAN's vendored `n_223.json` contains exactly eight bytes, `22 5c 75 30 30
30 30 22` (`"\\u0000"`), with no trailing newline. That is a valid top-level
JSON string: [RFC 8259 section 2](https://www.rfc-editor.org/rfc/rfc8259.html#section-2)
permits a scalar JSON text and [section 7](https://www.rfc-editor.org/rfc/rfc8259.html#section-7)
permits the escape for U+0000. This differs from a literal `00` byte in input.
The root corpus already has `y_string_null_escape.json`, whose bytes are an
array containing the same escape, and a separate negative case for a literal
NUL outside a string. The new `y_string_escaped_null_scalar.json` adds the
whole-text scalar shape using the exact eight upstream bytes.

CCAN's `json.c` explicitly disallows `\u0000` during string parsing, and its
`test-strings` labels that line `invalid`; `x.py` regenerates `n_223.json` from
that source. An isolated source build returned rejection for `n_223.json`.
Changing only the vendored filename would desynchronize its generated test
data and would hide the parser's limitation. The vendored source and fixture
therefore remain unchanged. A strict parser should accept the root `y_` case;
CCAN's rejection should appear as a discrepancy when that adapter is run.

## #93: extension candidates without changing strict expectations

`metadata/extension-candidates.json` starts a machine-readable, explicitly
non-exhaustive category with the six fixtures named in the issue's comment.
Their exact bytes are `[+Inf]`, `[-NaN]`, `[Inf]`, `[NaN]`, `[Infinity]`, and
`[-Infinity]`, respectively; none has a final newline. They remain `n_` cases:
[RFC 8259 section 6](https://www.rfc-editor.org/rfc/rfc8259.html#section-6)
excludes these nonfinite spellings from its number grammar. [Section 9](https://www.rfc-editor.org/rfc/rfc8259.html#section-9)
permits a parser to accept extensions. This metadata marks possible reasons
for an acceptance, not proof that a particular adapter used an extension.
Check its actual mode and input handling before interpreting the outcome.

The runner continues to classify those inputs against strict JSON syntax and
does not yet consume the metadata in reports. Broader classification of
comments, trailing commas, alternate escapes, and streaming texts needs a
separate reviewed inventory; this six-case list makes no completeness claim.

## Validation

The nested bytes, SHA-256 duplicate, generation source, and root overlap were
checked directly. On Linux x86_64, the isolated GCC 13.3 build of CCAN rejected
both the vendored and new root escaped-NUL scalar. The new root fixture and
extension manifest were checked against their documented byte values.

All 63 repository regression tests completed: 43 passed and 20 skipped for
unavailable optional runtimes/builds. A temporary runner copy used Perl 5.38.2 /
JSON::PP 4.16 against the full 325-case root corpus. Its log had 290 expected
results, 15 implementation-dependent acceptances, and 20 implementation-
dependent rejections, with no discrepancies, crashes, timeouts, skips, or
missing records. Both reports were generated; tracked historical reports were
untouched. The new scalar case was accepted by Perl and rejected by CCAN.
