"""Generate test results aligned to pathway timelines."""

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
        random_datetime_on,
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
        random_datetime_on,
        save_output,
        sorted_event_dates,
        timeline_dates,
    )


OUTPUT_FILE = "test_results.json"
TEST_CODES = {
    "Haemoglobin": "718-7",
    "Platelet count": "777-3",
    "White cell count": "6690-2",
    "Neutrophil count": "751-8",
    "Creatinine": "2160-0",
    "CEA": "2039-6",
    "PSA": "2857-1",
    "CA-125": "10334-1",
    "ALT": "1742-6",
    "Albumin": "1751-7",
}
SPECIALTY_BY_SITE = {
    "Haematology": "Haematology",
    "Breast": "Breast Surgery",
    "Lung": "Respiratory Oncology",
    "Colorectal": "Colorectal Surgery",
    "Upper GI": "Upper GI Surgery",
    "Head & Neck": "Head and Neck Oncology",
}


def numeric_value(test_name: str) -> tuple[str, float]:
    if test_name == "Haemoglobin":
        value = round(random.triangular(90, 170, 118))
    elif test_name == "Platelet count":
        value = round(random.triangular(100, 400, 240))
    elif test_name == "White cell count":
        value = round(random.triangular(3, 15, 7), 1)
    elif test_name == "Neutrophil count":
        value = round(random.triangular(1, 12, 4.5), 1)
    elif test_name == "Creatinine":
        value = round(random.triangular(40, 200, 92))
    elif test_name == "ALT":
        value = round(random.triangular(5, 80, 28))
    elif test_name == "Albumin":
        value = round(random.triangular(20, 50, 36))
    elif test_name == "CEA":
        value = round(random.triangular(0.5, 50, 4.8), 1)
    elif test_name == "PSA":
        value = round(random.triangular(0.5, 100, 8.7), 1)
    elif test_name == "CA-125":
        value = round(random.triangular(5, 500, 42), 1)
    elif test_name == "INR":
        value = round(random.triangular(0.9, 3.8, 1.2), 2)
    else:
        value = round(random.triangular(1, 100, 25), 1)
    return str(value), float(value)


def generate_test_results(pathways: list[dict[str, Any]], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    config = config or load_config()
    test_names = load_json(REFERENCE_DIR / "test_names.json")
    volume_cfg = config["generation"]["volume_per_patient"]["test_results"]
    records: list[dict[str, Any]] = []

    for pathway in pathways:
        if not pathway["timeline_skeleton"]["scenarios"].get("has_test_results"):
            continue

        dates = timeline_dates(pathway)
        window_start = dates["referral"] or pathway_end_date(pathway)
        window_end = pathway_end_date(pathway)
        test_dates = sorted_event_dates(window_start, window_end, choose_volume(volume_cfg), min_spacing_days=1)

        for test_day in test_dates:
            test_def = random.choice(test_names)
            value, value_double = numeric_value(test_def["test_name"])
            ordered_day = test_day - timedelta(days=random.randint(0, 2))
            expiry_date = None
            if test_def["test_name"] in {"INR"} and random.random() < 0.30:
                expiry_date = random_datetime_on(test_day + timedelta(days=3))

            records.append(
                {
                    "test_result_id": str(uuid.uuid4()),
                    "pathway_id": pathway["pathway_id"],
                    "person_id": pathway["person_id"],
                    "mrn": pathway["mrn"],
                    "nhs_number": pathway["nhs_number"],
                    "attendance_id": str(uuid.uuid4()),
                    "test_name": test_def["test_name"],
                    "test_id_code": TEST_CODES.get(test_def["test_name"]),
                    "test_date_time": random_datetime_on(test_day),
                    "test_ordered_timestamp": random_datetime_on(ordered_day),
                    "value": value,
                    "value_double": value_double,
                    "test_value_type": "Numeric",
                    "unit": test_def["unit"],
                    "ordering_specialty_name": SPECIALTY_BY_SITE.get(pathway["cancer_site"], "Oncology"),
                    "expiry_date": expiry_date,
                    "source_system_name": config["generation"]["source_systems"]["pathology"],
                    "last_refreshed_at_source_timestamp": current_timestamp(),
                }
            )

    return records


def main() -> None:
    pathways = load_pathways()
    records = generate_test_results(pathways)
    output_path = save_output(OUTPUT_FILE, records)
    print(f"Generated {len(records)} test results for {len(pathways)} pathways -> {output_path}")


if __name__ == "__main__":
    main()
