# JSON parser coverage and convenience-feature roadmap

Status: planning committed before implementation. Input PDF remains at
`json_parsers_ranked_by_rfc8259_deviation.pdf`; its temporary converted text is
`/tmp/jsonsuite-ranked-parsers.txt`. The machine-readable source is
[backlog.json](backlog.json).

## Ground truth used in planning

At `5c1adbf`, the registry has 123 modes, not the PDF Appendix A's 94.
The parsing corpus has 327 fixtures and the transformation corpus 26. Folly
is already registered despite appearing as a candidate; Euneus is registered
and will be reused as a control if runnable. QJson needs identity verification
against the existing Qt JSON mode. JSONpp is C++, while opack is Java, not C.
Registration is distinct from an installed or working adapter.

The exact baseline command `python3 -B -m unittest discover -s tests -v`
passed: 99 tests, 22 optional skips. Host Python 3.12.3, Node 24.21.0, curl,
and Docker are available. Go, JDK, .NET, Ruby, Lua, cc, and make are absent
from PATH; previously extracted toolchains under /tmp must be rechecked.
Core, Chromium, Firefox, JSC, V8, and Folly Docker images exist. These facts
will be captured reproducibly by P0-01; no fresh parser coverage is claimed.

## Execution and evidence rules

Execute tasks in the order below, one at a time; commit after every task.
A task is done only after its acceptance commands succeed and their output is
reported. Update both this table and backlog.json. Run the full unit suite
after every task, including documentation tasks. Append amendment evidence
before changing the sequence, splitting slow batches, or resolving an ambiguous
library name. No adapter work starts until this planning commit exists.

All basis tags and tiers are PDF claims. Heuristic/M claims are hypotheses;
Measured labels refer to external suites with different fixtures and versions.
Every parser prediction starts untested. Null version/license/source fields
mean unverified, not an invented pin. Verify source, license, checksum, build,
platform and complete-input behavior before adding a library. Native strict and
lenient modes receive distinct entries; binary/input transformations are explicit.

The feature corpus is separate from test_parsing. RFC grammar and permitted
limits determine expectations; parser consensus is used only to compare observed
value representations, never to decide syntax validity. The schema must preserve
null/false/zero, signed zero, integer/float storage, nonfinite values, string code
units, duplicate-key policy, getter observations, and serialized text when available.
Missing observations are unknown. Runs use fresh untracked output directories.

Section-7 primary candidates are integrated in batches of three; reduce slow
batches by recorded amendment. The long tail is fully catalogued as individual
discovery leads. Resolve four identities per task; independent parsers then need
a newly sequenced integration task before analysis. Exclude wrappers only with
engine evidence. Alternative controls are discovery leads rather than false coverage.

## Ordered tasks

