"""Parse Infoflex MDT JSON payloads."""

from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

import json
from pprint import pprint

from integration_engine import config


REQUIRED_FIELDS = ("meeting_id", "meeting_timestamp", "mdt_status")


def parse_mdt_json(json_text: str) -> dict:
    payload = json.loads(json_text)
    if not isinstance(payload, dict):
        raise ValueError("MDT JSON must be a single object")
    for field in REQUIRED_FIELDS:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")
    payload.setdefault("bookings", [])
    payload.setdefault("notes", [])
    return payload


def parse_json_file(filepath: str) -> list[dict]:
    payload = json.loads(open(filepath, "r", encoding="utf-8").read())
    if isinstance(payload, dict):
        return [parse_mdt_json(json.dumps(payload))]
    if isinstance(payload, list):
        return [parse_mdt_json(json.dumps(item)) for item in payload]
    raise ValueError("Unsupported JSON payload type")


def extract_meetings(parsed_list: list[dict]) -> list[dict]:
    meetings: list[dict] = []
    for record in parsed_list:
        meetings.append(
            {
                "meeting_id": record["meeting_id"],
                "meeting_timestamp": record.get("meeting_timestamp"),
                "mdt_status": record.get("mdt_status"),
                "cancer_site": record.get("cancer_site", ""),
                "source_system": record.get("source_system", "Infoflex"),
                "last_refreshed": record.get("last_refreshed", ""),
            }
        )
    return meetings


def extract_bookings(parsed_list: list[dict]) -> list[dict]:
    bookings: list[dict] = []
    for record in parsed_list:
        for booking in record.get("bookings", []):
            bookings.append(
                {
                    "meeting_id": record["meeting_id"],
                    "pathway_id": booking.get("pathway_id", ""),
                    "patient_nhs_number": booking.get("patient_nhs_number", ""),
                    "patient_name": booking.get("patient_name", ""),
                }
            )
    return bookings


def extract_notes(parsed_list: list[dict]) -> list[dict]:
    notes: list[dict] = []
    for record in parsed_list:
        for note in record.get("notes", []):
            flattened = dict(note)
            flattened["meeting_id"] = record["meeting_id"]
            notes.append(flattened)
    return notes


def main() -> None:
    sample = next(
        (path for path in config.JSON_DIR.glob("*.json") if path.name != "all_mdt_meetings.json"),
        None,
    )
    if not sample:
        print("No sample JSON file found.")
        return

    parsed = parse_json_file(str(sample))
    print(f"Sample file: {sample.name}")
    pprint(parsed[0])
    print(f"Meetings: {len(extract_meetings(parsed))}")
    print(f"Bookings: {len(extract_bookings(parsed))}")
    print(f"Notes: {len(extract_notes(parsed))}")


if __name__ == "__main__":
    main()
