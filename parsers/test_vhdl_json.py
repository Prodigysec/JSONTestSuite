#!/usr/bin/env python3
"""Run the pinned JSON-for-VHDL parser in GHDL and map its result markers."""

import os
from pathlib import Path
import shutil
import subprocess
import sys


BUILD_DIR = Path(__file__).resolve().parent / ".build" / "vhdl-json"


def main():
    if len(sys.argv) != 2:
        return 2
    ghdl = shutil.which(os.environ.get("JSONTESTSUITE_GHDL", "ghdl"))
    if ghdl is None or not (BUILD_DIR / "work-obj08.cf").is_file():
        return 2
    if sys.argv[1] == "--check":
        version = subprocess.run([ghdl, "--version"], capture_output=True, text=True)
        return 0 if version.returncode == 0 and version.stdout.startswith("GHDL 4.1.") else 2
    path = Path(sys.argv[1]).resolve()
    try:
        # T_JSON.Content is indexed by a 16-bit count in the pinned source.
        if path.stat().st_size >= 65535:
            return 1
        run = subprocess.run(
            [ghdl, "-r", "--std=08", "JSONSuiteVHDL", "-gG_FILENAME=" + str(path)],
            cwd=BUILD_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, errors="replace",
        )
    except OSError as exc:
        print(exc, file=sys.stderr)
        return 2
    if run.returncode != 0:
        print(run.stdout, file=sys.stderr)
        return 2
    markers = [line.rsplit(": ", 1)[-1] for line in run.stdout.splitlines()
               if "test_vhdl_json.vhdl:" in line and "(report note): " in line]
    if markers == ["JSONTESTSUITE_VHDL_ACCEPT"]:
        return 0
    if markers == ["JSONTESTSUITE_VHDL_REJECT"]:
        return 1
    print(run.stdout, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
