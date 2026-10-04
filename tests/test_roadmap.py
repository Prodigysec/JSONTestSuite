import copy
import unittest
from tools.check_roadmap import validate


class RoadmapTests(unittest.TestCase):
    def sample(self):
        return {'tasks': [dict(id='A', title='First', dependencies=[], deliverables=['first'],
                               acceptance_commands=['check'], status='todo'),
                          dict(id='B', title='Second', dependencies=['A'], deliverables=['second'],
                               acceptance_commands=['check'], status='todo')], 'parsers': []}

    def test_ordering_and_unsupported_done_claims_are_rejected(self):
        data = self.sample()
        self.assertEqual(len(validate(data)[0]), 2)
        for mutate in (
                lambda data: data['tasks'][1].update(status='done', verification={'exit': 0}),
                lambda data: data['tasks'][0].update(dependencies=['B']),
                lambda data: data['tasks'][0].update(status='done'),
                lambda data: data['tasks'][1].update(id='A'),
                lambda data: data['tasks'][0].update(status='unknown')):
            invalid = copy.deepcopy(data)
            mutate(invalid)
            with self.assertRaises(ValueError):
                validate(invalid)

    def test_external_basis_is_not_local_evidence(self):
        data = self.sample()
        entry = dict(id='parser-1', title='Lead', language='Go', tier='1A', basis_tag='Measured',
                     source_url=None, version_to_pin=None, build_steps=['verify'], priority=1,
                     status='todo', source_verified=False)
        data['parsers'] = [entry]
        validate(data)
        entry['source_verified'] = True
        with self.assertRaises(ValueError):
            validate(data)
        entry['source_verified'] = False
        entry['status'] = 'done'
        with self.assertRaises(ValueError):
            validate(data)
