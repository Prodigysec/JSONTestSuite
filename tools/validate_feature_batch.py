#!/usr/bin/env python3
"""Audit every standard-corpus and feature pair for a roadmap batch in isolated output.

Exit 0 proves audit completeness, not parser conformance. Runtime/skip counts and
feature CI verdict remain explicit in audit.json and must be reviewed separately.
"""
import argparse
from collections import Counter
import contextlib
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import run_features
import run_tests


def audit_standard(rows, names, fixtures):
    expected = {(name, fixture) for name in names for fixture in fixtures}
    seen = set()
    counts = {name:Counter() for name in names}
    for row in rows:
        fields = row.rstrip('\r\n').split('\t')
        if len(fields) != 3:
            raise ValueError('Invalid standard-corpus log row')
        name, status, fixture = fields
        key = name, fixture
        if key not in expected or key in seen or status not in run_tests.STATUS_LABELS:
            raise ValueError('Unexpected, duplicate, or invalid standard-corpus row')
        seen.add(key)
        counts[name][status] += 1
    if seen != expected:
        raise ValueError('Missing standard-corpus rows: '+str(len(expected-seen)))
    return {name:dict(sorted(counts[name].items())) for name in names}


def batch_names(task_id, backlog):
    task = next((task for task in backlog['tasks'] if task['id'] == task_id), None)
    if task is None:
        raise ValueError('Unknown roadmap task: '+task_id)
    if task_id == 'P2-04':
        return sorted(name for name, mode in run_tests.programs.items() if name.startswith('Python stdlib ') or name=='Node.js V8 JSON.parse (strict UTF-8)')
    entries = [parser for parser in backlog['parsers'] if parser['id'] in task['parser_ids']]
    names = []
    for parser in entries:
        modes = parser.get('registry_names', [])
        if not modes and parser.get('disposition') != 'SKIPPED_SETUP_FAILED':
            raise ValueError('Parser has no registered modes or explicit setup-failure disposition: '+parser['title'])
        names.extend(modes)
    if not names:
        raise ValueError('Batch has no executable modes; record setup failures without claiming a survey')
    if len(set(names)) != len(names) or any(name not in run_tests.programs for name in names):
        raise ValueError('Batch registry names are duplicate or unavailable')
    return sorted(names)


def validate_batch(task_id, output, jobs=1):
    backlog = json.loads((ROOT/'docs/roadmap/backlog.json').read_text())
    names = batch_names(task_id, backlog)
    if type(jobs) is not int or jobs < 1:
        raise ValueError('Jobs must be positive')
    run_features.load_manifest(ROOT/'metadata/convenience-features.json')
    output = Path(output).resolve()
    if output.is_relative_to(ROOT/'results'):
        raise ValueError('Batch output cannot replace historical reports')
    output.mkdir(parents=True, exist_ok=False)
    filter_path = output/'filter.json'
    filter_path.write_text(json.dumps(names,indent=2)+'\n')
    registry = {name:copy.deepcopy(run_tests.programs[name]) for name in names}
    features = run_features.run_observations(registry, ROOT/'metadata/convenience-features.json',
                                            output/'features', filter_path, jobs)
    setups = {item['parser']:item for item in features['setup_audits']}
    for name, mode in registry.items():
        mode.pop('setup', None)
        setup = setups.get(name)
        if setup and (setup['status'] != 'complete' or setup['exit_code'] != 0):
            mode['setup'] = [sys.executable,'-c','raise SystemExit(1)']
    with tempfile.TemporaryDirectory(prefix='jsonsuite-batch-copy-') as directory:
        disposable = Path(directory)
        shutil.copy2(ROOT/'run_tests.py', disposable/'run_tests.py')
        shutil.copytree(ROOT/'test_parsing', disposable/'test_parsing')
        (disposable/'results').mkdir()
        spec = importlib.util.spec_from_file_location('disposable_jsonsuite_runner', disposable/'run_tests.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.programs = registry  # Same authored commands; only the runner/corpus/output are disposable.
        with (output/'standard-console.txt').open('w') as console, contextlib.redirect_stdout(console):
            standard_ci_failures = module.run_tests(restrict_to_program=names, jobs=jobs)
        log_path = Path(module.LOG_FILE_PATH)
        shutil.copy2(log_path, output/'standard-logs.txt')
        fixtures = sorted(str(path.relative_to(disposable/'test_parsing')) for path in (disposable/'test_parsing').rglob('*.json'))
        corpus = [{'path':name,'sha256':hashlib.sha256((disposable/'test_parsing'/name).read_bytes()).hexdigest()} for name in fixtures]
        counts = audit_standard(log_path.read_text().splitlines(), names, fixtures)
    observation_rows = [json.loads(line) for line in (output/'features/observations.jsonl').read_text().splitlines()]
    manifest, _ = run_features.load_manifest(ROOT/'metadata/convenience-features.json')
    expected_features = {(name,probe['id']) for name in names for probe in manifest['probes']}
    actual_features = [(row['parser'],row['probe_id']) for row in observation_rows]
    if len(actual_features) != len(expected_features) or set(actual_features) != expected_features:
        raise ValueError('Feature rows are missing or duplicated')
    revision = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty = subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).splitlines()
    source_paths = [ROOT/'run_tests.py', ROOT/'run_features.py', Path(__file__).resolve()]
    for name in names:
        source_paths.extend(Path(part) for part in run_tests.programs[name].get('observation_commands',[])
                            if part.endswith(('.py','.js')) and Path(part).is_file())
        source_paths.extend(Path(part) for part in run_tests.programs[name].get('observation_source_files',[]))
    build_paths={Path(part) for name in names for part in run_tests.programs[name].get('observation_build_artifacts',[])
                 if Path(part).is_file()}
    build_hashes={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(build_paths)}
    source_hashes = {str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sorted(set(source_paths))}
    audit = dict(schema_version=1, task_id=task_id, revision=revision, dirty_worktree=dirty,
                 source_hashes=source_hashes, build_artifact_hashes=build_hashes, selected_parsers=names,
                 standard_planned_pairs=len(names)*len(fixtures), standard_recorded_pairs=sum(sum(c.values()) for c in counts.values()),
                 standard_counts=counts, standard_ci_failures=standard_ci_failures, feature_summary=features,
                 corpus=corpus, registry_commands={name:run_tests.programs[name]['commands'] for name in names},
                 audit_complete=True, audit_verdict=0,
                 verdict_meaning='Completeness only; skips/crashes/timeouts/deviations remain findings, never coverage or conformance proof.')
    (output/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    return audit


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task_id')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--jobs',type=int,default=1)
    args = parser.parse_args(argv)
    try:
        audit = validate_batch(args.task_id,args.output,args.jobs)
    except (OSError,ValueError,TypeError,KeyError) as error:
        parser.error(str(error))
    print('Batch audit complete: %d standard pairs; %d feature pairs; standard CI failures %d; feature CI verdict %d. Audit verdict is completeness only.' % (
        audit['standard_recorded_pairs'],audit['feature_summary']['recorded_pairs'],
        audit['standard_ci_failures'],audit['feature_summary']['ci_verdict']))
    return audit['audit_verdict']


if __name__ == '__main__':
    sys.exit(main())
