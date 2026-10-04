"""Native API, framing, and observation regressions for feature adapter batch two."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import run_features
import run_tests
from parsers.features.registry import batch_02_programs

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=batch_02_programs(ROOT/'parsers')


@unittest.skipUnless((ROOT/'parsers/.build/feature_go_batch_02').is_file() and (ROOT/'parsers/.build/json_smart/runtime.json').is_file(),'Build feature batch 02')
class BatchTwoTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'case.json'

    def observe(self,name,raw):
        self.path.write_bytes(raw)
        result=subprocess.run(REGISTRY[name]['observation_commands']+[str(self.path)],capture_output=True,timeout=5)
        self.assertIn(result.returncode,(0,1),result.stderr.decode('utf8','replace'))
        record=run_features.decode_observation(result.stdout,result.returncode)
        self.assertTrue(record['version'])
        return record

    def find(self,text):return next(name for name in REGISTRY if text in name)

    def test_scalar_roots_and_complete_framing(self):
        for name in REGISTRY:
            for raw in (b'null',b'false',b'0',b'""',b'[]',b'{"a":"x","b":[1,"y"]}',b' \t0\r\n'):
                with self.subTest(name=name,raw=raw):
                    self.assertEqual(self.observe(name,raw)['status'],'accept')
            for raw in (b'{"a":1}=',b'{"a":1}\x1afalse',b'null\x1afalse',b'{"a":1}\0false'):
                with self.subTest(name=name,raw=raw):
                    self.assertEqual(self.observe(name,raw)['status'],'reject')

    def test_native_parse_and_observation_commands_agree(self):
        for name,mode in REGISTRY.items():
            for raw in (b'false',b'{"a":1}=',b'"\xff"',b'"a\0b"'):
                with self.subTest(name=name,raw=raw):
                    record=self.observe(name,raw)
                    result=subprocess.run(mode['commands']+[str(self.path)],capture_output=True,timeout=5)
                    self.assertEqual(result.returncode,0 if record['status']=='accept' else 1)
            result=subprocess.run(mode['commands']+[str(self.path.parent/'missing')],capture_output=True,timeout=5)
            self.assertEqual(result.returncode,2)

    def test_jsonparser_modes_native_lookup_and_number_validation(self):
        default=self.find('DefaultConfig');lenient=self.find('(Lenient')
        self.assertEqual(self.observe(default,b"{'a':'x'}")['status'],'reject')
        self.assertEqual(self.observe(lenient,b"{'a':'x'}")['status'],'accept')
        self.assertEqual(self.observe(default,b'"\\q"')['status'],'reject')
        self.assertEqual(self.observe(lenient,b'"\\q"')['status'],'accept')
        for raw in (b'0\0false',b'1e+',b'null false'):
            self.assertEqual(self.observe(default,raw)['status'],'reject')
        leading_zero=self.observe(default,b'012')
        self.assertEqual(leading_zero['status'],'accept')
        self.assertEqual(leading_zero['normalized'],{'type':'number-lexeme','text':'012'})
        record=self.observe(default,b'{"test":1,"test":2}')
        self.assertEqual(len(record['normalized']['entries']),2)
        self.assertTrue(record['capabilities']['duplicate_entries'])
        probe={'duplicate_candidates':[{'key':'test','first':1,'last':2}]}
        self.assertEqual(run_features.duplicate_winners(probe,record)[0]['winner'],'first')
        self.assertFalse(record['capabilities']['serialization'])

    def test_gojay_native_callbacks_serialization_and_no_fake_getter(self):
        name=self.find('gojay')
        record=self.observe(name,b'{"test":1,"test":2,"null":null,"array":[false,"x"]}')
        self.assertEqual(len(record['normalized']['entries']),4)
        self.assertTrue(record['capabilities']['duplicate_entries'])
        self.assertFalse(record['capabilities']['lookup_all_keys'])
        self.assertEqual(record['key_observations'],[])
        self.assertEqual(record['serialized'],'{"test":1,"test":2,"null":null,"array":[false,"x"]}')
        self.assertEqual(self.observe(name,b'null')['serialized'],'null')
        self.assertEqual(self.observe(name,b'9007199254740993')['normalized']['bits'],'4340000000000000')
        source=(ROOT/'parsers/features/go_batch_02/main.go').read_text()
        self.assertNotIn('DecodeInterface(',source)
        self.assertNotIn('stdjson.Unmarshal(',source)
        self.assertNotIn('gojay.MarshalAny(',source)

    def test_json_smart_presets_bytes_and_decimal_values(self):
        permissive=self.find(', default,');strict=self.find('MODE_STRICTEST')
        record=self.observe(permissive,b'null false')
        self.assertEqual(record['normalized'],{'type':'string','units':run_features.units('null false')})
        self.assertEqual(self.observe(strict,b'null false')['status'],'reject')
        self.assertEqual(self.observe(permissive,b'')['status'],'accept')
        self.assertEqual(self.observe(strict,b'')['status'],'reject')
        for name in (permissive,strict):
            record=self.observe(name,b'"\xff"')
            self.assertEqual(record['normalized']['units'],[65533])
        record=self.observe(strict,b'0.123456789012345678901234567890123456789')
        self.assertEqual(record['normalized'],{'type':'decimal','text':'0.123456789012345678901234567890123456789'})
        self.assertIn('POM 2.6.0-SNAPSHOT',record['version'])

    def test_normalizer_limits_preserve_acceptance(self):
        for name in (self.find('DefaultConfig'),self.find('gojay'),self.find('MODE_STRICTEST')):
            record=self.observe(name,b'"'+b'a'*65536+b'"')
            self.assertEqual(record['status'],'accept')
            self.assertTrue(record['normalized']['truncated'])
            self.assertEqual(record['normalized']['original_length'],65536)


class BatchTwoProtocolTests(unittest.TestCase):
    def test_native_binary32_and_decimal_types(self):
        run_features.validate_tree({'type':'float','format':'binary32','bits':'80000000'})
        run_features.validate_tree({'type':'decimal','text':'0.123456789012345678901234567890123456789'})
        for tree in ({'type':'float','format':'binary32','bits':'0000'},{'type':'decimal','text':'NaN'}):
            with self.assertRaises(ValueError):run_features.validate_tree(tree)

    def test_registry_has_distinct_native_modes(self):
        self.assertEqual(len(REGISTRY),11)
        for name,mode in REGISTRY.items():
            self.assertEqual(run_tests.programs[name],mode)
            self.assertIn('setup',mode)
