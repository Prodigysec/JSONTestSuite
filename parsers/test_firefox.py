#!/usr/bin/env python3
"""Invoke headless Firefox JSON.parse through the pinned WebDriver image."""

import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
IMAGE = "jsonsuite-firefox:local"


def main(argv):
    if len(argv) != 2:
        return 2
    path = pathlib.Path(argv[1]).resolve()
    try:
        relative = path.relative_to(ROOT)
        if not path.is_file():
            return 2
    except (OSError, ValueError):
        return 2
    command = [
        "docker", "run", "--rm", "--network", "none", "--pull", "never",
        "--mount", f"type=bind,src={ROOT},dst=/suite,readonly",
        IMAGE, "timeout", "40s", "python3", "/usr/local/bin/firefox_probe.py",
        f"/suite/{relative}",
    ]
    try:
        result = subprocess.run(command, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=42)
    except (OSError, subprocess.TimeoutExpired):
        return 2
    return result.returncode if result.returncode in (0, 1) else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
