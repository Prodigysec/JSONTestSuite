# Task: Roadmap and implement new JSON parser coverage + "convenience feature" probing

You are working in a fork of nst/JSONTestSuite (Prodigysec/JSONTestSuite). Your job has two parts, done in this order:

1. Read the input document, inspect the repo, and write a roadmap (a sequenced, verifiable task list).
2. Execute the roadmap tasks one at a time, in order, committing after each.

Do not start part 2 until the roadmap is committed.

## Inputs

- The document `json_parsers_ranked_by_rfc8259_deviation.docx` (place it at `docs/input/` or tell me the path). If you cannot read .docx directly, convert it to text first (pandoc or python-docx) and keep the converted copy out of version control.
- The repo itself. Read these before planning: `README.md`, `AGENTS.md`, `docs/project-assessment.md`, the `programs` dict in `run_tests.py`, `run_transform.py`, `metadata/*.json`, the existing `docs/review-batch-*.md` files (they define the house style for documenting a parser batch), `tests/`, and the Dockerfiles.

## How to treat the document

- Appendix A lists parsers already covered. It was written from a pasted directory listing and the fork's README, and the repo moves quickly. Re-derive the true list from the `programs` registry and `parsers/` before deciding anything is missing. Where they disagree, the repo wins; note the discrepancy.
- Each entry carries a basis tag. [Measured] means someone ran a suite. [Documented] means docs or a survey say so. [Heuristic] and source "M" mean the author's inference or memory: these are hypotheses to test, not facts. Never copy a Heuristic claim into results or docs as if it were observed.
- Some rows are families ("pjson, FastJson, sheredom/json.h") or wrapper groups. Split them into one backlog item per installable library or mode. Skip pure wrappers of an engine already in the repo, as the document recommends.
- Before adding a library, verify it exists, note its version, license, build method and platforms. If you cannot obtain or build it, record that and move on. Never invent results.

## Part 1: Produce the roadmap

Write `docs/roadmap/ROADMAP.md` and a machine-readable `docs/roadmap/backlog.json`. Every task needs: ID, title, dependencies, deliverables, acceptance criteria stated as commands that can be run, and a status field (`todo`, `in_progress`, `done`, `blocked`). Keep tasks small enough to finish and verify in one sitting.

Cover at least these phases:

**Phase 0: Ground truth.** Reconcile Appendix A against the registry. Run the existing unit tests and record the baseline (`python3 -B -m unittest discover -s tests -v`). Identify which environments (Docker core, host toolchains) are available.

**Phase 1: Backlog.** Convert the document into `backlog.json`: one entry per parser or mode, with tier, basis tag, language, source URL, version to pin, build steps, and priority. Use the document's section 7 priority order: measured Go failures (goccy/go-json, bytedance/sonic, json-iterator/go, buger/jsonparser, gojay); documented lenient JVM and .NET libraries (json-smart, Fastjson 1.x, Genson, jsoniter Java, Groovy JsonSlurper, Utf8Json, Jayrock.Json, Manatee.Json); scripting gaps (Ruby pure JSON, simdjson gem, python-rapidjson, ijson, json-stream, rxi/json.lua, gjson); dialect contrast cases (JSON5, jsonc-parser, HJSON); hand-rolled C/C++ parsers (gason, microjson, mjson, frozen, tiny-json, lwjson, json.h, pjson); then one strict control per family (yyjson, orjson or msgspec, go-json-experiment/json, Euneus, lunajson or wjson, Boost.JSON or jsoncons).

**Phase 2: Convenience-feature probe corpus and harness.** Design this before adding parsers, because it changes what an adapter must emit (see next section).

**Phase 3: Adapter batches.** Work through the backlog in priority order, 3 to 5 parsers per batch, each batch with a `docs/review-batch-*.md` note and tests. Reduce it if builds are slow.

**Phase 4: Analysis.** Produce a parser-by-feature matrix, compare observed behaviour to the document's predicted tiers, and write down every place the prediction was wrong.

**Phase 5: Reproducibility.** Docker profiles or build scripts for the new adapters, a documented CI verdict mode, and updated README sections.

## The convenience-feature probe corpus

Keep it separate from `test_parsing/`. Do not change expectations of existing y_/n_/i_ fixtures. Put probes in a new directory (for example `test_features/`) with a manifest `metadata/convenience-features.json`. Each probe records: id, category, exact bytes, strict RFC 8259 expectation, why it matters, and the source of the idea (RFC section, Bishop Fox survey, or this task). Preserve bytes exactly: no formatters, encoding conversion or newline normalization.

Categories to cover, with several probes each:

