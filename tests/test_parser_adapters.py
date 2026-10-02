"""Contract checks for optional source-built adapters; no automatic downloads."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
JSONPP = ROOT / 'parsers/test_jsonpp_0_1_1/.build/test_jsonpp'
OPACK = ROOT / 'parsers/test_java_opack_0_2_1/.build/classes'
NEWTONSOFT = ROOT / 'parsers/test_dotnet_newtonsoft/bin/Release/net5.0/app.dll'


class AdapterContract:
    def invoke(self, arguments):
        return subprocess.run(self.command + arguments, capture_output=True, timeout=5)

    def test_scalars_containers_and_rejection(self):
        cases = [(value, 0) for value in
                 (b'null', b'false', b'0', b'""', b'[]', b'{}')]
        cases += [(value, 1) for value in
                  (b'', b' \r\n\t', b'{', b'{} garbage', b'null false', b'\xff')]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            for content, expected in cases:
                with self.subTest(content=content):
                    path.write_bytes(content)
                    result = self.invoke([str(path)])
                    self.assertEqual(result.returncode, expected, result.stderr)

    def test_invocation_errors_are_not_json_rejections(self):
        with tempfile.TemporaryDirectory() as directory:
            for arguments in ([], [str(Path(directory) / 'missing.json')]):
                with self.subTest(arguments=arguments):
                    result = self.invoke(arguments)
                    self.assertEqual(result.returncode, 2, result.stderr)


@unittest.skipUnless(JSONPP.is_file(), 'Build the optional JSONpp adapter first')
class JSONppTests(AdapterContract, unittest.TestCase):
    command = [str(JSONPP)]


@unittest.skipUnless(shutil.which('java') and (OPACK / 'TestJSONParsing.class').is_file(),
                     'Build opack and provide java on PATH first')
class OpackTests(AdapterContract, unittest.TestCase):
    command = [shutil.which('java'), '-cp', str(OPACK), 'TestJSONParsing']

    def test_numeric_rejection_and_unexpected_parser_failure(self):
        for name, expected in (('n_number_-01.json', 1),
                               ('i_number_huge_exp.json', 1),
                               ('n_incomplete_false.json', 2)):
            with self.subTest(name=name):
                result = self.invoke([str(ROOT / 'test_parsing' / name)])
                self.assertEqual(result.returncode, expected, result.stderr)

    def test_utf8_input_is_not_repaired(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            for content in (b'"\xff"', b'\xef\xbb\xbf{}', b'\xff\xfe{\x00}\x00'):
                with self.subTest(content=content):
                    path.write_bytes(content)
                    result = self.invoke([str(path)])
                    self.assertEqual(result.returncode, 1, result.stderr)


@unittest.skipUnless(shutil.which('dotnet') and NEWTONSOFT.is_file(),
                     'Build Newtonsoft.Json and provide dotnet on PATH first')
class NewtonsoftTests(AdapterContract, unittest.TestCase):
    command = [shutil.which('dotnet'), str(NEWTONSOFT)]

    def test_invalid_utf8_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_bytes(b'"\xff"')
            result = self.invoke([str(path)])
            self.assertEqual(result.returncode, 1, result.stderr)


if __name__ == '__main__':
    unittest.main()
