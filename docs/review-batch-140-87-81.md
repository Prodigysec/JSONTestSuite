# Build and corpus distribution issues #140, #87, and #81

Reviewed on 2026-10-03 against local parent `0848fc7`. The upstream issues
remain open; local dispositions do not close them.

## Source builds: issue #140

[Issue #140](https://github.com/nst/JSONTestSuite/issues/140) asks for Makefiles
or a build script so at least some checked-in parser sources can be compiled
after cloning. It had no discussion when refreshed; its last upstream update
was 2024-12-05. The local root `Makefile` now builds three C adapters from
checked-in source: jsmn, JSON Checker, and cJSON 1.7.3. `make` or
`make c-parsers` places the executables under ignored `parsers/.build/`.
`CC`, `CPPFLAGS`, `CFLAGS`, `LDFLAGS`, and `LDLIBS` may be passed to make as
usual. This build needs make, a C99 compiler, and the platform C library; cJSON
also links libm. No download or system installation is part of this target.

The source files and their existing license notices are preserved. Tracked
historical binaries and registry commands remain unchanged. The rebuilt
programs are available for direct comparison, but they are not registered as
new adapters yet: their old wrappers need separate contract fixes before that
would be reliable. In smoke checks, checked-in jsmn source accepted
`n_array_extra_comma.json`, and JSON Checker rejected the valid scalar
`y_structure_lonely_null.json`; cJSON 1.7.3 accepted the valid scalar and
rejected the extra comma. The wrappers also have file-error and input-length
handling gaps. These are parser/wrapper behavior and are not fixed by the
compiler target. The Makefile does not claim to build every historical parser
or make the repository binary-free. Other reviewed adapters have their own
version-pinned `build.sh` files and separate toolchain requirements.

## Executable flags: issue #87

[Issue #87](https://github.com/nst/JSONTestSuite/issues/87) reports execute
bits on fixtures and non-executable sources. It has one supporting comment and
was last updated upstream on 2020-06-09. This was already handled locally in
[PR #113's review and integration](review-batch-105-113-126.md#executable-flags):
234 file modes were corrected after a path-by-path audit. A current `git
ls-files -s` audit confirms that none of the tracked parsing or transformation
fixtures has an execute bit. No further mode changes were needed for this
issue; a regression check now guards that condition.

## Corpus-only use: issue #81

[Issue #81](https://github.com/nst/JSONTestSuite/issues/81) asks about a
separate fixture repository for a small Git submodule. It had no discussion
when refreshed; its last upstream update was 2018-04-26. This checkout has
about 166 MB of tracked files under `parsers/`, while the fixture trees occupy
about 1.8 MB in the working tree. Moving the authoritative corpus to a new
repository would change paths and downstream update workflows and require a
separate published repository. That split is not performed here.

Instead, `make corpus-archive` creates an ignored, corpus-only tarball from
the **committed** `HEAD` tree. It contains `LICENSE`, `test_parsing/`, and
`test_transform/` only. It does not include `parsers/`, historical reports,
untracked fixtures, or uncommitted fixture edits. Git supplies exact fixture
bytes and names; `gzip -n` suppresses host and time fields. Rebuilding the
archive at the same commit should produce identical bytes. Consumers who need
a Git working tree can use a partial clone with sparse checkout, selecting
`test_parsing` and `test_transform`; top-level files remain in a cone-mode
sparse checkout. See [corpus-only instructions](corpus-only.md).

Before this batch was committed, an archive of `0848fc7` contained exactly
347 tracked files (346 fixtures and `LICENSE`), with no parser paths and no
byte mismatches against `git show HEAD:<path>`. Its SHA-256 was
`bd42d6f906eca7d18b86bcaf7c9df0f150e65e706d443c79db8e0c49b9c72d6b`.
The output filename and hash change after a commit because the source revision
changes, even when fixture bytes do not. Historical reports and fixture bytes
were not modified.

Validation used Linux x86_64. The host lacked a C toolchain and make, so GCC,
binutils, and make extracted under `/tmp` were used without installing system
packages. `make CC=gcc -j2 c-parsers` built all three programs. Both positive
and negative smoke fixtures were run with five-second limits; the outcomes
above were observed. The corpus archive was inspected member by member and
rebuilt with an identical SHA-256. A local sparse checkout contained all 324
parsing fixtures and 22 transformation examples, with no `parsers/` or
`results/` directory; the remote partial-clone filter was not separately
tested. The full Python suite passed 60 tests, with 19 optional adapter tests
skipped because their independent dependencies were unavailable. The two new
distribution tests exercised the archive and fixture mode guard.
