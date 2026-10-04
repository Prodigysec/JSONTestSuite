"""Native framing, value preservation and mode regressions for Java feature batch three."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import run_features
import run_tests
from parsers.features.registry import batch_03_programs
from tools.build_java_feature_batch_03 import fetch

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = batch_03_programs(ROOT / 'parsers')


class BatchThreeBuildTests(unittest.TestCase):
    def test_registry_and_primary_artifact_pins(self):
        self.assertEqual(len(REGISTRY), 8)
        for name, mode in REGISTRY.items():
            self.assertEqual(run_tests.programs[name], mode)
        sources = json.loads((ROOT/'parsers/features/java_batch_03/sources.json').read_text())
        self.assertEqual(len(sources['libraries']), 3)
        self.assertEqual({p['library'] for p in sources['libraries']}, {'fastjson','genson','jsoniter'})

    def test_tampered_cached_artifact_fails_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'library.jar'
            path.write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                fetch('https://unused.invalid', path, '0'*64)


@unittest.skipUnless((ROOT/'parsers/.build/java_batch_03/runtime.json').is_file(), 'Build feature batch 03')
class BatchThreeNativeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name)/'case.json'

    def observe(self, name, raw):
        self.path.write_bytes(raw)
        process = subprocess.run(REGISTRY[name]['observation_commands']+[str(self.path)], capture_output=True, timeout=5)
        self.assertIn(process.returncode, (0,1), process.stderr.decode('utf8','replace'))
        observation = run_features.decode_observation(process.stdout, process.returncode)
        self.assertIn('/ Java ', observation['version'])
        return observation

    def find(self, text):
        return next(name for name in REGISTRY if text in name)

    def test_scalars_and_nested_values_are_accepted(self):
        for name in REGISTRY:
            for raw in (b'null', b'false', b'0', b'""', b'[]', b'{"a":[null,false,0,"x"]}', b' \t0\r\n'):
                with self.subTest(name=name, raw=raw):
                    self.assertEqual(self.observe(name,raw)['status'], 'accept')
        utf8 = self.find('default, explicit native UTF-8')
        self.assertEqual(self.observe(utf8,b'0')['normalized'], {'type':'integer','decimal':'0'})
        auto = self.find('native encoding detection')
        # Retain the native auto-detection defect rather than rewriting bytes or parsed values.
        self.assertEqual(self.observe(auto,b'0')['normalized'], {'type':'null'})

    def test_whole_input_and_empty_framing(self):
        for name in REGISTRY:
            for raw in (b'{"a":1}=', b'null false', b'null\x1a', b'{"a":1}\0false', b''):
                with self.subTest(name=name, raw=raw):
                    self.assertEqual(self.observe(name,raw)['status'], 'reject')
        # hasNext() alone misses this punctuation in Genson.
        for name in REGISTRY:
            if 'Genson' in name:
                self.assertEqual(self.observe(name,b'false]')['status'], 'reject')

    def test_modes_native_bytes_and_duplicates(self):
        default = self.find('Fastjson 1.2.83 (default features')
        flags_off = self.find('(extension flags off')
        self.assertEqual(self.observe(default,b"{'a':1}")['status'],'accept')
        self.assertEqual(self.observe(flags_off,b"{'a':1}")['status'],'reject')
        self.assertEqual(self.observe(default,b'"\xff"')['status'],'reject')
        genson = self.find('default, explicit native UTF-8')
        self.assertEqual(self.observe(genson,b'"\xff"')['normalized']['units'],[65533])
        for name in (default, genson, self.find('jsoniter')):
            observation = self.observe(name,b'{"test":1,"test":2}')
            probe = {'duplicate_candidates':[{'key':'test','first':1,'last':2}]}
            self.assertEqual(run_features.duplicate_winners(probe,observation)[0]['winner'],'last')
            self.assertEqual(len(observation['normalized']['entries']),1)
            self.assertEqual(observation['serialized'],'{"test":2}')

    def test_numeric_types_and_native_serialization(self):
        default = self.find('Fastjson 1.2.83 (default features')
        self.assertEqual(self.observe(default,b'1.0e4096')['normalized'], {'type':'decimal','text':'1.0E+4096'})
        doubles = self.find('(UseBigDecimal off')
        self.assertEqual(self.observe(doubles,b'1.0e4096')['serialized'],'null')
        jsoniter = self.find('jsoniter')
        self.assertEqual(self.observe(jsoniter,b'9007199254740993')['normalized'], {'type':'integer','decimal':'9007199254740992'})
        self.assertEqual(self.observe(jsoniter,b'null')['serialized'],'null')
        genson = self.find('default, explicit native UTF-8')
        self.assertEqual(self.observe(genson,b'1.0e4096')['serialized'],'"Infinity"')

    def test_parse_observe_agreement_and_file_errors(self):
        for name,mode in REGISTRY.items():
            for raw in (b'false',b'{"a":1}=',b'"\xff"'):
                with self.subTest(name=name,raw=raw):
                    observation = self.observe(name,raw)
                    result = subprocess.run(mode['commands']+[str(self.path)], capture_output=True, timeout=5)
                    self.assertEqual(result.returncode,0 if observation['status']=='accept' else 1)
            result = subprocess.run(mode['commands']+[str(self.path.parent/'missing')],capture_output=True,timeout=5)
            self.assertEqual(result.returncode,2)

    def test_native_numeric_exception_remains_a_crash(self):
        name = self.find('jsoniter')
        self.path.write_bytes(b'-Infinity')
        for command in ('commands','observation_commands'):
            result = subprocess.run(REGISTRY[name][command]+[str(self.path)], capture_output=True, timeout=5)
            self.assertEqual(result.returncode,2)
            self.assertIn(b'java.lang.NumberFormatException',result.stderr)
            self.assertEqual(result.stdout,b'')

    def test_long_value_is_bounded_without_rejecting(self):
        for name in (self.find('Fastjson 1.2.83 (default features'),self.find('default, explicit native UTF-8'),self.find('jsoniter')):
            observation = self.observe(name,b'"'+b'a'*65536+b'"')
            self.assertEqual(observation['status'],'accept')
            self.assertTrue(observation['normalized']['truncated'])
            self.assertEqual(observation['normalized']['original_length'],65536)
