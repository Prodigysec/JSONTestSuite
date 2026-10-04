# Feature adapter batch 03: Fastjson 1.x, Genson, jsoniter Java

Three independently maintained Java libraries are registered in eight modes.
The PDF's measured tiers remain external predictions pending phase 4. Native
values and extensions are observations, not RFC validity decisions.

| Library | Tested release | Source / license | Modes |
| --- | --- | --- | --- |
| [Fastjson 1.x](https://github.com/alibaba/fastjson) | 1.2.83 | Maven Central release sources; Apache-2.0 | default features, extension flags off, AllowComment, UseBigDecimal off; SafeMode and whole input in each |
| [Genson](https://github.com/owlike/genson) | 1.6 | Maven Central release sources; Apache-2.0 | default with native encoding detection, default with explicit native UTF-8 API, strict double conversion with explicit native UTF-8 API |
| [jsoniter Java](https://github.com/json-iterator/java) | 0.9.23 | Maven Central release sources; MIT | generic read with default reflection serializer, whole input |

## Reviewed sources and reproducible build

[Source pins](../parsers/features/java_batch_03/sources.json) identify the exact
SHA-256 of each official release runtime JAR, source JAR and POM. These are
release-artifact revisions. Genson 1.6 has no matching repository tag. Jsoniter
0.9.23 has tag revision 42e8df1ae1b553d070a6667f49cf63c6904ead5f. Fifteen
source files were reviewed
for parse, conversion, encoding, framing and configuration behavior, and their
hashes are checked at build time. Fastjson's 1.2.83 Git tag also identifies
26f13f84fdd522de10678e43f55fde918ab7b347; the actual build inputs are the pinned
Maven artifacts, not that Git archive.

```sh
sh parsers/features/build_batch_03.sh
python3 -B -m unittest discover -s tests -p test_feature_batch_03.py -v
python3 -B tools/validate_feature_batch.py P3-03 --output /tmp/jsonsuite-P3-03-audit --jobs 3
python3 -B tools/check_roadmap.py --task P3-03
python3 -B -m unittest discover -s tests -v
```

Use a fresh audit directory for repeat runs. JDK >=17 is required; set
JSONSUITE_JAVA_HOME if it is not on PATH. Tested: isolated OpenJDK/javac
21.0.12.1 on Linux x86_64, with --release 17 bytecode. Other platforms are
untested. This build compiles the repository observer against official release
JARs; it does **not** claim locally rebuilt library binaries. This avoids unrelated
optional servlet, Spring, JAX-RS and code-generation build dependencies. The
runtime/source/POM checksums and preserved notices make the chosen artifact
build explicit and repeatable. Runtime artifacts are fetched into ignored
parsers/.build/java_batch_03; no new opaque binaries are tracked.

Genson's upstream runtime shades ASM 5.0.3; its BSD-3-Clause notice is retained
from the pinned official ASM POM. That source JAR has overlapping ZIP entries
and was not extracted or executed. Primary licenses, Fastjson's NOTICE, and
the ASM notice are preserved under parsers/features/licenses. Fastjson notices
retain upstream CRLF and the license's final blank line; a .gitattributes rule
scopes the whitespace exception and disables text conversion for those two files. Jsoniter's MIT
notice is pinned to repository license revision
0aff30153d74e05344923a0c22f50582ca881166. The builder checks source notice bytes,
preserved hashes and the external license bytes. No vendored build script is
executed. Compiled observer classes are published in immutable digest directories
with atomic runtime-pointer replacement.

Invocation: `python3 -B parsers/features/java_batch_03/run.py MODE FIXTURE`.
Add `--observe` before MODE for one observation envelope. Registry entries
provide exact commands. Exit 0 means native acceptance, 1 native rejection or
explicit complete-input framing rejection, and 2 adapter/infrastructure failure.
Native uncaught exceptions and bounded timeouts remain failures. Input bytes
are unchanged; no wrapper BOM removal or replacement decoding occurs.

## Native API and mode review

Fastjson's public parse(byte[]) returns null on failed IOUtils.decodeUTF8, which
is ambiguous with valid JSON null. The adapter uses that same native decoder
and checks its negative result, then constructs DefaultJSONParser from the
decoded characters. Initial native EOF means no value token. parse(), reference
resolution and close() retain library behavior. A read-only inspection of the
pinned lexer bp cursor rejects a trailing literal 0x1a that is otherwise confused
with end of input. Reflection/layout failures are adapter failures.

SafeMode is enabled on the parser configuration in all Fastjson modes and is
part of every mode label; @type handling is consequently constrained. The
extension-flags-off mode retains only AutoCloseSource and UseBigDecimal. Its
name is not a strict-RFC claim: native comments or controls can remain supported
without those extension flags. Other modes retain default parsing flags and
independently enable AllowComment or disable UseBigDecimal.

Genson uses its native createReader(byte[]) in the default encoding mode and
createReader(InputStream, UTF_8) in the two explicitly labelled UTF-8 modes.
The latter is a public library API, not an external decoder. Empty or RFC-
whitespace-only input is rejected as lacking a value (RFC 8259 section 2); native empty decoding
otherwise produces null. Native byte auto-detection maps one-byte `0` to null;
this finding is preserved, while the UTF-8 mode observes integer zero. Auto-
detection can also interpret 0/NUL byte patterns as UTF-16 and skip decoded
non-ASCII characters. Those native encoding effects must not be mistaken for
UTF-8 syntax behavior. Malformed UTF-8 replacement in the explicit UTF-8 modes
occurs inside the native reader.

Genson hasNext() can return false for trailing `]` or `=`, leaving input
unconsumed. After generic Object deserialization, the adapter invokes the pinned
native readNextToken(false) and requires actual EOF. Native trailing comment
handling is retained. Reflection failures surface separately from native
JsonStreamException. useStrictDoubleParse controls conversion precision, not
syntax strictness; both conversion paths are tested.

Jsoniter uses JsonIterator.parse(byte[]) and eager generic read(), followed by
its native head cursor plus a trailing RFC-whitespace check. Lazy Any/skip APIs
are not used as a substitute for complete validation. Native Map lookup and
JsonStream serialization provide getter/output observations. Its no-argument
serializer dereferences null; the adapter invokes the native typed serializer
for null instead. The default serializer uses reflection; generic read() uses native token
conversion without object-binding code generation. The
DYNAMIC_MODE_AND_MATCH_FIELD_STRICTLY option compares bound object fields;
it does not add syntax restrictions to the generic target. Struct-only field
matching modes and static generated decoders are therefore not represented as
additional generic JSON syntax modes.

## Validation and measured results

The focused suite passed eight tests, then a ninth regression verified that
jsoniter's native NumberFormatException remains exit 2 with no acceptance/rejection
envelope. All scalars and nested controls accepted, whole-input/empty checks
rejected, parse/observation commands agreed, missing files remained adapter errors,
and the cached-artifact tamper check failed before execution.

The feature survey records 1000/1000 pairs: 652 accepts, 339 rejects and nine
native crashes. Each Genson mode crashed on limits.deep-unclosed and
limits.nested-2048. Jsoniter crashed on those two probes and
numbers.minus-infinity. Direct native Genson and jsoniter numeric calls reproduce
the exceptions without observation code; a diagnostic observer trace places
jsoniter's unclosed-array overflow in native IterImplArray/JsonIterator recursion.
The closed jsoniter 2048-level array accepted on direct repeats, so this depth
outcome is sensitive to the call stack and JVM execution state. The survey's
crash record is retained; no fixed JVM stack budget or stable threshold is claimed.
Feature CI is 1 because these crashes remain failures, including limit probes.

Fastjson's extension-flags-off mode still accepts the trailing-comma and
unterminated-comment probes; its name is consequently not a strictness claim.
Its default/BigDecimal modes preserve the long decimal and 1.0E+4096 exactly;
UseBigDecimal off stores Infinity and serializes null. Genson and jsoniter store
Infinity and serialize the string "Infinity". Jsoniter rounds 9007199254740993
to integer 9007199254740992, and serializes the long decimal's binary64 value
as 0.123457. Its overlong UTF-8 string becomes slash, whereas Genson replaces
the two invalid bytes and Fastjson rejects them through its native decoder.

All three libraries collapse duplicate test members to the last value, verified
through actual Map lookup and native output. Genson accepts a single-quoted root
as a bare string **including** the quote characters; that is not single-quote
syntax recognition. Its True probe is a native boolean. Normalized observations
make these distinctions visible. Authoritative fixture expectations are unchanged.

The standard survey records 2616/2616 pairs. All y_ cases accepted. CI reports
366 unexpected n_ acceptances and 30 native crashes; there are no timeouts,
skips, missing rows or observer protocol failures. All 30 standard crashes were
reproduced: eight StackOverflowError outcomes on the two pathological structure
fixtures, and 22 jsoniter NumberFormatException outcomes on malformed numerals.
These failures remain explicit, never valid JSON rejection or successful limit
handling. Standard CI has 396 failures; audit exit 0 proves completeness only.

| Mode | Standard expected / unexpected accept / crash | Feature accept / reject / crash |
| --- | --- | --- |
| Fastjson default, AllowComment, UseBigDecimal off (each) | 238 / 50 / 0 | 87 / 38 / 0 |
| Fastjson extension flags off | 251 / 37 / 0 | 76 / 49 / 0 |
| Genson default auto-detection | 227 / 59 / 2 | 87 / 36 / 2 |
| Genson default explicit UTF-8 | 229 / 57 / 2 | 87 / 36 / 2 |
| Genson strict double, explicit UTF-8 | 240 / 46 / 2 | 87 / 36 / 2 |
| Jsoniter generic read | 247 / 17 / 24 | 54 / 68 / 3 |

Each mode also records 39 implementation-dependent verdicts. Strict double
conversion changes Genson's standard numeric outcomes even though these feature
probes have equal acceptance counts. [Tracked evidence](roadmap/feature-batch-03.json)
contains every feature status, selected native values, all standard discrepancy
names, crash reproductions, actual runtime versions, commands, copied corpus
hashes and source/artifact hashes. The five reviewed jsoniter release source
files exactly match tag 0.9.23 at 42e8df1ae1b553d070a6667f49cf63c6904ead5f.
Existing Fastjson 2 coverage is a separate engine/version and is unchanged.

The full unit suite passed: 148 tests, 22 optional skips, exit 0. Historical
reports and existing fixtures are
unchanged. These finite observations do not prove complete RFC compliance;
prediction dispositions remain untested until phase 4.
