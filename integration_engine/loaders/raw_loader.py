"""Load raw source payloads into the raw schema."""

from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

import csv
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from integration_engine import config
from integration_engine.error_handler import log_error


logger = logging.getLogger(__name__)


def _derive_csv_message_type(filepath: Path) -> str:
    mapping = {
        "pas_patients": "PAS_PATIENT",
        "pas_appointments": "PAS_APPOINTMENT",
        "pas_encounters": "PAS_ENCOUNTER",
        "sact_treatments": "SACT_TREATMENT",
        "endoscopy_exams": "ENDOSCOPY_EXAM",
        "ipt_referrals": "IPT_REFERRAL",
        "tracking_comments": "TRACKING_COMMENT",
    }
    return mapping.get(filepath.stem.lower(), filepath.stem.upper())


def _extract_msh_value(payload_text: str, position: int) -> str:
    first_line = next((line for line in payload_text.splitlines() if line.startswith("MSH|")), "")
    fields = first_line.split("|")
    return fields[position] if len(fields) > position else ""


def _mark_loaded(table: str, row_id: int, connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE {table} SET processing_status = %s WHERE id = %s", ("loaded", row_id))
    connection.commit()


def get_raw_row_metadata(table: str, row_id: int, connection) -> dict[str, str] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT correlation_id, source_system, message_type, file_name FROM {table} WHERE id = %s",
            (row_id,),
        )
        row = cursor.fetchone()
    if not row:
        return None
    return {
        "correlation_id": row[0],
        "source_system": row[1],
        "message_type": row[2],
        "file_name": row[3],
    }


def load_hl7_file(filepath: str, connection) -> int | None:
    path = Path(filepath)
    try:
        payload = path.read_text(encoding="utf-8")
        source_system = _extract_msh_value(payload, 2) or "UNKNOWN"
        message_type = _extract_msh_value(payload, 8) or "UNKNOWN"
        correlation_id = str(uuid.uuid4())
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO raw.hl7_message (
                    source_system,
                    message_type,
                    payload_text,
                    file_name,
                    received_at,
                    correlation_id,
                    processing_status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    source_system,
                    message_type,
                    payload,
                    path.name,
                    datetime.now(),
                    correlation_id,
                    "received",
                ),
            )
            row_id = cursor.fetchone()[0]
        connection.commit()
        _mark_loaded("raw.hl7_message", row_id, connection)
        return row_id
    except Exception as exc:
        connection.rollback()
        logger.error("Failed to load HL7 file %s: %s", path, exc)
        log_error("UNKNOWN", None, "RAW_HL7_LOAD", str(exc), str(path))
        return None


def load_csv_file(filepath: str, source_system: str, connection) -> list[int]:
    path = Path(filepath)
    inserted_ids: list[int] = []
    correlation_id = str(uuid.uuid4())
    message_type = _derive_csv_message_type(path)
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                payload_text = json.dumps({(key or "").strip(): (value or "").strip() for key, value in row.items()})
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO raw.csv_extract (
                            source_system,
                            message_type,
                            payload_text,
                            file_name,
                            received_at,
                            correlation_id,
                            processing_status
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            source_system,
                            message_type,
                            payload_text,
                            path.name,
                            datetime.now(),
                            correlation_id,
                            "received",
                        ),
                    )
                    row_id = cursor.fetchone()[0]
                inserted_ids.append(row_id)
        connection.commit()
        for row_id in inserted_ids:
            _mark_loaded("raw.csv_extract", row_id, connection)
        return inserted_ids
    except Exception as exc:
        connection.rollback()
        logger.error("Failed to load CSV file %s: %s", path, exc)
        log_error(source_system, correlation_id, "RAW_CSV_LOAD", str(exc), str(path))
        return []


def load_xml_file(filepath: str, connection) -> int | None:
    path = Path(filepath)
    correlation_id = str(uuid.uuid4())
    try:
        payload = path.read_text(encoding="utf-8")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO raw.xml_payload (
                    source_system,
                    message_type,
                    payload_text,
                    file_name,
                    received_at,
                    correlation_id,
                    processing_status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                ("Somerset", "PATHWAY", payload, path.name, datetime.now(), correlation_id, "received"),
            )
            row_id = cursor.fetchone()[0]
        connection.commit()
        _mark_loaded("raw.xml_payload", row_id, connection)
        return row_id
    except Exception as exc:
        connection.rollback()
        logger.error("Failed to load XML file %s: %s", path, exc)
        log_error("Somerset", correlation_id, "RAW_XML_LOAD", str(exc), str(path))
        return None


def load_json_file(filepath: str, connection) -> int | None:
    path = Path(filepath)
    correlation_id = str(uuid.uuid4())
    try:
        payload = path.read_text(encoding="utf-8")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO raw.json_payload (
                    source_system,
                    message_type,
                    payload_text,
                    file_name,
                    received_at,
                    correlation_id,
                    processing_status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                ("Infoflex", "MDT_MEETING", payload, path.name, datetime.now(), correlation_id, "received"),
            )
            row_id = cursor.fetchone()[0]
        connection.commit()
        _mark_loaded("raw.json_payload", row_id, connection)
        return row_id
    except Exception as exc:
        connection.rollback()
        logger.error("Failed to load JSON file %s: %s", path, exc)
        log_error("Infoflex", correlation_id, "RAW_JSON_LOAD", str(exc), str(path))
        return None


def load_all_from_directory(source_dir: str, connection) -> dict:
    root = Path(source_dir)
    summary = {"hl7": 0, "csv": 0, "xml": 0, "json": 0}

    for path in sorted((root / "hl7").glob("*.hl7")):
        if path.name == "all_messages.hl7":
            continue
        row_id = load_hl7_file(str(path), connection)
        if row_id:
            summary["hl7"] += 1

    csv_source_map = {
        "pas_patients.csv": "PAS",
        "pas_appointments.csv": "PAS",
        "pas_encounters.csv": "PAS",
        "sact_treatments.csv": "ChemoCare",
        "endoscopy_exams.csv": "Unisoft",
        "ipt_referrals.csv": "Somerset",
        "tracking_comments.csv": "Somerset",
    }
    for path in sorted((root / "csv").glob("*.csv")):
        row_ids = load_csv_file(str(path), csv_source_map.get(path.name, "UNKNOWN"), connection)
        summary["csv"] += len(row_ids)

    for path in sorted((root / "xml").glob("*.xml")):
        if path.name == "all_pathways.xml":
            continue
        row_id = load_xml_file(str(path), connection)
        if row_id:
            summary["xml"] += 1

    for path in sorted((root / "json").glob("*.json")):
        if path.name == "all_mdt_meetings.json":
            continue
        row_id = load_json_file(str(path), connection)
        if row_id:
            summary["json"] += 1

    return summary


def main() -> None:
    connection = config.get_connection()
    try:
        summary = load_all_from_directory(str(config.SOURCE_OUTPUT_DIR), connection)
        print(
            f"Loaded raw payloads from {config.SOURCE_OUTPUT_DIR}: "
            f"hl7={summary['hl7']} csv_rows={summary['csv']} xml={summary['xml']} json={summary['json']}"
        )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
