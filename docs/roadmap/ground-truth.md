# Ground truth: P0-01

Recorded 2026-10-04 after the planning commit `ecd68e2`. The source document
remains at `json_parsers_ranked_by_rfc8259_deviation.pdf`; its SHA-256 and the
complete registry snapshot are in [ground-truth.json](ground-truth.json).
The converted PDF text is temporary at `/tmp/jsonsuite-ranked-parsers.txt`.

The registry contains 123 modes, with 327 parsing and 26 transformation fixtures.
Appendix A's 94-mode count copied the README's initial baseline, not its current
inventory. Its covered parser families all have corresponding registry names,
but registration does not prove availability, the same parser version, or
observation support. The JSONpp/opack grouping is also inaccurate: JSONpp is C++
and opack is Java. Folly appears among PDF candidates but is already registered.
Euneus is an existing registered control rather than a new library to add.
The QJson lead remains ambiguous: the existing Qt adapter uses Qt's
QJsonDocument API, which does not by itself verify a separate QJson library.
Generic Squeak and Crystal leads also overlap registered platform entries and
require backend identity checks before creating duplicate modes.

The PDF's tier counts came from different corpus revisions and package versions.
They are external claims, not locally measured results. Heuristic and M leads
remain hypotheses. The catalog separates these predictions from future local
acceptance and value observations.

The exact baseline command passed:

```text
python3 -B -m unittest discover -s tests -v
Ran 99 tests
OK (skipped=22)
```

These counts differ from the previous 107-test run because optional source-C
classes skip at setup when no compiler is on PATH. The frozen JSON record keeps
the complete output and every skip reason. No test failure was observed.

Host Python 3.12.3, Node 24.21.0, Docker and curl are available. Go, Java,
.NET, Ruby, Lua, cc and make are not on PATH. Extracted cc/make, Java,
.NET and GHDL executables exist under /tmp; their paths are recorded, but this
inventory does not claim that all their dependencies work. Per-batch preflight
must check them before using them. No system packages were installed.

All six scoped JSONSuite images (core, Chromium, Firefox, JSC, V8, Folly) were
inspected successfully. The core image's Python command ran with networking
disabled and reported Python 3.11.2. This verifies the core interpreter, not
universal availability of historical adapters. Each image's exact ID is recorded.

Reproduce/check this baseline:

```sh
python3 -B tools/roadmap_inventory.py --check
python3 -B -m unittest discover -s tests -v
```

The check validates the frozen planning snapshot; later registry additions are
expected and do not redefine the old baseline. Running the tool without
`--check` deliberately refreshes its snapshot. Corpus bytes, historical reports,
and parser behavior were preserved.

Phase 0 summary: added a registry/environment snapshot and documented Appendix A
discrepancies. No library was newly covered or skipped as a candidate. Optional
unit tests skipped for absent dependencies; the main surprise was the PDF's
stale count and candidate overlap with Folly and the registered platform modes.
