#!/usr/bin/env python3
"""List first-stage executables required by every registered parser mode."""

import json
import os
import shutil

from run_tests import programs


def executable(command):
    if not command:
        return None
    if os.path.basename(command[0]) == "env":
        return command[1] if len(command) > 1 else None
    return command[0]


def resolve(program):
    if program is None:
        return None
    if os.path.isabs(program) or "/" in program:
        return program if os.path.isfile(program) and os.access(program, os.X_OK) else None
    return shutil.which(program)


def main():
    modes = []
    for name, entry in sorted(programs.items()):
        program = executable(entry["commands"])
        modes.append({
            "name": name,
            "executable": program,
            "resolved": resolve(program),
            "setup": entry.get("setup"),
        })
    print(json.dumps({"modes": modes}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
