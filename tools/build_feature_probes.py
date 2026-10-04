#!/usr/bin/env python3
"""Generate only the separate feature corpus from explicit reviewed byte literals."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBES = []
WHY = {
    'comments': 'Comment recognition can hide tokens or change visible object members.',
    'quotes': 'Alternative delimiters may produce different strings or object keys.',
    'quoteless': 'Bare names and values reveal identifier and implicit-string extensions.',
    'commas': 'Separator recovery can create, omit, or merge array elements and object members.',
    'roots': 'One-text framing and literal/whitespace rules differ from streaming and relaxed formats.',
    'strings': 'Escape and byte decoding can replace, truncate, or reinterpret string code units.',
    'keys': 'Lookalike or truncated keys can alter lookup and duplicate-member precedence.',
    'serialization': 'A successful parse does not imply preservation by getter or serialization APIs.',
    'numbers': 'Stored numeric type, rounding, overflow, underflow, and extension grammar affect values.',
    'limits': 'Finite size/depth probes separate implementation limits from syntax errors.'}


def add(category, name, raw, sections, outcome='reject', syntax=None, inspect_keys=None, duplicates=None):
    if isinstance(raw, str):
        raw = raw.encode('utf-8')
    syntax = syntax or ('valid' if outcome != 'reject' else 'invalid')
    probe = {'id': category + '.' + name, 'category': category,
             'path': category + '/' + name + '.json', 'bytes_hex': raw.hex(),
             'sha256': hashlib.sha256(raw).hexdigest(), 'byte_length': len(raw),
             'rfc8259': {'syntax': syntax, 'parser_outcome': outcome, 'sections': sections,
                         'reason': WHY[category] + ' Apply the cited RFC grammar, encoding, or permitted limit.'},
             'why': WHY[category], 'source': {'kind': 'task', 'reference': 'prompt.md', 'rfc_sections': sections}}
    if inspect_keys:
        probe['inspect_keys'] = inspect_keys
    if duplicates:
        probe['duplicate_candidates'] = duplicates
    PROBES.append((probe, raw))


def generate():
    for name, raw in [
        ('line-slash', b'// comment\n{"a":1}'), ('block', b'{/* comment */"a":1}'),
        ('hash', b'# comment\n{"a":1}'), ('nested-block', b'/* outer /* inner */ outer */1'),
        ('between-tokens', b'/*a*/{/*b*/"a"/*c*/:/*d*/[/*e*/1/*f*/,/*g*/2/*h*/]/*i*/}/*j*/'),
        ('unterminated', b'{"a":1}/* unfinished'), ('key-position', b'{/*"hidden":0,*/"a":1}'),
        ('line-trailing', b'{"a":1}// trailing'), ('token-split', b'[tr/*x*/ue]')]:
        add('comments', name, raw, ['2','4','5'])
    add('comments', 'inside-string-control', b'{"a":"// /* # */"}', ['7'], 'accept')
    for name, raw in [('single-string', b"'value'"), ('single-key', b"{'a':1}"),
                      ('backtick-string', b'`value`'), ('backtick-key', b'{`a`:1}'),
                      ('smart-string', '“value”'), ('smart-key', '{“a”:1}'),
                      ('mixed', b'{"a":\'value\',\'b\':"other"}')]:
        add('quotes', name, raw, ['4','7'])
    add('quotes', 'double-control', b'{"a":"value"}', ['4','7'], 'accept')
    for name, raw in [('key', b'{a:1}'), ('value', b'{"a":value}'),
                      ('dollar-key', b'{$key:1}'), ('underscore-key', b'{_key:1}'),
                      ('space-value', b'{"a":hello world}'), ('identifier-root', b'hello'),
                      ('dollar-value', b'{"a":$value}')]:
        add('quoteless', name, raw, ['2','4','7'])
    add('quoteless', 'quoted-control', b'{"a":"hello world"}', ['4','7'], 'accept')
    for name, raw in [('array-trailing', b'[1,]'), ('object-trailing', b'{"a":1,}'),
                      ('array-leading', b'[,1]'), ('object-leading', b'{,"a":1}'),
                      ('array-repeated', b'[1,,2]'), ('object-repeated', b'{"a":1,,"b":2}'),
                      ('array-newline-missing', b'[1\n2]'),
                      ('object-newline-missing', b'{"a":1\n"b":2}')]:
        add('commas', name, raw, ['4','5'])
    add('commas', 'ordinary-control', b'[1,2]', ['5'], 'accept')
    for name, raw in [('python-true', b'True'), ('python-false', b'False'), ('python-none', b'None'),
                      ('undefined', b'undefined'), ('upper-null', b'NULL'),
                      ('implicit-object', b'a:1\nb:2'), ('ndjson', b'{"a":1}\n{"b":2}\n'),
                      ('multiple-values', b'null false'), ('trailing-equals', b'{"a":1}='),
                      ('empty', b''), ('nbsp', b'1\xc2\xa0'), ('formfeed', b'[\x0c]'),
                      ('vertical-tab', b'[\x0b]'), ('line-separator', '1\u2028')]:
        add('roots', name, raw, ['2','3'])
    add('roots', 'bom', b'\xef\xbb\xbf{}', ['8.1'], 'implementation-dependent', 'invalid')
    for name, raw in [('null-control', b'null'), ('false-control', b'false'), ('zero-control', b'0'),
                      ('whitespace-control', b' \t\r\n0\r\n')]:
        add('roots', name, raw, ['2','3'], 'accept')
    for name, raw in [('line-continuation', b'"a\\\nb"'), ('crlf-continuation', b'"a\\\r\nb"'),
                      ('multiline', b'"a\nb"'), ('triple-single', b"'''a\nb'''"),
                      ('triple-double', b'"""a\nb"""'), ('raw-tab', b'"a\tb"'),
                      ('raw-nul', b'"a\x00b"'), ('hex-escape', b'"\\x41"'),
                      ('vertical-escape', b'"\\v"'), ('zero-escape', b'"\\0"'),
                      ('unknown-escape', b'"\\q"')]:
        add('strings', name, raw, ['7'])
    add('strings', 'lone-high-surrogate', b'"\\ud800"', ['7','8.2'], 'implementation-dependent')
    add('strings', 'lone-low-surrogate', b'"\\udc00"', ['7','8.2'], 'implementation-dependent')
    add('strings', 'invalid-utf8', b'"\xff"', ['8.1'], 'reject', 'invalid-encoding')
    add('strings', 'overlong-utf8', b'"\xc0\xaf"', ['8.1'], 'reject', 'invalid-encoding')
    add('strings', 'escaped-control', b'"a\\n\\t\\u0000b"', ['7'], 'accept')
    add('strings', 'surrogate-pair-control', b'"\\ud83d\\ude00"', ['7','8.2'], 'accept')
    add('keys', 'duplicate-first-last', b'{"test":1,"test":2}', ['4'], 'accept',
        inspect_keys=['test'], duplicates=[{'key':'test','first':1,'last':2}])
    add('keys', 'duplicate-reversed', b'{"test":2,"test":1}', ['4'], 'accept',
        inspect_keys=['test'], duplicates=[{'key':'test','first':2,'last':1}])
    add('keys', 'surrogate-suffix', b'{"test\\ud800":1,"test":2}', ['7','8.2'],
        'implementation-dependent', inspect_keys=['test\ud800','test'])
    add('keys', 'raw-cr-suffix', b'{"test\r":1,"test":2}', ['7'], inspect_keys=['test\r','test'])
    add('keys', 'stray-quote', b'{"test"":1,"test":2}', ['4','7'], inspect_keys=['test'])
    add('keys', 'stray-backslash', b'{"te\\st":1,"test":2}', ['7'], inspect_keys=['test','te\\st'])
    add('keys', 'escaped-nul', b'{"test\\u0000":1,"test":2}', ['7'], 'accept', inspect_keys=['test\0','test'])
    add('keys', 'raw-nul', b'{"test\0":1,"test":2}', ['7'], inspect_keys=['test\0','test'])
    add('keys', 'comment-hide-second', b'{"description":"x","test":2,"extra":/*,"test":1,"extra2":*/ ""}',
        ['2','4'], inspect_keys=['description','test','extra','extra2'])
    add('keys', 'comment-after-value', b'{"test":1,"extra":"a"/*, "test":2 */}', ['2','4'], inspect_keys=['test','extra'])
    add('keys', 'comment-in-key-position', b'{"a"/*, "test":2 */:1}', ['2','4'], inspect_keys=['a','test'])
    add('keys', 'case-lookalikes', b'{"test":1,"Test":2}', ['4','8.3'], 'accept', inspect_keys=['test','Test'])
    add('keys', 'unicode-normalization', '{"é":1,"e\u0301":2}', ['4','8.3'], 'accept', inspect_keys=['é','e\u0301'])
    add('keys', 'escaped-same-name', b'{"a":1,"\\u0061":2}', ['4','8.3'], 'accept', inspect_keys=['a'],
        duplicates=[{'key':'a','first':1,'last':2}])
    for name, raw in [('duplicate-output', b'{"a":1,"a":2}'), ('ordering', b'{"z":1,"a":2,"m":3}'),
                      ('ordering-reversed', b'{"m":3,"a":2,"z":1}'), ('slash-escape', b'"\\/"'),
                      ('unicode-slash-escape', b'"\\u002f"'), ('negative-int-zero', b'-0'),
                      ('negative-float-zero', b'-0.0'), ('float-one', b'1.0'),
                      ('getter-versus-serialization', b'{"test":1,"test":2,"value":1.0}')]:
        add('serialization', name, raw, ['4','6','7','8.3'], 'accept', inspect_keys=['test','value','a'])
    for name, raw in [('overflow', b'1.0e4096'), ('integer-96-digits', b'9'*96),
                      ('int53-minus', b'9007199254740991'), ('int53', b'9007199254740992'),
                      ('int53-plus', b'9007199254740993'), ('int64-max', b'9223372036854775807'),
                      ('int64-over', b'9223372036854775808'), ('underflow', b'1E-400'),
                      ('long-decimal', b'0.123456789012345678901234567890123456789')]:
        add('numbers', name, raw, ['6','9'], 'implementation-dependent')
    for name, raw in [('negative-zero', b'-0'), ('negative-float-zero', b'-0.0'), ('integer-one', b'1'),
                      ('float-one', b'1.0'), ('upper-plus-exponent', b'1E+2'), ('lower-exponent', b'1e0')]:
        add('numbers', name, raw, ['6'], 'accept')
    for name, raw in [('hex', b'0x10'), ('octal-prefix', b'0o10'), ('octal-leading', b'012'),
                      ('plus-sign', b'+1'), ('leading-dot', b'.5'), ('trailing-dot', b'5.'),
                      ('nan', b'NaN'), ('infinity', b'Infinity'), ('minus-infinity', b'-Infinity'),
                      ('digit-separator', b'1_000')]:
        add('numbers', name, raw, ['6'])
    for name, raw in [('nested-32', b'['*32+b'0'+b']'*32),
                      ('nested-512', b'['*512+b'0'+b']'*512),
                      ('nested-2048', b'['*2048+b'0'+b']'*2048),
                      ('long-string', b'"'+b'a'*65536+b'"'),
                      ('long-key', b'{"'+b'a'*65536+b'":1}')]:
        add('limits', name, raw, ['7','9'], 'implementation-dependent')
    add('limits', 'deep-unclosed', b'['*4096, ['2','5','9'])


def main():
    generate()
    existing = defaultdict(list)
    for path in (ROOT / 'test_parsing').rglob('*.json'):
        existing[hashlib.sha256(path.read_bytes()).hexdigest()].append(str(path.relative_to(ROOT)))
    entries = []
    for probe, raw in PROBES:
        path = ROOT / 'test_features' / probe['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        if probe['sha256'] in existing:
            probe['existing_corpus_overlap'] = sorted(existing[probe['sha256']])
        entries.append(probe)
    manifest = {'schema_version': 1, 'description': 'Separate exact-byte convenience and value probes; no root corpus expectation is changed.',
                'probe_root': 'test_features', 'probes': entries}
    (ROOT / 'metadata/convenience-features.json').write_text(json.dumps(manifest, ensure_ascii=True, indent=2)+'\n')
    print('Generated %d probes across %d categories.' % (len(entries), len({p['category'] for p in entries})))


if __name__ == '__main__':
    main()
