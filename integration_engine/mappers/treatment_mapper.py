"""Map staged SACT treatment rows into canonical treatment rows."""

from __future__ import annotations

from typing import Any

from .mapper_utils import current_timestamp, parse_bool, parse_date


def map_treatment(staged_record: dict[str, Any]) -> dict[str, Any]:
    return {
        "cancer_treatment_id": staged_record.get("treatment_id") or staged_record.get("cancer_treatment_id"),
        "person_id": staged_record.get("person_id"),
        "treatment_type": staged_record.get("treatment_type"),
        "treatment_description": staged_record.get("regimen_name") or staged_record.get("treatment_description"),
        "treatment_status": staged_record.get("treatment_status"),
        "attendance_date": parse_date(staged_record.get("attendance_date")),
        "ordered_date": parse_date(staged_record.get("ordered_date")),
        "scheduled_date": parse_date(staged_record.get("scheduled_date")),
        "poa_attendance_id": staged_record.get("poa_attendance_id") or None,
        "poa_booking_status": staged_record.get("poa_booking_status") or None,
        "prescription_status": staged_record.get("prescription_status") or None,
        "is_prescription_prepared": parse_bool(staged_record.get("is_prescription_prepared")),
        "source_system_name": "ChemoCare",
        "last_refreshed_at_source_timestamp": current_timestamp(),
    }


def map_treatments(staged_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [map_treatment(record) for record in staged_records]
