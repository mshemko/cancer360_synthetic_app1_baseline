"""Generate histology samples aligned to pathway timelines."""

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
        sorted_event_dates,
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
        sorted_event_dates,
        timeline_dates,
    )


OUTPUT_FILE = "histology.json"


def build_histology_report(histology_type: str, cancer_site: str) -> str:
    grade = random.choice(["grade 1", "grade 2", "grade 3"])
    receptor_line = random.choice(
        [
            "ER positive, PR positive, HER2 negative.",
            "No definite lymphovascular invasion is seen.",
            "Tumour shows moderate pleomorphism with focal necrosis.",
        ]
    )
    conclusion = random.choice(
        [
            "Features are in keeping with invasive malignancy.",
            "Findings support malignant epithelial neoplasm.",
            "Overall appearances are suspicious for carcinoma.",
        ]
    )
    return (
        f"{histology_type} obtained for suspected {cancer_site.lower()} cancer. "
        f"Microscopy shows malignant tissue, {grade}. "
        f"{receptor_line} {conclusion}"
    )


def generate_histology(pathways: list[dict[str, Any]], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    config = config or load_config()
    histology_types = load_json(REFERENCE_DIR / "histology_types.json")
    volume_cfg = config["generation"]["volume_per_patient"]["histology_samples"]
    records: list[dict[str, Any]] = []

    for pathway in pathways:
        if not pathway["timeline_skeleton"]["scenarios"].get("has_histology"):
            continue

        dates = timeline_dates(pathway)
        window_start = dates["first_seen"] or dates["referral"] or pathway_end_date(pathway)
        window_end = pathway_end_date(pathway)
        sample_dates = sorted_event_dates(window_start, window_end, choose_volume(volume_cfg), min_spacing_days=2)

        for sample_taken_date in sample_dates:
            received_at_lab_date = min(window_end, sample_taken_date + timedelta(days=random.randint(0, 2)))
            sample_prepared_date = min(window_end, received_at_lab_date + timedelta(days=random.randint(1, 3)))
            report_prepared_date = min(window_end, sample_prepared_date + timedelta(days=random.randint(2, 7)))
            completed = random.random() < 0.84 or report_prepared_date < window_end - timedelta(days=4)
            report_authorised_date = (
                min(window_end, report_prepared_date + timedelta(days=random.randint(1, 3)))
                if completed
                else None
            )

            histology_type = random.choice(histology_types)["histology_type"]
            records.append(
                {
                    "histology_id": str(uuid.uuid4()),
                    "pathway_id": pathway["pathway_id"],
                    "person_id": pathway["person_id"],
                    "mrn": pathway["mrn"],
                    "nhs_number": pathway["nhs_number"],
                    "histology_type": histology_type,
                    "priority": random.choices(
                        ["Urgent", "Routine", "Cancer Pathway"],
                        weights=[0.30, 0.50, 0.20],
                        k=1,
                    )[0],
                    "histology_status": "Completed" if completed else "In Progress",
                    "sample_taken_date": sample_taken_date.isoformat(),
                    "received_at_lab_date": received_at_lab_date.isoformat(),
                    "sample_prepared_date": sample_prepared_date.isoformat(),
                    "report_prepared_date": report_prepared_date.isoformat(),
                    "report_authorised_date": report_authorised_date.isoformat() if report_authorised_date else None,
                    "is_reported": completed,
                    "histology_report_text": build_histology_report(histology_type, pathway["cancer_site"]),
                    "source_system_name": config["generation"]["source_systems"]["pathology"],
                    "last_refreshed_at_source_timestamp": current_timestamp(),
                }
            )

    return records


def main() -> None:
    pathways = load_pathways()
    records = generate_histology(pathways)
    output_path = save_output(OUTPUT_FILE, records)
    print(f"Generated {len(records)} histology samples for {len(pathways)} pathways -> {output_path}")


if __name__ == "__main__":
    main()
