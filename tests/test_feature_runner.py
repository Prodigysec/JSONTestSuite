"""Feature-runner regression cases using controlled observers and raw fixtures."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

import run_features as runner

ACCEPT = dict(status='accept', parsed_value_type='NoneType', normalized={'type':'null'},
              key_observations=[], serialized='null', capabilities={'lookup_all_keys':True})
REJECT = dict(status='reject', parsed_value_type=None, normalized=None,
              key_observations=[], serialized=None, capabilities={})


class FeatureRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.probes = self.root/'probes'
        self.probes.mkdir()
        self.manifest = self.root/'manifest.json'
        self.filter = self.root/'filter.json'
        self.registry = {}
        self.entries = []
        self.case('a', b'null')
        self.case('b', b'false')

    def case(self, name, raw):
        (self.probes/(name+'.json')).write_bytes(raw)
        self.entries.append(dict(id='roots.'+name, category='roots', path=name+'.json', bytes_hex=raw.hex(),
            sha256=hashlib.sha256(raw).hexdigest(), byte_length=len(raw), why='controlled case',
            source={'reference':'test'}, rfc8259=dict(syntax='valid', parser_outcome='accept', sections=['3'], reason='control')))
        self.manifest.write_text(json.dumps(dict(schema_version=1, probe_root='probes', probes=self.entries)))

    def adapter(self, name, body=None, **kwargs):
        body = body or ('import json; print(json.dumps('+repr(ACCEPT)+'))')
        self.registry[name] = dict(observation_commands=[sys.executable, '-B', '-c', body], observation_version='controlled-1', **kwargs)
        return self.registry[name]

    def run_cases(self, names=None, jobs=1, output=None):
        if names is not None:
            self.filter.write_text(json.dumps(names))
        return runner.run_observations(self.registry, self.manifest, output or self.root/'out',
                                      self.filter if names is not None else None, jobs, self.probes)

    def records(self):
        return [json.loads(line) for line in (self.root/'out/observations.jsonl').read_text().splitlines()]

    def test_accept_reject_raw_stdin_and_provenance(self):
        self.entries = []
        self.case('a', b'"\xff\x00"')
        self.case('b', b'false')
        body = 'import sys,json; raw=sys.stdin.buffer.read(); d='+repr(REJECT)+'; d["detail"]=raw.hex(); print(json.dumps(d)); sys.exit(1)'
        self.adapter('stdin', body, observation_use_stdin=True)
        summary = self.run_cases()
        self.assertEqual(summary['counts'], {'reject':2})
        self.assertEqual(summary['ci_verdict'], 0)
        records = self.records()
        self.assertEqual(records[0]['detail'], '22ff0022')
        self.assertEqual(records[0]['fixture_sha256'], hashlib.sha256(b'"\xff\x00"').hexdigest())
        self.assertEqual(records[0]['command'][-1], body)
        self.assertEqual(records[0]['version'], 'controlled-1')

    def test_first_timeout_does_not_skip_next(self):
        self.adapter('slow-first', 'import sys,time,json; from pathlib import Path; '+
            'time.sleep(2) if Path(sys.argv[-1]).name=="a.json" else None; print(json.dumps('+repr(ACCEPT)+'))', timeout=.3)
        summary = self.run_cases()
        self.assertEqual([r['status'] for r in self.records()], ['timeout','accept'])
        self.assertEqual(summary['ci_verdict'], 1)

    def test_crashes_and_malformed_protocol(self):
        bodies = ['import os,signal; os.kill(os.getpid(), signal.SIGTERM)',
                  'print("{}")', 'print("{}\\n{}")',
                  'import json; print(json.dumps('+repr(REJECT)+'))',
                  'print("{\\"status\\":NaN}")',
                  'import json; print(json.dumps('+repr(dict(ACCEPT, normalized={'type':'float','format':'binary64','bits':'bad'}))+'))']
        for index, body in enumerate(bodies):
            with self.subTest(index=index):
                self.registry = {}
                self.adapter('invalid', body)
                summary = self.run_cases(output=self.root/('out'+str(index)))
                self.assertEqual(summary['counts'], {'crash':2})
                self.assertEqual(summary['ci_verdict'], 1)

    def test_missing_and_unsupported_and_failed_setup_are_explicit(self):
        self.registry['missing'] = dict(observation_commands=['/no/such/observer'])
        self.registry['unsupported'] = dict(commands=['irrelevant'])
        self.adapter('setup', setup=[sys.executable,'-c','raise SystemExit(2)'])
        summary = self.run_cases(['missing','unsupported','setup'])
        records = self.records()
        self.assertEqual(summary['counts'], {'skipped':6})
        self.assertEqual({r['reason'] for r in records}, {'SKIPPED_UNAVAILABLE','SKIPPED_UNSUPPORTED_OBSERVER','SKIPPED_SETUP_FAILED'})
        self.assertTrue(all(r['normalized'] is None for r in records))

    def test_validation_precedes_output_and_setup(self):
        marker = self.root/'setup-ran'
        self.adapter('real', setup=[sys.executable,'-c','from pathlib import Path; Path('+repr(str(marker))+').touch()'])
        for names in ([], ['typo'], ['real','real'], 'real', [False]):
            with self.subTest(names=names), self.assertRaises(ValueError):
                self.run_cases(names)
            self.assertFalse((self.root/'out').exists())
        for jobs in (0,-1,False):
            with self.assertRaises(ValueError):
                self.run_cases(['real'],jobs)
        self.assertFalse(marker.exists())
        self.entries[0]['sha256'] = '0'*64
        self.manifest.write_text(json.dumps(dict(schema_version=1, probes=self.entries)))
        with self.assertRaises(ValueError):
            self.run_cases(['real'])
        self.assertFalse(marker.exists())

    def test_output_isolation_and_no_overwrite(self):
        self.adapter('real')
        existing = self.root/'out'
        existing.mkdir()
        sentinel = existing/'sentinel'
        sentinel.write_bytes(b'preserve')
        with self.assertRaises(FileExistsError):
            self.run_cases()
        self.assertEqual(sentinel.read_bytes(), b'preserve')
        with self.assertRaises(ValueError):
            self.run_cases(output=runner.ROOT/'results/new-feature-output')
        link = self.root/'historical'
        link.symlink_to(runner.ROOT/'results', target_is_directory=True)
        with self.assertRaises(ValueError):
            self.run_cases(output=link/'new-feature-output')

    def test_parallel_overlap_deterministic_order_and_serial_setup(self):
        events = self.root/'events'
        for name in ('z-last','a-first'):
            setup = 'import time; from pathlib import Path; p=Path('+repr(str(events))+'); '+\
                'f=p.open("a"); f.write('+repr(name+' start\n')+'); f.flush(); time.sleep(.05); f.write('+repr(name+' end\n')+'); f.close()'
            body = 'import time,json; from pathlib import Path; p=Path('+repr(str(events))+'); '+\
                'f=p.open("a"); f.write('+repr(name+' observer\n')+'); f.close(); '+\
                'Path('+repr(str(self.root/(name+'.started')))+').touch(); '+\
                '\nwhile len(list(p.parent.glob("*.started"))) < 2: time.sleep(.005)\n'+\
                'print(json.dumps('+repr(ACCEPT)+'))'
            self.adapter(name, body, setup=[sys.executable,'-c',setup])
        self.run_cases(jobs=2)
        records = self.records()
        self.assertEqual([(r['parser'],r['probe_id']) for r in records], [('a-first','roots.a'),('a-first','roots.b'),('z-last','roots.a'),('z-last','roots.b')])
        lines = events.read_text().splitlines()
        self.assertEqual(lines[:4], ['a-first start','a-first end','z-last start','z-last end'])
        self.assertEqual(set(lines[4:6]), {'a-first observer','z-last observer'})
        self.assertEqual(records[0]['status'], 'accept')

    def test_stdout_and_stderr_are_bounded_and_stdin_does_not_deadlock(self):
        noisy = [sys.executable,'-c','import sys; sys.stdout.write("x"*100000); sys.stdout.flush()']
        result = runner.bounded_process(noisy,2,output_limit=100)
        self.assertEqual(result['status'], 'output_limit')
        self.assertLessEqual(len(result['stdout']), 100)
        command = [sys.executable,'-c','import sys; sys.stderr.write("x"*100000); sys.stdout.write("ok"); sys.stdin.buffer.read()']
        result = runner.bounded_process(command,2,b'x'*100000)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['stdout'], b'ok')
        self.assertEqual(len(result['stderr']), runner.MAX_STDERR)

    @unittest.skipUnless(os.name == 'posix', 'POSIX process groups')
    def test_descendant_pipe_is_bounded_even_after_parent_exit(self):
        command = [sys.executable,'-c','import subprocess,sys; subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"])']
        started = time.monotonic()
        result = runner.bounded_process(command,.2)
        self.assertEqual(result['status'], 'timeout')
        self.assertLess(time.monotonic()-started, 2)

    def test_duplicate_winner_uses_actual_lookup_not_serialization(self):
        probe = dict(duplicate_candidates=[dict(key='test',first=1,last=2)])
        record = dict(status='accept',key_observations=[dict(key=runner.units('test'),found=True,value={'type':'integer','decimal':'1'})],
                      capabilities={'lookup_all_keys':True}, serialized='{"test":2}')
        self.assertEqual(runner.duplicate_winners(probe,record)[0]['winner'], 'first')
        record['key_observations'] = []
        self.assertEqual(runner.duplicate_winners(probe,record)[0]['winner'], 'missing')
        record['status'] = 'reject'
        self.assertEqual(runner.duplicate_winners(probe,record)[0]['winner'], 'unknown')

    def test_invalid_serialization_bytes_are_validated_and_retained(self):
        record=dict(ACCEPT,serialized='"replacement"',serialized_invalid_utf8=True,serialized_bytes_hex='22ff22')
        raw=(json.dumps(record)+'\n').encode()
        self.assertEqual(runner.decode_observation(raw,0)['serialized_bytes_hex'],'22ff22')
        for changes in ({'serialized_bytes_hex':'226122'},{'serialized_bytes_hex':'not hex'},{'serialized_bytes_hex':None}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                runner.decode_observation((json.dumps(dict(record,**changes))+'\n').encode(),0)
