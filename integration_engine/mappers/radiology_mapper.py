"""Map parsed HL7 radiology messages into canonical radiology rows."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Callable

from .mapper_utils import current_timestamp, parse_date, person_id_from_lookup


def _derive_modality(exam_type: str | None) -> str | None:
    text = str(exam_type or "").upper()
    if "PET" in text:
        return "PET"
    if "MRI" in text:
        return "MRI"
    if text.startswith("CT") or " CT " in f" {text} ":
        return "CT"
    if text.startswith("US") or "ULTRASOUND" in text:
        return "US"
    if "XRAY" in text or "X-RAY" in text or " X " in f" {text} ":
        return "XR"
    if "NM" in text or "NUCLEAR" in text or "SPECT" in text:
        return "NM"
    return None


def map_radiology(
    parsed_hl7: dict[str, Any],
    person_lookup: dict[str, str] | None = None,
    resolver: Callable[[str | None, str | None], str | None] | None = None,
) -> dict[str, Any]:
    pid = parsed_hl7.get("PID", {})
    obr = parsed_hl7.get("OBR", {})
    obx = parsed_hl7.get("OBX", [])
    ordered_date = parse_date(obr.get("ordered_datetime"))
    scheduled_date = ordered_date + timedelta(days=1) if ordered_date else None
    attendance_date = scheduled_date + timedelta(days=1) if scheduled_date else None
    report_authorised_date = parse_date(parsed_hl7.get("MSH", {}).get("timestamp"))
    report_text = " ".join(str(item.get("value", "")).strip() for item in obx if item.get("value")).strip() or None
    return {
        "radiology_exam_id": obr.get("order_number"),
        "person_id": person_id_from_lookup(pid.get("nhs_number"), pid.get("mrn"), person_lookup, resolver),
        "radiology_exam_type": obr.get("exam_type"),
        "modality": _derive_modality(obr.get("exam_type")),
        "radiology_priority": None,
        "exam_status": "Completed" if report_authorised_date else "Scheduled",
        "ordered_date": ordered_date,
        "scheduled_date": scheduled_date,
        "attendance_date": attendance_date,
        "report_authorised_date": report_authorised_date,
        "is_reported": report_authorised_date is not None,
        "radiology_report_text": report_text,
        "source_system_name": "CRIS",
        "last_refreshed_at_source_timestamp": current_timestamp(),
    }


def map_radiology_batch(
    parsed_messages: list[dict[str, Any]],
    person_lookup: dict[str, str] | None = None,
    resolver: Callable[[str | None, str | None], str | None] | None = None,
) -> list[dict[str, Any]]:
    return [map_radiology(message, person_lookup, resolver) for message in parsed_messages]
