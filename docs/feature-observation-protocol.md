# Convenience-feature observation protocol: P2-01

This protocol adds optional observations without changing the parsing adapter
contract: a normal invocation returns 0 for acceptance, 1 for rejection, and
other codes for adapter/runtime failure. Feature probes live in `test_features/`
with `metadata/convenience-features.json`; authoritative `test_parsing/` fixtures
and their expectations remain unchanged. Feature output never replaces historical
logs or reports.

## Manifest and RFC expectation

The version-1 manifest has a `probes` array. Each entry contains a unique `id`,
`category`, relative `path`, exact `bytes_hex`, `sha256`, `rfc8259` expectation,
`why`, and `source`. Sources identify a precise RFC section, the supplied task,
or the Bishop Fox survey. Optional `inspect_keys` lists object names to query;
optional `duplicate_candidates` documents known first/last candidate values.
Hex and hashes are checked against the file; fixtures are always read as bytes.
Paths must resolve inside the probe directory, including symlink resolution.

`rfc8259` separates `syntax` (`valid`, `invalid`, or `invalid-encoding`) from
`parser_outcome` (`accept`, `reject`, or `implementation-dependent`), with
`sections` and `reason`. Extension acceptance is observed, not reclassification.
BOM handling (§8.1), unpaired-surrogate interoperability (§8.2), numeric range
(§6), and resource limits (§9) have explicit implementation-dependent outcomes.
A malformed-UTF-8 probe has invalid interchange encoding under §8.1, even when
an existing corpus `i_` case records closed-ecosystem decoder variation.
Duplicate keys and key ordering are not syntax violations (§4).

The corpus covers comments, alternative quotes, quoteless names/values, commas,
literals/root forms, string extensions, key collisions, serialization, number
representation, and limits, with several probes in each category. Deep nesting
and long strings are finite, sized in the manifest, and use the parser's bounded
execution budget. No standalone grammar oracle rewrites the bytes.

## Optional observer command

A registry entry may add `observation_commands` and `observation_version`.
The runner appends the fixture path as its final argument, as for ordinary
path-based adapters; stdin observers may instead set `observation_use_stdin`.
The observer reads exactly the same input as its parsing mode and emits exactly
one UTF-8 JSON object, followed by LF. It should include `status`,
`parsed_value_type`, `normalized`, `key_observations`, `serialized`,
`capabilities`, and any `detail`. Native parse failure is `status: reject` and
exit 1; an accepted text is `status: accept` and exit 0. Unexpected failures
return a different code or terminate by signal. No native failure is hidden as
JSON rejection. Serialization failure after parsing retains acceptance, with
`serialization_error` and null `serialized`.

The observer may query all root object names, so it does not need the manifest
inside an adapter. `key_observations` records a name, whether it was found, and
the native getter's normalized value. Native duplicate-member traversal is
retained when the library exposes it; otherwise `duplicate_entries` capability
is false. The harness never reparses the source with a different library to
invent the tested parser's value. Optional `getter_serialized` can capture a
library's get/toString divergence separately from whole-value serialization.

The harness produces one record per selected parser/probe pair, containing
`schema_version`, `parser`, `version`, `probe_id`, `status`,
`parsed_value_type`, `normalized`, `key_observations`, `duplicate_key_winner`,
`serialized`, and `capabilities`. It attaches the manifest expectation,
fixture SHA-256, command, exit code, and measured elapsed time. Status is one of
`accept`, `reject`, `crash`, `timeout`, `skipped`. Skips include a machine-readable
reason (`SKIPPED_SETUP_FAILED`, unavailable executable, or unsupported observer)
and explanatory detail. An unavailable library is not counted as covered.
Malformed/multiple records or a status/exit-code mismatch are observer crashes.
Missing fields never imply success or preserved values.

## Neutral normalized representation

Normalization is a tagged observation tree, not a JSON-validity reference or
source of an expected parsed value. Independent observers implement this public
schema. Consensus groups identical semantic observations and reports the counts
and disagreements; no parser, including Python, defines the correct outcome.
Predictions are compared with measured outcomes at the tested versions only.

- Null: `{"type":"null"}`; boolean: `{"type":"boolean","value":false}`.
- Strings: `{"type":"string","units":[116,101,115,116]}`. Units are unsigned
  UTF-16 code units, preserving escaped lone surrogates; supplementary scalars
  use their surrogate pairs. A parser that replaces/truncates characters emits
  its actual result. This representation compares language APIs without silently
  normalizing Unicode, deleting NULs, or merging lookalike names.
- Integers: `{"type":"integer","decimal":"9007199254740993"}`. The decimal
  string is the exact stored integer, not a rounded JSON number in the record.
