"""Smoke and value regressions for the pinned Go feature batch, when built."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import run_features
import run_tests
from parsers.features.registry import GO_BATCH_01_MODES
from tools.validate_feature_batch import batch_names

ROOT=Path(__file__).resolve().parents[1]
BINARY=ROOT/'parsers/.build/feature_go_batch_01'


@unittest.skipUnless(BINARY.is_file(),'Build with sh parsers/features/build_batch_01.sh')
class GoFeatureBatchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'case.json'

    def run_mode(self,mode,raw,observe=False):
        self.path.write_bytes(raw)
        result=subprocess.run([str(BINARY)]+(['--observe'] if observe else [])+[mode,str(self.path)],capture_output=True,timeout=5)
        self.assertIn(result.returncode,(0,1),result.stderr.decode('utf8','replace'))
        if observe:return run_features.decode_observation(result.stdout,result.returncode)
        return result.returncode

    def test_all_modes_scalar_contract_and_framing(self):
        for mode,name in GO_BATCH_01_MODES:
            for raw in (b'null',b'false',b'0',b'""',b'[]',b'{"a":1}',b' \tfalse\r\n'):
                with self.subTest(mode=mode,raw=raw):
                    self.assertEqual(self.run_mode(mode,raw),0)
                    self.assertEqual(self.run_mode(mode,raw,True)['status'],'accept')
            for raw in (b'',b'{',b'[1,]',b'null false',b'{"a":1}=',b'0\0',b'null\0false',b'{"a":1}\0garbage'):
                with self.subTest(mode=mode,raw=raw):
                    self.assertEqual(self.run_mode(mode,raw),1)
                    self.assertEqual(self.run_mode(mode,raw,True)['status'],'reject')

    def test_framing_after_native_buffer_boundary(self):
        raw=b'{"a":"'+b'x'*65536+b'"}'+b' '*2048+b'\r\n'
        for mode,name in GO_BATCH_01_MODES:
            with self.subTest(mode=mode):
                self.assertEqual(self.run_mode(mode,raw),0)
                self.assertEqual(self.run_mode(mode,raw+b'\0false'),1)

    def test_missing_input_and_unknown_mode_are_failures(self):
        for args in (['goccy-default',str(self.path.parent/'missing')],['unknown',str(self.path)],[]):
            result=subprocess.run([str(BINARY)]+args,capture_output=True,timeout=5)
            self.assertEqual(result.returncode,2)

    def test_native_number_policies(self):
        for mode in ('goccy-number','sonic-number','jsoniter-number'):
            record=self.run_mode(mode,b'9007199254740993',True)
            self.assertEqual(record['normalized'],{'type':'number-lexeme','text':'9007199254740993'})
        record=self.run_mode('sonic-int64',b'9007199254740993',True)
        self.assertEqual(record['normalized'],{'type':'integer','decimal':'9007199254740993'})
        record=self.run_mode('sonic-default',b'9007199254740993',True)
        self.assertEqual(record['normalized']['bits'],'4340000000000000')

    def test_native_raw_control_and_malformed_byte_findings(self):
        for mode in ('sonic-default','sonic-fastest','sonic-number','sonic-int64'):
            record=self.run_mode(mode,b'"a\0b"',True)
            self.assertEqual(record['status'],'accept')
            self.assertEqual(record['normalized']['units'],[97,0,98])
        for mode in ('sonic-std','sonic-unicode-errors'):
            self.assertEqual(self.run_mode(mode,b'"a\0b"'),1)
        # Malformed UTF-8 is a native finding, not wrapper preprocessing.
        for mode,name in GO_BATCH_01_MODES:
            record=self.run_mode(mode,b'"\xff"',True)
            self.assertEqual(record['status'],'accept')
            self.assertTrue(record['normalized']['units'])
            if record['normalized']['units']==[65533]:
                self.assertIn(record['normalized'].get('invalid_native_utf8_hex'),(None,'ff'))

    def test_native_serializer_bytes_are_not_hidden_by_envelope(self):
        record=self.run_mode('sonic-default',b'"\xff"',True)
        self.assertEqual(record['normalized']['invalid_native_utf8_hex'],'ff')
        self.assertTrue(record['serialized_invalid_utf8'])
        self.assertEqual(record['serialized_bytes_hex'],'22ff22')

    def test_duplicate_lookup_and_budget_preserve_acceptance(self):
        probe={'duplicate_candidates':[{'key':'test','first':1,'last':2}]}
        for mode,name in GO_BATCH_01_MODES:
            record=self.run_mode(mode,b'{"test":1,"test":2}',True)
            self.assertEqual(run_features.duplicate_winners(probe,record)[0]['winner'], 'last')
            record=self.run_mode(mode,b'"'+b'x'*65536+b'"',True)
            self.assertEqual(record['status'],'accept')
            self.assertTrue(record['normalized']['truncated'])
            self.assertEqual(record['normalized']['original_length'],65536)


class GoFeatureRegistryTests(unittest.TestCase):
    def test_registered_source_modes_and_baseline_remains_scoped(self):
        for mode,name in GO_BATCH_01_MODES:
            self.assertEqual(run_tests.programs[name]['commands'],[str(BINARY),mode])
            self.assertEqual(run_tests.programs[name]['observation_commands'],[str(BINARY),'--observe',mode])
            self.assertIn('setup',run_tests.programs[name])
        names=batch_names('P2-04',json.loads((ROOT/'docs/roadmap/backlog.json').read_text()))
        self.assertEqual(len(names),3)
        self.assertFalse(any(name.startswith('Go ') for name in names))
