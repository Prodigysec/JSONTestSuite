# Parser coverage batch: #95, #62, and #40

Reviewed on 2026-10-03 against upstream [#95](https://github.com/nst/JSONTestSuite/issues/95),
[#62](https://github.com/nst/JSONTestSuite/issues/62), and
[#40](https://github.com/nst/JSONTestSuite/issues/40), all still open. #95's
[paper](https://arxiv.org/abs/1902.08318) names simdjson. #62 follows
[PR #61](https://github.com/nst/JSONTestSuite/pull/61), proposed by `gsstark`
at head `b719e998f3dba1cba7ec5df13ef55f43a1422c3b` against base
`def38d06e579db1d13f32a60e60bcd86ce69444b`. The PR closed unmerged;
its discussion identified its unconditional `psycopg2` dependency. It also
connects to whichever default PostgreSQL server is available, decodes fixture
bytes as Python text, and maps most database errors to JSON rejection. The
new adapter requires an explicit DSN, binds raw bytes as `bytea`, and treats
connection and unexpected database errors as adapter failures. #40's existing
`Swift Apple JSONSerialization` binary is Mach-O for macOS; this batch adds a
distinct Linux Foundation mode.

| Registry mode | Source and tested version | Dependencies and invocation | Parser mode |
| --- | --- | --- | --- |
| `C++ simdjson 5.0.1 DOM` | [simdjson](https://github.com/simdjson/simdjson) v5.0.1, commit `8c512a3227ad322bfcb43c57c71fac67a83b5b8e`, Apache-2.0 | `sh parsers/build_simdjson.sh`; C++17 compiler, curl, tar, sha256sum. Runs `parsers/.build/simdjson/test_simdjson FILE`. | DOM parser validates one complete byte buffer. Parser limit errors are rejections; allocation and adapter errors exit 2. |
| `PostgreSQL 16 JSONB UTF8` | [PostgreSQL 16.15](https://www.postgresql.org/docs/16/datatype-json.html) on this host | Python 3 and `psycopg2` 2.9.9, plus an explicitly selected PostgreSQL UTF8 server. `JSONTESTSUITE_POSTGRES_DSN='host=... port=... dbname=... user=...' python3 parsers/test_postgres_jsonb.py FILE`. | `convert_from(bytea, 'UTF8')::jsonb` validates the complete fixture without Python decoding. Only known input/limit SQLSTATEs map to rejection. |
| `Swift Foundation 6.1.3 Linux Docker` | [Swift corelibs Foundation](https://github.com/swiftlang/swift-corelibs-foundation) in official `swift:6.1.3-jammy` Linux x86-64 image, pinned manifest digest `sha256:19792fa7ef68fb0e0ca5763ec3dfd40d6461afca7c081eb689e2e374fa80c0be` | Docker daemon and CLI. `sh parsers/build_swift_foundation_linux.sh` builds the binary into ignored `parsers/.build/`; the registered Docker command mounts the checkout read-only and disables networking. | `JSONSerialization.jsonObject(with:options: [.fragmentsAllowed])` on raw `Data`; file errors exit 2, parser errors exit 1. |

The simdjson script downloads a SHA-256-pinned archive and keeps its source and
`LICENSE` in ignored `parsers/.build/`. Its source was inspected before build.
The simdjson build was tested on Linux x86-64; the source adapter requires a
C++17 toolchain on other supported hosts. The PostgreSQL adapter is portable
where Python 3, psycopg2, and PostgreSQL 16 are available; this survey used
Linux x86-64. The Swift image is explicitly Linux x86-64 and requires Docker.
The local C++ compiler was assembled under `/tmp` from matching Ubuntu GCC
13.3 packages, with no system installation. The tested PostgreSQL binaries,
libpq, and psycopg2 were likewise extracted under `/tmp` from Ubuntu packages;
no PostgreSQL source build was performed. The isolated package preparation was
`apt-get download postgresql-16 postgresql-client-16 libpq5 libllvm17t64 python3-psycopg2`
followed by `dpkg-deb -x PACKAGE.deb /tmp/jsonsuite-postgres-tools/root` for
each downloaded package. The server was initialized with `initdb -D DATA`
using the extracted `usr/share/postgresql/16` directory via `-L`, with
`--encoding=UTF8`,
and started through `pg_ctl` with `-k` pointing to a private socket directory,
`-h ''` disabling TCP, and `jit=off`. `PYTHONPATH` pointed to the extracted
`usr/lib/python3/dist-packages`, and `LD_LIBRARY_PATH` to the extracted
`usr/lib/x86_64-linux-gnu` for this survey. Package builds from other Ubuntu
revisions may differ; the adapter enforces PostgreSQL major version 16. The
private PostgreSQL 16.15 cluster used a UTF8 database, a Unix socket in
`/tmp`, and no TCP listener. The server was stopped after testing. A production
run must point `JSONTESTSUITE_POSTGRES_DSN` at a deliberately provisioned UTF8
test database; the adapter verifies major version 16. Absent drivers, DSN, or
server return 2 on direct invocation, while the runner's preflight records
`SKIPPED_SETUP_FAILED` for each selected fixture. A stopped-server preflight
was verified. The Swift builder pulls the pinned image only if absent; normal
adapter invocations require the image already present and use `--pull never`.
The runner checks for the image before executing Swift fixtures.

Smoke checks covered `null`, `false`, `0`, objects and arrays, trailing text,
incomplete input, malformed UTF-8, BOMs, literal NUL, and missing files. All
three modes use exit 0 for acceptance, 1 for rejection, and 2 for adapter or
environment errors. The 327-file corpus was run in temporary runner copies,
with explicit per-case logging and temporary HTML reports. simdjson recorded
288 expected results, eight implementation-dependent passes, and 31
implementation-dependent failures, with no unexpected outcomes, skips,
crashes, or timeouts. PostgreSQL recorded 285 expected results, 13
implementation-dependent passes, 26 implementation-dependent failures, and
three unexpected rejections, again with no skips, crashes, or timeouts. The
three rejected valid fixtures contain escaped U+0000:
`y_object_escaped_null_in_key.json` has `7B 22 66 6F 6F 5C 75 30 30 30 30 62 61 72 22 3A 20 34 32 7D`;
`y_string_escaped_null_scalar.json` has `22 5C 75 30 30 30 30 22`;
`y_string_null_escape.json` has `5B 22 5C 75 30 30 30 30 22 5D`.
[PostgreSQL's JSONB documentation](https://www.postgresql.org/docs/16/datatype-json.html)
explicitly says JSONB rejects `\u0000` because PostgreSQL `text` cannot
represent it. The fixture expectations remain valid under RFC 8259 §7: these
contain an escaped character, not a literal NUL byte. The result is a JSONB
storage limitation, not a fixture error. RFC 8259 §9 also permits parser limits
on number range and nesting depth.

Swift Foundation recorded 285 expected results, 14 implementation-dependent
passes, 25 implementation-dependent failures, and three unexpected
acceptances, with no skips, crashes, or timeouts. The accepted `n_` fixtures
are `n_array_extra_comma.json` (`5B 22 22 2C 5D`),
`n_array_number_and_comma.json` (`5B 31 2C 5D`), and
`n_object_trailing_comma.json` (`7B 22 69 64 22 3A 30 2C 7D`). In each,
a comma is immediately followed by `]` or `}`; RFC 8259 §4 and §5 require
another member or value after a separator. This is the Linux Foundation
parser's observed extension; no corpus reclassification was made. The
existing macOS binary was not run on this Linux host, so this survey does not
establish a platform comparison at equal Swift versions. After adding the
PostgreSQL version and Swift-image preflights, focused runner cases verified
the expected PostgreSQL result, a missing-configuration skip, and Swift's
trailing-comma result. The existing regression suite ran 69 tests successfully,
with 21 optional-runtime skips.

Tracked historical reports and fixture bytes are unchanged. These surveys
describe the specified versions and modes, not universal parser behavior.