- Binary64 values: `{"type":"float","format":"binary64","bits":"8000000000000000"}`.
  Bits are eight bytes in big-endian hex, preserving signed zero and nonfinite
  values. A human-readable `display` field may accompany them. Other formats
  identify their width or exact decimal coefficient/exponent. Comparison ignores
  optional display text, not storage type or bits.
- An unconverted native number token uses `{"type":"number-lexeme","text":"012"}`;
  it is not mislabeled as a parsed integer. Opaque native types are explicitly
  unsupported rather than converted through a reference parser.
- Arrays: `{"type":"array","items":[...]}`; objects:
  `{"type":"object","entries":[{"key":[97],"value":...}]}`. Entries retain
  native traversal order and duplicates if exposed. Collapsed maps record only
  surviving entries. Object ordering is observed separately from semantic
  key/value consensus, and keys are never lowercased or Unicode-normalized.

The normalizer has an explicit depth/item/string budget. Truncated subtrees
carry `truncated: true`, original length where known, and a digest where
available; absent pieces are unknown, not empty. A normalizer limit must not
turn a successful parse into rejection. Getter and serialization observations
can remain available when complete normalization is not.

For declared duplicate candidates, the analysis compares the actual getter
observation with the manifest candidates, recording `first`, `last`, `all`,
`other`, `missing`, or `unknown`. It must not derive a winner by assuming that
serialization and lookup use the same policy. Key-collision probes query the
separate source names and record exactly which survived.

## Runner and analysis behavior

`run_features.py` supports exact-name JSON `--filter`, positive `--jobs`, and a
fresh `--output` directory. Selection and manifest validation happen before
output or setup side effects. Default selection is observer-capable modes;
explicitly selected unsupported modes receive skips. Setup is serialized,
fixtures for each parser are sequential, and final records use deterministic
parser/probe ordering. Each invocation uses the registered timeout (default
five seconds). Setup also receives a finite budget. Output collection is
bounded, and stdout/stderr are retained only as diagnostics where appropriate.
No empty filter means all modes, no missing row means success, and no skip counts
as a parse. Interrupted runs are not complete surveys.

The output directory stores `observations.jsonl` and an audited summary containing
planned, recorded, skipped, crashed, and timed-out counts. Creation refuses an
existing output directory and any location inside tracked historical `results/`.
CI verdict 1 covers crashes/timeouts/skips and incomplete protocol observations;
native extension acceptance remains a finding, not a harness failure. A separate
strict-expectation verdict may fail deviations but must keep implementation limits
separate. Analysis prints parser-by-feature observations and marks every document
prediction `confirmed`, `contradicted`, or `untested`, with record/source references.
A clean finite corpus run never proves complete RFC compliance.

P2-04 supplies `tools/validate_feature_batch.py` to build exact filters for a
roadmap batch, run its standard corpus in a disposable copy, run the feature
harness, and audit every expected pair. New batch build scripts pin source,
licenses, runtime/compiler profiles, and dependencies before their adapters run.
Their review notes distinguish native parser crashes from adapter failures and
unavailable builds, and record modes, platforms, fixture revisions, and commands.

Phase 2 design summary: defined exact-byte manifests, optional observations,
neutral typed normalization, duplicate/getter evidence, deterministic bounded
execution, output isolation, and evidence-driven analysis. No probes or new
parser adapters were added in this design task. Nothing was inferred from the
PDF's heuristic or external measured rankings.

P2-03 implementation: `run_features.py` validates the manifest and exact-name
filter before creating a fresh directory, serializes bounded setup, and schedules
parsers concurrently with deterministic records. POSIX pipes/process groups are
the tested platform. Stdout is capped at 2 MiB and stderr diagnostics at 8 KiB;
stdin is written while draining both output streams. Setup has a 120-second
budget. Missing observer/version fields, invalid typed trees, extra JSON lines,
and inconsistent status/exit codes are protocol crashes. CI rejects skips,
crashes, and timeouts; native rejection or extension acceptance remains evidence.
The summary includes setup commands/status and observation/manifest hashes.
Ten controlled regressions cover failure recovery, isolation, raw bytes, bounded
output, descendants, concurrency, and getter-based duplicate decisions.

P2-04 audit verdict clarification: `tools/validate_feature_batch.py` returns 0
when every standard and feature pair is accounted for. Its `audit.json` exposes
standard CI discrepancies and the feature runner's separate CI verdict.
Completeness must never be reported as coverage, conformance, or runtime success.
Review notes explain each discrepancy and identify skipped or crashed modes.
The helper records the actual registry commands, copied corpus hashes, source
hashes, revision and dirty-worktree provenance.
