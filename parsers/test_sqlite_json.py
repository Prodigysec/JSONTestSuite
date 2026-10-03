#!/usr/bin/env python3
"""SQLite JSON1's default, strict JSON mode, on the fixture's original bytes."""

import sqlite3
import sys


def main():
    if len(sys.argv) != 2:
        return 2
    try:
        with open(sys.argv[1], "rb") as fixture:
            data = fixture.read()
        # SQLite's JSON text path can stop at a literal NUL (for example,
        # b"123\x00"), so reject this invalid JSON byte before binding it.
        if b"\x00" in data:
            return 1
        with sqlite3.connect(":memory:") as connection:
            # Binding a BLOB and casting inside SQLite avoids Python text decoding.
            result, = connection.execute(
                "SELECT json_valid(CAST(? AS TEXT))", (sqlite3.Binary(data),)
            ).fetchone()
    except (OSError, sqlite3.Error) as exc:
        print(exc, file=sys.stderr)
        return 2
    return 0 if result == 1 else 1


if __name__ == "__main__":
    sys.exit(main())