| ID | Phase | Task | Dependencies | Status |
| --- | ---: | --- | --- | --- |
| P0-01 | 0 | Record registry, Appendix A reconciliation, environments, and baseline |  | done |
| P1-01 | 1 | Validate split catalog, source tags, exclusions, and first Go pins | P0-01 | done |
| P2-01 | 2 | Specify observation protocol and neutral normalization | P1-01 | done |
| P2-02 | 2 | Add exact-byte convenience probes and manifest | P2-01 | done |
| P2-03 | 2 | Implement filtered, parallel, bounded observation runner | P2-02 | done |
| P2-04 | 2 | Add Python and Node observations and record a feature baseline | P2-03 | todo |
| P3-01 | 3 | Integrate goccy/go-json, bytedance/sonic, json-iterator/go | P2-04 | todo |
| P3-02 | 3 | Integrate buger/jsonparser, francoispqt/gojay, json-smart | P3-01 | todo |
| P3-03 | 3 | Integrate Fastjson 1.x, Genson, jsoniter Java | P3-02 | todo |
| P3-04 | 3 | Integrate Groovy JsonSlurper, Utf8Json, Jayrock.Json | P3-03 | todo |
| P3-05 | 3 | Integrate Manatee.Json, Ruby pure JSON, simdjson_ruby | P3-04 | todo |
| P3-06 | 3 | Integrate python-rapidjson, ijson, json-stream | P3-05 | todo |
| P3-07 | 3 | Integrate rxi/json.lua, gjson, JSON5 JavaScript | P3-06 | todo |
| P3-08 | 3 | Integrate json5 Rust, jsonc-parser, HJSON JavaScript | P3-07 | todo |
| P3-09 | 3 | Integrate SmarterJSON, gason, microjson | P3-08 | todo |
| P3-10 | 3 | Integrate mjson cpq, frozen, tiny-json | P3-09 | todo |
| P3-11 | 3 | Integrate lwjson, sheredom/json.h, pjson | P3-10 | todo |
| P3-12 | 3 | Integrate yyjson, orjson, go-json-experiment/json | P3-11 | todo |
| P3-13 | 3 | Integrate Euneus, lunajson, Boost.JSON | P3-12 | todo |
| P3-D01 | 3 | Resolve remaining candidates: msgspec, wjson, jsoncons, libjson SourceForge | P3-13 | todo |
| P3-D02 | 3 | Resolve remaining candidates: Boost.PropertyTree, mikeando/FastJson, jsonic Go, jsonvx | P3-D01 | todo |
| P3-D03 | 3 | Resolve remaining candidates: jsonic TypeScript, SafeJsonParser, best-effort-json-parser, ujson4c | P3-D02 | todo |
| P3-D04 | 3 | Resolve remaining candidates: go-ujson, nujson, ujson C++, Configuru | P3-D03 | todo |
| P3-D05 | 3 | Resolve remaining candidates: serde-hjson, colinodell/json5, SerafimArts/Json5, hiroto-k/JSON5-php | P3-D04 | todo |
| P3-D06 | 3 | Resolve remaining candidates: json5 gem, json5 PyPI, JSON6, stream-json JSONC | P3-D05 | todo |
| P3-D07 | 3 | Resolve remaining candidates: Amazon Ion text, mu_json, LibU json, M JSON parser SourceForge mjson | P3-D06 | todo |
| P3-D08 | 3 | Resolve remaining candidates: cisson, nanoJSONc, jsonsl, WJElement | P3-D07 | todo |
| P3-D09 | 3 | Resolve remaining candidates: cson, nosjob, mm_json.h, qajson4c | P3-D08 | todo |
| P3-D10 | 3 | Resolve remaining candidates: facil.io, vincenthz/libjson, NXJSON, ULib | P3-D09 | todo |
| P3-D11 | 3 | Resolve remaining candidates: StiX Json, last.json, JsonBox, CAJUN | P3-D10 | todo |
| P3-D12 | 3 | Resolve remaining candidates: json-voorhees, jvar, jeayeson, Jzon | P3-D11 | todo |
| P3-D13 | 3 | Resolve remaining candidates: nbsdx/SimpleJSON, MJPA/SimpleJSON, hjiang/jsonxx, tunnuz/JSON++ | P3-D12 | todo |
| P3-D14 | 3 | Resolve remaining candidates: minijson, jsonme--, jsovon, qmjson | P3-D13 | todo |
| P3-D15 | 3 | Resolve remaining candidates: JsonWax, Real Time Logic JSON IoT, Qentem-Engine, QJson | P3-D14 | todo |
| P3-D16 | 3 | Resolve remaining candidates: univalue, parson, ArduinoJson, JsonCpp | P3-D15 | todo |
| P3-D17 | 3 | Resolve remaining candidates: dropbox/json11, Poco::JSON, Folly dynamic, Qt QJsonDocument | P3-D16 | todo |
| P3-D18 | 3 | Resolve remaining candidates: Casablanca, ThorsSerializer, Boon, DSL-JSON | P3-D17 | todo |
| P3-D19 | 3 | Resolve remaining candidates: avaje-jsonb, minimal-json, bolerio/mjson, underscore-java | P3-D18 | todo |
| P3-D20 | 3 | Resolve remaining candidates: antonsjava/json, Tapestry JSON, LoganSquare, purejson | P3-D19 | todo |
| P3-D21 | 3 | Resolve remaining candidates: qson, Quickbuf JSON, json-io, Jettison | P3-D20 | todo |
| P3-D22 | 3 | Resolve remaining candidates: XStream JSON driver, Jodd JSON, Moshi, Jackson jr | P3-D21 | todo |
| P3-D23 | 3 | Resolve remaining candidates: kotlinx.serialization, Klaxon, Flexjson, json-lib | P3-D22 | todo |
| P3-D24 | 3 | Resolve remaining candidates: JSON-util, Argo Java, jsonij, jjson | P3-D23 | todo |
| P3-D25 | 3 | Resolve remaining candidates: FOSS Nova JSON, Corn CONVERTER, cookjson, Stringtree | P3-D24 | todo |
| P3-D26 | 3 | Resolve remaining candidates: SOJO, json-taglib, esson, JSONUtil | P3-D25 | todo |
| P3-D27 | 3 | Resolve remaining candidates: MOXy, Play JSON, spray-json, uPickle | P3-D26 | todo |
| P3-D28 | 3 | Resolve remaining candidates: weePickle, json4s, Argonaut, ZIO JSON | P3-D27 | todo |
| P3-D29 | 3 | Resolve remaining candidates: jsoniter-scala, borer, smithy4s-json, zio-schema-json | P3-D28 | todo |
| P3-D30 | 3 | Resolve remaining candidates: Lift JSON, scalajack, tupson, AVSystem scala-commons | P3-D29 | todo |
| P3-D31 | 3 | Resolve remaining candidates: Cheshire, jsonista, charred, Jil | P3-D30 | todo |
| P3-D32 | 3 | Resolve remaining candidates: NetJSON, SpanJson, ServiceStack.Text, fastJSON | P3-D31 | todo |
| P3-D33 | 3 | Resolve remaining candidates: FastJsonParser, LightJson, csjson, Liersch.Json | P3-D32 | todo |
| P3-D34 | 3 | Resolve remaining candidates: Liersch.JsonSerialization, JSON Essentials, JSON_checker C#, LitJson | P3-D33 | todo |
| P3-D35 | 3 | Resolve remaining candidates: JavaScriptSerializer, DataContractJsonSerializer, Windows.Data.Json, Swifter.Json | P3-D34 | todo |
| P3-D36 | 3 | Resolve remaining candidates: FSharp.Data, Thoth.Json, segmentio/encoding, sugawarayuuta/sonnet | P3-D35 | todo |
| P3-D37 | 3 | Resolve remaining candidates: mailru/easyjson, pquerna/ffjson, valyala/fastjson, bitly/go-simplejson | P3-D36 | todo |
| P3-D38 | 3 | Resolve remaining candidates: jscan, ojg, simd-json, simdjson-rust | P3-D37 | todo |
| P3-D39 | 3 | Resolve remaining candidates: sonic-rs, jiter, Pikkr, A-JSON | P3-D38 | todo |
| P3-D40 | 3 | Resolve remaining candidates: GJSON Rust, tinyjson, nanoserde, asmjson | P3-D39 | todo |
| P3-D41 | 3 | Resolve remaining candidates: kowito-json, rust-json-parse, yapic.json, hyperjson | P3-D40 | todo |
| P3-D42 | 3 | Resolve remaining candidates: pydantic-core, json2.js, json_parse.js, JSON 3 | P3-D41 | todo |
| P3-D43 | 3 | Resolve remaining candidates: clarinet, Oboe.js, jsonparse, json-stream npm | P3-D42 | todo |
| P3-D44 | 3 | Resolve remaining candidates: big-json, yieldable-json, stream-json, parse-json | P3-D43 | todo |
| P3-D45 | 3 | Resolve remaining candidates: json-parse-better-errors, jsonlint, json-buffer, buffer-json | P3-D44 | todo |
| P3-D46 | 3 | Resolve remaining candidates: seld/jsonlint, halaxa/json-machine, salsify/jsonstreamingparser, Webmozart JSON | P3-D45 | todo |
| P3-D47 | 3 | Resolve remaining candidates: jsond, rapidjson-ruby, fast_jsonparser, json-stream Ruby | P3-D46 | todo |
| P3-D48 | 3 | Resolve remaining candidates: jsone, jsx, jiffy, erl-json exograd | P3-D47 | todo |
| P3-D49 | 3 | Resolve remaining candidates: jhn_stdlib json, ojson, Exneus, torque | P3-D48 | todo |
| P3-D50 | 3 | Resolve remaining candidates: glazer, IkigaJSON, rarestype/swift-json, SwiftyJSON | P3-D49 | todo |
| P3-D51 | 3 | Resolve remaining candidates: HandyJSON, Himotoki, JBird, universal | P3-D50 | todo |
| P3-D52 | 3 | Resolve remaining candidates: SmartCodable, CodableJSON, Jay, Argo Swift | P3-D51 | todo |
| P3-D53 | 3 | Resolve remaining candidates: Unbox, Mantle, JSONModel, yajl-objc | P3-D52 | todo |
| P3-D54 | 3 | Resolve remaining candidates: lua-cjson, lua-yajl, JSON::MaybeXS, JSON::Create | P3-D53 | todo |
| P3-D55 | 3 | Resolve remaining candidates: JSON::Streaming::Reader, Racket json-parsing, MZScheme JSON, JSON-struct | P3-D54 | todo |
| P3-D56 | 3 | Resolve remaining candidates: Guile json, Chicken json, cl-json, jsown | P3-D55 | todo |
| P3-D57 | 3 | Resolve remaining candidates: yason, jonathan, shasht, JSON.jl | P3-D56 | todo |
| P3-D58 | 3 | Resolve remaining candidates: JSON3.jl, std.json, asdf, vibe.data.json | P3-D57 | todo |
| P3-D59 | 3 | Resolve remaining candidates: mir-ion, jsonm, ezjsonm, jsonaf | P3-D58 | todo |
| P3-D60 | 3 | Resolve remaining candidates: Text.JSON, RJson, hjson Haskell, jsony | P3-D59 | todo |
| P3-D61 | 3 | Resolve remaining candidates: JSON::Fast, RJSONIO, yyjsonr, dart:convert | P3-D60 | todo |
| P3-D62 | 3 | Resolve remaining candidates: 8th json, as3corelib, GNATCOLL.JSON, JSON-ADVPL | P3-D61 | todo |
| P3-D63 | 3 | Resolve remaining candidates: APL JSON, JSON for ASP, JSON ASP utility class, VB-JSON | P3-D62 | todo |
| P3-D64 | 3 | Resolve remaining candidates: PW.JSON, .NET-JSON-Transformer, rhawk json.awk, bmx-rjson | P3-D63 | todo |
| P3-D65 | 3 | Resolve remaining candidates: Redvers COBOL JSON Interface, GnuCOBOL JSON, SerializeJSON, Delphi Web Utils | P3-D64 | todo |
| P3-D66 | 3 | Resolve remaining candidates: JSON Delphi Library, SuperObject, JsonTools, System.JSON | P3-D65 | todo |
| P3-D67 | 3 | Resolve remaining candidates: JSON in TermL, Fantom Json, FileMaker JSON, LabVIEW flatten | P3-D66 | todo |
| P3-D68 | 3 | Resolve remaining candidates: LiveCode mergJSON, LotusScript JSON LS, M DataBallet, Net.Data netdata-json | P3-D67 | todo |
| P3-D69 | 3 | Resolve remaining candidates: json-fortran, YAJL-Fort, jsonff, groovy-io | P3-D68 | todo |
| P3-D70 | 3 | Resolve remaining candidates: JSONlab, MATLAB File Exchange 20565, MATLAB File Exchange 23393, PascalScript JsonParser | P3-D69 | todo |
| P3-D71 | 3 | Resolve remaining candidates: Photoshop JSON scripting, picolisp-json, Public.Parser.JSON Pike, JSON2 Pike | P3-D70 | todo |
| P3-D72 | 3 | Resolve remaining candidates: pljson, PL/JSON, PureBasic JSON, PuRestJson | P3-D71 | todo |
| P3-D73 | 3 | Resolve remaining candidates: json.r Rebol, RPG JSON Utilities, Squeak, Tcl JSON wiki | P3-D72 | todo |
| P3-D74 | 3 | Resolve remaining candidates: fwJSON, vfpjson, Wing json-type, Jshon | P3-D73 | todo |
| P3-D75 | 3 | Resolve remaining candidates: JSON.sh derivatives, jwalk, jsawk, json CLI | P3-D74 | todo |
| P3-D76 | 3 | Resolve remaining candidates: jl, fx, gojq, jaq | P3-D75 | todo |
| P3-D77 | 3 | Resolve remaining candidates: jql, dasel, Miller, yq | P3-D76 | todo |
| P3-D78 | 3 | Resolve remaining candidates: PowerShell ConvertFrom-Json, MySQL JSON, MariaDB JSON, Oracle JSON | P3-D77 | todo |
| P3-D79 | 3 | Resolve remaining candidates: SQL Server OPENJSON, DuckDB, ClickHouse, MongoDB Extended JSON | P3-D78 | todo |
| P3-D80 | 3 | Resolve remaining candidates: Thoas, OTP json, @streamparser/json, secure-json-parse | P3-D79 | todo |
| P3-D81 | 3 | Resolve remaining candidates: taocpp/json, glaze, Jakarta JSON-P Glassfish, Eclipse Yasson | P3-D80 | todo |
| P3-D82 | 3 | Resolve remaining candidates: Apache Johnzon, Jawn, circe, trivet JSON parser | P3-D81 | todo |
| P3-D83 | 3 | Resolve remaining candidates: Kson, json-event-parser, simdjson-go, simdjson-java | P3-D82 | todo |
| P3-D84 | 3 | Resolve remaining candidates: SimdJsonSharp, QuickJS, Duktape, Hermes | P3-D83 | todo |
| P3-D85 | 3 | Resolve remaining candidates: Rhino, Nashorn, GraalJS, Elm Json.Decode | P3-D84 | todo |
| P3-D86 | 3 | Resolve remaining candidates: PureScript argonaut, Crystal, V, Odin | P3-D85 | todo |
| P3-D87 | 3 | Resolve remaining candidates: Gleam, Pony, Haxe | P3-D86 | todo |
| P4-01 | 4 | Build parser-by-feature matrix and compare each prediction | P3-D87 | todo |
| P5-01 | 5 | Verify reproducible profiles, CI verdicts, and usage | P4-01 | todo |

