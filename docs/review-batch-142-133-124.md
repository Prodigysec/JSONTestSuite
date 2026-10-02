# Review batch: fastjson2, jsoncgx, and clojure.data.json

Reviewed on 2026-10-02 from local commit `2b5eabd`. The three upstream PRs,
patches, discussions, and reviews were refreshed. All remain open, with no
discussion or reviews. This is an adapted local integration, not an upstream
merge. No parsing fixture or historical report was changed.

| Proposal | Reviewed base | Reviewed head | Local work |
| --- | --- | --- | --- |
| [#142](https://github.com/nst/JSONTestSuite/pull/142), Cooperzzy | `1ef36fa01286573e846ac449e8683f8833c5b26a` | `1b29d1c8c80c424ee70b884e17e92d478845684e` | Source-built adapter against a verified fastjson2 2.0.53 dependency; omit proposed binaries. |
| [#133](https://github.com/nst/JSONTestSuite/pull/133), cigix | `984defc2deaa653cb73cd29f4144a720ec9efe7c` | `b19a6181fda05c19900c071813b4bf641fde8910` | Register explicit JSON and JSONC comment modes with pinned jsoncgx 1.1 source. |
| [#124](https://github.com/nst/JSONTestSuite/pull/124), slipset | `d64aefb55228d9584d3e5b2433f720ea8fd00c82` | `7135428253dbeaeb058d5751bb4c6e527f560d25` | Register data.json 1.0.0 and 2.2.0 with complete-input checks and reproducible dependencies. |

## fastjson2 2.0.53

The PR adds a precompiled class and two JARs. Its Java source uses the platform
default charset when reading bytes. The local wrapper decodes UTF-8 with
malformed-input reporting, never strips a BOM, rejects empty input, and calls
`JSON.parse` without extra reader features. In the [2.0.53
source](https://github.com/alibaba/fastjson2/blob/2.0.53/core/src/main/java/com/alibaba/fastjson2/JSON.java),
that method checks for trailing input. The native mode accepts comments and
other extensions; the registry labels it accordingly. `JSONException` and
decoding errors return `1`; unexpected runtime errors and file/dependency
failures return `2`.

`build.sh` downloads the official
[Maven artifact](https://repo.maven.apache.org/maven2/com/alibaba/fastjson2/fastjson2/2.0.53/fastjson2-2.0.53.jar),
verifies SHA-256
`ad1085113d3c42a45194baab44b5d0e1c4028e7422a4d39a6084133d58dfd877`,
and compiles only the local adapter into ignored `.build/`. The dependency is
Apache-2.0 licensed according to its
[POM](https://repo.maven.apache.org/maven2/com/alibaba/fastjson2/fastjson2/2.0.53/fastjson2-2.0.53.pom).
It is not committed. Tested with OpenJDK **21.0.12.1** on Linux x86_64:

```sh
sh parsers/test_java_fastjson2_2_0_53/build.sh
java -cp parsers/test_java_fastjson2_2_0_53/.build/classes:parsers/test_java_fastjson2_2_0_53/.build/fastjson2-2.0.53.jar TestJSONParsing test_parsing/y_structure_lonely_null.json
```

The build needs `curl`, `sha256sum`, and a JDK (`JAVAC` may override `javac`).
The shown classpath separator is for POSIX systems; the registry uses the host
path separator.

## jsoncgx 1.1

The PR's wrapper catches every exception as a JSON rejection and uses `loadf`,
which opens text using the platform's default encoding. The local wrapper
reads raw bytes, strictly decodes UTF-8, and passes the full string to
`jsoncgx.loads`. Its documented `LexCeption` and `ParseXception` mean rejection;
missing source, I/O failures, and unexpected exceptions return `2`. Empty or
JSON-whitespace-only input is rejected explicitly because jsoncgx 1.1 raises
an internal `IndexError` for it. The two registry entries select
`allow_comments=False` and `True` explicitly. The latter is JSONC mode and
accepts comment-bearing `n_` fixtures as an extension.

`build.sh` downloads the official [jsoncgx 1.1 source
archive](https://files.pythonhosted.org/packages/source/j/jsoncgx/jsoncgx-1.1.tar.gz),
verifies SHA-256
`1b3b736e6f7c4092dd5b8db2547cc47c78e2b577a436ddcff34214dc551f94a6`,
and extracts it into ignored `.build/`. The wrapper imports that pinned copy;
it refuses to use a system installation if the copy is missing. Its source
archive contains the GPL-3.0-or-later `LICENCE`. Tested with Python **3.12.3**
on Linux x86_64:

```sh
sh parsers/test_jsoncgx_1_1/build.sh
python3 parsers/test_jsoncgx_1_1/TestJSONParsing.py off test_parsing/y_structure_lonely_null.json
python3 parsers/test_jsoncgx_1_1/TestJSONParsing.py on test_parsing/y_structure_lonely_null.json
```

The build needs `curl`, `sha256sum`, and `tar`; the adapter needs Python 3.

## clojure.data.json 1.0.0 and 2.2.0

The PR's two wrappers call `read-str` on text from `slurp`. Those versions read
one value and ignore trailing input. The local adapter strictly decodes UTF-8,
then calls the pinned library's internal `-read` on a retained pushback reader
so it can require only RFC 8259 JSON whitespace after the value. A small Java
reader handles these versions' attempt to unread EOF after a number. The
version-specific compiled classes are isolated in `.build/`. Reliance on the
two versions' private `-read` function is intentional and must be rechecked
before changing either dependency. The library's native parsing mode remains
in effect; it accepts some nonstandard array and number syntax.

Syntax exceptions return `1`, including the libraries' generic "No matching
clause" errors on invalid escape characters. Missing files and dependencies,
unexpected errors, and stack overflows return `2`. This distinction matters:
an uncaught error in `clojure.main` otherwise exits `1` and looks like ordinary
rejection to the runner.

`build.sh` verifies SHA-256 values for Clojure **1.10.1**, `spec.alpha`
**0.2.176**, `core.specs.alpha` **0.2.44**, and both data.json JARs from
[Maven Central](https://repo.maven.apache.org/maven2/org/clojure/data.json/).
It compiles the Java reader and AOT-compiles the adapter separately for each
data.json version. The dependencies are never committed. Both data.json source
versions carry an EPL-1.0 notice. Tested with OpenJDK **21.0.12.1** on Linux
x86_64:

```sh
sh parsers/test_clojure_data_json/build.sh
sh parsers/test_clojure_data_json/run.sh 1.0.0 test_parsing/y_structure_lonely_null.json
sh parsers/test_clojure_data_json/run.sh 2.2.0 test_parsing/y_structure_lonely_null.json
```

The build needs `curl`, `sha256sum`, a POSIX shell, `javac` (`JAVAC` may
override it), and `java` (`JAVA` may override it). Runtime needs a POSIX shell
and `java`. AOT compilation reduced direct startup from roughly four seconds
to under three on the tested host, within the runner's five-second limit in
the focused tests.

## Validation and limitations

The full regression suite passed **50 tests** with the isolated Java, .NET,
and Ruby toolchains available. Focused tests cover scalars, empty containers,
empty input, invalid syntax, trailing input, malformed bytes, missing paths,
comment modes, missing pinned jsoncgx source, and Clojure syntax errors versus
stack overflow. Parser invocations in these tests are bounded to five seconds.

A temporary runner copy executed all 324 fixtures for fastjson2 and both
jsoncgx modes. All **972** selected parser/fixture outcomes were logged; full
and pruned reports each accounted for 324 executions per parser, with no skips
or missing records. Both Clojure versions were surveyed against all 324
fixture bytes in a reused JVM using the same adapter parsing function; their
per-fixture runner timeouts were **not** measured. Direct Clojure contract
invocations, including a stack-overflow case, passed within five seconds.

| Parser/mode | Expected | `i_` accepted | `i_` rejected | `n_` accepted | Crash | Timeout |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fastjson2 native | 232 | 16 | 19 | 52 | 5 | 0 |
| jsoncgx comments off | 288 | 20 | 14 | 0 | 1 | 1 |
| jsoncgx comments on | 286 | 20 | 14 | 2 | 1 | 1 |
| data.json 1.0.0 survey | 257 | 21 | 14 | 30 | 2 | not measured |
| data.json 2.2.0 survey | 259 | 21 | 14 | 28 | 2 | not measured |

For `i_` cases, both acceptance and rejection are allowed; crashes and
timeouts are not. Neither runner-tested parser rejected a `y_` fixture.
fastjson2's five crashes are `ArrayIndexOutOfBoundsException`s on malformed
`n_` inputs. jsoncgx crashes on the deeply nested
`i_structure_500_nested_arrays.json` and times out on
`n_structure_open_array_object.json` in both modes. The two comment fixtures
accepted in JSONC mode are `n_object_trailing_comment.json` and
`n_structure_object_with_comment.json`. Both Clojure versions overflow the
stack on `n_structure_100000_opening_arrays.json` and
`n_structure_open_array_object.json`; those errors remain crashes. The
numerous accepted invalid arrays and numbers reflect the libraries' native
modes. These observations do not establish behavior on other platforms or
toolchains, nor complete RFC compliance. Historical reports remain untouched.
