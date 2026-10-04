#!/usr/bin/env python3
"""Observe this interpreter's json decoder without changing its parsing policy."""
import hashlib
import json
from pathlib import Path
import platform
import struct
import sys

from test_python_json import reject_constant

VERSION = platform.python_implementation()+' '+platform.python_version()+' / json stdlib'
DEPTH_LIMIT, ITEM_LIMIT, STRING_LIMIT = 64, 4096, 4096


def units(text):
    raw = text.encode('utf-16-be', 'surrogatepass')
    return [int.from_bytes(raw[i:i+2], 'big') for i in range(0, len(raw), 2)]


def normalize(value, depth=0, budget=None):
    if budget is None:
        budget = [ITEM_LIMIT]
    kind = 'object' if isinstance(value, dict) else 'array' if isinstance(value, list) else None
    if kind and (depth >= DEPTH_LIMIT or budget[0] <= 0):
        return dict(type=kind, truncated=True, original_length=len(value))
    budget[0] -= 1
    if value is None:
        return dict(type='null')
    if isinstance(value, bool):
        return dict(type='boolean', value=value)
    if isinstance(value, int):
        return dict(type='integer', decimal=str(value))
    if isinstance(value, float):
        return dict(type='float', format='binary64', bits=struct.pack('>d', value).hex())
    if isinstance(value, str):
        raw = value.encode('utf-16-be', 'surrogatepass')
        result = dict(type='string', units=units(value[:STRING_LIMIT])[:STRING_LIMIT])
        if len(raw)//2 > STRING_LIMIT:
            result.update(truncated=True, original_length=len(raw)//2, sha256_utf16be=hashlib.sha256(raw).hexdigest())
        return result
    if kind:
        result = dict(type=kind)
        limit = min(len(value), max(0, budget[0]))
        if kind == 'object':
            result['entries'] = []
            for index, (key, child) in enumerate(value.items()):
                if index >= limit or budget[0] <= 0:
                    break
                result['entries'].append(dict(key=units(key), value=normalize(child, depth+1, budget)))
            observed = len(result['entries'])
        else:
            result['items'] = []
            for child in value[:limit]:
                if budget[0] <= 0:
                    break
                result['items'].append(normalize(child, depth+1, budget))
            observed = len(result['items'])
        if observed < len(value):
            result.update(truncated=True, original_length=len(value))
        return result
    return dict(type='unsupported', native_type=type(value).__name__)


def observe(raw, reject_nonfinite=False):
    record = dict(status='reject', version=VERSION, parsed_value_type=None, normalized=None,
                  key_observations=[], serialized=None,
                  capabilities=dict(normalized=True, serialization=True, duplicate_entries=False, lookup_all_keys=False))
    try:
        text = raw.decode('utf-8', 'strict')
        value = json.loads(text, **({'parse_constant':reject_constant} if reject_nonfinite else {}))
    except (ValueError, RecursionError) as error:
        record['detail'] = str(error)
        return record
    record.update(status='accept', parsed_value_type=type(value).__name__, normalized=normalize(value))
    if isinstance(value, dict):
        keys = list(value)
        record['capabilities']['lookup_all_keys'] = len(keys) <= ITEM_LIMIT
        record['key_observations'] = [dict(key=units(key), found=key in value, value=normalize(value[key]))
                                      for key in keys[:ITEM_LIMIT]]
    try:
        # Native serialization is observed independently; it may emit NaN/Infinity.
        record['serialized'] = json.dumps(value, ensure_ascii=True, separators=(',', ':'))
    except (ValueError, RecursionError, OverflowError) as error:
        record['serialization_error'] = str(error)
    return record


def main(argv):
    args = argv[1:]
    strict = args[:1] == ['--reject-nonfinite']
    if strict:
        args = args[1:]
    if len(args) != 1:
        return 2
    try:
        raw = Path(args[0]).read_bytes()
    except OSError as error:
        print(str(error), file=sys.stderr)
        return 2
    record = observe(raw, strict)
    print(json.dumps(record, ensure_ascii=True, allow_nan=False))
    return 0 if record['status'] == 'accept' else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
