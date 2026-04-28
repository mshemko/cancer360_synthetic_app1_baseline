"""Map PAS staging records into canonical patient rows."""

from __future__ import annotations

from typing import Any

from .mapper_utils import current_timestamp, parse_date


def map_patient(staged_record: dict[str, Any]) -> dict[str, Any]:
    return {
        "person_id": staged_record.get("person_id"),
        "mrn": staged_record.get("mrn"),
        "nhs_number": staged_record.get("nhs_number"),
        "first_name": staged_record.get("first_name"),
        "surname": staged_record.get("surname"),
        "title": staged_record.get("title"),
        "date_of_birth": parse_date(staged_record.get("date_of_birth")),
        "date_of_death": parse_date(staged_record.get("date_of_death")),
        "sex": staged_record.get("sex") or None,
        "gender_identity": staged_record.get("gender_identity") or None,
        "address_line_1": staged_record.get("address_line_1") or None,
        "address_line_2": staged_record.get("address_line_2") or None,
        "postcode": staged_record.get("postcode") or None,
        "phone_number": staged_record.get("phone_number") or None,
        "registered_gp": staged_record.get("registered_gp") or None,
        "next_of_kin_name": staged_record.get("next_of_kin_name") or None,
        "next_of_kin_number": staged_record.get("next_of_kin_number") or None,
        "source_system_name": "PAS",
        "last_refreshed_at_source_timestamp": current_timestamp(),
    }


def map_patients(staged_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [map_patient(record) for record in staged_records]
