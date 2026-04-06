"""Run a SQL file against PostgreSQL."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg2


DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/cancer360"


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def execute_sql_file(sql_file: Path, database_url: str | None = None) -> None:
    if not sql_file.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file}")

    sql_text = sql_file.read_text(encoding="utf-8")
    conn = None
    try:
        conn = psycopg2.connect(database_url or get_database_url())
        conn.autocommit = False
        with conn.cursor() as cursor:
            cursor.execute(sql_text)
        conn.commit()
        print(f"[OK] Executed: {sql_file}")
    except Exception as exc:
        if conn is not None:
            conn.rollback()
        print(f"[ERROR] Failed: {sql_file}")
        print(str(exc))
        raise
    finally:
        if conn is not None:
            conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute a SQL file against PostgreSQL.")
    parser.add_argument("sql_file", help="Path to the SQL file to execute.")
    args = parser.parse_args()

    try:
        execute_sql_file(Path(args.sql_file).resolve())
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    sys.exit(main())
