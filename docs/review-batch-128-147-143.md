# Review batch: Newtonsoft.Json, JSONpp, and opack

Reviewed on 2026-10-02 from local commit `dbb0afc`. The three upstream PRs,
file diffs, comments, and reviews were refreshed; all remain open, with no
discussion or reviews. Integration here is adapted and does not merge them
upstream. No new corpus fixtures or historical reports are changed.

| Proposal | Reviewed base | Reviewed head | Local work |
| --- | --- | --- | --- |
| [#128](https://github.com/nst/JSONTestSuite/pull/128), Dependabot | `d64aefb55228d9584d3e5b2433f720ea8fd00c82` | `155657ad68afd6b425c196d7fb20bd7d2c6a8839` | Update the package reference to 13.0.2 and the registry label; validate complete input and strict UTF-8. |
| [#147](https://github.com/nst/JSONTestSuite/pull/147), `mikami-w` | `1ef36fa01286573e846ac449e8683f8833c5b26a` | `a29bf4188c1914aafa79724e9b8de7eddae9cf6e` | Add a source-built JSONpp 0.1.1 adapter; omit the proposed binary. |
| [#143](https://github.com/nst/JSONTestSuite/pull/143), `devjeonghwan` | `1ef36fa01286573e846ac449e8683f8833c5b26a` | `6d17cbeeb180316e63d5f99a1b6ffe5b81679595` | Add a source-built opack 0.2.1 adapter; omit the proposed class and JAR binaries. |

## .NET Newtonsoft.Json 13.0.2

PR #128 changes only the `PackageReference` from 12.0.3 to 13.0.2. The local
registry label had remained `12.0.3`, so it is updated too. The project still
targets `net5.0`; the registry invokes `dotnet build --configuration Release`
before using `bin/Release/net5.0/app.dll`. No runtime version detection is
claimed. A normal run needs a matching .NET runtime or explicit roll-forward
configuration. NuGet restore is required.

The existing wrapper called `Deserialize` once and returned success for empty
input, trailing garbage, and a second JSON text. This violates the adapter's
single-complete-text contract. It now checks for an initial token and sets
`CheckAdditionalContent = true`. Its UTF-8 reader throws on malformed bytes
instead of replacing them; it does not auto-detect or strip a BOM. Syntax and
decoding failures return `1`; missing files and other runtime failures return
`2`. The configured `MaxDepth = 512` remains an implementation limit. The
project's `bin/` and `obj/` build outputs are ignored.

The package was restored and compiled with the isolated .NET SDK **8.0.131**,
package **13.0.2**, targeting `net5.0` and running on .NET **8.0.31** with
`DOTNET_ROLL_FORWARD=Major`. This tests the declared package version and
wrapper behavior on Linux x86_64; it does not test a native .NET 5 runtime.

## C++ JSONpp 0.1.1

The upstream PR supplied a precompiled executable, an unverified tag download,
and a C++ wrapper. The binary is omitted. Local `build.sh` downloads source at
tag commit `eb7860e0f58cf0829d35d70d0f5dea9fe38b1593`, verifies archive
SHA-256 `715affe9d34d52cce49553a3d15db5cbf111961c6f50044f2b07a670c6a2aab4`,
then builds with a C++17 compiler. Build outputs go under ignored `.build/`.
JSONpp source is Apache-2.0 licensed; its source and license stay in the pinned
download and are not vendored into this repository.

The parser's `empty()` means its internal monostate, used for empty input;
it does not mean JSON `null`, `false`, `0`, `[]`, `{}`, or `""`. The upstream
wrapper's check is therefore retained. The adapted wrapper opens input in
binary mode, handles missing/read errors as `2`, catches parse and depth-limit
errors as `1`, and translates other failures to `2`. `json::parse` requires
end-of-input after a value. The library's own syntax and Unicode behavior
remain its native mode; a probe accepted the malformed-byte text `22 ff 22`,
which is an observed limit, not a claim of RFC 8259 compliance. The registry
name records the source version, not an installed runtime probe.

The source build passed with GCC **13.3.0** on Linux x86_64. Run:

```sh
sh parsers/test_jsonpp_0_1_1/build.sh
parsers/test_jsonpp_0_1_1/.build/test_jsonpp test_parsing/y_structure_lonely_null.json
```

The build requires `curl`, `sha256sum`, `tar`, and a C++17 compiler (or `CXX`).

## Java opack 0.2.1

The PR bundles an opack JAR, adapter class, and adapter JAR, with no reproducible
dependency fetch. Its wrapper auto-detected BOMs, stripped them, and decoded
malformed input with replacement characters. Direct baseline probes accepted
`22 ff 22` and a UTF-8 BOM before `{}`. These were transformations of fixture
bytes before the parser saw them. The local wrapper instead decodes only UTF-8,
reports malformed bytes, leaves a BOM in the input, and passes the complete
string to opack's `Json.decodeObject`. A returned `null` is success. Decode
failures, including numeric `NumberFormatException`s, return `1`; file,
linkage, and other runtime failures return `2`.
The library's native JSON mode is used, with no wrapper extensions enabled.

The local build downloads opack commit
`921f3e3314edcd12eb9484435d651974454ce456` (tag `0.2.1`) and JetBrains
annotations **24.1.0**, verifying SHA-256 values in `build.sh`, and compiles
the original Java sources plus the adapter. Outputs go under ignored `.build/`.
The upstream source permits Apache-2.0 or GPL-2.0-or-later with Classpath
exception; source notices and license remain in the pinned download. No
third-party binary is committed. Validation used OpenJDK **21.0.12.1** on Linux
x86_64. Run:

```sh
sh parsers/test_java_opack_0_2_1/build.sh
java -cp parsers/test_java_opack_0_2_1/.build/classes TestJSONParsing test_parsing/y_structure_lonely_null.json
```

The build requires `curl`, `sha256sum`, `tar`, `find`, `sort`, and a JDK (or
`JAVAC`). The registry requires `java` on PATH.

## Validation and remaining work

All three adapters compiled from source or restored package references in
temporary or ignored build directories. The complete regression suite passed:
**33 tests**, including nine focused adapter contract tests, with the isolated
toolchains on PATH. They exercise accepted scalars and empty containers,
invalid syntax, empty input, trailing content, malformed bytes, missing
arguments/files, UTF-8/BOM handling, and opack's distinction between numeric
rejection and an unexpected parser failure. The unmodified baseline probes
reproduced the .NET complete-input defect and opack's lossy decoding before
editing.

A temporary copy of the runner executed all **324** fixtures for each of the
three adapters and Perl JSON::PP, with a five-second limit per invocation.
The four-parser run logged all **1,296** selected parser/fixture outcomes.
After correcting opack's numeric-exception classification, its 324 fixtures
were rerun. Both runs generated full and pruned reports; each selected parser
had 324 executions, with no skips or missing records. Combining the unchanged
three parser results with the corrected opack rerun gives:

| Parser | Expected | `i_` accepted | `i_` rejected | `n_` accepted | Crash |
| --- | ---: | ---: | ---: | ---: | ---: |
| Newtonsoft.Json 13.0.2 | 239 | 21 | 14 | 50 | 0 |
| JSONpp 0.1.1 | 275 | 14 | 21 | 14 | 0 |
| opack 0.2.1 | 280 | 20 | 15 | 4 | 5 |
| Perl JSON::PP 4.16 | 289 | 15 | 20 | 0 | 0 |

Here `i_` acceptance and rejection are both allowed outcomes; `n_` acceptance
is unexpected. No selected parser timed out. Newtonsoft.Json accepts multiple
invalid forms, including an unclosed array and a leading-zero number; JSONpp's
14 unexpected acceptances are number-grammar cases. opack accepts the four
new leading-zero fraction/exponent cases. Its five crashes are
`ArrayIndexOutOfBoundsException`s on truncated input; 22 numeric parse
exceptions that originally appeared as crashes are now correctly recorded as
rejections. These are observed library behaviors or limitations, not claims
about every parser mode or platform. Historical reports remain untouched.