1. **Comments:** `//`, `/* */`, `#`, nested block comments, comments between every pair of tokens, unterminated comment, comment inside a key position.
2. **Alternative quotes:** single-quoted strings and keys, backticks, smart quotes, mixed quote styles.
3. **Quoteless strings and keys:** unquoted keys, unquoted values, identifiers with `$` and `_`, values with spaces.
4. **Commas:** trailing commas in arrays and objects, leading commas, repeated commas, missing commas separated by newlines (HJSON style).
5. **Literals and root forms:** `True/False/None`, `undefined`, `NULL`, implicit root object, multiple top-level values (NDJSON), trailing garbage such as `{"a":1}=`, empty input, BOM, odd whitespace (NBSP, form feed, vertical tab, U+2028).
6. **String extensions:** line continuations, multiline and triple-quoted strings, raw control characters, `\x41`, `\v`, `\0`, unknown escapes like `\q`, lone surrogates, invalid UTF-8.
7. **Key collisions:** duplicate keys (first, last, error, or all kept); character truncation (`"test\ud800"` vs `"test"`, raw 0x0d after `test`, stray quote, stray backslash as in `"te\st"`, NUL); comment truncation, where a comment hides or reveals a second key (for example `{"description":"x","test":2,"extra":/*,"test":1,"extra2":*/ ""}` and the `"a"/*, "test": 2 */` form); case and Unicode-normalization lookalikes.
8. **Serialization quirks:** parse then re-serialize; value from `get` differing from value from `toString`; duplicate keys emitted on output; key ordering; escape normalization (`\/`, `\u002f`); `-0` becoming `0`; `1.0` becoming `1`.
9. **Float and integer representation:** `1.0e4096` (Infinity, null, string, 0, or rounded), a 96-digit integer, 2^53 and 2^53±1, 9223372036854775807 and 9223372036854775808, `-0`, `-0.0`, `1E-400` underflow, 30+ digit decimals, `1` versus `1.0` typing, exponent forms `1E+2` and `1e0`, and hex, octal, `+1`, `.5`, `5.`, `NaN`, `Infinity`, digit separators.
10. **Limits:** deep nesting and very long strings, bounded by the existing timeout.

## Harness design requirements

- Existing adapters only report accept (exit 0) or reject (exit 1), which cannot show *what* a lenient parser did. Define an optional observation mode that emits one JSON Lines record per probe: parser name and version, probe id, status (accept, reject, crash, timeout, skipped), parsed value type, a normalized representation of the parsed value (document the normalization and keep it consensus-based so no single parser defines "correct"), which duplicate-key value won, and the re-serialized text where the library supports it. Follow the pattern of `run_transform.py`, and do not change the existing exit-code contract.
- Reuse the existing metadata approach (`extension-candidates.json`, `streaming-candidates.json`) for labelling probes. Add a runner flag or script to run only probes, with `--filter` and `--jobs` support.
- Observation runs must not overwrite tracked results. CLI runs of `run_tests.py` replace `results/logs.txt` and the HTML reports, so write probe output to a new directory and use a disposable copy when running the standard suite.
- Add unit tests for the new runner code using temporary fixtures and controlled adapters, matching the style in `tests/`.

## Adapter requirements (every new parser)

- Add a small adapter under `parsers/` and register it in `run_tests.py`. Consume the entire input. Distinguish `null`, `false` and `0` from failure. Exit 0 on accept, 1 on reject, and let genuine crashes surface.
- Test acceptance, rejection, scalar roots, trailing garbage and malformed bytes before trusting the adapter.
- Pin and record the library version, source, license, dependencies, build steps, platforms and parser mode. Register strict and lenient modes as separate entries when a library has them (json-smart `MODE_RFC4627` versus `MODE_PERMISSIVE`, kotlinx.serialization `isLenient`, Groovy `JsonSlurper` LAX). Test the default mode and every documented strict mode.
- Capture the observation-mode output for each parser as well as the accept/reject results.
- If the library cannot be built or run in this environment, record `SKIPPED_SETUP_FAILED` with the reason in the batch note. Do not mark it as covered.

## Execution rules (Part 2)

- Work tasks strictly in roadmap order and one at a time. A task is `done` only when its acceptance commands pass and you have shown their output.
- After each task: update the status in `ROADMAP.md` and `backlog.json`, run `python3 -B -m unittest discover -s tests -v`, and commit with a message in the repo's style (for example "Add goccy/go-json and sonic adapters").
- Never edit existing fixture bytes or existing expectations without a written review note explaining the RFC section and the evidence.
- Keep results honest: separate observed behaviour from the document's predictions. In the analysis, mark each prediction as confirmed, contradicted, or untested. If a result contradicts the document, report it plainly.
- Stop and report instead of guessing when: a library's license forbids redistribution, a build needs network access you do not have, results look implausible (for example every parser agreeing on a probe designed to split them), or a roadmap task turns out to be wrong. Propose a roadmap amendment, record it in the roadmap, then continue.
- At the end of each phase, write a short summary: what was added, what was skipped and why, and what surprised you.
