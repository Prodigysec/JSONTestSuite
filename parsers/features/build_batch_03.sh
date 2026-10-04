#!/bin/sh
set -eu
repo=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
exec python3 -B "$repo/tools/build_java_feature_batch_03.py"
