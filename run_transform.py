#!/usr/bin/env python3
"""Observe value and serialization behavior for transform fixtures."""

import json
import argparse
import math
import os
import subprocess
import sys

from parsers.chromium_browser import observe as observe_chromium


BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CASES = (
    ("number_positive_zero.json", "zero"),
    ("number_negative_zero.json", "zero"),
    ("object_case_distinct_keys.json", "keys"),
    ("object_case_distinct_keys_reversed.json", "keys"),
)


def observe_python(path, kind):
    try:
        with open(path, "rb") as stream:
            value = json.loads(stream.read().decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return {"status": "reject" if kind == "survey" and isinstance(error, (UnicodeError, json.JSONDecodeError)) else "error",
                "detail": str(error)}

    if kind == "survey":
        observation = {"value_type": type(value).__name__}
    elif kind == "zero":
        if not (isinstance(value, list) and len(value) == 1
                and isinstance(value[0], (int, float)) and not isinstance(value[0], bool)
                and value[0] == 0):
            return {"status": "error", "detail": "expected a one-element zero array"}
        observation = {"negative_zero": math.copysign(1.0, value[0]) < 0}
    else:
        if not isinstance(value, dict):
            return {"status": "error", "detail": "expected an object"}
        observation = {"members": list(value.items())}

    observation.update(status="ok", serialized=json.dumps(value, separators=(",", ":"), ensure_ascii=False))
    return observation


def observe_node(path, kind):
    command = ["node", os.path.join(BASE_DIR, "parsers", "observe_node_transform.js"), kind, path]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
    except FileNotFoundError:
        return {"status": "unavailable", "detail": "node is not installed"}
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    if result.returncode != 0:
        if kind == "survey" and result.returncode == 1:
            return {"status": "reject", "detail": result.stderr.strip()}
        return {"status": "error", "detail": result.stderr.strip(), "exit_code": result.returncode}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "error", "detail": "invalid observer output"}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="survey every transformation fixture")
    args = parser.parse_args(argv)
    cases = ((name, "survey") for name in sorted(os.listdir(os.path.join(BASE_DIR, "test_transform")))
             if name.endswith(".json")) if args.all else CASES
    failed = False
    for filename, kind in cases:
        path = os.path.join(BASE_DIR, "test_transform", filename)
        record = {
            "fixture": filename,
            "python": observe_python(path, kind),
            "node_v8": observe_node(path, kind),
            "chromium": observe_chromium(path, kind),
        }
        print(json.dumps(record, ensure_ascii=True, sort_keys=True))
        failed |= any(record[mode]["status"] in ("error", "timeout")
                      for mode in ("python", "node_v8", "chromium"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
