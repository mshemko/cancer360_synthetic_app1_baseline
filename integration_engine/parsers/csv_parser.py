"""CSV parsing helpers for integration staging."""

from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

import csv
import json
from pathlib import Path

from integration_engine import config


CSV_CLASSIFICATIONS = {
    "pas_patients": "patient",
    "pas_appointments": "appointment",
    "pas_encounters": "encounter",
    "sact_treatments": "treatment",
    "endoscopy_exams": "endoscopy",
    "ipt_referrals": "ipt",
    "tracking_comments": "comment",
}


def _clean_record(record: dict[str, str | None]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for key, value in record.items():
        clean_key = (key or "").strip()
        clean_value = "" if value is None else value.strip()
        cleaned[clean_key] = clean_value
    return cleaned


def parse_csv_file(filepath: str) -> list[dict]:
    path = Path(filepath)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames:
            reader.fieldnames = [(field or "").strip() for field in reader.fieldnames]
        return [_clean_record(row) for row in reader]


def classify_csv(filepath: str) -> str:
    stem = Path(filepath).stem.lower()
    return CSV_CLASSIFICATIONS.get(stem, stem)


def parse_csv_row_from_raw(payload_text: str) -> dict:
    loaded = json.loads(payload_text)
    if not isinstance(loaded, dict):
        raise ValueError("Expected CSV row payload to be a JSON object")
    return _clean_record(loaded)


def main() -> None:
    for path in sorted(config.CSV_DIR.glob("*.csv")):
        rows = parse_csv_file(str(path))
        print(f"{path.name}: {len(rows)} rows ({classify_csv(str(path))})")


if __name__ == "__main__":
    main()
