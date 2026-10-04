# Exact-byte convenience probes: P2-02

The separate manifest contains 125 probes in ten categories. Each records its
literal bytes in hex, SHA-256, length, RFC expectation, purpose, and idea source.
The generating script uses explicit byte literals and writes only `test_features/`
and `metadata/convenience-features.json`. It is a maintenance tool, not a parser
oracle. The checker reads files without decoding or modifying them.

| Category | Probes |
| --- | ---: |
| Comments | 10 |
| Quotes | 8 |
| Quoteless names/values | 8 |
| Commas | 9 |
| Roots/literals/whitespace | 19 |
| Strings/decoding | 17 |
| Keys/collisions | 14 |
| Serialization | 9 |
| Numbers | 25 |
| Limits | 6 |

Expectations follow [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html):
one complete value and four whitespace characters (§2), lowercase literals (§3),
quoted names and object/array separators (§§4–5), decimal number grammar (§6),
and quoted strings with the defined escapes and no raw controls (§7). BOMs
(§8.1), lone surrogates (§8.2), numeric range (§6), and finite implementation
limits (§9) are explicitly separated from invalid syntax. Duplicate members
are syntactically allowed (§4), without a required winner. Distinct case,
normalization forms, NULs, and surrogate suffixes retain their original units
(§8.3); observations must show native lookups and serialization.

Depth probes contain 32, 512, or 2048 balanced arrays; string/key probes contain
65536 ASCII characters. The malformed depth probe has 4096 opening brackets.
Each invocation remains bounded by the registered timeout. The manifest records
9 byte-identical overlaps with the authoritative corpus for visibility;
names and bytes of existing fixtures remain unchanged. Controls repeated across
feature categories deliberately provide independent category baselines.

Validation: `python3 -B tools/check_feature_manifest.py` and
`python3 -B -m unittest discover -s tests -p test_feature_manifest.py -v`.
The tests exercise corruption, path/symlink escapes, literal NUL/invalid UTF-8,
line continuations, empty input, surrogate keys, and bounded long probes.
No parser observations have been collected by this task.
