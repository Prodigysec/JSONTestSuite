import os
import shutil
import tempfile
import unittest

import run_transform


class TransformObserverTests(unittest.TestCase):
    def test_signed_zero_is_distinct_from_serialization(self):
        positive = run_transform.observe_python(
            os.path.join(run_transform.BASE_DIR, "test_transform", "number_positive_zero.json"), "zero")
        negative = run_transform.observe_python(
            os.path.join(run_transform.BASE_DIR, "test_transform", "number_negative_zero.json"), "zero")
        self.assertEqual((positive["negative_zero"], negative["negative_zero"]), (False, True))
        self.assertEqual((positive["serialized"], negative["serialized"]), ("[0.0]", "[-0.0]"))

    def test_case_distinct_keys_survive_both_orders(self):
        for filename in ("object_case_distinct_keys.json", "object_case_distinct_keys_reversed.json"):
            with self.subTest(filename=filename):
                observation = run_transform.observe_python(
                    os.path.join(run_transform.BASE_DIR, "test_transform", filename), "keys")
                self.assertEqual({key: value for key, value in observation["members"]}, {"a": 1, "A": 2})
                self.assertEqual(len(observation["members"]), 2)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required")
    def test_node_preserves_parsed_negative_zero_but_serializes_it_as_zero(self):
        path = os.path.join(run_transform.BASE_DIR, "test_transform", "number_negative_zero.json")
        observation = run_transform.observe_node(path, "zero")
        self.assertEqual(observation, {"status": "ok", "negative_zero": True, "serialized": "[0]"})

    def test_malformed_bytes_are_reported_as_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "bad.json")
            with open(path, "wb") as stream:
                stream.write(b'["\xff"]')
            self.assertEqual(run_transform.observe_python(path, "zero")["status"], "error")
            if shutil.which("node"):
                self.assertEqual(run_transform.observe_node(path, "zero")["status"], "error")
                self.assertEqual(run_transform.observe_node(path, "survey")["status"], "reject")
            self.assertEqual(run_transform.observe_python(path, "survey")["status"], "reject")

    def test_survey_reports_type_and_serialization(self):
        path = os.path.join(run_transform.BASE_DIR, "test_transform", "number_negative_zero.json")
        self.assertEqual(run_transform.observe_python(path, "survey"),
                         {"status": "ok", "value_type": "list", "serialized": "[-0.0]"})
        if shutil.which("node"):
            self.assertEqual(run_transform.observe_node(path, "survey"),
                             {"status": "ok", "value_type": "array", "serialized": "[0]"})


if __name__ == "__main__":
    unittest.main()