## Deliverables and acceptance commands

Full deliverables and exact command arrays are recorded per task in backlog.json.
The commands below are duplicated for review; future script paths are deliverables
of the named task, not claims that they already exist.

### P0-01 — Record registry, Appendix A reconciliation, environments, and baseline

Deliverables: `docs/roadmap/ground-truth.md`; `docs/roadmap/ground-truth.json`.

```sh
python3 -B tools/roadmap_inventory.py --check
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P1-01 — Validate split catalog, source tags, exclusions, and first Go pins

Deliverables: `tools/check_roadmap.py`; `docs/roadmap/backlog.json`; `docs/roadmap/catalog-review.md`.

```sh
python3 -B tools/check_roadmap.py
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P2-01 — Specify observation protocol and neutral normalization

Deliverables: `docs/feature-observation-protocol.md`.

```sh
python3 -B tools/check_roadmap.py --task P2-01
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P2-02 — Add exact-byte convenience probes and manifest

Deliverables: `test_features/`; `metadata/convenience-features.json`; `tools/check_feature_manifest.py`; `tests/test_feature_manifest.py`.

```sh
python3 -B tools/check_feature_manifest.py
python3 -B -m unittest discover -s tests -p test_feature_manifest.py -v
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P2-03 — Implement filtered, parallel, bounded observation runner

