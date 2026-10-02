"""Ruby adapter regressions; skipped when no Ruby executable is available."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUBY = shutil.which('ruby') or shutil.which('ruby3.2')


@unittest.skipUnless(RUBY, 'Ruby runtime is not installed')
class RubyAdapterTests(unittest.TestCase):
    def parse(self, content):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / 'input.json'
            fixture.write_bytes(content)
            return subprocess.run(
                [RUBY, str(ROOT / 'parsers/test_json.rb'), str(fixture)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5,
            )

    def test_accepts_scalars_and_containers(self):
        # RFC 8259 sections 2 and 3 permit scalar JSON texts, including null.
        for content in (b'null', b'false', b'true', b'0', b'""', b'[]', b'{}'):
            with self.subTest(content=content):
                result = self.parse(content)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_invalid_syntax_and_trailing_input(self):
        for content in (b'', b'[1,]', b'null false', b'{} garbage',
                        b'"a\x00b"', b'\xff', b'[\xff]'):
            with self.subTest(content=content):
                result = self.parse(content)
                self.assertEqual(result.returncode, 1, result.stderr)
                # A Ruby runtime failure also exits 1; require a parse diagnostic.
                self.assertEqual(result.stderr, b'')
                self.assertGreater(len(result.stdout.splitlines()), 1)

    def test_implementation_dependent_cases_do_not_crash(self):
        for name in ('i_string_invalid_utf-8.json', 'i_string_lone_second_surrogate.json',
                     'i_number_huge_exp.json', 'i_structure_500_nested_arrays.json'):
            with self.subTest(name=name):
                result = self.parse((ROOT / 'test_parsing' / name).read_bytes())
                self.assertIn(result.returncode, (0, 1), result.stderr)
                self.assertEqual(result.stderr, b'')


if __name__ == '__main__':
    unittest.main()
