"""Map parsed HL7 pathology messages into canonical test result rows."""

from __future__ import annotations

from typing import Any, Callable

from .mapper_utils import current_timestamp, parse_datetime, person_id_from_lookup


def map_test_result(
    parsed_hl7: dict[str, Any],
    person_lookup: dict[str, str] | None = None,
    resolver: Callable[[str | None, str | None], str | None] | None = None,
) -> dict[str, Any]:
    pid = parsed_hl7.get("PID", {})
    obr = parsed_hl7.get("OBR", {})
    obx = parsed_hl7.get("OBX", [])
    first_obx = obx[0] if obx else {}
    value = first_obx.get("value")
    try:
        value_double = float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        value_double = None
    value_type = str(first_obx.get("value_type") or "").upper()
    return {
        "test_result_id": obr.get("order_number"),
        "person_id": person_id_from_lookup(pid.get("nhs_number"), pid.get("mrn"), person_lookup, resolver),
        "attendance_id": None,
        "test_name": obr.get("exam_type"),
        "test_id_code": first_obx.get("observation_identifier") or None,
        "test_date_time": parse_datetime(obr.get("ordered_datetime"))
        or parse_datetime(parsed_hl7.get("MSH", {}).get("timestamp")),
        "test_ordered_timestamp": parse_datetime(obr.get("ordered_datetime")),
        "value": str(value) if value is not None else None,
        "value_double": value_double,
        "test_value_type": "Numeric" if value_type == "NM" else "Text",
        "unit": first_obx.get("unit") or None,
        "ordering_specialty_name": None,
        "expiry_date": None,
        "source_system_name": "ICE",
        "last_refreshed_at_source_timestamp": current_timestamp(),
    }


def map_test_result_batch(
    parsed_messages: list[dict[str, Any]],
    person_lookup: dict[str, str] | None = None,
    resolver: Callable[[str | None, str | None], str | None] | None = None,
) -> list[dict[str, Any]]:
    return [map_test_result(message, person_lookup, resolver) for message in parsed_messages]