Deliverables: `run_features.py`; `tests/test_feature_runner.py`.

```sh
python3 -B -m unittest discover -s tests -p test_feature_runner.py -v
python3 -B run_features.py --help
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P2-04 — Add Python and Node observations and record a feature baseline

Deliverables: `parsers/observe_python_features.py`; `parsers/observe_node_features.js`; `docs/review-batch-feature-baseline.md`; `tests/test_feature_observers.py`.

```sh
python3 -B -m unittest discover -s tests -p test_feature_observers.py -v
python3 -B tools/check_roadmap.py --task P2-04
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-01 — Integrate goccy/go-json, bytedance/sonic, json-iterator/go

Deliverables: `docs/review-batch-feature-01.md`; `pinned adapter builds, registry modes, and observers`; `per-mode standard corpus and feature audit`.

```sh
sh parsers/features/build_batch_01.sh
python3 -B tools/validate_feature_batch.py P3-01 --output /tmp/jsonsuite-P3-01-audit
python3 -B tools/check_roadmap.py --task P3-01
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-02 — Integrate buger/jsonparser, francoispqt/gojay, json-smart

Deliverables: `docs/review-batch-feature-02.md`; `pinned adapter builds, registry modes, and observers`; `per-mode standard corpus and feature audit`.

```sh
sh parsers/features/build_batch_02.sh
python3 -B tools/validate_feature_batch.py P3-02 --output /tmp/jsonsuite-P3-02-audit
python3 -B tools/check_roadmap.py --task P3-02
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-03 — Integrate Fastjson 1.x, Genson, jsoniter Java

