"""Run the original fixture bytes through headless Chromium JSON.parse."""

import base64
import html
import json
import pathlib
import re
import shutil
import subprocess
import tempfile


IMAGE = "jsonsuite-chromium:local"
TEMPLATE = pathlib.Path(__file__).with_name("chromium_probe.html")
RESULT = re.compile(r'<pre id="result">([^<]*)</pre>')


def observe(path, mode="parse"):
    if mode not in ("parse", "zero", "keys", "survey"):
        return {"status": "error", "detail": "unknown probe mode"}
    try:
        payload = base64.b64encode(pathlib.Path(path).read_bytes()).decode("ascii")
    except OSError as error:
        return {"status": "error", "detail": str(error)}
    if not shutil.which("docker"):
        return {"status": "unavailable", "detail": "docker is not installed"}
    try:
        image_check = subprocess.run(["docker", "image", "inspect", IMAGE],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "unavailable", "detail": "Docker image check failed"}
    if image_check.returncode != 0:
        return {"status": "unavailable", "detail": "Chromium image is not built"}
    source = TEMPLATE.read_text(encoding="utf-8")
    page = source.replace("__PAYLOAD__", payload).replace("__MODE__", mode)
    with tempfile.TemporaryDirectory(prefix="jsonsuite-chromium-") as directory:
        probe = pathlib.Path(directory, "probe.html")
        probe.write_text(page, encoding="utf-8")
        command = [
            "docker", "run", "--rm", "--network", "none", "--pull", "never",
            "--mount", f"type=bind,src={directory},dst=/probe,readonly",
            IMAGE, "timeout", "4s", "chromium", "--headless", "--no-sandbox",
            "--disable-gpu", "--disable-dev-shm-usage", "--no-first-run",
            "--disable-background-networking", "--dump-dom", "file:///probe/probe.html",
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            return {"status": "error", "detail": "browser invocation failed or timed out"}
    if result.returncode != 0:
        return {"status": "error", "detail": f"browser exited {result.returncode}"}
    match = RESULT.search(result.stdout)
    if match is None:
        return {"status": "error", "detail": "browser result marker missing"}
    marker = html.unescape(match.group(1))
    if not marker.startswith("JSONTESTSUITE:"):
        return {"status": "error", "detail": "browser result marker malformed"}
    try:
        return json.loads(marker[len("JSONTESTSUITE:"):])
    except ValueError:
        return {"status": "error", "detail": "browser result marker malformed"}
