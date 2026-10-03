#!/usr/bin/env python3
"""Survey parsing fixtures in one browser page, emitting every outcome as JSONL."""

import base64
import html
import json
import pathlib
import re
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parent
IMAGE = "jsonsuite-chromium:local"
RESULT = re.compile(r'<pre id="result">([^<]*)</pre>')


def main():
    files = sorted((ROOT / "test_parsing").glob("*.json"))
    cases = [[path.name, base64.b64encode(path.read_bytes()).decode("ascii")] for path in files]
    script = """
const cases = __CASES__;
const results = [];
for (const [name, payload] of cases) {
    try {
        const bytes = Uint8Array.from(atob(payload), char => char.charCodeAt(0));
        const text = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes);
        JSON.parse(text);
        results.push([name, 0]);
    } catch (error) {
        results.push([name, error instanceof SyntaxError || error instanceof TypeError ? 1 : 2]);
    }
}
document.getElementById('result').textContent = 'JSONTESTSUITE:' + JSON.stringify(results);
""".replace("__CASES__", json.dumps(cases))
    with tempfile.TemporaryDirectory(prefix="jsonsuite-chromium-survey-") as directory:
        page = pathlib.Path(directory, "survey.html")
        page.write_text('<!doctype html><meta charset="utf-8"><pre id="result"></pre><script>'
                        + script + '</script>', encoding="utf-8")
        command = [
            "docker", "run", "--rm", "--network", "none", "--pull", "never",
            "--mount", f"type=bind,src={directory},dst=/probe,readonly", IMAGE,
            "timeout", "30s", "chromium", "--headless", "--no-sandbox", "--disable-gpu",
            "--disable-dev-shm-usage", "--no-first-run", "--disable-background-networking",
            "--dump-dom", "file:///probe/survey.html",
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=35)
        except (OSError, subprocess.TimeoutExpired) as error:
            print(f"browser invocation failed: {error}", file=sys.stderr)
            return 2
    if result.returncode != 0:
        print(f"browser exited {result.returncode}", file=sys.stderr)
        return 2
    match = RESULT.search(result.stdout)
    if match is None:
        print("browser result marker missing", file=sys.stderr)
        return 2
    marker = html.unescape(match.group(1))
    if not marker.startswith("JSONTESTSUITE:"):
        print("browser result marker malformed", file=sys.stderr)
        return 2
    try:
        rows = json.loads(marker[len("JSONTESTSUITE:"):])
    except ValueError:
        print("browser result JSON malformed", file=sys.stderr)
        return 2
    if len(rows) != len(files) or [row[0] for row in rows] != [path.name for path in files]:
        print("browser result rows incomplete or out of order", file=sys.stderr)
        return 2
    for name, status in rows:
        print(json.dumps({"fixture": name, "exit_code": status}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
