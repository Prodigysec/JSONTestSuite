# Review batch: leading zeros, executable flags, duplicate minus zero

Reviewed on 2026-10-02 from local commit `8520ebc`. This batch covers three
upstream proposals. Each PR, related issue, discussion, review list, and complete
patch was refreshed before integration. All three PRs remain open upstream;
local dispositions below do not close upstream items.

| PR | Reviewed base | Reviewed head | Local disposition |
| --- | --- | --- | --- |
| [#105](https://github.com/nst/JSONTestSuite/pull/105) / [#104](https://github.com/nst/JSONTestSuite/issues/104) | `9f23c68b521dd700e8c99151d6dc1c5c52a0246e` | `0ad6ba7154f37937d71cad1e1151e3e50534531b` | Four fixtures integrated unchanged. |
| [#113](https://github.com/nst/JSONTestSuite/pull/113) / [#87](https://github.com/nst/JSONTestSuite/issues/87) | `9f23c68b521dd700e8c99151d6dc1c5c52a0246e` | `43c3269626272688f33e1903e0e05feb09aef59e` | Mode cleanup integrated with current-path and debug-symbol adaptations. |
| [#126](https://github.com/nst/JSONTestSuite/pull/126) | `d64aefb55228d9584d3e5b2433f720ea8fd00c82` | `691312faace1b02b2c85d3308cb1ad64c1d071e4` | Deletion declined locally to preserve fixture-name compatibility. |

## Leading-zero syntax

Tyler Waters (`tswaters`) supplied the four fixtures in PR #105. The PR and
issue #104 had no comments or reviews. Byte comparison against the existing
root corpus found no duplicates. Existing `n_number_-01.json`,
`n_number_neg_int_starting_with_zero.json`, and `n_number_with_leading_zero.json`
cover integers with leading zeros; these additions cover a fraction or exponent
after a multi-digit zero integer part.

| Added fixture | Exact bytes (hex), no final newline | Upstream Git blob |
| --- | --- | --- |
| `n_number_00.0.json` | `5b 30 30 2e 30 5d` | `3d954dd35a465aad68f03a64598aa80efa7ae0df` |
| `n_number_-00.0.json` | `5b 2d 30 30 2e 30 5d` | `2d2f18d71e06c22b249124705a6e6b94f86d1a6f` |
| `n_number_00e0.json` | `5b 30 30 65 30 5d` | `e058ab8d14b6754d10642c222c47e6e87dd31b37` |
| `n_number_-00e0.json` | `5b 2d 30 30 65 30 5d` | `edbbbd50cfc8a65c6fcfb0836cb1ec0c4d75b825` |

[RFC 8259 section 6](https://www.rfc-editor.org/rfc/rfc8259.html#section-6)
allows an integer part consisting of a single zero or a nonzero digit followed
by digits. Neither the optional minus sign nor a following fraction/exponent
makes `00` a valid integer part. These are syntax rejection cases, not numeric
range or precision limits. Section 9 allows extensions, whose acceptance should
be interpreted in that mode rather than changing these `n_` expectations.
All four downloaded raw fixtures match the upstream blob hashes above.

## Executable flags

Mark Conway (`themobiusproject`) supplied PR #113. Its three commits are
`e0914c84ac269bb961e5b38fa7e924027a267d46`,
`3ead92bbef064c2e3a66fc54214c30cba16e3ffd`, and
`43c3269626272688f33e1903e0e05feb09aef59e`. The complete patch contains only mode
changes, with 246 final path dispositions. Four PR comments discuss additional
files and executable detection; issue #87 has one supporting comment. There
were no formal reviews or inline review comments.

The local adaptation changes **234** file modes:

- Remove execute bits from 122 parsing fixtures, six transformation fixtures,
  and 91 parser source/resource files. Source extensions are `.swift`, `.h`,
  `.m`, and `.c`; resources include seven `.icns` files and the Jackson
  annotations `.jar`. Interpreter-only `.cr`, `.php`, and regex `.rb` files
  lack shebangs and also become non-executable.
- Add execute bits to 15 existing scripts, each verified to have a shebang:
  `test_cjson.py`, `test_demjson.py`, `test_json-jq.py`, `test_simplejson.py`,
  `test_ujson.py`, `test_ccan_json/json/_test/x.py`, `test_cpanel_json_xs.pl`,
  `test_json_xs.pl`, `test_marpax_eslif_ecma404.pl`, `test_mojo_json.pl`,
  `test_jsonlite.r`, `test_rjson.r`, `test_oj_compat.rb`, `test_oj_strict.rb`,
  and `test_yajl.rb` (all paths relative to `parsers/`).

Adaptations from the upstream patch:

- Nine paths under the removed `parsers/test_Json.NET/` project are omitted.
- The old `n_string_unescaped_crtl_char.json` path is mapped to the current
  `n_string_unescaped_ctrl_char.json`; its bytes are not changed.
- Three Mach-O files under `.dSYM/Contents/Resources/DWARF/` remain
  non-executable: the ObjC serializer's `a.out`, Rust JSON's `tj`, and
  rustc_serialize's `rj`. Their headers identify file type 10 (`MH_DSYM`),
  which is debug-symbol data. They are not adapter entry points.

Every affected file's content hash was checked before and after the mode change.
No content, native executable, license, or parser command was changed. The
registry was checked to ensure no removed execute bit belongs to a directly
invoked command. Registered scripts receiving execute bits are already invoked
through interpreters; `test_json-jq.py` and the CCAN helper are not registry
entries. No root parsing or transformation JSON fixture remains executable.

These checks validate permission metadata and invocation compatibility. They do
not establish that all optional Python/Perl/R/Ruby dependencies or historical
interpreter paths work. The newly executable scripts were not all run, and no
macOS toolchains were used. The existing `python` shebangs and dependency
requirements are preserved rather than silently migrated.

## Duplicate minus zero

PR #126 by `smm-h` removes `y_number_minus_zero.json`; it had no discussion or
reviews. Its duplicate claim is correct: both it and `y_number_negative_zero.json`
contain the four bytes `5b 2d 30 5d` (`[-0]`) with no final newline. RFC 8259
section 6 permits this syntax; parsed-value preservation is a separate concern.

The deletion is **not integrated**. Both names occur in tracked historical
`results/logs.txt`, `results/parsing.html`, and `results/parsing_pruned.html`.
Deleting one would remove an established identifier for downstream consumers
and historical fixture previews without adding coverage. Both names and bytes
are retained as compatibility duplicates and counted as two cases. This is a
completed local review disposition, not a claim that the deletion was applied
or the upstream PR closed. No external consumer inventory was attempted.

## Validation

On Linux x86_64 with Python 3.12.3, all **24** regression tests passed using the
isolated Ruby 3.2.3 / JSON 2.6.3 runtime described in [Ruby notes](ruby-adapter.md).

A temporary copy of the current runner and corpus (`8520ebc` plus this batch)
ran all **324** distinct fixtures using Perl **5.38.2** / JSON::PP **4.16** with
the existing adapter options: **289** expected outcomes, **15** implementation-
dependent acceptances, and **20** implementation-dependent rejections. There
were no unexpected outcomes, crashes, timeouts, skips, or missing records.
Full and pruned reports both counted 324 executions. The log explicitly included
all four new fixtures and both retained minus-zero names.

Temporary controls rejected `[00.0]`, `[-00.0]`, `[00e0]`, and `[-00e0]`, and
accepted `[0.0]`, `[-0.0]`, `[0e0]`, `[-0e0]`, and `[-0]`, with five-second
invocation limits. Corpus totals are **95** `y_`, **194** `n_`, and **35** `i_`.
Existing fixture contents and tracked historical reports were preserved.
