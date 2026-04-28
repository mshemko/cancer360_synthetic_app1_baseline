"""Upsert canonical records into PostgreSQL."""

from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from typing import Any

from psycopg2 import sql
from psycopg2.extras import RealDictCursor


def build_person_lookup(connection) -> dict[str, str]:
    lookup: dict[str, str] = {}
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT person_id, nhs_number, mrn FROM canonical.patient")
        for row in cursor.fetchall():
            if row["nhs_number"]:
                lookup[str(row["nhs_number"])] = row["person_id"]
            if row["mrn"]:
                lookup[str(row["mrn"])] = row["person_id"]
    return lookup


def _existing_ids(schema_name: str, table_name: str, pk_column: str, connection) -> set[str]:
    query = sql.SQL("SELECT {pk} FROM {table}").format(
        pk=sql.Identifier(pk_column),
        table=sql.Identifier(schema_name, table_name),
    )
    with connection.cursor() as cursor:
        cursor.execute(query)
        return {str(row[0]) for row in cursor.fetchall() if row[0] is not None}


def _upsert_records(
    table_name: str,
    pk_column: str,
    records: list[dict[str, Any]],
    connection,
) -> int:
    if not records:
        return 0

    columns = list(records[0].keys())
    update_columns = [column for column in columns if column != pk_column]
    statement = sql.SQL(
        """
        INSERT INTO {table} ({columns})
        VALUES ({values})
        ON CONFLICT ({pk_column}) DO UPDATE
        SET {updates}, updated_at = NOW()
        """
    ).format(
        table=sql.Identifier("canonical", table_name),
        columns=sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        values=sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        pk_column=sql.Identifier(pk_column),
        updates=sql.SQL(", ").join(
            sql.SQL("{col} = EXCLUDED.{col}").format(col=sql.Identifier(column))
            for column in update_columns
        ),
    )

    with connection.cursor() as cursor:
        for record in records:
            cursor.execute(statement, [record.get(column) for column in columns])
    connection.commit()
    return len(records)


def upsert_patients(records: list[dict[str, Any]], connection) -> int:
    return _upsert_records("patient", "person_id", records, connection)


def upsert_pathways(records: list[dict[str, Any]], connection) -> int:
    return _upsert_records("cancer_pathway", "pathway_id", records, connection)


def upsert_radiology(records: list[dict[str, Any]], connection) -> int:
    return _upsert_records("radiology", "radiology_exam_id", records, connection)


def upsert_histology(records: list[dict[str, Any]], connection) -> int:
    return _upsert_records("histology", "histology_id", records, connection)


def upsert_test_results(records: list[dict[str, Any]], connection) -> int:
    return _upsert_records("test_result", "test_result_id", records, connection)


def upsert_treatments(records: list[dict[str, Any]], connection) -> int:
    appointment_ids = _existing_ids("canonical", "outpatient_appointment", "attendance_id", connection)
    prepared_records: list[dict[str, Any]] = []
    for record in records:
        prepared = dict(record)
        poa_attendance_id = prepared.get("poa_attendance_id")
        if poa_attendance_id and str(poa_attendance_id) not in appointment_ids:
            prepared["poa_attendance_id"] = None
        prepared_records.append(prepared)
    return _upsert_records("cancer_treatment", "cancer_treatment_id", prepared_records, connection)
