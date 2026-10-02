#!/usr/bin/env python3
"""Run pinned jsoncgx 1.1 in a specified JSON or JSONC mode."""

from pathlib import Path
import sys


def main(argv):
    if len(argv) != 3 or argv[1] not in ('off', 'on'):
        print('Usage: TestJSONParsing.py off|on FILE', file=sys.stderr)
        return 2

    source = Path(__file__).resolve().parent / '.build/jsoncgx-1.1'
    if not (source / 'jsoncgx/__init__.py').is_file():
        print('Missing pinned jsoncgx 1.1 source; run build.sh', file=sys.stderr)
        return 2
    sys.path.insert(0, str(source))
    try:
        import jsoncgx
    except Exception as error:
        print(error, file=sys.stderr)
        return 2

    try:
        data = Path(argv[2]).read_bytes()
    except OSError as error:
        print(error, file=sys.stderr)
        return 2

    try:
        text = data.decode('utf-8')
        if not text or all(char in ' \t\r\n' for char in text):
            return 1
        jsoncgx.loads(text, name=argv[2], allow_comments=(argv[1] == 'on'))
        return 0
    except (UnicodeDecodeError, jsoncgx.LexCeption, jsoncgx.ParseXception) as error:
        print(error, file=sys.stderr)
        return 1
    except Exception as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
