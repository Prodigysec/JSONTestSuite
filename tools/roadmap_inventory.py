#!/usr/bin/env python3
"""Record/check the fixed planning baseline without claiming parser availability."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import run_tests
from inventory_parser_tools import executable, resolve
DESTINATION = ROOT / 'docs/roadmap/ground-truth.json'
IMAGES = ['jsonsuite-' + name + ':local' for name in
          ('core', 'chromium', 'firefox', 'jsc', 'v8', 'folly')]


def command(arguments, timeout=20):
    try:
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=timeout)
        return {'command': arguments, 'exit_code': result.returncode,
                'stdout': result.stdout.strip(), 'stderr': result.stderr.strip()}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'command': arguments, 'error': str(error)}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect():
    modes = []
    for name, entry in sorted(run_tests.programs.items()):
        modes.append({'name': name, 'source_url': entry.get('url', ''),
                      'commands': entry['commands'], 'setup': entry.get('setup'),
                      'resolved_first_executable': resolve(executable(entry['commands'])),
                      'resolved_setup_executable': resolve(executable(entry.get('setup'))),
                      'note': 'Resolution alone does not prove library/image/platform availability.'})
    baseline = command([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'], 120)
    report = baseline.get('stderr', '')
    count = re.search(r'Ran (\d+) tests', report)
    skipped = re.search(r'OK \(skipped=(\d+)\)', report)
    baseline.update(tests_run=int(count[1]) if count else None,
                    skipped=int(skipped[1]) if skipped else 0)
    snapshot = {'schema_version': 1, 'observed_revision': command(['git', 'rev-parse', 'HEAD'])['stdout'],
                'date': '2026-10-04', 'platform': platform.platform(),
                'python_version': platform.python_version(), 'input_pdf': {
                    'path': 'json_parsers_ranked_by_rfc8259_deviation.pdf',
                    'sha256': digest(ROOT / 'json_parsers_ranked_by_rfc8259_deviation.pdf')},
                'registry_count': len(modes), 'registry': modes,
                'parser_top_level_paths': sorted(p.name for p in (ROOT / 'parsers').iterdir()),
                'corpus_counts': {name: len(list((ROOT / name).rglob('*.json')))
                                  for name in ('test_parsing', 'test_transform')},
                'host_tools': {name: shutil.which(name) for name in
                               ('docker', 'go', 'java', 'dotnet', 'ruby', 'node', 'lua', 'cc', 'make', 'curl')},
                'images': [command(['docker', 'image', 'inspect', '--format', '{{.Id}}', image]) for image in IMAGES],
                'core_python': command(['docker', 'run', '--rm', '--network', 'none', '--pull', 'never',
                                        'jsonsuite-core:local', 'python3', '--version']),
                'isolated_tools': {name: str(path) if path.is_file() else None for name, path in {
                    'cc': Path('/tmp/jsonsuite-c-adapter-tools/bin/cc'),
                    'make': Path('/tmp/jsonsuite-c-adapter-tools/bin/make'),
                    'java': Path('/tmp/jsonsuite-parser-tools/runtime/usr/lib/jvm/java-21-openjdk-amd64/bin/java'),
                    'dotnet': Path('/tmp/jsonsuite-parser-tools/runtime/usr/lib/dotnet/dotnet'),
                    'ghdl': Path('/tmp/jsonsuite-ghdl-tools/root/usr/bin/ghdl')}.items()},
                'baseline_tests': baseline,
                'appendix_discrepancies': [
                    {'claim': '94 registered configurations', 'actual': len(modes),
                     'reason': 'PDF interpreted the README initial-assessment count as current.'},
                    {'claim': 'Folly candidate', 'actual': 'Folly v2025.09.29.00 already registered'},
                    {'claim': 'opack under C/C++', 'actual': 'Java opack 0.2.1; JSONpp is C++'},
                    {'claim': 'Euneus addition/control', 'actual': 'Already registered; observation support still pending'},
                    {'claim': 'QJson candidate and Appendix A QJson',
                     'actual': 'Existing Qt JSON uses QJsonDocument; independent QJson identity unresolved'}]}
    return snapshot


def check(snapshot):
    assert snapshot['registry_count'] == len(snapshot['registry'])
    assert len({mode['name'] for mode in snapshot['registry']}) == snapshot['registry_count']
    assert snapshot['baseline_tests']['exit_code'] == 0
    assert snapshot['baseline_tests']['tests_run'] is not None
    assert snapshot['input_pdf']['sha256'] == digest(ROOT / snapshot['input_pdf']['path'])
    assert snapshot['corpus_counts'] == {'test_parsing': 327, 'test_transform': 26}
    assert all(image.get('exit_code') == 0 for image in snapshot['images'])
    print('Ground truth: %s registry modes; %s parsing / %s transform fixtures; baseline %s tests, %s skips; six images inspected.' %
          (snapshot['registry_count'], snapshot['corpus_counts']['test_parsing'], snapshot['corpus_counts']['test_transform'],
           snapshot['baseline_tests']['tests_run'], snapshot['baseline_tests']['skipped']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='check the frozen recorded baseline')
    args = parser.parse_args()
    snapshot = json.loads(DESTINATION.read_text()) if args.check else collect()
    check(snapshot)
    if not args.check:
        DESTINATION.write_text(json.dumps(snapshot, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
