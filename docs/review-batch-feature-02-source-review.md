# Batch 02 source/API review: P3-02

Reviewed and checksum-pinned buger/jsonparser v1.6.1, gojay v1.2.13, and
json-smart's v2.6.0 tag. Archive revisions, reviewed file hashes, findings and
preserved licenses are in `docs/roadmap/feature-batch-02-sources.json`. All
three remain candidates; none is registered or claimed as parser coverage by
this source-review task.

## Native API barriers and roadmap amendment

[gojay's pinned DecodeInterface](https://github.com/francoispqt/gojay/blob/1398296d938f9fae26750ddc2fe356b6d897f799/decode_interface.go)
imports encoding/json and calls `json.Unmarshal` for the extracted value.
Its typed scalar/object/array APIs are native. An arbitrary-value adapter must
use those APIs and native callbacks, preserving all root types and complete
framing; a generic stdlib-backed wrapper would measure another engine. The
library is not excluded wholesale as a pure wrapper. Its native adapter remains
required in the next task, with API limitations made explicit.

[jsonparser configuration source](https://github.com/buger/jsonparser/blob/5663ba4b4f9836695ac8a47d213dd3052583abf9/config.go)
now exposes DefaultConfig and Lenient, plus separate single-quote and
unknown-escape flags. The adapter needs separate mode entries, recursive native
container validation and native lookups; merely calling a selective getter
cannot establish whole-text acceptance. Record duplicate traversal separately
from getter winners, and number token text separately from native conversions.

[json-smart's tagged POM](https://github.com/netplex/json-smart-v2/blob/ebf7cf8cf0dccef246cd1ed0d052074d787a2de4/json-smart/pom.xml)
declares 2.6.0-SNAPSHOT at the release tag. Source builds must identify the exact
revision and POM label, rather than claiming to be the published Maven binary.
The parser has MODE_PERMISSIVE, MODE_PERMISSIVE_WITH_INCOMPLETE, MODE_RFC4627,
MODE_JSON_SIMPLE and MODE_STRICTEST. Permissive/simple presets enable trailing
data; integration must enforce one complete text while documenting the framing
adaptation. The isolated JDK 21 runtime/compiler is available under `/tmp`;
Maven/source dependency builds and resulting native observations remain pending.

The original combined integration task assumed a straightforward generic native
adapter. These verified facts require a source/API review first. The roadmap
now places P3-02-ADAPTERS immediately after this task and before P3-03, preserving
library order and all three candidates. No fixtures, expectations, historical
reports or runtime packages changed. No unavailable-build disposition is
invented: these adapters have not yet been built.

## Verification

```sh
python3 -B tools/review_feature_batch_02_sources.py
python3 -B tools/check_roadmap.py --task P3-02
python3 -B -m unittest discover -s tests -v
git diff --check
```

The source checker downloads exact commit archives if absent, verifies SHA-256,
checks all eleven reviewed files and three retained licenses, and asserts the
five recorded API findings against the original files without executing build
scripts. Source tags and licenses were refreshed from primary upstream sources.
Full suite: 131 tests, 22 optional skips. Native adapter validation and coverage
remain pending in P3-02-ADAPTERS; predictions remain untested.
