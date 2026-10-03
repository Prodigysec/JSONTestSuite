# Review batch: article JavaScript and Unicode examples

Reviewed on 2026-10-03 against local baseline `abf7284`. Upstream issues
[#148](https://github.com/nst/JSONTestSuite/issues/148),
[#134](https://github.com/nst/JSONTestSuite/issues/134), and
[#75](https://github.com/nst/JSONTestSuite/issues/75) were open when their bodies
and discussions were refreshed through the public GitHub API. #148 was last
updated 2026-05-20 and had no comments; #134 was last updated 2024-09-26 and
had four comments; #75 was last updated 2017-11-27 and had no comments.
They are issue reports without proposed PR base/head revisions to integrate.

## #148: date the JavaScript string-literal comparison

The article used unescaped U+2028 and U+2029 as a present-tense reason why JSON
could not be a JavaScript subset. This was true for [ECMAScript 5.1 string
literals](https://262.ecma-international.org/5.1/#sec-7.8.4), but the
[JSON superset change](https://tc39.es/proposal-json-superset/) was adopted in
[ECMAScript 2019](https://tc39.es/ecma262/2019/#sec-literals-string-literals). The
article now marks the earlier rule as historical and says the specific
counterexample no longer applies to ES2019 and later. It does not claim that an
arbitrary JSON text is a standalone JavaScript program.

The existing `y_string_u+2028_line_sep.json` is exactly `5b 22 e2 80 a8 22 5d`;
`y_string_u+2029_par_sep.json` is `5b 22 e2 80 a9 22 5d`. Node 24.21.0
parsed each both with `JSON.parse` and as a parenthesized JavaScript string
literal, yielding the same code point. This checks the current runtime's
behavior, not historical engines.

## #134: retain existing fixes and repair two more displays

The reported “more that 300” typo was already corrected in commit `388c667`
by Wumpie (ChristanVersteeg; upstream PR #138). Lars H. Rohwedder's `cae8527`
had already restored the backslashes in the examples
named by the discussion, including `n_string_escape_x.json`,
`y_string_allowed_escapes.json`, and `n_string_invalid_unicode_escape.json`.
Those fixes were verified rather than duplicated. The article's later
historical results section still omitted the backslashes from `A\u0000B` and
`\uD800` examples, so those displays were corrected. No parser result was
recomputed from a historical report.

## #75: distinguish bytes, classifications, and surrogate results

The article's table still named `n_string_invalid_utf-8.json`, while the root
corpus has `i_string_invalid_utf-8.json` with exact bytes `5b 22 ff 22 5d`.
The separate `n_array_invalid_utf8.json` is `5b ff 5d`. The table now names the
current file, and the prose explains that the inside-string `i_` label records
decoder-mode variation, including replacement of malformed input. It does not
make byte `ff` valid UTF-8. The array case remains `n_` because the bare byte
cannot form a JSON value. [RFC 8259 section 8.1](https://www.rfc-editor.org/rfc/rfc8259.html#section-8.1)
requires UTF-8 for exchange outside a closed ecosystem; section 8.2 discusses
the unpredictable treatment of unpaired surrogate escapes.

The existing transformation file `string_2_escaped_invalid_codepoints.json`
is exactly `5b 22 5c 75 44 38 30 30 5c 75 44 38 30 30 22 5d`, or
`["\uD800\uD800"]`. Both escaped code units are high surrogates; a valid pair
for U+10000 is `\uD800\uDC00`. The historical result bytes `f0 90 80 80` are
UTF-8 for U+10000. A decoder that fails to validate the second surrogate's
range can produce that value by discarding its high bits. The article now
explains this as a plausible cause of the historical output, not as a fresh
measurement of the old R or Ruby parser. Node 24.21.0 retained two high
surrogate code units in a direct parse.

The article also now identifies `i_string_UTF8_surrogate_U+D800.json` as the
`5b 22 ed a0 80 22 5d` ill-formed UTF-8 case. These examples concern parser
modes and decoded values; no fixture bytes, prefixes, runner behavior, or
historical reports changed.

## Validation and limits

The six cited root/transform fixtures were inspected as bytes against their
claims. The previously fixed #134 examples and the current fixture names were
checked in this checkout. Node 24.21.0 supplied the two JavaScript-literal
checks and the surrogate check. The new specification links, the assessment's
local review link, and `git diff --check` were checked. The parsing runner was
not rerun because neither its code nor its 327-case corpus changed. The
article's other historical parser results were not remeasured; some depend on
unavailable old toolchains.
