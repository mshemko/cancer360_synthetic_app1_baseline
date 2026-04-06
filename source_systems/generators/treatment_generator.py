"""Generate treatment events aligned to pathway timelines."""

from __future__ import annotations

import random
import uuid
from datetime import timedelta
from typing import Any

try:
    from .generator_utils import (
        REFERENCE_DIR,
        choose_volume,
        current_timestamp,
        load_config,
        load_json,
        load_pathways,
        pathway_end_date,
        save_output,
        timeline_dates,
    )
except ImportError:
    from generator_utils import (
        REFERENCE_DIR,
        choose_volume,
        current_timestamp,
        load_config,
        load_json,
        load_pathways,
        pathway_end_date,
        save_output,
        timeline_dates,
    )


OUTPUT_FILE = "treatments.json"
TYPE_MAP = {
    "Chemotherapy": "chemotherapy",
    "Radiotherapy": "radiotherapy",
    "Surgery": "surgery",
    "Immunotherapy": "immunotherapy",
}


def treatment_spacing_days(treatment_type: str) -> int:
    if treatment_type == "Chemotherapy":
        return random.randint(14, 21)
    if treatment_type == "Immunotherapy":
        return random.randint(14, 28)
    if treatment_type == "Radiotherapy":
        return 1
    return random.randint(21, 35)


def treatment_status(attendance_date, timeline_end):
    if attendance_date > timeline_end - timedelta(days=5) and random.random() < 0.25:
        return "Scheduled"
    return random.choices(
        ["Completed", "In Progress", "Scheduled", "Cancelled"],
        weights=[0.68, 0.12, 0.14, 0.06],
        k=1,
    )[0]


def generate_treatments(pathways: list[dict[str, Any]], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    config = config or load_config()
    regimens = load_json(REFERENCE_DIR / "treatment_regimens.json")
    volume_cfg = config["generation"]["volume_per_patient"]["cancer_treatments"]
    records: list[dict[str, Any]] = []

    for pathway in pathways:
        if not pathway["timeline_skeleton"]["scenarios"].get("has_first_treatment"):
            continue

        dates = timeline_dates(pathway)
        dtt_date = dates["dtt"]
        first_treatment_date = dates["first_treatment"]
        if dtt_date is None or first_treatment_date is None:
            continue

        timeline_end = pathway_end_date(pathway)
        event_count = max(1, choose_volume(volume_cfg))
        current_attendance = first_treatment_date
        base_type = pathway["first_treatment_type"] or random.choice(list(TYPE_MAP.keys()))

        for index in range(event_count):
            treatment_type = base_type if index == 0 else random.choices(
                [base_type, "Chemotherapy", "Radiotherapy", "Surgery", "Immunotherapy"],
                weights=[0.55, 0.15, 0.12, 0.10, 0.08],
                k=1,
            )[0]
            regimen_key = TYPE_MAP[treatment_type]
            description = random.choice(regimens[regimen_key])
            attendance_date = min(timeline_end, current_attendance)
            scheduled_offset = random.randint(1, 14)
            ordered_offset = scheduled_offset + random.randint(0, 7)
            scheduled_date = max(dtt_date, attendance_date - timedelta(days=scheduled_offset))
            ordered_date = max(dtt_date, attendance_date - timedelta(days=ordered_offset))
            status = treatment_status(attendance_date, timeline_end)
            poa_booking_status = random.choices(
                ["Attended", "Booked", "Did Not Attend"],
                weights=[0.85, 0.10, 0.05],
                k=1,
            )[0]

            if treatment_type == "Chemotherapy":
                prescription_status = random.choices(
                    ["Prepared", "Dispensed", "Pending"],
                    weights=[0.45, 0.35, 0.20],
                    k=1,
                )[0]
            else:
                prescription_status = "N/A"

            records.append(
                {
                    "cancer_treatment_id": str(uuid.uuid4()),
                    "pathway_id": pathway["pathway_id"],
                    "person_id": pathway["person_id"],
                    "mrn": pathway["mrn"],
                    "nhs_number": pathway["nhs_number"],
                    "treatment_type": treatment_type,
                    "treatment_description": description,
                    "treatment_status": status,
                    "attendance_date": attendance_date.isoformat(),
                    "ordered_date": ordered_date.isoformat(),
                    "scheduled_date": scheduled_date.isoformat(),
                    "poa_attendance_id": str(uuid.uuid4()),
                    "poa_booking_status": poa_booking_status,
                    "prescription_status": prescription_status,
                    "is_prescription_prepared": prescription_status in {"Prepared", "Dispensed"},
                    "source_system_name": config["generation"]["source_systems"]["treatment"],
                    "last_refreshed_at_source_timestamp": current_timestamp(),
                }
            )

            current_attendance = attendance_date + timedelta(days=treatment_spacing_days(treatment_type))
            if current_attendance > timeline_end:
                current_attendance = timeline_end

    return records


def main() -> None:
    pathways = load_pathways()
    records = generate_treatments(pathways)
    output_path = save_output(OUTPUT_FILE, records)
    print(f"Generated {len(records)} treatment events for {len(pathways)} pathways -> {output_path}")


if __name__ == "__main__":
    main()
