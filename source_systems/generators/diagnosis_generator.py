"""Generate diagnosis events aligned to pathway timelines."""

from __future__ import annotations

import random
import uuid
from pathlib import Path
from typing import Any

try:
    from .generator_utils import (
        REFERENCE_DIR,
        current_timestamp,
        load_config,
        load_json,
        load_pathways,
        parse_date,
        save_output,
    )
except ImportError:
    from generator_utils import (
        REFERENCE_DIR,
        current_timestamp,
        load_config,
        load_json,
        load_pathways,
        parse_date,
        save_output,
    )


OUTPUT_FILE = "diagnoses.json"
BENIGN_CODES = {
    "Breast": [("D24", "Benign neoplasm of breast")],
    "Lung": [("D14.3", "Benign neoplasm of bronchus and lung")],
    "Colorectal": [("D12.6", "Benign neoplasm of colon, unspecified")],
    "Prostate": [("D29.1", "Benign neoplasm of prostate")],
    "Head & Neck": [("D10.3", "Benign neoplasm of mouth, unspecified")],
    "Upper GI": [("D13.1", "Benign neoplasm of stomach")],
    "Haematology": [("D47.9", "Neoplasm of uncertain behaviour of lymphoid tissue")],
    "Gynaecology": [("D27", "Benign neoplasm of ovary")],
    "Skin": [("D23.9", "Other benign neoplasm of skin, unspecified")],
    "Urology": [("D30.0", "Benign neoplasm of kidney")],
    "Brain/CNS": [("D33.2", "Benign neoplasm of brain, unspecified")],
    "Sarcoma": [("D21.9", "Benign neoplasm of connective and soft tissue, unspecified")],
}


def derive_stage(staging_t: str, staging_n: str, staging_m: str) -> str:
    if staging_m == "M1":
        return "Stage IV"
    if staging_t in {"T3", "T4"} or staging_n in {"N2", "N3"}:
        return "Stage III"
    if staging_t == "T2" or staging_n == "N1":
        return "Stage II"
    return "Stage I"


def generate_diagnoses(pathways: list[dict[str, Any]], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    config = config or load_config()
    icd10_codes = load_json(REFERENCE_DIR / "icd10_codes.json")
    benign_rate = float(config["generation"]["pathway_settings"]["benign_rate"])
    records: list[dict[str, Any]] = []

    for pathway in pathways:
        scenarios = pathway["timeline_skeleton"]["scenarios"]
        diagnosis_date = parse_date(pathway["timeline_skeleton"]["key_dates"].get("diagnosis"))
        if not scenarios.get("has_diagnosis") or diagnosis_date is None:
            continue

        is_benign = random.random() < benign_rate
        if is_benign:
            code, diagnosis = random.choice(BENIGN_CODES[pathway["cancer_site"]])
            staging_t = None
            staging_n = None
            staging_m = None
            overall_stage = "Benign"
        else:
            picked = random.choice(icd10_codes[pathway["cancer_site"]])
            code = picked["code"]
            diagnosis = picked["description"]
            staging_t = random.choices(["T1", "T2", "T3", "T4"], weights=[0.30, 0.32, 0.24, 0.14], k=1)[0]
            staging_n = random.choices(["N0", "N1", "N2", "N3"], weights=[0.45, 0.28, 0.19, 0.08], k=1)[0]
            staging_m = random.choices(["M0", "M1"], weights=[0.84, 0.16], k=1)[0]
            overall_stage = derive_stage(staging_t, staging_n, staging_m)

        records.append(
            {
                "diagnosis_id": str(uuid.uuid4()),
                "pathway_id": pathway["pathway_id"],
                "person_id": pathway["person_id"],
                "mrn": pathway["mrn"],
                "nhs_number": pathway["nhs_number"],
                "cancer_site": pathway["cancer_site"],
                "cancer_sub_site": pathway["cancer_sub_site"],
                "diagnosis": diagnosis,
                "diagnosis_icd_10_code": code,
                "diagnosis_date": diagnosis_date.isoformat(),
                "is_benign": is_benign,
                "staging_t": staging_t,
                "staging_n": staging_n,
                "staging_m": staging_m,
                "overall_stage": overall_stage,
                "source_system_name": pathway["source_system_name"],
                "last_refreshed_at_source_timestamp": current_timestamp(),
            }
        )

    return records


def main() -> None:
    pathways = load_pathways()
    records = generate_diagnoses(pathways)
    output_path = save_output(OUTPUT_FILE, records)
    print(f"Generated {len(records)} diagnoses for {len(pathways)} pathways -> {output_path}")


if __name__ == "__main__":
    main()
