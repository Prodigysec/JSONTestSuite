# Working on JSONTestSuite

## Purpose and scope

This fork of `nst/JSONTestSuite` aims to broaden JSON parser coverage, resolve
upstream issues, and integrate reviewed upstream contributions. Work toward
reproducible testing across parser versions, platforms, and modes; do not claim
that the current corpus covers every parser or proves complete RFC compliance.

Read `README.md`, `docs/project-assessment.md`, and the relevant parts of
`run_tests.py` before changing behavior. The assessment records the initial
baseline and review queue, not a permanently current inventory.

## Repository map

- `test_parsing/`: authoritative acceptance/rejection corpus for the runner.
- `test_transform/`: examples of value/serialization differences; the current
  runner does not execute these as transformation tests.
- `parsers/`: adapters, vendored libraries, build projects, and historical binaries.
  Nested vendor tests are not automatically part of the root corpus.
- `run_tests.py`: parser registry, subprocess execution, logging, and HTML reports.
- `results/`: tracked historical reports and assets; normal CLI runs overwrite
  `logs.txt`, `parsing.html`, and `parsing_pruned.html` here.
- `article/parsing_json.md`: source of the original article.

## Preserve test bytes and meaning

- Treat fixtures as byte sequences. Some deliberately contain invalid UTF-8,
  literal NULs, unusual whitespace, or incomplete input. Do not format, normalize,
  transcode, or add final newlines across the corpus.
- Use descriptive `y_`, `n_`, or `i_` filenames for new parsing fixtures. These
  mean expected acceptance, expected rejection, and implementation-dependent
  acceptance/rejection respectively. Crashes and timeouts are never successful
  outcomes for `i_` cases.
- Justify new expectations or reclassifications with an exact RFC 8259 section
  and a byte-level example. Distinguish syntax, permitted implementation limits,
  Unicode interoperability, extension modes, and preservation of parsed values.
- Do not decide validity by majority vote among parsers or by Python's `json`
  module alone. Check standards and parser configuration.
- Check existing filenames and bytes for overlapping coverage. Before deleting
  or renaming duplicates, consider consumers that use fixture names and historic
  reports; document any compatibility impact.

## Parser adapter contract

- Adapters ordinarily receive a fixture path as their final argument. Registry
  entries with `use_stdin: True` receive its raw bytes on standard input instead.
- Return `0` for acceptance and `1` for rejection. Other return codes, including
  signal termination, are classified as `CRASH` by the existing runner. Do not
  disguise missing dependencies or adapter failures as valid JSON rejection.
- Validate one complete JSON text, including trailing input. Valid scalar values
  such as `null`, `false`, and `0` must not be rejected because they are falsey.
- Document strict/extension/streaming modes explicitly. Avoid input preprocessing
  that changes what the parser is being tested on.
- Add the adapter to `programs` in `run_tests.py`. Record its source, actual tested
  version, dependencies, build command, supported platforms, and invocation.
  Prefer reproducible source builds to new opaque binaries; preserve third-party
  license notices.
- Keep version labels consistent with the installed dependency. Historical
  registry labels are not runtime version detection.

## Upstream issue and PR workflow

1. Refresh the upstream item, discussion, diff, base, and head revision. Check
   whether the local code already addresses it; an open issue is not proof of a
   remaining defect. Record source links and reviewed revisions.
2. Reproduce a reported defect, or identify the missing coverage, before editing.
   For standards disputes, record the relevant specification and reasoning.
3. Review proposed changes for correct fixture bytes, adapter behavior, build
   reproducibility, dependency versions, licensing, and overlap with other work.
   Treat PR code and build scripts as review material before executing them.
4. Integrate coherent changes with attribution to the original author and PR.
   Preserve authorship when cherry-picking; document substantive adaptations.
   Resolve conflicts based on intended behavior, not by blindly choosing a side.
5. Validate the affected behavior and record what ran, what was unavailable,
   and any remaining limitations. Update the assessment or a subsequent tracking
   document with dispositions and local commits when available.

## Validation and reporting

- Check `git status --short` first and preserve unrelated work. Keep fixture,
  runner, adapter, documentation, and generated-report changes understandable.
- For documentation edits, verify commands, paths, links, and claims against the
  actual checkout. Use `git diff --check` before finishing.
- Use a temporary copy for runner experiments when refreshed reports are not
  part of the change. Keep scratch filters and build output out of tracked files.
- For runner changes, add focused regression coverage for the changed behavior
  (for example rejection, first-case timeout, missing executable, or filtering),
  using controlled adapters where practical. Then run a known available parser
  against the corpus. Avoid requiring every historical toolchain for a small fix.
- For adapters, check acceptance, rejection, scalar input, trailing garbage,
  malformed bytes, and relevant implementation-dependent cases. Exercise stdin
  handling when used. Bound execution time for pathological fixtures.
- The existing runner logs discrepancies and `i_` outcomes, not every execution.
  Missing log rows and a zero runner exit status do not prove that all tests ran
  or passed. Inspect executed commands, skips, and report behavior.
- Do not silently regenerate historical reports as part of unrelated work. When
  publishing fresh results, record OS, architecture, runtime/parser versions,
  modes, corpus revision, and skipped/unavailable adapters.
- State the concrete change, validation evidence, limitations, and remaining
  work. Distinguish reviewed, integrated, tested, and pending upstream items.
