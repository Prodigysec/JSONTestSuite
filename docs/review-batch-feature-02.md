# Feature adapter batch 02: jsonparser, gojay, json-smart

Three source-reviewed libraries are integrated in eleven modes. The prior
[source review](review-batch-feature-02-source-review.md) records exact source
revisions, archive hashes, licenses and API barriers. PDF tiers remain predictions
pending phase 4; registration does not establish RFC conformance.

| Library | Pin / reviewed revision | License | Modes |
| --- | --- | --- | --- |
| [buger/jsonparser](https://github.com/buger/jsonparser) | v1.6.1 / 5663ba4b4f9836695ac8a47d213dd3052583abf9 | MIT | DefaultConfig, Lenient, single quotes, unknown escapes; each with native numeric conversion |
| [gojay](https://github.com/francoispqt/gojay) | v1.2.13 / 1398296d938f9fae26750ddc2fe356b6d897f799 | MIT | native typed callbacks |
| [json-smart](https://github.com/netplex/json-smart-v2) | v2.6.0 tag / ebf7cf8cf0dccef246cd1ed0d052074d787a2de4; POM 2.6.0-SNAPSHOT | Apache-2.0 | default, MODE_PERMISSIVE, MODE_PERMISSIVE_WITH_INCOMPLETE, MODE_RFC4627, MODE_JSON_SIMPLE, MODE_STRICTEST |

## Build and invocation

```sh
sh parsers/features/build_batch_02.sh
python3 -B tools/validate_feature_batch.py P3-02-ADAPTERS --output /tmp/jsonsuite-P3-02-audit --jobs 3
python3 -B tools/check_roadmap.py --task P3-02-ADAPTERS
python3 -B -m unittest discover -s tests -p test_feature_batch_02.py -v
python3 -B -m unittest discover -s tests -v
```

Repeat audits require a fresh output directory. Go uses the batch-01 checksum-
pinned Go 1.25.1 Linux amd64 bootstrap, go.mod/go.sum, primary license checks,
and `go mod verify`. The Java builder compiles reviewed json-smart and
accessors-smart sources using javac --release 17 and checksum-pinned ASM 9.7.1.
It was tested with isolated OpenJDK/javac 21.0.12.1 on Linux x86_64. Set
JSONSUITE_JAVA_HOME to a compatible JDK; other platforms remain untested.
ASM's BSD-3-Clause notice and the primary library notices are preserved under
parsers/features/licenses. Build artifacts and fetched archives remain ignored.
The source build is explicitly labelled POM SNAPSHOT, not a published 2.6.0 jar.

Go invocation is `parsers/.build/feature_go_batch_02 MODE FIXTURE`, with
`--observe` before MODE. Java invocation is `python3 -B
parsers/features/json_smart/run.py MODE FIXTURE`, also accepting --observe.
Registry entries supply these arguments. Exit 0 means native acceptance, 1
rejection, and 2 infrastructure/adapter failure. Input bytes are unchanged.

## Native API and framing adaptations

jsonparser recursively traverses native token/callback APIs and invokes its own
ParseFloat for numeric validity and range. Number tokens remain exact lexemes;
the additional conversion is disclosed in every mode label. Its native getter
is observed separately from duplicate-preserving traversal. It has no general
value serializer, so serialization is unavailable rather than reconstructed.

Gojay's generic DecodeInterface delegates to encoding/json and is deliberately
excluded. Native EmbeddedJSON extraction, typed scalar decoding and object/array
callbacks perform parsing. Native serialization preserves callback duplicates;
there is no arbitrary-object getter, so a duplicate winner is unknown. The
stdlib JSON encoder writes only the observation envelope. A read-only inspection
of the pinned decoder position enforces whole-input framing; an unexpected
layout is an adapter failure, not a JSON rejection.

Json-smart clears ACCEPT_TAILLING_DATA and checks the pinned byte-parser position
after parsing. Its internal 0x1a end marker otherwise hides trailing garbage.
Reflection failure surfaces as an adapter failure. Relaxed modes can consume
`null false` as a single bare string; the observer records that actual value.
Native UTF-8 replacement belongs to json-smart, not wrapper preprocessing.
The independent ASCII envelope writer preserves native UTF-16 units. Binary32
and exact BigDecimal representations extend the documented observation schema.

An initial concurrent rebuild exposed truncated Java class files. The builder
now compiles to a fresh directory, publishes immutable classes by digest, and
atomically changes the runtime pointer. Fourteen observations accepted during
an overlapping successful rebuild. The interrupted preliminary audit under
/tmp/jsonsuite-P3-02-audit-before-key-and-atomic-build is diagnostic only.

## Measured results

The final audit records 3597/3597 standard pairs and 1375/1375 feature pairs:
821 feature acceptances and 554 rejections. Neither run has crashes, timeouts,
skips or protocol failures. Standard CI reports 580 expectation discrepancies;
audit exit 0 means complete records, not a passing conformance test.

| Mode | Standard expected / deviations | Feature accept / reject |
| --- | --- | --- |
| jsonparser DefaultConfig | 268 / 20 | 59 / 66 |
| jsonparser Lenient | 257 / 31 | 69 / 56 |
| jsonparser single quotes | 266 / 22 | 62 / 63 |
| jsonparser unknown escapes | 259 / 29 | 66 / 59 |
| gojay native callbacks | 261 / 27 | 59 / 66 |
| json-smart MODE_JSON_SIMPLE | 257 / 31 | 61 / 64 |
| json-smart default, MODE_PERMISSIVE (each) | 173 / 115 | 111 / 14 |
| json-smart MODE_PERMISSIVE_WITH_INCOMPLETE | 138 / 150 | 111 / 14 |
| json-smart MODE_RFC4627 | 270 / 18 | 56 / 69 |
| json-smart MODE_STRICTEST | 266 / 22 | 56 / 69 |

Each mode additionally records 39 implementation-dependent outcomes. Gojay
rejects two y_ number fixtures; json-smart MODE_JSON_SIMPLE rejects the two
DEL string fixtures, and MODE_STRICTEST also rejects three trailing-whitespace
fixtures. Other discrepancies are n_ acceptance, retained without hiding native
extensions. Default jsonparser still accepts leading-zero numerals, some raw
controls and malformed UTF-8; native ParseFloat does not make it a strict parser.

For duplicate `test` members, jsonparser traverses both and its getter returns
the first; gojay traverses and serializes both, without a getter winner;
json-smart keeps and serializes the last. At 2^53+1, jsonparser retains the
lexeme, gojay rounds binary64 and serializes 9007199254740992, and json-smart
preserves the integer. Json-smart accepts 1.0e4096 as Infinity and serializes
null; its long decimal remains an exact BigDecimal. Go modes retain invalid
native string/key bytes beside their display projection; json-smart replaces
them natively. Acceptance of a comment-looking bare string does not establish
comment recognition: inspect its normalized value.

Tracked [evidence](roadmap/feature-batch-02.json) contains copied corpus hashes,
commands, actual runtimes, build/source hashes, all standard discrepancy names,
and selected value observations. Eight adapter tests pass; the full suite passes
139 tests with 22 optional skips. Existing fixture bytes and historical reports
are unchanged. Predictions remain untested until the planned analysis.
