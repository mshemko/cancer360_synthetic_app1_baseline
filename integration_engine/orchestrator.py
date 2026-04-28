"""Orchestrate raw loading, parsing, and staging for generated source payloads."""

from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[1]))

import json
from pathlib import Path

from integration_engine import config
from integration_engine.loaders.raw_loader import (
    get_raw_row_metadata,
    load_csv_file,
    load_hl7_file,
    load_json_file,
    load_xml_file,
)
from integration_engine.loaders.staging_loader import (
    load_staging_appointment,
    load_staging_comment,
    load_staging_encounter,
    load_staging_endoscopy,
    load_staging_histology,
    load_staging_ipt,
    load_staging_mdt,
    load_staging_pathway,
    load_staging_patient,
    load_staging_radiology,
    load_staging_test_result,
    load_staging_treatment,
)
from integration_engine.parsers.csv_parser import classify_csv, parse_csv_file
from integration_engine.parsers.hl7_parser import classify_message, parse_message
from integration_engine.parsers.json_parser import (
    extract_bookings,
    extract_meetings,
    extract_notes,
    parse_json_file,
)
from integration_engine.parsers.xml_parser import parse_xml_file


def _csv_source_system(filename: str) -> str:
    mapping = {
        "pas_patients.csv": "PAS",
        "pas_appointments.csv": "PAS",
        "pas_encounters.csv": "PAS",
        "sact_treatments.csv": "ChemoCare",
        "endoscopy_exams.csv": "Unisoft",
        "ipt_referrals.csv": "Somerset",
        "tracking_comments.csv": "Somerset",
    }
    return mapping.get(filename, "UNKNOWN")


def _load_csv_records(filepath: Path, connection) -> tuple[str, list[dict], str]:
    row_ids = load_csv_file(str(filepath), _csv_source_system(filepath.name), connection)
    if not row_ids:
        return "", [], ""
    metadata = get_raw_row_metadata("raw.csv_extract", row_ids[0], connection) or {}
    correlation_id = metadata.get("correlation_id", "")
    classification = classify_csv(str(filepath))
    records = parse_csv_file(str(filepath))
    return correlation_id, records, classification


def _process_hl7_files(connection, hl7_dir: Path) -> dict[str, int]:
    summary = {"radiology": 0, "histology": 0, "test_result": 0}
    for filepath in sorted(hl7_dir.glob("*.hl7")):
        if filepath.name == "all_messages.hl7":
            continue
        row_id = load_hl7_file(str(filepath), connection)
        if not row_id:
            continue
        metadata = get_raw_row_metadata("raw.hl7_message", row_id, connection) or {}
        parsed = parse_message(filepath.read_text(encoding="utf-8"))
        correlation_id = metadata.get("correlation_id", "")
        classification = classify_message(parsed)
        if classification == "radiology":
            summary["radiology"] += load_staging_radiology([parsed], correlation_id, connection)
        elif classification == "histology":
            summary["histology"] += load_staging_histology([parsed], correlation_id, connection)
        else:
            summary["test_result"] += load_staging_test_result([parsed], correlation_id, connection)
    return summary


def _process_csv_files(connection, csv_dir: Path) -> dict[str, int]:
    summary = {
        "patient": 0,
        "appointment": 0,
        "encounter": 0,
        "treatment": 0,
        "endoscopy": 0,
        "ipt": 0,
        "comment": 0,
    }
    for filepath in sorted(csv_dir.glob("*.csv")):
        correlation_id, records, classification = _load_csv_records(filepath, connection)
        if not records:
            continue
        if classification == "patient":
            summary["patient"] += load_staging_patient(records, correlation_id, connection)
        elif classification == "appointment":
            summary["appointment"] += load_staging_appointment(records, correlation_id, connection)
        elif classification == "encounter":
            summary["encounter"] += load_staging_encounter(records, correlation_id, connection)
        elif classification == "treatment":
            summary["treatment"] += load_staging_treatment(records, correlation_id, connection)
        elif classification == "endoscopy":
            summary["endoscopy"] += load_staging_endoscopy(records, correlation_id, connection)
        elif classification == "ipt":
            summary["ipt"] += load_staging_ipt(records, correlation_id, connection)
        elif classification == "comment":
            summary["comment"] += load_staging_comment(records, correlation_id, connection)
    return summary


def _process_xml_files(connection, xml_dir: Path) -> int:
    inserted = 0
    for filepath in sorted(xml_dir.glob("*.xml")):
        if filepath.name == "all_pathways.xml":
            continue
        row_id = load_xml_file(str(filepath), connection)
        if not row_id:
            continue
        metadata = get_raw_row_metadata("raw.xml_payload", row_id, connection) or {}
        correlation_id = metadata.get("correlation_id", "")
        records = parse_xml_file(str(filepath))
        inserted += load_staging_pathway(records, correlation_id, connection)
    return inserted


def _process_json_files(connection, json_dir: Path) -> dict[str, int]:
    summary = {"meetings": 0, "bookings": 0, "notes": 0}
    for filepath in sorted(json_dir.glob("*.json")):
        if filepath.name == "all_mdt_meetings.json":
            continue
        row_id = load_json_file(str(filepath), connection)
        if not row_id:
            continue
        metadata = get_raw_row_metadata("raw.json_payload", row_id, connection) or {}
        correlation_id = metadata.get("correlation_id", "")
        parsed_documents = parse_json_file(str(filepath))
        meetings = extract_meetings(parsed_documents)
        bookings = extract_bookings(parsed_documents)
        notes = extract_notes(parsed_documents)
        staged = load_staging_mdt(meetings, bookings, notes, correlation_id, connection)
        summary["meetings"] += staged["meetings"]
        summary["bookings"] += staged["bookings"]
        summary["notes"] += staged["notes"]
    return summary


def run_replay(source_dir: Path | None = None) -> dict[str, dict | int]:
    if source_dir is not None:
        output_root = Path(source_dir)
        hl7_dir = output_root / "hl7"
        csv_dir = output_root / "csv"
        xml_dir = output_root / "xml"
        json_dir = output_root / "json"
    else:
        hl7_dir = config.HL7_DIR
        csv_dir = config.CSV_DIR
        xml_dir = config.XML_DIR
        json_dir = config.JSON_DIR

    connection = config.get_connection()
    try:
        hl7_summary = _process_hl7_files(connection, hl7_dir)
        csv_summary = _process_csv_files(connection, csv_dir)
        xml_count = _process_xml_files(connection, xml_dir)
        json_summary = _process_json_files(connection, json_dir)
        summary = {
            "hl7": hl7_summary,
            "csv": csv_summary,
            "xml": xml_count,
            "json": json_summary,
        }
        print(json.dumps(summary, indent=2))
        return summary
    finally:
        connection.close()


def main() -> None:
    run_replay()


if __name__ == "__main__":
    main()
