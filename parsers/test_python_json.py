#!/usr/bin/env python3
"""Test this interpreter's json decoder with explicit UTF-8 input."""

import json
from pathlib import Path
import sys


def reject_constant(value):
    raise ValueError("Nonfinite constant: " + value)


def main(argv):
    arguments = argv[1:]
    reject_nonfinite = arguments[:1] == ["--reject-nonfinite"]
    if reject_nonfinite:
        arguments = arguments[1:]
    if len(arguments) != 1:
        return 2
    try:
        raw = Path(arguments[0]).read_bytes()
    except Exception:
        return 2
    try:
        text = raw.decode("utf-8", errors="strict")
        options = {"parse_constant": reject_constant} if reject_nonfinite else {}
        json.loads(text, **options)
    except (ValueError, RecursionError):
        # JSON syntax, malformed UTF-8, configured constant policy, or limits.
        return 1
    except Exception:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
