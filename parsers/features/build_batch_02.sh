#!/bin/sh
set -eu
project_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
python3 -B "$project_root/tools/build_go_feature_batch.py" 02
python3 -B "$project_root/tools/build_json_smart_features.py"
