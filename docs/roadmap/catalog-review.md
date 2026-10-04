# Split candidate catalog: P1-01

The PDF is represented as 405 named parser/mode leads. Section 7's priority
order is retained before the long tail. Families such as pjson, FastJson, and
sheredom/json.h, and language-specific JSON5 implementations, have separate
entries. Platforms, aliases, and serializer-only names remain discovery leads;
they are not claimed as installable parsers. Sources M and heuristic tags are
hypotheses. The generic sources for unresolved names are discovery listings;
null source/version/license fields mean verification is pending.

orjson, lunajson, and Boost.JSON are the selected strict-control families;
msgspec, wjson, and jsoncons remain explicit alternatives in discovery rather
than implied coverage. Existing Euneus is reused if its toolchain and observation
mode can be validated. Folly is existing coverage, not a duplicate addition.
QJson, Crystal, and Squeak require backend identity checks against existing modes.

The document recommends excluding pure simdjson/yyjson bindings and Deno/Bun/
standalone SpiderMonkey. Exclusion dispositions retain their external prediction
as untested and do not count as new parser coverage. The Ruby simdjson gem is
retained because the document specifically reports wrapper-level differences.
Ports and independent readers remain candidates. Broader aliases and backend
wrappers must be resolved before integration, with a recorded amendment if an
additional independent adapter needs a task.

The first three Go sources were verified through their official release API,
tag object, commit archive, go.mod, configuration source, and license. Source
archives and inspected files are temporary under `/tmp/jsonsuite-roadmap-go-sources`.
The exact commits and archive SHA-256 values are recorded in backlog.json.

| Library | Pin | License | Minimum module Go version |
| --- | --- | --- | --- |
| goccy/go-json | v0.11.2 | MIT | 1.23 |
| bytedance/sonic | v1.15.4 | Apache-2.0 | 1.18 |
| json-iterator/go | v1.1.12 | MIT | 1.12 |

These are verified sources, not built or measured adapters. Sonic documents
AMD64/ARM64 and Linux/macOS/Windows with Go 1.18–1.27 (ARM64 needs Go 1.20+),
and excludes Go 1.24.0 without a workaround. The first build must choose and
pin a compatible toolchain, retain transitive go.sum hashes and license notices,
and test default and validation configurations. json-iterator's default and
standard-compatible APIs are different configuration names, not proof of a
strict validator. Sonic's ConfigStd enables ValidateString; actual byte handling
must be observed rather than inferred from that name.

Roadmap validation checks unique IDs, valid statuses and basis tags, predecessor
dependencies, task order, verification for done tasks, and source evidence for
verified libraries. Tests reject an early done claim, a forward dependency,
unknown status, and a measured tag incorrectly substituted for local evidence.

Acceptance commands:

```sh
python3 -B tools/check_roadmap.py
python3 -B -m unittest discover -s tests -v
```

Phase 1 summary: split the document, recorded source/exclusion distinctions,
and pinned the first three Go sources. No new parser result was claimed. Other
versions/licenses remain pending ordered source verification, and the stale
QJson classification was amended before integration.
