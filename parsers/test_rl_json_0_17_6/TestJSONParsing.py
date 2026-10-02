#!/usr/bin/env python3
"""Supply UTF-8 characters to rl_json's Tcl API without repairing bad bytes."""

import os
from pathlib import Path
import subprocess
import sys


def main():
    if len(sys.argv) != 1:
        return 2
    raw = sys.stdin.buffer.read()
    malformed_utf8 = False
    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        # Probe a known-valid scalar so a missing Tcl package remains an
        # adapter error even when the fixture itself has malformed UTF-8.
        malformed_utf8 = True
        source = "null"

    package_dir = Path(os.environ.get(
        "RL_JSON_PACKAGE_DIR",
        Path(__file__).resolve().parent / ".build" / "rl_json-v0.17.6",
    ))
    if not (package_dir / "pkgIndex.tcl").is_file():
        return 2
    script = Path(__file__).with_name("validate.tcl")
    try:
        result = subprocess.run(
            [os.environ.get("TCLSH", "tclsh"), str(script), str(package_dir)],
            input=source.encode("utf-8"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return 2
    if result.returncode not in (0, 1) or (malformed_utf8 and result.returncode != 0):
        return 2
    return 1 if malformed_utf8 else result.returncode


if __name__ == "__main__":
    sys.exit(main())
