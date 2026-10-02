#!/bin/sh
base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$#" -ne 1 ] || [ ! -f "$1" ]; then
    exit 2
fi
tool=${FY_TOOL_BIN:-"$base_dir/.build/libfyaml-0.9.6/src/fy-tool"}
if [ ! -x "$tool" ]; then
    exit 2
fi
"$tool" --testsuite --streaming --json=force -- "$1" >/dev/null 2>/dev/null
status=$?
case "$status" in
    0|1) exit "$status" ;;
    *) exit 2 ;;
esac
