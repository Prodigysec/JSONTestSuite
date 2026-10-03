#!/usr/bin/env python3
"""Run one complete JSON text through Firefox's browser JSON.parse."""

import json
import pathlib
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


SCRIPT = "try { JSON.parse(arguments[0]); return true; } catch (error) { if (error instanceof SyntaxError) return false; throw error; }"


def request(base, method, path, data=None):
    body = None if data is None else json.dumps(data).encode("utf-8")
    # Creating a browser session can exceed 10 seconds during concurrent runs.
    with urllib.request.urlopen(urllib.request.Request(
            base + path, data=body, method=method,
            headers={"Content-Type": "application/json"}), timeout=25) as response:
        return json.load(response)


def main(argv):
    survey = len(argv) == 3 and argv[1] == "--survey"
    if len(argv) != 2 and not survey:
        return 2
    try:
        root = pathlib.Path(argv[-1])
        paths = sorted(root.rglob("*.json")) if survey else [root]
        if not paths:
            return 2
    except OSError:
        return 2
    if not survey:
        try:
            source = root.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            return 1
        except OSError:
            return 2
    try:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
    except OSError:
        return 2
    base = f"http://127.0.0.1:{port}"
    try:
        driver = subprocess.Popen(["geckodriver", "--port", str(port)],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return 2
    session = None
    failed = False
    try:
        deadline = time.monotonic() + 5
        while True:
            try:
                request(base, "GET", "/status")
                break
            except urllib.error.URLError:
                if driver.poll() is not None or time.monotonic() >= deadline:
                    return 2
                time.sleep(0.05)
        response = request(base, "POST", "/session", {
            "capabilities": {"alwaysMatch": {
                "browserName": "firefox", "moz:firefoxOptions": {"args": ["-headless"]}}}})
        session = response["value"]["sessionId"]
        for path in paths:
            if survey:
                try:
                    source = path.read_bytes().decode("utf-8")
                except UnicodeDecodeError:
                    print(f"{path.relative_to(root)}\t1", flush=True)
                    continue
            result = request(base, "POST", f"/session/{session}/execute/sync",
                             {"script": SCRIPT, "args": [source]})
            verdict = 0 if result["value"] is True else 1 if result["value"] is False else 2
            if survey:
                print(f"{path.relative_to(root)}\t{verdict}", flush=True)
                failed |= verdict == 2
            else:
                return verdict
        return 2 if failed else 0
    except (OSError, ValueError, KeyError, TypeError, urllib.error.URLError):
        return 2
    finally:
        if session is not None:
            try:
                request(base, "DELETE", f"/session/{session}")
            except (OSError, ValueError):
                pass
        driver.terminate()
        try:
            driver.wait(timeout=2)
        except subprocess.TimeoutExpired:
            driver.kill()
            driver.wait()


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception:
        sys.exit(2)
