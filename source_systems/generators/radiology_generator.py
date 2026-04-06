"""Generate radiology exams aligned to pathway timelines."""

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


OUTPUT_FILE = "radiology.json"
SITE_MODALITY_BIAS = {
    "Lung": ["CT", "XR", "PET"],
    "Breast": ["US", "MRI", "CT"],
    "Colorectal": ["CT", "MRI", "US"],
    "Head & Neck": ["CT", "MRI", "PET"],
    "Upper GI": ["CT", "US", "PET"],
    "Brain/CNS": ["MRI", "CT"],
    "Gynaecology": ["US", "MRI", "CT"],
    "Urology": ["US", "CT", "MRI"],
    "Sarcoma": ["MRI", "CT", "XR"],
    "Haematology": ["CT", "PET", "XR"],
}


def pick_exam_type(cancer_site: str, radiology_types: list[dict[str, str]]) -> dict[str, str]:
    preferred = SITE_MODALITY_BIAS.get(cancer_site, [])
    weighted_pool: list[dict[str, str]] = []
    for exam in radiology_types:
        weight = 4 if exam["modality"] in preferred else 1
        weighted_pool.extend([exam] * weight)
    return random.choice(weighted_pool)


def build_report_text(exam_type: str, cancer_site: str) -> str:
    lesion_size = round(random.uniform(1.1, 4.8), 1)
    lymph_text = random.choice(
        [
            "No pathologically enlarged lymph nodes are identified.",
            "Small volume nodal prominence is present but not pathologically enlarged.",
            "There is mild regional nodal enlargement requiring correlation.",
        ]
    )
    impression = random.choice(
        [
            "Recommend tissue sampling if clinically appropriate.",
            "Findings should be discussed at MDT.",
            "Interval imaging follow-up is advised.",
        ]
    )
    return (
        f"{exam_type} performed for suspected {cancer_site.lower()} malignancy. "
        f"There is a {lesion_size} cm abnormal lesion demonstrated. "
        f"{lymph_text} {impression}"
    )


def generate_radiology(pathways: list[dict[str, Any]], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    config = config or load_config()
    radiology_types = load_json(REFERENCE_DIR / "radiology_types.json")
    volume_cfg = config["generation"]["volume_per_patient"]["radiology_exams"]
    records: list[dict[str, Any]] = []

    for pathway in pathways:
        scenarios = pathway["timeline_skeleton"]["scenarios"]
        if not scenarios.get("has_radiology"):
            continue

        dates = timeline_dates(pathway)
        window_start = dates["referral"] or random_date_between(pathway_end_date(pathway), pathway_end_date(pathway))
        window_end = pathway_end_date(pathway)
        exam_count = choose_volume(volume_cfg)
        ordered_dates = sorted_event_dates(window_start, window_end, exam_count, min_spacing_days=2)

        for ordered_date in ordered_dates:
            exam = pick_exam_type(pathway["cancer_site"], radiology_types)
            scheduled_date = min(window_end, ordered_date + timedelta(days=random.randint(1, 7)))
            completed = random.random() < 0.82 or scheduled_date < window_end - timedelta(days=7)
            attendance_date = None
            report_authorised_date = None
            exam_status = "Scheduled"
            is_reported = False
            if completed:
                attendance_date = min(window_end, scheduled_date + timedelta(days=random.randint(0, 3)))
                report_authorised_date = min(window_end, attendance_date + timedelta(days=random.randint(1, 14)))
                exam_status = "Completed"
                is_reported = True

            records.append(
                {
                    "radiology_exam_id": str(uuid.uuid4()),
                    "pathway_id": pathway["pathway_id"],
                    "patient_id": pathway["person_id"],
                    "person_id": pathway["person_id"],
                    "mrn": pathway["mrn"],
                    "nhs_number": pathway["nhs_number"],
                    "radiology_exam_type": exam["exam_type"],
                    "modality": exam["modality"],
                    "radiology_priority": random.choices(
                        ["Urgent", "Routine", "Two Week Wait"],
                        weights=[0.40, 0.40, 0.20],
                        k=1,
                    )[0],
                    "exam_status": exam_status,
                    "ordered_date": ordered_date.isoformat(),
                    "scheduled_date": scheduled_date.isoformat(),
                    "attendance_date": attendance_date.isoformat() if attendance_date else None,
                    "report_authorised_date": report_authorised_date.isoformat() if report_authorised_date else None,
                    "is_reported": is_reported,
                    "radiology_report_text": build_report_text(exam["exam_type"], pathway["cancer_site"]),
                    "source_system_name": config["generation"]["source_systems"]["radiology"],
                    "last_refreshed_at_source_timestamp": current_timestamp(),
                }
            )

    return records


def main() -> None:
    pathways = load_pathways()
    records = generate_radiology(pathways)
    output_path = save_output(OUTPUT_FILE, records)
    print(f"Generated {len(records)} radiology exams for {len(pathways)} pathways -> {output_path}")


if __name__ == "__main__":
    main()
