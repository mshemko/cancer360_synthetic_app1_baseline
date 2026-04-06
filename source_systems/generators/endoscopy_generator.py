"""Generate synthetic endoscopy events for Cancer 360."""

from __future__ import annotations

import random
import uuid
from datetime import date, timedelta
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


OUTPUT_FILE = "endoscopy.json"
SITE_BIAS = {
    "Colorectal": {"Colonoscopy": 0.45, "Sigmoidoscopy": 0.25, "Diagnostic fibreoptic endoscopic procedure": 0.15},
    "Upper GI": {"Gastroscopy": 0.35, "ERCP": 0.20, "EUS": 0.20},
    "Lung": {"Bronchoscopy": 0.55, "Diagnostic fibreoptic endoscopic procedure": 0.20},
    "Urology": {"Flexible cystoscopy": 0.60},
}

REPORT_TEMPLATES = {
    "Colonoscopy": "Colonoscopy performed to caecum. Mucosal lesion identified and targeted biopsies taken. No immediate complication noted. Recommend histology correlation and colorectal MDT review.",
    "Gastroscopy": "Gastroscopy completed without complication. Irregular mucosa noted in the upper gastrointestinal tract and biopsies were taken. Findings are suspicious and should be correlated with pathology.",
    "Flexible cystoscopy": "Flexible cystoscopy performed. Focal mucosal abnormality visualised and documented. Biopsy or formal urology review recommended depending on histology.",
    "Bronchoscopy": "Bronchoscopy performed with endobronchial visualisation of an abnormal lesion. Washings and biopsies obtained. Recommend pathology review and thoracic MDT discussion.",
}


def pick_endoscopy_type(cancer_site: str, types: list[dict[str, str]]) -> str:
    weighted_types: list[tuple[str, float]] = []
    bias = SITE_BIAS.get(cancer_site, {})
    for row in types:
        name = row["endoscopy_type"]
        weighted_types.append((name, bias.get(name, 0.08)))
    names, weights = zip(*weighted_types)
    return random.choices(names, weights=weights, k=1)[0]


def report_text(endoscopy_type: str) -> str:
    return REPORT_TEMPLATES.get(
        endoscopy_type,
        "Endoscopic examination completed. Target area inspected and relevant samples obtained where indicated. No immediate post-procedural concern recorded. Follow-up to depend on histology and clinical review.",
    )


def generate_endoscopy(pathways: list[dict[str, Any]], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    config = config or load_config()
    endoscopy_types = load_json(REFERENCE_DIR / "endoscopy_types.json")
    volume_cfg = config["generation"]["volume_per_patient"]["endoscopy_exams"]
    source_name = config["generation"]["source_systems"]["endoscopy"]
    records: list[dict[str, Any]] = []

    for pathway in pathways:
        if not pathway["timeline_skeleton"]["scenarios"].get("has_endoscopy"):
            continue
        dates = timeline_dates(pathway)
        timeline_end = pathway_end_date(pathway)
        count = max(1, choose_volume(volume_cfg))
        ordered_days = sorted_event_dates(
            dates["referral"] or timeline_end,
            timeline_end,
            count,
            min_spacing_days=4,
        )

        for ordered_day in ordered_days:
            endoscopy_type = pick_endoscopy_type(pathway["cancer_site"], endoscopy_types)
            scheduled_date = min(timeline_end, ordered_day + timedelta(days=random.randint(1, 14)))
            if scheduled_date > date.today():
                exam_status = "Scheduled"
                attendance_date = None
                report_prepared_date = None
                report_authorised_date = None
                is_reported = False
            else:
                exam_status = "Completed"
                attendance_date = min(timeline_end, scheduled_date + timedelta(days=random.randint(0, 3)))
                report_prepared_date = min(timeline_end, attendance_date + timedelta(days=random.randint(1, 5)))
                report_authorised_date = min(
                    timeline_end,
                    report_prepared_date + timedelta(days=random.randint(1, 3)),
                )
                is_reported = True

            records.append(
                {
                    "endoscopy_id": str(uuid.uuid4()),
                    "pathway_id": pathway["pathway_id"],
                    "person_id": pathway["person_id"],
                    "mrn": pathway["mrn"],
                    "nhs_number": pathway["nhs_number"],
                    "endoscopy_type": endoscopy_type,
                    "modality": endoscopy_type,
                    "endoscopy_priority": random.choices(
                        ["Urgent", "Routine", "Two Week Wait"],
                        weights=[0.30, 0.40, 0.30],
                        k=1,
                    )[0],
                    "exam_status": exam_status,
                    "ordered_date": ordered_day.isoformat(),
                    "scheduled_date": scheduled_date.isoformat(),
                    "attendance_date": attendance_date.isoformat() if attendance_date else None,
                    "report_prepared_date": report_prepared_date.isoformat() if report_prepared_date else None,
                    "report_authorised_date": report_authorised_date.isoformat() if report_authorised_date else None,
                    "is_reported": is_reported,
                    "endoscopy_report_text": report_text(endoscopy_type),
                    "source_system_name": source_name,
                    "last_refreshed_at_source_timestamp": current_timestamp(),
                }
            )

    return records


def main() -> None:
    pathways = load_pathways()
    records = generate_endoscopy(pathways)
    output_path = save_output(OUTPUT_FILE, records)
    print(f"Generated {len(records)} endoscopy exams for {len(pathways)} pathways -> {output_path}")


if __name__ == "__main__":
    main()