Deliverables: `docs/review-batch-feature-03.md`; `pinned adapter builds, registry modes, and observers`; `per-mode standard corpus and feature audit`.

```sh
sh parsers/features/build_batch_03.sh
python3 -B tools/validate_feature_batch.py P3-03 --output /tmp/jsonsuite-P3-03-audit
python3 -B tools/check_roadmap.py --task P3-03
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-04 — Integrate Groovy JsonSlurper, Utf8Json, Jayrock.Json

Deliverables: `docs/review-batch-feature-04.md`; `pinned adapter builds, registry modes, and observers`; `per-mode standard corpus and feature audit`.

```sh
sh parsers/features/build_batch_04.sh
python3 -B tools/validate_feature_batch.py P3-04 --output /tmp/jsonsuite-P3-04-audit
python3 -B tools/check_roadmap.py --task P3-04
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-05 — Integrate Manatee.Json, Ruby pure JSON, simdjson_ruby

Deliverables: `docs/review-batch-feature-05.md`; `pinned adapter builds, registry modes, and observers`; `per-mode standard corpus and feature audit`.

```sh
sh parsers/features/build_batch_05.sh
python3 -B tools/validate_feature_batch.py P3-05 --output /tmp/jsonsuite-P3-05-audit
python3 -B tools/check_roadmap.py --task P3-05
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-06 — Integrate python-rapidjson, ijson, json-stream

Deliverables: `docs/review-batch-feature-06.md`; `pinned adapter builds, registry modes, and observers`; `per-mode standard corpus and feature audit`.

```sh
sh parsers/features/build_batch_06.sh
python3 -B tools/validate_feature_batch.py P3-06 --output /tmp/jsonsuite-P3-06-audit
python3 -B tools/check_roadmap.py --task P3-06
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-07 — Integrate rxi/json.lua, gjson, JSON5 JavaScript

Deliverables: `docs/review-batch-feature-07.md`; `pinned adapter builds, registry modes, and observers`; `per-mode standard corpus and feature audit`.

```sh
sh parsers/features/build_batch_07.sh
python3 -B tools/validate_feature_batch.py P3-07 --output /tmp/jsonsuite-P3-07-audit
python3 -B tools/check_roadmap.py --task P3-07
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-08 — Integrate json5 Rust, jsonc-parser, HJSON JavaScript

Deliverables: `docs/review-batch-feature-08.md`; `pinned adapter builds, registry modes, and observers`; `per-mode standard corpus and feature audit`.

```sh
sh parsers/features/build_batch_08.sh
python3 -B tools/validate_feature_batch.py P3-08 --output /tmp/jsonsuite-P3-08-audit
python3 -B tools/check_roadmap.py --task P3-08
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-09 — Integrate SmarterJSON, gason, microjson

Deliverables: `docs/review-batch-feature-09.md`; `pinned adapter builds, registry modes, and observers`; `per-mode standard corpus and feature audit`.

