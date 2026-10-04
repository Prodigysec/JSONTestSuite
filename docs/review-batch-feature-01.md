# Feature adapter batch 01: goccy/go-json, Sonic, json-iterator/go

Integrated three independently maintained Go libraries in twelve separate modes.
Sources and pins were reviewed before building; measured PDF tiers remain external
predictions pending phase 4, not local correctness claims.

| Library | Pin / reviewed revision | License | Registered modes |
| --- | --- | --- | --- |
| [goccy/go-json](https://github.com/goccy/go-json) | v0.11.2 / 3ce7333e2c03dcb8801817bf516c60545154a66c | MIT | default, UseNumber |
| [Sonic](https://github.com/bytedance/sonic) | v1.15.4 / f1003e13e7899a6e536181fa66e986c4f29db5d5 | Apache-2.0 | ConfigDefault, ConfigStd, ConfigFastest, ValidateString + UseUnicodeErrors, UseNumber, UseInt64 |
| [json-iterator/go](https://github.com/json-iterator/go) | v1.1.12 / 024077e996b048517130b21ea6bf12aa23055d3d | MIT | ConfigDefault, ConfigCompatibleWithStandardLibrary, ConfigFastest, UseNumber |

## Build and contract

```sh
sh parsers/features/build_batch_01.sh
python3 -B tools/validate_feature_batch.py P3-01 --output /tmp/jsonsuite-P3-01-audit --jobs 3
python3 -B -m unittest discover -s tests -p test_feature_go_batch_01.py -v
python3 -B -m unittest discover -s tests -v
```

Use a fresh audit directory on repeats. The build pins Go 1.25.1 Linux amd64
and its official archive SHA-256; modules and transitive versions/checksums are
in go.mod/go.sum. It verifies the primary license hashes against reviewed source
archives and uses Go's checksum database plus `go mod verify`. Licenses are
preserved under `parsers/features/licenses/`; build artifacts remain ignored
under `parsers/.build/`. `JSONSUITE_GO` can select an identical installed
compiler, and `JSONSUITE_GO_MOD_CACHE` can isolate the module cache. Source
archives are not vendored. Only Linux x86_64 was tested; other profiles remain
unavailable to this bootstrap. Sonic refuses stdlib fallback, so acceptance
cannot silently measure another engine.

Normal invocation is `feature_go_batch_01 MODE FIXTURE`; observations add
`--observe` before MODE. Exit 0 means native acceptance, 1 rejection, 2 adapter
failure; panic/signal behavior surfaces. Input is raw bytes. No UTF-8 prefilter,
BOM removal or replacement is imposed on Go libraries. Compatibility preset
names are not claims of strict RFC compliance. Struct-only unknown-field and
case options have no effect on the generic-interface target and are not
presented as syntax modes. Goccy's first-field option applies to struct fields,
not a separate arbitrary-object syntax policy.

## Whole-input adaptations

Goccy and Sonic Unmarshal enforce trailing-input checks. Goccy UseNumber uses
its native Decoder and inspects Buffered plus unread input for RFC whitespace.
json-iterator Unmarshal incorrectly accepts `null\0false`, `0\0`, and object
followed by NUL/garbage. Native Decoder.Buffered also retained stale numeric
bytes at EOF, incorrectly rejecting scalar `0` in the initial adaptation.
The final adapter uses the configured BorrowIterator/ReadVal/WhatIsNext APIs
and requires genuine io.EOF, distinguishing NUL from end of input without
altering native decoding or input bytes. Focused tests cover this and a 64 KiB
buffer boundary. The initial interrupted audit and pre-serializer-byte audit
are explicitly diagnostic; final evidence is `/tmp/jsonsuite-P3-01-audit`.

## Measured results

All 3924 standard pairs and 1500 feature pairs are recorded, with no crashes,
timeouts, skips, or protocol failures. Feature outcomes total 613 acceptances
and 887 rejections. Standard CI reports 42 discrepancies; audit exit 0 means
complete records, not compliance.

| Mode | Standard expected / deviations | Feature accept / reject |
| --- | --- | --- |
| Goccy default | 288 / 0 | 49 / 76 |
| Goccy UseNumber | 288 / 0 | 50 / 75 |
| json-iterator default, compatible, fastest (each) | 288 / 0 | 49 / 76 |
| json-iterator UseNumber | 258 / 30 | 52 / 73 |
| Sonic default, fastest, UseInt64 (each) | 285 / 3 | 54 / 71 |
| Sonic UseNumber | 285 / 3 | 55 / 70 |
| Sonic ConfigStd, ValidateString + UseUnicodeErrors (each) | 288 / 0 | 49 / 76 |

Each mode also logs 39 implementation-dependent cases. Exact individual
outcomes, discrepancy names, copied corpus hashes, commands, source/binary
hashes, runtime versions and environment are in the tracked evidence JSON.
Sonic's four relaxed configurations accept three `n_string_unescaped_*`
controls (control character, newline, tab). ConfigStd and the Unicode-error
configuration reject them. json-iterator UseNumber accepts 30 malformed numeric
fixtures including lone minus, leading zeros, incomplete exponent/fraction,
and invalid expressions. These are native findings retained in the observer;
no stdlib validation is added to conceal them.

Malformed UTF-8 inside strings is accepted by all tested configurations, with
replacement or retention depending on native decoding. Stored invalid bytes
are retained in `invalid_native_utf8_hex` / `invalid_native_key_utf8_hex` beside
the UTF-16 projection. Sonic ConfigDefault can serialize raw `22ff22`; ten
records preserve invalid serializer bytes through `serialized_bytes_hex` and
`serialized_invalid_utf8`, preventing the JSON envelope from concealing them.
Go map traversal is explicitly unstable and never presented as source order.
Native number tokens are observed as number-lexeme; they are not converted by
another JSON parser. Duplicate winners come from native map lookup.

Eight adapter tests and eleven runner regressions passed. Full suite: 131 tests,
22 optional skips. No historical reports or authoritative fixtures changed.
This finite corpus does not establish complete RFC compliance; predictions are
still untested until the planned cross-library analysis.
