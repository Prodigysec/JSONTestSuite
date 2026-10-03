#!/usr/bin/env python3
"""Parser adapter for Chromium's browser-context JSON.parse."""

import sys

if __package__:
    from .chromium_browser import observe
else:
    from chromium_browser import observe


def main(argv):
    if len(argv) != 2:
        return 2
    status = observe(argv[1])["status"]
    return {"ok": 0, "reject": 1}.get(status, 2)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
