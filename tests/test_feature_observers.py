"""Native observations preserve values and parsing contract independently of consensus."""
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

import run_features
import run_tests
from tools.validate_feature_batch import audit_standard

ROOT = Path(__file__).resolve().parents[1]


class FeatureObserverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'case.json'
        self.python = [sys.executable,'-B',str(ROOT/'parsers/observe_python_features.py')]
        self.node = ['node',str(ROOT/'parsers/observe_node_features.js')]

    def observe(self, command, raw):
        self.path.write_bytes(raw)
        result = subprocess.run(command+[str(self.path)],capture_output=True,timeout=5)
        self.assertIn(result.returncode,(0,1),result.stderr)
        record = run_features.decode_observation(result.stdout,result.returncode)
        self.assertTrue(record['version'])
        return record

    def commands(self):
        commands = [self.python]
        if shutil.which('node'):
            commands.append(self.node)
        return commands

    def test_contract_and_strict_raw_bytes(self):
        for command in self.commands():
            for raw in (b'null',b'false',b'0',b'{"a":1}',b'"\\ud800"'):
                with self.subTest(command=command,raw=raw):
                    self.assertEqual(self.observe(command,raw)['status'],'accept')
            for raw in (b'',b'null false',b'{"a":1}=',b'"\xff"',b'\xef\xbb\xbf{}',b'"a\0b"'):
                with self.subTest(command=command,raw=raw):
                    self.assertEqual(self.observe(command,raw)['status'],'reject')
            missing = subprocess.run(command+[str(self.path.parent/'missing.json')],capture_output=True,timeout=5)
            self.assertEqual(missing.returncode,2)

    def test_python_types_nonfinite_policy_and_exact_integer(self):
        self.assertEqual(self.observe(self.python,b'false')['normalized'], {'type':'boolean','value':False})
        self.assertEqual(self.observe(self.python,b'9007199254740993')['normalized'], {'type':'integer','decimal':'9007199254740993'})
        self.assertEqual(self.observe(self.python,b'1')['parsed_value_type'],'int')
        self.assertEqual(self.observe(self.python,b'1.0')['parsed_value_type'],'float')
        self.assertEqual(self.observe(self.python,b'-0.0')['normalized']['bits'],'8000000000000000')
        self.assertEqual(self.observe(self.python,b'NaN')['status'],'accept')
        self.assertEqual(self.observe(self.python+['--reject-nonfinite'],b'NaN')['status'],'reject')
        self.assertEqual(self.observe(self.python+['--reject-nonfinite'],b'1.0e4096')['normalized']['bits'],'7ff0000000000000')

    @unittest.skipUnless(shutil.which('node'),'Node unavailable')
    def test_node_native_rounding_negative_zero_and_overflow_serialization(self):
        record = self.observe(self.node,b'9007199254740993')
        self.assertEqual(record['normalized'], {'type':'float','format':'binary64','bits':struct.pack('>d',9007199254740992.0).hex()})
        self.assertEqual(record['serialized'],'9007199254740992')
        record = self.observe(self.node,b'-0')
        self.assertEqual(record['normalized']['bits'],'8000000000000000')
        self.assertEqual(record['serialized'],'0')
        record = self.observe(self.node,b'1.0e4096')
        self.assertEqual(record['normalized']['bits'],'7ff0000000000000')
        self.assertEqual(record['serialized'],'null')
        self.assertEqual(self.observe(self.node,b'NaN')['status'],'reject')

    def test_key_units_getters_and_native_duplicate_winner(self):
        raw=b'{"test":1,"test":2,"test\\ud800":3,"test\\u0000":4}'
        probe={'duplicate_candidates':[{'key':'test','first':1,'last':2}]}
        for command in self.commands():
            record=self.observe(command,raw)
            observations={tuple(item['key']):item for item in record['key_observations']}
            self.assertEqual(set(observations),{tuple(run_features.units(key)) for key in ('test','test\ud800','test\0')})
            self.assertEqual(run_features.duplicate_winners(probe,record)[0]['winner'],'last')
            self.assertFalse(record['capabilities']['duplicate_entries'])
            self.assertEqual(len(record['normalized']['entries']),3)
            self.assertEqual(self.observe(command,b'"\\ud83d\\ude00"')['normalized']['units'],[0xd83d,0xde00])

    def test_normalizer_limits_do_not_change_acceptance(self):
        for command in self.commands():
            record=self.observe(command,b'"'+b'a'*65536+b'"')
            self.assertEqual(record['status'],'accept')
            self.assertEqual(record['normalized']['original_length'],65536)
            self.assertEqual(len(record['normalized']['units']),4096)
            self.assertTrue(record['normalized']['truncated'])
            self.assertEqual(len(record['serialized']),65538)
            record=self.observe(command,b'['*128+b'0'+b']'*128)
            self.assertEqual(record['status'],'accept')
            tree=record['normalized']
            for _ in range(64): tree=tree['items'][0]
            self.assertTrue(tree['truncated'])

    def test_serialization_failure_remains_accepted(self):
        # Exercise a native value's successful parse followed by serializer failure.
        sys.path.insert(0,str(ROOT/'parsers'))
        self.addCleanup(sys.path.remove,str(ROOT/'parsers'))
        spec=importlib.util.spec_from_file_location('feature_python_observer',ROOT/'parsers/observe_python_features.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        from unittest.mock import patch
        with patch.object(module.json,'dumps',side_effect=ValueError('serializer limit')):
            record=module.observe(b'null')
        self.assertEqual(record['status'],'accept')
        self.assertIsNone(record['serialized'])
        self.assertEqual(record['serialization_error'],'serializer limit')

    def test_registry_preserves_parsing_commands_and_has_observers(self):
        names=[name for name in run_tests.programs if name.startswith('Python stdlib') or name=='Node.js V8 JSON.parse (strict UTF-8)']
        self.assertEqual(len(names),3)
        for name in names:
            self.assertIn('observation_commands',run_tests.programs[name])
            self.assertNotEqual(run_tests.programs[name]['commands'],run_tests.programs[name]['observation_commands'])

    def test_standard_audit_does_not_infer_absent_success(self):
        names=['p'];fixtures=['y_null.json','n_bad.json']
        valid=['p\tEXPECTED_RESULT\ty_null.json','p\tSKIPPED_SETUP_FAILED\tn_bad.json']
        counts=audit_standard(valid,names,fixtures)
        self.assertEqual(counts['p']['SKIPPED_SETUP_FAILED'],1)
        for rows in (valid[:1],valid+[valid[0]],valid+['p\tEXPECTED_RESULT\textra.json'], ['p\tUNKNOWN\ty_null.json',valid[1]]):
            with self.subTest(rows=rows),self.assertRaises(ValueError): audit_standard(rows,names,fixtures)
