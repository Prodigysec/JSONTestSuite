#!/usr/bin/env python3
"""Run JavaScriptCore JSON.parse on an unchanged, strictly decoded fixture."""

import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
IMAGE = "jsonsuite-jsc:local"


def main(argv):
    if len(argv) != 2:
        return 2
    path = pathlib.Path(argv[1]).resolve()
    try:
        relative = path.relative_to(ROOT)
        path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return 1
    except (ValueError, OSError):
        return 2

    command = [
        "docker", "run", "--rm", "--network", "none", "--pull", "never",
        "--mount", f"type=bind,src={ROOT},dst=/suite,readonly",
        IMAGE, "timeout", "4s", "jsc", "/suite/parsers/test_jsc.js", "--", f"/suite/{relative}",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return 2
    if result.returncode != 0:
        return 2
    return {"JSONTESTSUITE_ACCEPT": 0, "JSONTESTSUITE_REJECT": 1}.get(result.stdout.strip(), 2)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
