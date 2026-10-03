#!/usr/bin/env python3
"""Validate raw fixture bytes with PostgreSQL's JSONB input parser."""

import os
import sys


REJECTION_CODES = {
    "22P02",  # invalid_text_representation: JSON syntax
    "22021",  # character_not_in_repertoire: invalid UTF-8
    "22P05",  # untranslatable_character: \u0000
    "22003",  # numeric_value_out_of_range: JSONB numeric limit
    "54001",  # statement_too_complex: nesting limit
}


def main():
    if len(sys.argv) != 2:
        return 2
    check_only = sys.argv[1] == "--check"
    dsn = os.environ.get("JSONTESTSUITE_POSTGRES_DSN")
    if not dsn:
        print("JSONTESTSUITE_POSTGRES_DSN is required", file=sys.stderr)
        return 2
    try:
        import psycopg2
    except ImportError as exc:
        print(exc, file=sys.stderr)
        return 2
    try:
        if not check_only:
            with open(sys.argv[1], "rb") as fixture:
                data = fixture.read()
        with psycopg2.connect(dsn, connect_timeout=2) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SHOW server_encoding")
                if cursor.fetchone()[0] != "UTF8":
                    print("PostgreSQL database must use UTF8", file=sys.stderr)
                    return 2
                cursor.execute("SHOW server_version_num")
                version = int(cursor.fetchone()[0])
                if not 160000 <= version < 170000:
                    print("PostgreSQL 16 is required for this mode", file=sys.stderr)
                    return 2
                # bytea preserves the fixture bytes. PostgreSQL converts to
                # UTF-8 text and then invokes its JSONB parser on the whole text.
                if not check_only:
                    cursor.execute(
                        "SELECT convert_from(%s, 'UTF8')::jsonb",
                        (psycopg2.Binary(data),),
                    )
    except (OSError, MemoryError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 2
    except psycopg2.Error as exc:
        if exc.pgcode in REJECTION_CODES:
            return 1
        print(exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