```sh
sh parsers/features/build_batch_09.sh
python3 -B tools/validate_feature_batch.py P3-09 --output /tmp/jsonsuite-P3-09-audit
python3 -B tools/check_roadmap.py --task P3-09
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-10 — Integrate mjson cpq, frozen, tiny-json

Deliverables: `docs/review-batch-feature-10.md`; `pinned adapter builds, registry modes, and observers`; `per-mode standard corpus and feature audit`.

```sh
sh parsers/features/build_batch_10.sh
python3 -B tools/validate_feature_batch.py P3-10 --output /tmp/jsonsuite-P3-10-audit
python3 -B tools/check_roadmap.py --task P3-10
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-11 — Integrate lwjson, sheredom/json.h, pjson

Deliverables: `docs/review-batch-feature-11.md`; `pinned adapter builds, registry modes, and observers`; `per-mode standard corpus and feature audit`.

```sh
sh parsers/features/build_batch_11.sh
python3 -B tools/validate_feature_batch.py P3-11 --output /tmp/jsonsuite-P3-11-audit
python3 -B tools/check_roadmap.py --task P3-11
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-12 — Integrate yyjson, orjson, go-json-experiment/json

Deliverables: `docs/review-batch-feature-12.md`; `pinned adapter builds, registry modes, and observers`; `per-mode standard corpus and feature audit`.

```sh
sh parsers/features/build_batch_12.sh
python3 -B tools/validate_feature_batch.py P3-12 --output /tmp/jsonsuite-P3-12-audit
python3 -B tools/check_roadmap.py --task P3-12
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-13 — Integrate Euneus, lunajson, Boost.JSON

Deliverables: `docs/review-batch-feature-13.md`; `pinned adapter builds, registry modes, and observers`; `per-mode standard corpus and feature audit`.

