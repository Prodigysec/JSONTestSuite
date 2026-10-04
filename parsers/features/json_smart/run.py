#!/usr/bin/env python3
"""Invoke the audited json-smart source build; unavailable build is an adapter failure."""
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[3]
try:
    runtime=json.loads((ROOT/'parsers/.build/json_smart/runtime.json').read_text())
    sys.exit(subprocess.call([runtime['java'],'-cp',runtime['classpath'],'ObserveJsonSmart']+sys.argv[1:]))
except (OSError,ValueError,KeyError) as error:
    print(str(error),file=sys.stderr);sys.exit(2)
