#!/usr/bin/env python3
"""Verify probe metadata and exact bytes without using a parser as a grammar oracle."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {'comments', 'quotes', 'quoteless', 'commas', 'roots', 'strings',
              'keys', 'serialization', 'numbers', 'limits'}


def load_manifest(path, probe_root=None):
    path = Path(path)
    data = json.loads(path.read_text())
    if data.get('schema_version') != 1 or not isinstance(data.get('probes'), list) or not data['probes']:
        raise ValueError('Expected a nonempty version-1 probe manifest')
    if probe_root is None:
        probe_root = path.parent.parent / data['probe_root']
    probe_root = Path(probe_root).resolve()
    ids, paths = set(), set()
    for probe in data['probes']:
        for key in ('id', 'category', 'path', 'bytes_hex', 'sha256', 'byte_length', 'rfc8259', 'why', 'source'):
            if key not in probe:
                raise ValueError('Missing probe field: ' + key)
        if not isinstance(probe['id'], str) or not re.fullmatch(r'[a-z0-9][a-z0-9_.-]*', probe['id']):
            raise ValueError('Invalid probe ID')
        if probe['id'] in ids or probe['path'] in paths:
            raise ValueError('Duplicate probe ID/path')
        if probe['category'] not in CATEGORIES:
            raise ValueError('Unknown probe category')
        relative = Path(probe['path'])
        resolved = (probe_root / relative).resolve()
        if relative.is_absolute() or not resolved.is_relative_to(probe_root):
            raise ValueError('Probe path escapes the probe root')
        raw = resolved.read_bytes()
        if raw.hex() != probe['bytes_hex'] or len(raw) != probe['byte_length']:
            raise ValueError('Probe bytes/length do not match: ' + probe['id'])
        if hashlib.sha256(raw).hexdigest() != probe['sha256']:
            raise ValueError('Probe SHA-256 does not match: ' + probe['id'])
        expectation = probe['rfc8259']
        if expectation.get('syntax') not in {'valid', 'invalid', 'invalid-encoding'}:
            raise ValueError('Invalid syntax expectation')
        if expectation.get('parser_outcome') not in {'accept', 'reject', 'implementation-dependent'}:
            raise ValueError('Invalid parser expectation')
        if not expectation.get('sections') or not expectation.get('reason'):
            raise ValueError('RFC section and reason required')
        if not probe['why'] or not probe['source'].get('reference'):
            raise ValueError('Purpose and source are required')
        if any(not isinstance(key, str) for key in probe.get('inspect_keys', [])):
            raise ValueError('Inspected keys must be strings')
        ids.add(probe['id'])
        paths.add(probe['path'])
    return data, probe_root


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, default=ROOT / 'metadata/convenience-features.json')
    args = parser.parse_args(argv)
    try:
        manifest, _ = load_manifest(args.manifest)
        counts = Counter(probe['category'] for probe in manifest['probes'])
        if counts.keys() != CATEGORIES or any(count < 3 for count in counts.values()):
            raise ValueError('Each of the ten categories requires at least three probes')
    except (OSError, KeyError, TypeError, ValueError) as error:
        parser.error(str(error))
    print('Manifest valid: %d exact-byte probes; categories %s.' %
          (sum(counts.values()), ', '.join('%s=%d' % pair for pair in sorted(counts.items()))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
