import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.check_feature_manifest import load_manifest, ROOT


class FeatureManifestTests(unittest.TestCase):
    def test_shipped_bytes_and_category_coverage(self):
        manifest, _ = load_manifest(ROOT / 'metadata/convenience-features.json')
        self.assertEqual(len(manifest['probes']), 125)
        by_id = {probe['id']: bytes.fromhex(probe['bytes_hex']) for probe in manifest['probes']}
        self.assertEqual(by_id['strings.invalid-utf8'], b'"\xff"')
        self.assertEqual(by_id['strings.raw-nul'], b'"a\x00b"')
        self.assertEqual(by_id['strings.line-continuation'], b'"a\\\nb"')
        self.assertEqual(by_id['roots.empty'], b'')
        self.assertEqual(by_id['roots.bom'], b'\xef\xbb\xbf{}')
        self.assertEqual(by_id['numbers.integer-96-digits'], b'9' * 96)
        self.assertEqual(by_id['keys.surrogate-suffix'], b'{"test\\ud800":1,"test":2}')
        self.assertEqual(by_id['limits.long-string'], b'"' + b'a' * 65536 + b'"')

    def test_corruption_and_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'case.json').write_bytes(b'null')
            probe = dict(id='roots.control', category='roots', path='case.json', bytes_hex='6e756c6c',
                         sha256=hashlib.sha256(b'null').hexdigest(), byte_length=4,
                         rfc8259=dict(syntax='valid', parser_outcome='accept', sections=['3'], reason='null'),
                         why='control', source={'reference':'RFC 8259 section 3'})
            valid = dict(schema_version=1, probe_root='.', probes=[probe])
            path = root / 'manifest.json'
            path.write_text(json.dumps(valid))
            load_manifest(path, root)
            for change in ({'bytes_hex':'6e756c6c0a'}, {'sha256':'0'*64}, {'path':'../outside.json'},
                           {'category':'unknown'}, {'rfc8259':{'syntax':'valid'}}):
                with self.subTest(change=change):
                    data = copy.deepcopy(valid)
                    data['probes'][0].update(change)
                    path.write_text(json.dumps(data))
                    with self.assertRaises(ValueError):
                        load_manifest(path, root)
            path.write_text(json.dumps(dict(valid, probes=[probe,probe])))
            with self.assertRaises(ValueError):
                load_manifest(path, root)

    def test_symlink_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inner = root / 'inside'
            inner.mkdir()
            outside = root / 'outside.json'
            outside.write_bytes(b'null')
            (inner / 'case.json').symlink_to(outside)
            probe = dict(id='roots.control', category='roots', path='case.json', bytes_hex='6e756c6c',
                         sha256=hashlib.sha256(b'null').hexdigest(), byte_length=4,
                         rfc8259=dict(syntax='valid', parser_outcome='accept', sections=['3'], reason='null'),
                         why='control', source={'reference':'RFC 8259 section 3'})
            path = root / 'manifest.json'
            path.write_text(json.dumps(dict(schema_version=1, probe_root='inside', probes=[probe])))
            with self.assertRaises(ValueError):
                load_manifest(path, inner)
