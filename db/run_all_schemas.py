"""Run all Phase 1 schema and seed SQL files in the required order."""

from __future__ import annotations

import sys
from pathlib import Path

from run_sql import execute_sql_file


ROOT = Path(__file__).resolve().parent.parent
DB_ROOT = ROOT / "db"


def ordered_canonical_files() -> list[Path]:
    canonical_dir = DB_ROOT / "schemas" / "canonical"
    files = sorted(canonical_dir.glob("*.sql"), key=lambda path: path.name.lower())
    patient_file = canonical_dir / "patient.sql"
    if patient_file in files:
        files.remove(patient_file)
        files.insert(0, patient_file)
    return files


def build_sql_order() -> list[Path]:
    sql_files = [
        DB_ROOT / "schemas" / "create_schemas.sql",
        DB_ROOT / "schemas" / "ref" / "reference_tables.sql",
        *ordered_canonical_files(),
        DB_ROOT / "schemas" / "raw" / "raw_tables.sql",
        DB_ROOT / "schemas" / "staging" / "staging_tables.sql",
        DB_ROOT / "schemas" / "audit" / "audit_tables.sql",
        DB_ROOT / "seeds" / "seed_reference_data.sql",
    ]
    return sql_files


def main() -> int:
    try:
        sql_files = build_sql_order()
        print("Running schema setup...")
        for sql_file in sql_files:
            print(f" -> {sql_file.relative_to(ROOT)}")
            execute_sql_file(sql_file)
        print("Schema setup completed successfully.")
        return 0
    except Exception as exc:
        print(f"Schema setup failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
