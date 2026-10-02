# Review batch: RFC 8259 encoding and value transformations

Reviewed on 2026-10-03 against local baseline `a6ccf5d`. Upstream issues
[#77](https://github.com/nst/JSONTestSuite/issues/77),
[#76](https://github.com/nst/JSONTestSuite/issues/76), and
[#71](https://github.com/nst/JSONTestSuite/issues/71) remained open when their
bodies and discussions were refreshed. #77 had two comments, including the
maintainer's 2018-02-26 explanation of RFC 8259 section 8.1; #76 and #71 had
no comments. None has a proposed PR base/head revision to merge.

## #77: align the article with RFC 8259 and current bytes

[RFC 7159 section 8.1](https://www.rfc-editor.org/rfc/rfc7159.html#section-8.1)
allowed UTF-8, UTF-16, or UTF-32 JSON text and prohibited generators from
adding a BOM. [RFC 8259 section 8.1](https://www.rfc-editor.org/rfc/rfc8259.html#section-8.1)
requires UTF-8 for JSON text exchanged outside a closed ecosystem, prohibits
adding a BOM to network-transmitted JSON text, and permits parsers to ignore a
BOM. It does not expressly authorize BOM generation in other contexts.

The original article already mentioned RFC 8259 but still said non-networked
generators `MAY` add a BOM and that UTF-16/UTF-32 should be unconditional
passing tests. Those claims were corrected without changing fixture bytes.
The current root corpus has `i_string_UTF-16LE_with_BOM.json` (12 bytes,
`ff fe 5b 00 22 00 e9 00 22 00 5d 00`), two UTF-16 inputs without BOM, and
no UTF-32 fixture. It also has `i_structure_UTF-8_BOM_empty_object.json`
(`ef bb bf 7b 7d`), a BOM-only `n_` file (`ef bb bf`), and an incomplete-BOM
`n_` file (`ef bb 7b 7d`). A BOM alone has no JSON value under section 2, so
it is not an `i_` case. The article's old `y_string_utf16.json` example was
replaced with the current `i_` name; `git show f9804b5` confirmed that the
old and current files have identical bytes. A historical STJSON discussion now
identifies the old name as historical.

This is a documentation and classification audit, not a claim that all RFC
8259 requirements or parser modes have been tested. The root corpus and
historical reports were not regenerated or reclassified for #77.

## #76: positive and negative zero after parsing

The new transformation examples are `number_positive_zero.json` with bytes
`5b 30 2e 30 5d 0a` (`[0.0]` plus LF) and `number_negative_zero.json` with
`5b 2d 30 2e 30 5d 0a` (`[-0.0]` plus LF). They are not byte duplicates of
existing transformation cases. The parsing corpus already accepts `[-0]` in
two compatibility-named fixtures, but an exit code cannot reveal the parsed
zero's sign. [RFC 8259 section 6](https://www.rfc-editor.org/rfc/rfc8259.html#section-6)
permits the `-0.0` spelling; it does not define a post-parse signed-zero
representation or require round-trip preservation.

With Python 3.12.3 `json.loads`, `math.copysign(1.0, value[0])` returned `1.0`
for `[0.0]` and `-1.0` for `[-0.0]`; `json.dumps` emitted `[0.0]` and
`[-0.0]`. Perl 5.38.2 / JSON::PP 4.16 also retained distinct parsed IEEE sign
bits (`POSIX::signbit` returned `0` and `1`), but its encoder emitted `[0]`
for both. This is an observed parse-versus-serialization difference, not a
standards failure verdict.

## #71: case-distinct object names

`object_case_distinct_keys.json` contains exactly `{"a":1,"A":2}` and
`object_case_distinct_keys_reversed.json` contains `{"A":2,"a":1}`; neither
has a final newline. The reverse order helps reveal parsers that collapse keys
by case and retain only the first or last member. These cases differ from the
existing duplicate-same-name and NFC/NFD transformation examples.
[RFC 8259 section 4](https://www.rfc-editor.org/rfc/rfc8259.html#section-4)
recommends unique member names, and [section 8.3](https://www.rfc-editor.org/rfc/rfc8259.html#section-8.3)
describes code-unit comparison as interoperable; ASCII `a` and `A` are distinct
under that comparison. Python `json` and Perl JSON::PP retained both names in
both orders, with lookups `a = 1` and `A = 2`. Their behavior does not establish
what historical cJSON or other adapters do.

## Validation and limits

All four new fixtures were inspected as bytes and checked for overlap with
the existing `test_transform/` corpus. The Python and Perl probes inspected
parsed values as well as serialization; acceptance alone was not used as a
value assertion. `run_tests.py` still runs only `test_parsing/`, so these
transformation inputs do not change the 327-case parsing count or its reports.
No general transformation runner or adapter protocol was added in this batch;
cross-parser value comparisons beyond these direct probes remain pending.
On Linux x86_64, the full Python regression suite completed 66 tests: 47
passed and 19 optional-runtime tests were skipped using isolated make/GCC.
The parsing runner was not rerun because neither its code nor its 327-case
input corpus changed. Historical reports remain untouched.
