#!/usr/bin/env python3
"""Launch the pinned Java batch-three native observer without transforming input."""
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[3]
try:
    runtime=json.loads((ROOT/'parsers/.build/java_batch_03/runtime.json').read_text())
    code=subprocess.call([runtime['java'],'-cp',runtime['classpath'],'ObserveJavaBatch03']+sys.argv[1:])
except (OSError,ValueError,KeyError) as error:
    print('Adapter unavailable: '+str(error),file=sys.stderr);code=2
sys.exit(code)
