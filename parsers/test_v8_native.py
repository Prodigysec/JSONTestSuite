#!/usr/bin/env python3
"""Invoke the native V8 JSON parser on the original fixture bytes."""

import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
IMAGE = "jsonsuite-v8:local"


def main(argv):
    if len(argv) != 2:
        return 2
    path = pathlib.Path(argv[1]).resolve()
    try:
        relative = path.relative_to(ROOT)
        # V8's NewFromUtf8 replaces malformed sequences; reject them before
        # invoking the parser, without changing valid input bytes.
        path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return 1
    except (ValueError, OSError):
        return 2
    command = [
        "docker", "run", "--rm", "--network", "none", "--pull", "never",
        "--mount", f"type=bind,src={ROOT},dst=/suite,readonly",
        IMAGE, "timeout", "4s", "test_v8_native", f"/suite/{relative}",
    ]
    try:
        result = subprocess.run(command, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return 2
    return result.returncode if result.returncode in (0, 1) else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
