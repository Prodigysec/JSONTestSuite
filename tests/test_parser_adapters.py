"""Contract checks for optional source-built adapters; no automatic downloads."""

from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
JSONPP = ROOT / 'parsers/test_jsonpp_0_1_1/.build/test_jsonpp'
OPACK = ROOT / 'parsers/test_java_opack_0_2_1/.build/classes'
NEWTONSOFT = ROOT / 'parsers/test_dotnet_newtonsoft/bin/Release/net5.0/app.dll'
FASTJSON2 = ROOT / 'parsers/test_java_fastjson2_2_0_53/.build'
JSONCGX = ROOT / 'parsers/test_jsoncgx_1_1/.build/jsoncgx-1.1'
CLOJURE = ROOT / 'parsers/test_clojure_data_json/.build'
RL_JSON = ROOT / 'parsers/test_rl_json_0_17_6'
LIBFYAML = ROOT / 'parsers/test_libfyaml_0_9_6'


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


@unittest.skipUnless(shutil.which('tclsh') and
                     (RL_JSON / '.build/rl_json-v0.17.6/rl_json0.17.6.so').is_file(),
                     'Build rl_json and provide tclsh on PATH first')
class RlJsonTests(unittest.TestCase):
    command = ['python3', str(RL_JSON / 'TestJSONParsing.py')]

    def test_strict_bytes_comments_and_complete_text(self):
        cases = [(b'null', 0), (b'false', 0), (b'0', 0),
                 (b'"\xe2\x82\xac"', 0), (b'{} garbage', 1),
                 (b'{} {}', 1), (b'// comment\n{}', 1),
                 (b'"\xff"', 1), (b'"\xed\xa0\x80"', 1)]
        for data, expected in cases:
            with self.subTest(data=data):
                result = subprocess.run(self.command, input=data,
                                        capture_output=True, timeout=5)
                self.assertEqual(result.returncode, expected, result.stderr)

    def test_missing_package_is_not_rejection_even_for_malformed_bytes(self):
        env = os.environ.copy()
        env['RL_JSON_PACKAGE_DIR'] = '/nonexistent-rl-json-package'
        for data in (b'null', b'"\xff"'):
            with self.subTest(data=data):
                result = subprocess.run(self.command, input=data, env=env,
                                        capture_output=True, timeout=5)
                self.assertEqual(result.returncode, 2, result.stderr)


@unittest.skipUnless((LIBFYAML / '.build/libfyaml-0.9.6/src/fy-tool').is_file(),
                     'Build the optional libfyaml adapter first')
class LibfyamlTests(AdapterContract, unittest.TestCase):
    command = ['sh', str(LIBFYAML / 'run.sh')]

    def test_comment_and_malformed_utf8_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input with space.json'
            for data in (b'// comment\n{}', b'"\xff"'):
                with self.subTest(data=data):
                    path.write_bytes(data)
                    self.assertEqual(self.invoke([str(path)]).returncode, 1)


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


@unittest.skipUnless(shutil.which('java') and
                     (FASTJSON2 / 'classes/TestJSONParsing.class').is_file() and
                     (FASTJSON2 / 'fastjson2-2.0.53.jar').is_file(),
                     'Build fastjson2 and provide java on PATH first')
class Fastjson2Tests(AdapterContract, unittest.TestCase):
    command = [shutil.which('java'), '-cp',
               str(FASTJSON2 / 'classes') + ':' + str(FASTJSON2 / 'fastjson2-2.0.53.jar'),
               'TestJSONParsing']

    def test_native_comment_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_bytes(b'/* comment */ {}')
            self.assertEqual(self.invoke([str(path)]).returncode, 0)


class JSONcgxContract(AdapterContract):
    def test_comment_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_bytes(b'/* comment */ {}')
            expected = 0 if self.mode == 'on' else 1
            self.assertEqual(self.invoke([str(path)]).returncode, expected)

    def test_missing_pinned_source_is_not_json_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = Path(directory) / 'TestJSONParsing.py'
            shutil.copy2(ROOT / 'parsers/test_jsoncgx_1_1/TestJSONParsing.py', adapter)
            result = subprocess.run(['python3', str(adapter), self.mode,
                                     str(ROOT / 'test_parsing/y_structure_lonely_null.json')],
                                    capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 2, result.stderr)


@unittest.skipUnless(JSONCGX.is_dir(), 'Prepare pinned jsoncgx 1.1 first')
class JSONcgxCommentsOffTests(JSONcgxContract, unittest.TestCase):
    mode = 'off'
    command = ['python3', str(ROOT / 'parsers/test_jsoncgx_1_1/TestJSONParsing.py'), mode]


@unittest.skipUnless(JSONCGX.is_dir(), 'Prepare pinned jsoncgx 1.1 first')
class JSONcgxCommentsOnTests(JSONcgxContract, unittest.TestCase):
    mode = 'on'
    command = ['python3', str(ROOT / 'parsers/test_jsoncgx_1_1/TestJSONParsing.py'), mode]


class ClojureDataJsonContract(AdapterContract):
    def test_parser_errors_are_distinguished(self):
        for name, expected in (('n_string_octal_escape.json', 1),
                               ('n_structure_open_open.json', 1),
                               ('n_structure_open_array_object.json', 2)):
            with self.subTest(name=name):
                result = self.invoke([str(ROOT / 'test_parsing' / name)])
                self.assertEqual(result.returncode, expected, result.stderr[:500])


@unittest.skipUnless(shutil.which('java') and
                     (CLOJURE / 'clojure-1.10.1.jar').is_file() and
                     (CLOJURE / 'data.json-1.0.0.jar').is_file() and
                     (CLOJURE / 'classes/1.0.0/jsonsuite/adapter__init.class').is_file(),
                     'Prepare Clojure jars and provide java on PATH first')
class ClojureDataJson1Tests(ClojureDataJsonContract, unittest.TestCase):
    command = ['sh', str(ROOT / 'parsers/test_clojure_data_json/run.sh'), '1.0.0']


@unittest.skipUnless(shutil.which('java') and
                     (CLOJURE / 'clojure-1.10.1.jar').is_file() and
                     (CLOJURE / 'data.json-2.2.0.jar').is_file() and
                     (CLOJURE / 'classes/2.2.0/jsonsuite/adapter__init.class').is_file(),
                     'Prepare Clojure jars and provide java on PATH first')
class ClojureDataJson2Tests(ClojureDataJsonContract, unittest.TestCase):
    command = ['sh', str(ROOT / 'parsers/test_clojure_data_json/run.sh'), '2.2.0']


if __name__ == '__main__':
    unittest.main()
