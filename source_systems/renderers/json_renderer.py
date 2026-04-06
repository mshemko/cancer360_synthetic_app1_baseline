"""Render MDT journey data into Infoflex-style JSON messages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
JOURNEY_DIR = ROOT / "source_systems" / "output" / "journeys"
OUTPUT_DIR = ROOT / "source_systems" / "output" / "json"

MEETINGS_FILE = JOURNEY_DIR / "mdt_meetings.json"
BOOKINGS_FILE = JOURNEY_DIR / "mdt_bookings.json"
NOTES_FILE = JOURNEY_DIR / "mdt_notes.json"
PATHWAYS_FILE = JOURNEY_DIR / "pathways.json"


def load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def render_mdt_json(
    journey_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, int]:
    journey_dir = journey_dir or JOURNEY_DIR
    output_dir = output_dir or OUTPUT_DIR

    meetings = load_json(journey_dir / "mdt_meetings.json")
    bookings = load_json(journey_dir / "mdt_bookings.json")
    notes = load_json(journey_dir / "mdt_notes.json")
    pathways = {row["pathway_id"]: row for row in load_json(journey_dir / "pathways.json")}

    bookings_by_meeting: dict[str, list[dict[str, Any]]] = {}
    for booking in bookings:
        bookings_by_meeting.setdefault(booking["meeting_id"], []).append(booking)

    notes_by_meeting: dict[str, list[dict[str, Any]]] = {}
    for note in notes:
        notes_by_meeting.setdefault(note["meeting_id"], []).append(note)

    documents: list[dict[str, Any]] = []

    for meeting in meetings:
        meeting_id = meeting["mdt_meeting_id"]
        meeting_bookings = []
        for booking in bookings_by_meeting.get(meeting_id, []):
            pathway = pathways.get(booking["pathway_id"], {})
            meeting_bookings.append(
                {
                    "pathway_id": booking["pathway_id"],
                    "patient_nhs_number": pathway.get("nhs_number"),
                    "patient_name": pathway.get("full_name"),
                }
            )

        meeting_notes = [
            {
                "note_id": note["mdt_note_id"],
                "pathway_id": note["cancer_pathway_id"],
                "note_type": note["note_type"],
                "note_text": note["mdt_note_text"],
                "last_updated": note["last_updated_timestamp"],
            }
            for note in notes_by_meeting.get(meeting_id, [])
        ]

        document = {
            "source_system": "Infoflex",
            "message_type": "MDT_MEETING",
            "meeting_id": meeting_id,
            "meeting_timestamp": meeting.get("meeting_timestamp"),
            "mdt_status": meeting.get("mdt_status"),
            "cancer_site": meeting.get("cancer_site"),
            "bookings": meeting_bookings,
            "notes": meeting_notes,
            "last_refreshed": meeting.get("last_refreshed_at_source_timestamp"),
        }
        write_json(output_dir / f"infoflex_mdt_{meeting_id}.json", document)
        documents.append(document)

    write_json(output_dir / "all_mdt_meetings.json", documents)
    return {
        "meeting_files": len(meetings),
        "combined_files": 1,
        "total_documents": len(documents),
    }


def main() -> None:
    summary = render_mdt_json()
    print(
        f"Wrote {summary['meeting_files']} MDT meeting JSON files and {summary['combined_files']} combined file "
        f"to {OUTPUT_DIR} ({summary['total_documents']} meetings)"
    )


if __name__ == "__main__":
    main()
