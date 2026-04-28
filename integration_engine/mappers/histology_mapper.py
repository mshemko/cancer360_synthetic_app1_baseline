"""Map parsed HL7 pathology messages into canonical histology rows."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Callable

from .mapper_utils import current_timestamp, parse_date, person_id_from_lookup


def map_histology(
    parsed_hl7: dict[str, Any],
    person_lookup: dict[str, str] | None = None,
    resolver: Callable[[str | None, str | None], str | None] | None = None,
) -> dict[str, Any]:
    pid = parsed_hl7.get("PID", {})
    obr = parsed_hl7.get("OBR", {})
    obx = parsed_hl7.get("OBX", [])
    sample_taken_date = parse_date(obr.get("ordered_datetime"))
    received_at_lab_date = sample_taken_date + timedelta(days=1) if sample_taken_date else None
    sample_prepared_date = received_at_lab_date + timedelta(days=1) if received_at_lab_date else None
    report_prepared_date = sample_prepared_date + timedelta(days=3) if sample_prepared_date else None
    report_authorised_date = parse_date(parsed_hl7.get("MSH", {}).get("timestamp"))
    report_text = " ".join(str(item.get("value", "")).strip() for item in obx if item.get("value")).strip() or None
    return {
        "histology_id": obr.get("order_number"),
        "person_id": person_id_from_lookup(pid.get("nhs_number"), pid.get("mrn"), person_lookup, resolver),
        "histology_type": obr.get("exam_type"),
        "priority": None,
        "histology_status": "Completed" if report_authorised_date else "In Progress",
        "sample_taken_date": sample_taken_date,
        "received_at_lab_date": received_at_lab_date,
        "sample_prepared_date": sample_prepared_date,
        "report_prepared_date": report_prepared_date,
        "report_authorised_date": report_authorised_date,
        "is_reported": report_authorised_date is not None,
        "histology_report_text": report_text,
        "source_system_name": "ICE",
        "last_refreshed_at_source_timestamp": current_timestamp(),
    }


def map_histology_batch(
    parsed_messages: list[dict[str, Any]],
    person_lookup: dict[str, str] | None = None,
    resolver: Callable[[str | None, str | None], str | None] | None = None,
) -> list[dict[str, Any]]:
    return [map_histology(message, person_lookup, resolver) for message in parsed_messages]
