"""Generate inpatient encounters aligned to pathway timelines."""

from __future__ import annotations

import random
import uuid
from datetime import date, datetime, time, timedelta
from typing import Any

try:
    from .generator_utils import (
        choose_volume,
        current_timestamp,
        load_config,
        load_pathways,
        pathway_end_date,
        save_output,
        timeline_dates,
    )
except ImportError:
    from generator_utils import (
        choose_volume,
        current_timestamp,
        load_config,
        load_pathways,
        pathway_end_date,
        save_output,
        timeline_dates,
    )


OUTPUT_FILE = "encounters.json"
SPECIALTY_BY_SITE = {
    "Breast": "Breast Surgery",
    "Lung": "Thoracic Surgery",
    "Colorectal": "General Surgery",
    "Prostate": "Urology",
    "Head & Neck": "Maxillofacial Surgery",
    "Upper GI": "Upper GI Surgery",
    "Haematology": "Haematology",
    "Gynaecology": "Gynaecology Oncology",
    "Skin": "Plastic Surgery",
    "Urology": "Urology",
    "Brain/CNS": "Neurosurgery",
    "Sarcoma": "Orthopaedic Oncology",
}


def status_for(encounter_day: date) -> str:
    if encounter_day > date.today():
        return random.choices(
            ["Scheduled", "Cancelled", "In Progress"],
            weights=[0.70, 0.15, 0.15],
            k=1,
        )[0]
    return random.choices(
        ["Completed", "Scheduled", "In Progress", "Cancelled"],
        weights=[0.60, 0.20, 0.10, 0.10],
        k=1,
    )[0]


def generate_encounters(pathways: list[dict[str, Any]], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    config = config or load_config()
    volume_cfg = config["generation"]["volume_per_patient"]["inpatient_encounters"]
    source_name = config["generation"]["source_systems"]["encounters"]
    records: list[dict[str, Any]] = []

    for pathway in pathways:
        if not pathway["timeline_skeleton"]["scenarios"].get("has_inpatient"):
            continue

        dates = timeline_dates(pathway)
        anchor = dates["dtt"] or dates["diagnosis"] or dates["first_seen"] or dates["referral"]
        if anchor is None:
            continue
        count = max(1, choose_volume(volume_cfg))
        timeline_end = pathway_end_date(pathway)
        encounter_day = anchor + timedelta(days=random.randint(0, 14))
        specialty = SPECIALTY_BY_SITE.get(pathway["cancer_site"], "Oncology")

        for _ in range(count):
            encounter_day = min(timeline_end, encounter_day)
            surgical_order_date = max(anchor, encounter_day - timedelta(days=random.randint(1, 14)))
            admission_offer_timestamp = datetime.combine(
                surgical_order_date + timedelta(days=random.randint(1, 14)),
                time(hour=random.randint(8, 17), minute=random.choice([0, 15, 30, 45])),
            ).astimezone()
            status = status_for(encounter_day)
            if status == "Scheduled" and encounter_day <= date.today():
                encounter_day = min(timeline_end, date.today() + timedelta(days=random.randint(1, 30)))
            attendance_dt = datetime.combine(
                encounter_day,
                time(hour=random.randint(7, 16), minute=random.choice([0, 15, 30, 45])),
            ).astimezone()

            records.append(
                {
                    "encounter_id": str(uuid.uuid4()),
                    "pathway_id": pathway["pathway_id"],
                    "person_id": pathway["person_id"],
                    "mrn": pathway["mrn"],
                    "nhs_number": pathway["nhs_number"],
                    "title": f"{specialty}, {pathway['first_name']} {pathway['surname']}",
                    "tci_status": status,
                    "surgical_order_date": surgical_order_date.isoformat(),
                    "admission_offer_timestamp": admission_offer_timestamp.isoformat(),
                    "attendance_date": attendance_dt.isoformat(),
                    "source_system_name": source_name,
                    "last_refreshed_at_source_timestamp": current_timestamp(),
                }
            )
            encounter_day = encounter_day + timedelta(days=random.randint(14, 45))

    return records


def main() -> None:
    pathways = load_pathways()
    records = generate_encounters(pathways)
    output_path = save_output(OUTPUT_FILE, records)
    print(f"Generated {len(records)} inpatient encounters for {len(pathways)} pathways -> {output_path}")


if __name__ == "__main__":
    main()