```sh
sh parsers/features/build_batch_13.sh
python3 -B tools/validate_feature_batch.py P3-13 --output /tmp/jsonsuite-P3-13-audit
python3 -B tools/check_roadmap.py --task P3-13
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D01 — Resolve remaining candidates: msgspec, wjson, jsoncons, libjson SourceForge

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D01
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D02 — Resolve remaining candidates: Boost.PropertyTree, mikeando/FastJson, jsonic Go, jsonvx

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D02
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D03 — Resolve remaining candidates: jsonic TypeScript, SafeJsonParser, best-effort-json-parser, ujson4c

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D03
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D04 — Resolve remaining candidates: go-ujson, nujson, ujson C++, Configuru

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D04
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D05 — Resolve remaining candidates: serde-hjson, colinodell/json5, SerafimArts/Json5, hiroto-k/JSON5-php

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D05
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D06 — Resolve remaining candidates: json5 gem, json5 PyPI, JSON6, stream-json JSONC

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D06
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D07 — Resolve remaining candidates: Amazon Ion text, mu_json, LibU json, M JSON parser SourceForge mjson

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D07
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D08 — Resolve remaining candidates: cisson, nanoJSONc, jsonsl, WJElement

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D08
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D09 — Resolve remaining candidates: cson, nosjob, mm_json.h, qajson4c

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D09
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D10 — Resolve remaining candidates: facil.io, vincenthz/libjson, NXJSON, ULib

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D10
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D11 — Resolve remaining candidates: StiX Json, last.json, JsonBox, CAJUN

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D11
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D12 — Resolve remaining candidates: json-voorhees, jvar, jeayeson, Jzon

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D12
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D13 — Resolve remaining candidates: nbsdx/SimpleJSON, MJPA/SimpleJSON, hjiang/jsonxx, tunnuz/JSON++

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D13
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D14 — Resolve remaining candidates: minijson, jsonme--, jsovon, qmjson

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D14
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D15 — Resolve remaining candidates: JsonWax, Real Time Logic JSON IoT, Qentem-Engine, QJson

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D15
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D16 — Resolve remaining candidates: univalue, parson, ArduinoJson, JsonCpp

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D16
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D17 — Resolve remaining candidates: dropbox/json11, Poco::JSON, Folly dynamic, Qt QJsonDocument

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D17
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D18 — Resolve remaining candidates: Casablanca, ThorsSerializer, Boon, DSL-JSON

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D18
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D19 — Resolve remaining candidates: avaje-jsonb, minimal-json, bolerio/mjson, underscore-java

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D19
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D20 — Resolve remaining candidates: antonsjava/json, Tapestry JSON, LoganSquare, purejson

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D20
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D21 — Resolve remaining candidates: qson, Quickbuf JSON, json-io, Jettison

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D21
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D22 — Resolve remaining candidates: XStream JSON driver, Jodd JSON, Moshi, Jackson jr

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D22
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D23 — Resolve remaining candidates: kotlinx.serialization, Klaxon, Flexjson, json-lib

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D23
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D24 — Resolve remaining candidates: JSON-util, Argo Java, jsonij, jjson

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D24
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D25 — Resolve remaining candidates: FOSS Nova JSON, Corn CONVERTER, cookjson, Stringtree

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D25
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D26 — Resolve remaining candidates: SOJO, json-taglib, esson, JSONUtil

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D26
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D27 — Resolve remaining candidates: MOXy, Play JSON, spray-json, uPickle

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D27
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D28 — Resolve remaining candidates: weePickle, json4s, Argonaut, ZIO JSON

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D28
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D29 — Resolve remaining candidates: jsoniter-scala, borer, smithy4s-json, zio-schema-json

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D29
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D30 — Resolve remaining candidates: Lift JSON, scalajack, tupson, AVSystem scala-commons

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D30
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D31 — Resolve remaining candidates: Cheshire, jsonista, charred, Jil

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D31
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D32 — Resolve remaining candidates: NetJSON, SpanJson, ServiceStack.Text, fastJSON

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D32
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D33 — Resolve remaining candidates: FastJsonParser, LightJson, csjson, Liersch.Json

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D33
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D34 — Resolve remaining candidates: Liersch.JsonSerialization, JSON Essentials, JSON_checker C#, LitJson

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D34
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D35 — Resolve remaining candidates: JavaScriptSerializer, DataContractJsonSerializer, Windows.Data.Json, Swifter.Json

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D35
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D36 — Resolve remaining candidates: FSharp.Data, Thoth.Json, segmentio/encoding, sugawarayuuta/sonnet

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D36
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D37 — Resolve remaining candidates: mailru/easyjson, pquerna/ffjson, valyala/fastjson, bitly/go-simplejson

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D37
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D38 — Resolve remaining candidates: jscan, ojg, simd-json, simdjson-rust

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D38
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D39 — Resolve remaining candidates: sonic-rs, jiter, Pikkr, A-JSON

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D39
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D40 — Resolve remaining candidates: GJSON Rust, tinyjson, nanoserde, asmjson

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D40
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D41 — Resolve remaining candidates: kowito-json, rust-json-parse, yapic.json, hyperjson

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D41
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D42 — Resolve remaining candidates: pydantic-core, json2.js, json_parse.js, JSON 3

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D42
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D43 — Resolve remaining candidates: clarinet, Oboe.js, jsonparse, json-stream npm

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D43
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D44 — Resolve remaining candidates: big-json, yieldable-json, stream-json, parse-json

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D44
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D45 — Resolve remaining candidates: json-parse-better-errors, jsonlint, json-buffer, buffer-json

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D45
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D46 — Resolve remaining candidates: seld/jsonlint, halaxa/json-machine, salsify/jsonstreamingparser, Webmozart JSON

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D46
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D47 — Resolve remaining candidates: jsond, rapidjson-ruby, fast_jsonparser, json-stream Ruby

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D47
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D48 — Resolve remaining candidates: jsone, jsx, jiffy, erl-json exograd

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D48
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D49 — Resolve remaining candidates: jhn_stdlib json, ojson, Exneus, torque

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D49
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D50 — Resolve remaining candidates: glazer, IkigaJSON, rarestype/swift-json, SwiftyJSON

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D50
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D51 — Resolve remaining candidates: HandyJSON, Himotoki, JBird, universal

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D51
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D52 — Resolve remaining candidates: SmartCodable, CodableJSON, Jay, Argo Swift

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D52
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D53 — Resolve remaining candidates: Unbox, Mantle, JSONModel, yajl-objc

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D53
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D54 — Resolve remaining candidates: lua-cjson, lua-yajl, JSON::MaybeXS, JSON::Create

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D54
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D55 — Resolve remaining candidates: JSON::Streaming::Reader, Racket json-parsing, MZScheme JSON, JSON-struct

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D55
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D56 — Resolve remaining candidates: Guile json, Chicken json, cl-json, jsown

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D56
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D57 — Resolve remaining candidates: yason, jonathan, shasht, JSON.jl

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D57
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D58 — Resolve remaining candidates: JSON3.jl, std.json, asdf, vibe.data.json

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D58
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D59 — Resolve remaining candidates: mir-ion, jsonm, ezjsonm, jsonaf

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D59
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D60 — Resolve remaining candidates: Text.JSON, RJson, hjson Haskell, jsony

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D60
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D61 — Resolve remaining candidates: JSON::Fast, RJSONIO, yyjsonr, dart:convert

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D61
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D62 — Resolve remaining candidates: 8th json, as3corelib, GNATCOLL.JSON, JSON-ADVPL

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D62
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D63 — Resolve remaining candidates: APL JSON, JSON for ASP, JSON ASP utility class, VB-JSON

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D63
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D64 — Resolve remaining candidates: PW.JSON, .NET-JSON-Transformer, rhawk json.awk, bmx-rjson

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D64
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D65 — Resolve remaining candidates: Redvers COBOL JSON Interface, GnuCOBOL JSON, SerializeJSON, Delphi Web Utils

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D65
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D66 — Resolve remaining candidates: JSON Delphi Library, SuperObject, JsonTools, System.JSON

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D66
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D67 — Resolve remaining candidates: JSON in TermL, Fantom Json, FileMaker JSON, LabVIEW flatten

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D67
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D68 — Resolve remaining candidates: LiveCode mergJSON, LotusScript JSON LS, M DataBallet, Net.Data netdata-json

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D68
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D69 — Resolve remaining candidates: json-fortran, YAJL-Fort, jsonff, groovy-io

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D69
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D70 — Resolve remaining candidates: JSONlab, MATLAB File Exchange 20565, MATLAB File Exchange 23393, PascalScript JsonParser

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D70
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D71 — Resolve remaining candidates: Photoshop JSON scripting, picolisp-json, Public.Parser.JSON Pike, JSON2 Pike

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D71
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D72 — Resolve remaining candidates: pljson, PL/JSON, PureBasic JSON, PuRestJson

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D72
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D73 — Resolve remaining candidates: json.r Rebol, RPG JSON Utilities, Squeak, Tcl JSON wiki

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D73
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D74 — Resolve remaining candidates: fwJSON, vfpjson, Wing json-type, Jshon

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D74
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D75 — Resolve remaining candidates: JSON.sh derivatives, jwalk, jsawk, json CLI

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D75
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D76 — Resolve remaining candidates: jl, fx, gojq, jaq

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D76
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D77 — Resolve remaining candidates: jql, dasel, Miller, yq

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D77
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D78 — Resolve remaining candidates: PowerShell ConvertFrom-Json, MySQL JSON, MariaDB JSON, Oracle JSON

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D78
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D79 — Resolve remaining candidates: SQL Server OPENJSON, DuckDB, ClickHouse, MongoDB Extended JSON

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D79
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D80 — Resolve remaining candidates: Thoas, OTP json, @streamparser/json, secure-json-parse

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D80
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D81 — Resolve remaining candidates: taocpp/json, glaze, Jakarta JSON-P Glassfish, Eclipse Yasson

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D81
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D82 — Resolve remaining candidates: Apache Johnzon, Jawn, circe, trivet JSON parser

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D82
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D83 — Resolve remaining candidates: Kson, json-event-parser, simdjson-go, simdjson-java

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D83
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D84 — Resolve remaining candidates: SimdJsonSharp, QuickJS, Duktape, Hermes

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D84
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D85 — Resolve remaining candidates: Rhino, Nashorn, GraalJS, Elm Json.Decode

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D85
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D86 — Resolve remaining candidates: PureScript argonaut, Crystal, V, Odin

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D86
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P3-D87 — Resolve remaining candidates: Gleam, Pony, Haxe

Deliverables: `per-item primary-source identity, engine ownership, pin, license, and disposition`; `roadmap amendment for any independently implemented library requiring integration`.

```sh
python3 -B tools/check_roadmap.py --task P3-D87
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P4-01 — Build parser-by-feature matrix and compare each prediction

