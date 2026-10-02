# Review batch: uppercase escapes, text streams, and fixture encoding

Reviewed on 2026-10-03 against local baseline `37f40ea`. Upstream issues
[#112](https://github.com/nst/JSONTestSuite/issues/112),
[#91](https://github.com/nst/JSONTestSuite/issues/91), and
[#85](https://github.com/nst/JSONTestSuite/issues/85) remained open when their
bodies and discussions were refreshed. #112 had three explanatory comments
(last updated 2020-06-09); #91 had one comment naming two root examples (last
updated 2019-04-22); #85 had no comments (last updated 2018-08-25). These are
issues without proposed PR base/head revisions or patches to merge.

## #112: uppercase `U` is not a JSON escape

`n_string_unicode_CapitalU.json` is exactly `22 5c 55 41 36 36 44 22`
(`"\\UA66D"`). [RFC 8259 section 7](https://www.rfc-editor.org/rfc/rfc8259.html#section-7)
allows `\\u` with a lowercase `u` and four hexadecimal digits, or one of its
listed two-character escapes. `\\U` is not listed. The sentence allowing any
character to be escaped describes the `\\uXXXX` form; it does not allow an
arbitrary letter after a backslash. The existing `n_` expectation is correct.

The root corpus already has an array containing `"\\uA66D"` in
`y_string_unicode.json`. A new scalar companion,
`y_string_unicode_lowercase_u_A66D.json`, contains exactly `22 5c 75 41 36
36 44 22` (`"\\uA66D"`), with no final newline or byte-identical root
fixture. It makes the one-byte `U`/`u` distinction visible for top-level
strings. Perl JSON::PP rejected the uppercase form and accepted the lowercase
form. No existing fixture was renamed or rewritten.

## #91: two texts are a stream, not one JSON text

The issue mentions CCAN's nested `n_31.json`; the authoritative root corpus
has two directly reviewed examples. [RFC 8259 section 2](https://www.rfc-editor.org/rfc/rfc8259.html#section-2)
defines a JSON text as one value with optional surrounding whitespace.

| Root fixture | Exact bytes | Complete texts at byte offsets (end exclusive) |
| --- | --- | --- |
| `n_structure_double_array.json` | `[][]` | `[]` at `[0, 2)`, `[]` at `[2, 4)` |
| `n_structure_object_with_trailing_garbage.json` | `{"a": true} "x"` | `{"a": true}` at `[0, 11)`, `"x"` at `[12, 15)` |

Each slice was accepted separately by Perl JSON::PP 4.16, while each complete
file was rejected as one JSON text. jq 1.7 in its default streaming invocation
accepted each full file and emitted two results. A scan of root `n_` files
found no other jq-successful input that emitted multiple results. These are
mode differences, not grounds to relabel the full inputs `i_`: they remain
invalid in the runner's one-text contract.

`metadata/streaming-candidates.json` records the two root paths, their
category, and byte spans without changing fixture names or expectations. It
is a reviewed starting set, not an exhaustive list for every extension or
vendor subcorpus. The runner does not yet consume this metadata; an acceptance
by a streaming parser still appears as a strict-mode discrepancy in the
current report. Consumers can use the sidecar to interpret that observation.
The nested CCAN example remains outside the root runner, as reviewed for
[#92](review-batch-92-94-93.md#92-two-identical-ccan-cases).

## #85: preserve the malformed and alternate-encoding byte cases

The issue points to `i_string_truncated-utf-8.json`. Its bytes are `5b 22 e0
ff 22 5d` (`["` + `e0 ff` + `"]`). `e0` starts a three-byte UTF-8 sequence,
but `ff` cannot continue it. Calling the file Latin-1 would reinterpret those
same bytes as different characters, destroying this malformed-UTF-8 test. A
separate `i_string_iso_latin_1.json` deliberately contains `5b 22 e9 22 5d`;
UTF-16 fixtures likewise preserve their original encoded bytes. These inputs
probe decoder behavior and interoperability, not a repository-wide Latin-1
encoding policy.

In the 327-file root corpus, 25 files fail strict UTF-8 decoding: 12 `n_`, 13
`i_`, and no `y_` cases. The other 302 decode as UTF-8; that alone does not
establish JSON validity. [RFC 8259 section 8.1](https://www.rfc-editor.org/rfc/rfc8259.html#section-8.1)
requires UTF-8 for JSON text exchanged outside a closed ecosystem, while
section 9 permits parser limits and extensions. No fixture bytes were
transcoded. The runner supplies paths or raw stdin bytes to adapters; wrapper
decoding modes must be documented when interpreting these cases.

## Validation and limits

The new scalar byte sequence has no root duplicate. Both stream entries and
their byte spans were checked against the files, with each slice tested as a
complete JSON text. jq 1.7 emitted exactly two values for each full file. A
temporary Perl JSON::PP runner copy exercised all 327 root fixtures and
generated both reports without changing tracked historical results. On Linux
x86_64 with Python 3.12.3 and Perl 5.38.2 / JSON::PP 4.16, it recorded 288
expected outcomes, 19 implementation-dependent acceptances, and 20
implementation-dependent rejections, with no discrepancies, crashes, timeouts,
skips, or missing rows. The full regression suite completed 66 tests: 47
passed and 19 optional-runtime tests were skipped. Neither jq's broader parser
behavior nor any non-Perl adapter's response to the new scalar was surveyed
here; the direct jq check was limited to the two stream fixtures.
