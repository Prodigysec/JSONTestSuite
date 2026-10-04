#!/usr/bin/env python3
"""Run isolated, bounded native-value observations; see docs/feature-observation-protocol.md."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time

from tools.check_feature_manifest import load_manifest

ROOT = Path(__file__).resolve().parent
MAX_OUTPUT = 2 * 1024 * 1024
MAX_STDERR = 8192
SETUP_TIMEOUT = 120


def terminate(process):
    try:
        if os.name == 'posix':
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except ProcessLookupError:
        pass


def bounded_process(command, timeout, raw_stdin=None, cwd=None, output_limit=MAX_OUTPUT):
    """Drain pipes incrementally, including stdin; cap memory and the whole process group."""
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Timeout must be finite and positive')
    start = time.monotonic()
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE if raw_stdin is not None else subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd,
                                   start_new_session=os.name == 'posix')
    except OSError as error:
        return dict(status='skipped', reason='SKIPPED_UNAVAILABLE', detail=str(error),
                    exit_code=None, elapsed_seconds=time.monotonic()-start)
    buffers = {'stdout': bytearray(), 'stderr': bytearray()}
    position = 0
    failure = None
    with selectors.DefaultSelector() as selector:
        for name in buffers:
            stream = getattr(process, name)
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, name)
        if raw_stdin is not None:
            os.set_blocking(process.stdin.fileno(), False)
            selector.register(process.stdin, selectors.EVENT_WRITE, 'stdin')
        try:
            while selector.get_map():
                remaining = timeout - (time.monotonic()-start)
                if remaining <= 0:
                    failure = 'timeout'
                    break
                for key, _ in selector.select(min(remaining, .05)):
                    stream, name = key.fileobj, key.data
                    if name == 'stdin':
                        try:
                            count = os.write(stream.fileno(), raw_stdin[position:position+65536]) if position < len(raw_stdin) else 0
                        except BrokenPipeError:
                            count = 0
                        position += count
                        if not count or position == len(raw_stdin):
                            selector.unregister(stream)
                            stream.close()
                        continue
                    chunk = os.read(stream.fileno(), 65536)
                    if not chunk:
                        selector.unregister(stream)
                        stream.close()
                        continue
                    cap = output_limit if name == 'stdout' else MAX_STDERR
                    previous_length = len(buffers[name])
                    buffers[name].extend(chunk[:max(0, cap-previous_length)])
                    if name == 'stdout' and previous_length + len(chunk) > cap:
                        failure = 'output_limit'
                        break
                if failure:
                    break
            if not failure:
                try:
                    process.wait(timeout=max(.001, timeout-(time.monotonic()-start)))
                except subprocess.TimeoutExpired:
                    failure = 'timeout'
        finally:
            terminate(process)  # Also stop descendants retaining pipe descriptors after parent exit.
            process.wait()
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
    return dict(status=failure or 'complete', stdout=bytes(buffers['stdout']),
                stderr=bytes(buffers['stderr']).decode('utf-8', 'replace'), exit_code=process.returncode,
                elapsed_seconds=time.monotonic()-start)


def units(text):
    raw = text.encode('utf-16-be', 'surrogatepass')
    return [int.from_bytes(raw[i:i+2], 'big') for i in range(0, len(raw), 2)]


def validate_tree(tree, depth=0):
    if depth > 128 or not isinstance(tree, dict):
        raise ValueError('Invalid or excessively deep normalized tree')
    kind = tree.get('type')
    if tree.get('truncated') is True:
        if kind not in {'array', 'object', 'string', 'integer', 'unsupported'}:
            raise ValueError('Invalid truncated type')
        return
    if kind == 'null':
        return
    if kind == 'boolean' and isinstance(tree.get('value'), bool):
        return
    if kind == 'integer':
        import re
        if isinstance(tree.get('decimal'), str) and re.fullmatch(r'-?(0|[1-9][0-9]*)', tree['decimal']):
            return
    if kind == 'float' and tree.get('format') == 'binary64':
        import re
        if isinstance(tree.get('bits'), str) and re.fullmatch('[0-9a-f]{16}', tree['bits']):
            return
    if kind == 'number-lexeme' and isinstance(tree.get('text'), str):
        return
    if kind == 'string' and isinstance(tree.get('units'), list):
        if all(type(unit) is int and 0 <= unit <= 65535 for unit in tree['units']):
            return
    if kind == 'array' and isinstance(tree.get('items'), list):
        for child in tree['items']:
            validate_tree(child, depth+1)
        return
    if kind == 'object' and isinstance(tree.get('entries'), list):
        for entry in tree['entries']:
            validate_tree(dict(type='string', units=entry['key']), depth+1)
            validate_tree(entry['value'], depth+1)
        return
    if kind == 'unsupported' and isinstance(tree.get('native_type'), str):
        return
    raise ValueError('Invalid normalized type/value: ' + str(kind))


def decode_observation(raw, exit_code):
    if not raw.endswith(b'\n') or len(raw.splitlines()) != 1:
        raise ValueError('Expected exactly one JSON object followed by LF')
    def invalid_constant(value):
        raise ValueError('Nonfinite observation JSON token: '+value)
    data = json.loads(raw.decode('utf-8'), parse_constant=invalid_constant)
    if not isinstance(data, dict) or data.get('status') not in {'accept', 'reject'}:
        raise ValueError('Expected an accept/reject observation object')
    if exit_code != (0 if data['status'] == 'accept' else 1):
        raise ValueError('Observation status and exit code disagree')
    for field in ('parsed_value_type', 'normalized', 'key_observations', 'serialized', 'capabilities'):
        if field not in data:
            raise ValueError('Missing observer field: '+field)
    if not isinstance(data['key_observations'], list) or not isinstance(data['capabilities'], dict):
        raise ValueError('Invalid key observations/capabilities')
    if any(not isinstance(value, bool) for value in data['capabilities'].values()):
        raise ValueError('Capabilities must be boolean')
    if data['serialized'] is not None and not isinstance(data['serialized'], str):
        raise ValueError('Serialized observation must be text or null')
    if data.get('serialized_invalid_utf8'):
        if data['serialized_invalid_utf8'] is not True or not isinstance(data.get('serialized_bytes_hex'), str):
            raise ValueError('Invalid UTF-8 serialization requires exact native bytes')
        native_bytes = bytes.fromhex(data['serialized_bytes_hex'])
        try:
            native_bytes.decode('utf-8', 'strict')
        except UnicodeError:
            pass
        else:
            raise ValueError('Invalid-UTF-8 serialization flag contradicts its bytes')
    if data['status'] == 'accept':
        if not isinstance(data['parsed_value_type'], str):
            raise ValueError('Accepted observations require native type')
        validate_tree(data['normalized'])
        for item in data['key_observations']:
            validate_tree(dict(type='string', units=item['key']))
            if not isinstance(item.get('found'), bool):
                raise ValueError('Lookup observation requires found boolean')
            if item['found']:
                validate_tree(item['value'])
    return data


def duplicate_winners(probe, record):
    winners = []
    for candidate in probe.get('duplicate_candidates', []):
        matches = [item for item in record['key_observations'] if item['key'] == units(candidate['key'])]
        winner = 'unknown'
        if record['status'] == 'accept':
            if not matches and record['capabilities'].get('lookup_all_keys'):
                winner = 'missing'
            elif len(matches) > 1:
                winner = 'all'
            elif matches:
                item = matches[0]
                winner = 'missing' if not item['found'] else 'other'
                if item['found']:
                    value = item['value']
                    for label in ('first', 'last'):
                        expected = candidate[label]
                        # Current candidates are exact small integers; never reparse source JSON here.
                        if type(expected) is int:
                            import struct
                            if value == {'type':'integer', 'decimal':str(expected)} or (
                                value.get('type') == 'number-lexeme' and value.get('text') == str(expected)) or (
                                value.get('type') == 'float' and value.get('format') == 'binary64' and
                                value.get('bits') == struct.pack('>d', float(expected)).hex()):
                                winner = label
        winners.append(dict(key=units(candidate['key']), winner=winner))
    return winners


def select_names(registry, filter_path=None):
    if filter_path is None:
        names = [name for name, mode in registry.items() if mode.get('observation_commands')]
    else:
        names = json.loads(Path(filter_path).read_text())
        if not isinstance(names, list) or not names or any(not isinstance(name, str) for name in names):
            raise ValueError('Filter must be a nonempty JSON array of exact parser names')
        if len(set(names)) != len(names) or any(name not in registry for name in names):
            raise ValueError('Filter has duplicate or unknown parser names')
    if not names:
        raise ValueError('No observer modes selected')
    return sorted(names)


def observe_parser(name, mode, probes, probe_root, setup_failure=None):
    records = []
    for probe in probes:
        record = dict(schema_version=1, parser=name, version=mode.get('observation_version'),
                      probe_id=probe['id'], category=probe['category'], rfc8259=probe['rfc8259'],
                      fixture_sha256=probe['sha256'], status='skipped', parsed_value_type=None,
                      normalized=None, key_observations=[], duplicate_key_winner=[], serialized=None,
                      capabilities={}, command=None, exit_code=None, elapsed_seconds=0)
        if setup_failure:
            record.update(setup_failure)
        elif not mode.get('observation_commands'):
            record.update(reason='SKIPPED_UNSUPPORTED_OBSERVER', detail='Registry mode has no observation command')
        else:
            path = probe_root / probe['path']
            stdin = mode.get('observation_use_stdin', False)
            command = list(mode['observation_commands']) + ([] if stdin else [str(path)])
            result = bounded_process(command, float(mode.get('timeout', 5)), path.read_bytes() if stdin else None)
            record.update(command=command, exit_code=result['exit_code'], elapsed_seconds=result['elapsed_seconds'])
            if result['status'] == 'skipped':
                record.update(status='skipped', reason=result['reason'], detail=result['detail'])
            elif result['status'] == 'timeout':
                record.update(status='timeout', detail='Invocation exceeded its time budget')
            elif result['status'] == 'output_limit':
                record.update(status='crash', reason='OBSERVER_OUTPUT_LIMIT', detail='Observer stdout exceeded the byte budget')
            elif result['exit_code'] not in (0, 1):
                record.update(status='crash', detail=result['stderr'])
            else:
                try:
                    data = decode_observation(result['stdout'], result['exit_code'])
                    # Only protocol fields come from the observer; harness identity/provenance cannot be spoofed.
                    for field in ('status', 'parsed_value_type', 'normalized', 'key_observations', 'serialized',
                                  'capabilities', 'detail', 'serialization_error', 'getter_serialized', 'version',
                                  'serialized_invalid_utf8', 'serialized_bytes_hex'):
                        if field in data:
                            record[field] = data[field]
                    if not isinstance(record['version'], str) or not record['version']:
                        raise ValueError('Runtime/library version is required')
                except (KeyError, TypeError, UnicodeError, ValueError, RecursionError) as error:
                    record.update(status='crash', reason='OBSERVER_PROTOCOL_ERROR', detail=str(error))
            record['duplicate_key_winner'] = duplicate_winners(probe, record)
        records.append(record)
    return records


def run_observations(registry, manifest_path, output, filter_path=None, jobs=1, probe_root=None):
    if type(jobs) is not int or jobs < 1:
        raise ValueError('Jobs must be a positive integer')
    manifest, probe_root = load_manifest(manifest_path, probe_root)
    names = select_names(registry, filter_path)
    for name in names:
        mode = registry[name]
        timeout = float(mode.get('timeout', 5))
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('Timeout must be finite and positive: '+name)
        for field in ('observation_commands', 'setup'):
            command = mode.get(field)
            if command is not None and (not isinstance(command, list) or not command or
                    any(not isinstance(part, str) or not part for part in command)):
                raise ValueError('Invalid '+field+' command: '+name)
    output = Path(output).resolve()
    if output.is_relative_to(ROOT / 'results'):
        raise ValueError('Feature output cannot be inside historical results/')
    output.mkdir(parents=True, exist_ok=False)
    probes = sorted(manifest['probes'], key=lambda probe: probe['id'])
    setup_failures = {}
    setup_audits = []
    for name in names:
        mode = registry[name]
        if mode.get('observation_commands') and mode.get('setup'):
            result = bounded_process(mode['setup'], SETUP_TIMEOUT, cwd=ROOT)
            setup_audits.append(dict(parser=name, command=mode['setup'],
                **{key:value for key,value in result.items() if key != 'stdout'}))
            if result['status'] != 'complete' or result['exit_code'] != 0:
                setup_failures[name] = dict(reason='SKIPPED_SETUP_FAILED',
                    detail='%s: %s' % (result['status'], result.get('detail', result.get('stderr', ''))))
    with ThreadPoolExecutor(max_workers=min(jobs, len(names))) as executor:
        futures = {name: executor.submit(observe_parser, name, registry[name], probes, probe_root,
                                        setup_failures.get(name)) for name in names}
        records = [record for name in names for record in futures[name].result()]
    target = output / 'observations.jsonl'
    with target.open('w', encoding='utf-8') as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=True, allow_nan=False, sort_keys=True)+'\n')
    counts = Counter(record['status'] for record in records)
    summary = dict(schema_version=1, selected_parsers=names, manifest_sha256=hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest(),
                   planned_pairs=len(names)*len(probes), recorded_pairs=len(records), counts=dict(sorted(counts.items())),
                   complete=len(records) == len(names)*len(probes),
                   observations_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                   environment=dict(os=sys.platform, python=sys.version, architecture=os.uname().machine))
    summary['setup_audits'] = setup_audits
    summary['ci_verdict'] = int(not summary['complete'] or any(counts[status] for status in ('crash', 'timeout', 'skipped')))
    (output / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT/'metadata/convenience-features.json')
    parser.add_argument('--filter', type=Path, help='JSON array of exact registry mode names')
    parser.add_argument('--jobs', type=int, default=1)
    parser.add_argument('--output', type=Path, required=True, help='Fresh output directory outside results/')
    args = parser.parse_args(argv)
    from run_tests import programs
    try:
        summary = run_observations(programs, args.manifest, args.output, args.filter, args.jobs)
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.error(str(error))
    print('Feature audit: %(recorded_pairs)d/%(planned_pairs)d pairs; %(counts)s; CI verdict %(ci_verdict)d.' % summary)
    return summary['ci_verdict']


if __name__ == '__main__':
    sys.exit(main())
