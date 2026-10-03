# Folly JSON adapter: issue #21

The adapter adds the Folly parser requested in
[upstream issue #21](https://github.com/nst/JSONTestSuite/issues/21). The issue
was refreshed on 2026-10-03: it remains open, has no comments, and lists Folly
alongside the other C++ parsers already represented locally. There is no PR
revision to integrate. This adapter is a local implementation of that request.
Local integration commit: `c33b1b3fa09c809d71486466da1dac095595593d`.

The source is Folly `v2025.09.29.00`, commit
`af67dd1016a6e75785ae8905262d63b441123fb2`. Its source archive SHA-256 is
`079e5add12810f143504e87a8ec2452e0fe9d9ebf9d4b82e384477e4f957aadb`.
The native C++ adapter calls `folly::parseJson` with default
`serialization_opts`, reads the fixture in binary mode, and ignores the
returned value when deciding acceptance. Successful `null`, `false`, and
zero values therefore return 0. Parse and numeric conversion exceptions
return 1; file, runtime, and unexpected adapter errors return 2.

The wrapper preserves Folly's native extensions and representation limits.
Default integer storage is signed 64-bit, `double_fallback` is false, and the
default recursion limit is 100. The `validate_utf8` option is used in
serialization code, so this mode does not claim strict input UTF-8 validation.
It does not strip comments, remove a BOM, replace bytes, or enable extra
parsing options. All input goes to the parser unchanged, except that literal
NUL is rejected before parsing: the native parser's whole-input check permits
a trailing NUL. RFC 8259 §§2 and 7 exclude literal `00` in every position of
a JSON text, while the escaped sequence `5c 75 30 30 30 30` (`\u0000`) is legal
within strings. This guard is explicit in the registry label.

Build on Linux with Docker:

```sh
docker build -f Dockerfile.folly -t jsonsuite-folly:local .
python3 parsers/test_folly.py test_parsing/y_structure_lonely_null.json
```

`Dockerfile.folly` uses the digest-pinned PHP 8.3.27 Bookworm base as a build
environment, GCC 12, CMake, Ninja, Boost, double-conversion, fast_float, fmt,
gflags, glog, libevent, OpenSSL, compression libraries, and libunwind. Folly
is built from its verified source archive using its CMake build, with tests
and benchmarks disabled. Bookworm's fast_float package lacks the API needed
by this Folly release, so the build uses fast_float 8.0.0, exactly as specified
in Folly's dependency manifest, with SHA-256
`f312f2dc34c61e665f4b132c0307d6f70ad9420185fa831911bc24408acf625d`.
Folly and fast_float source trees and license notices remain in `/build`;
Folly's Apache 2.0 license is also copied to `/usr/share/doc/folly/LICENSE`.
Debian dependency packages retain their notices. Transitive APT package
revisions are not snapshot-pinned, so later rebuilds can differ.

The host command requires Python 3, Docker, and the built image. It resolves
fixture paths inside the checkout, mounts the checkout read-only, disables
container networking, and runs `test_folly` with a four-second inner timeout
and a five-second host timeout. The registry checks that the image exists
before running fixtures. The mode is
`C++ Folly v2025.09.29.00 parseJson (native defaults, NUL guard)`.

Validation on Linux x86-64 used host Python 3.12.3, GCC 12.2.0, Boost 1.74,
double-conversion 3.2.1, fmt 9.1.0, and glog 0.6.0. The tested image ID was
`sha256:433ca09463288dfc5c9b96d538fad8027e8d902c972ceb1dfaa9dfdcc212c2df`.
Corpus revision: `24b0dde931f0b35bf2869769815b415841669fa4`.

Smoke checks accepted `null`, `false`, zero, and an escaped-NUL scalar;
rejected an extra comma, trailing `#`, a literal trailing NUL, a UTF-8 BOM,
and 100,000 opening arrays; and returned 2 for a missing file. A malformed
UTF-8 string from the implementation-dependent corpus was accepted. A
temporary diagnostic binary calling `parseJson` directly accepted
`n_multidigit_number_then_00.json` (`31 32 33 00`, `123` followed by NUL),
while the guarded adapter rejected it. Both accepted the legal escaped-NUL
scalar, confirming the guard preserves that case.

The actual registered command was invoked separately on all 327 fixtures,
with the runner's five-second per-fixture limit. Both temporary HTML reports
were generated and the log audit found no missing, extra, or duplicate rows:

| Outcome | Count |
| --- | ---: |
| Expected `y_`/`n_` result | 270 |
| Unexpected acceptance | 18 |
| Unexpected rejection | 0 |
| `i_` acceptance / rejection | 21 / 18 |
| Crash / timeout / skip | 0 / 0 / 0 |

The CI verdict was 1 because of the 18 native unexpected acceptances, which
are retained as observations of this mode:

| Native extension | Count | Representative bytes |
| --- | ---: | --- |
| Leading-zero numbers | 7 | `5b 30 31 32 5d` (`[012]`) |
| Decimal point without fraction digits | 6 | `5b 2d 32 2e 5d` (`[-2.]`) |
| NaN / Infinity / -Infinity | 3 | `5b 4e 61 4e 5d` (`[NaN]`) |
| Unescaped newline / tab in strings | 2 | `5b 22 09 22 5d` (tab between quotes) |

RFC 8259 §6 excludes leading zeros and requires digits after a decimal point;
it also excludes NaN and Infinity spellings. Section 7 requires escaping
control characters U+0000–U+001F, including newline and tab. Folly's
`allow_nan_inf` option does not disable these native parsing spellings; it
controls serialization. No fixture was reclassified to accommodate the
library. Three large integer fixtures were rejected under the default
signed-64-bit limit, recorded as implementation-dependent under §§6 and 9.

Temporary logs, summaries, and reports are at
`/tmp/jsonsuite-folly-run-rt2hg6wv`; this location is ephemeral. The regression
suite passed 94 tests with 21 optional dependency skips, and
`git diff --check` passed. Fixture bytes and tracked historical reports were
preserved. This integration provides the remaining named parser for issue
#21, while broader parser versions, platforms, and modes remain open goals.
