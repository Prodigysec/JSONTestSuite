# Feature baseline: P2-04

This batch observes existing modes rather than adding libraries. Python stdlib
JSON and Node/V8 already have complete-text UTF-8 adapters. Optional observer
commands use the same native decoder/configuration and leave normal commands
and exit statuses unchanged. The two Python policies remain separate: default
constants and rejection of literal NaN/Infinity constants. The latter does not
claim complete RFC compliance or reject overflow of otherwise valid numbers.

## Sources, versions, and invocation

Python: [stdlib documentation](https://docs.python.org/3/library/json.html),
CPython 3.12.3 on Linux x86_64; project PSF license. Node: [Buffer UTF-8 API](https://nodejs.org/api/buffer.html#bufferisutf8input),
Node 24.21.0, V8 13.6.233.17-node.53; Node MIT and V8 BSD notices belong to the
installed runtimes. No third-party runtime/library source is vendored here.
The Node observer requires `buffer.isUtf8` (Node >=18.14), validates bytes before
`Buffer.toString`, and preserves BOM input for `JSON.parse`. Python explicitly
decodes UTF-8 before `json.loads`. Neither strips BOMs nor replaces malformed
bytes. Missing files remain adapter failures (exit 2).

```sh
python3 -B parsers/observe_python_features.py test_features/roots/null-control.json
python3 -B parsers/observe_python_features.py --reject-nonfinite test_features/roots/null-control.json
node parsers/observe_node_features.js test_features/roots/null-control.json
python3 -B tools/validate_feature_batch.py P2-04 --output /tmp/jsonsuite-P2-04-baseline-v2 --jobs 3
```

Choose a fresh output path for repeat runs. The helper stores the exact-name
filter, all raw observations, summary, standard logs/console, and an audit. Its
standard run imports a disposable copy of `run_tests.py`, copies corpus bytes,
and invokes the original registry commands. Setup is bounded by the feature
runner and shared with the corpus run, avoiding unbounded repeated builds.
Historical reports are preserved. Audit exit 0 means every planned pair was
accounted for; standard discrepancy counts and the separate feature CI verdict
remain explicit. A skip is a record, never parser coverage.

## Observations and limits

| Mode | Feature accept | Feature reject | Standard expected | Standard discrepancies |
| --- | ---: | ---: | ---: | ---: |
| Node strict UTF-8 | 48 | 77 | 288 | 0 |
| Python default constants | 51 | 74 | 285 | 3 |
| Python constants rejected | 48 | 77 | 288 | 0 |

Every mode also logged 25 implementation-dependent acceptances and 14
implementation-dependent rejections in the standard corpus. There are 981/981
standard pairs and 375/375 feature pairs; no crash, timeout, skip, or protocol
failure occurred. Python's three standard discrepancies are its documented
acceptance of `n_number_NaN.json`, `n_number_infinity.json`, and
`n_number_minus_infinity.json` in default mode. No result changes a fixture's
expectation.

Native value observations show Python retaining integer 9007199254740993 while
Node stores binary64 9007199254740992. Node preserves the stored sign of `-0`
but serializes `0`; Python stores integer zero for `-0` and preserves binary64
negative zero for `-0.0`. Both decode `1.0e4096` to binary64 Infinity; Node
serializes it as `null`, Python as `Infinity`. The literal-constant rejection
option leaves exponent overflow unchanged. Both tested APIs collapse duplicate
keys with the last value, while preserving NUL and lone-surrogate suffixes as
distinct lookup names. No source bytes are reparsed by another library to
invent the winner.

Strings are compared through UTF-16 units with exact lone surrogates. Native
objects retain traversal order; normalization does not merge case or Unicode
normalization forms. Normalization limits are depth 64, 4096 nodes and 4096
string units, with explicit truncation, original length, and UTF-16BE SHA-256
for long strings. Object keys preserve their units. Parsing and serialization
remain separate: a normalization/serialization limit cannot turn acceptance
into rejection. Complete raw records stay in the isolated run directory;
`docs/roadmap/feature-baseline.json` retains hashes, counts, provenance, and
selected compact observations. Large/truncated observations are not treated
as complete semantic agreement.

## Validation and phase summary

Eight focused tests check acceptance/rejection, scalars, whole input, malformed
bytes/BOM, runtime failure, signed zero, numeric precision/overflow, surrogate
and NUL keys, native duplicate lookups, bounded normalization, serialization
failure, registry metadata, and missing/duplicate corpus records. Full suite:
122 tests, 22 optional skips, exit 0. The standard corpus is also audited above.

Phase 2 added the protocol, 125 exact-byte probes, bounded parallel runner,
Python/Node observers, and reusable batch audit. No runtime was unavailable for
this baseline; optional legacy environment tests retain their explicit skips.
The overflow/serialization differences are measured behavior, not new claims
about the PDF rankings. Document predictions for new libraries remain untested;
phase 4 compares those only after pinned adapter runs.