Deliverables: `analyze_features.py`; `docs/feature-analysis.md`; `machine-readable feature matrix and prediction dispositions`; `tests/test_feature_analysis.py`.

```sh
python3 -B -m unittest discover -s tests -p test_feature_analysis.py -v
python3 -B tools/check_roadmap.py --task P4-01
python3 -B -m unittest discover -s tests -v
git diff --check
```

### P5-01 — Verify reproducible profiles, CI verdicts, and usage

Deliverables: `Docker/build profiles for integrated adapters`; `README.md feature usage`; `docs/feature-reproducibility.md`.

```sh
python3 -B tools/check_roadmap.py --task P5-01
python3 -B -m unittest discover -s tests -v
git diff --check
python3 -B -m unittest discover -s tests -v
git diff --check
```

## Phase summaries

Phase 0 completed: recorded 123 registry modes, the 327/26 fixture counts,
six scoped image IDs, and the successful 99-test baseline (22 optional skips).
The PDF inventory predates 29 registry modes and overlaps existing Folly and
platform entries. No new parser coverage is claimed. Phase 1 completed the split catalog and
first Go source verification: three pins, 101 tests with 22 optional skips.
Phases 2–5 remain pending.

## Amendments

2026-10-04, P1-01: QJson remains an unresolved library identity rather than
verified existing coverage; the existing Qt adapter uses QJsonDocument. Source
URLs for unresolved names point to the document's discovery source, not an
invented library repository. M-only rows retain null URLs. Concrete library
URLs and pins must be verified before integration.

2026-10-04, P1-01: batch acceptance now includes its concrete build script and
`tools/validate_feature_batch.py` corpus/probe audit. P2-04 provides that helper.
A document check alone cannot mark an adapter integrated; failed setup remains
an explicit untested disposition with its reason and no claimed coverage.
