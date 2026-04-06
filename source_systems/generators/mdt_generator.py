"""Generate synthetic MDT meetings, bookings, and notes for Cancer 360."""

from __future__ import annotations

import random
import uuid
from datetime import date, datetime, time, timedelta
from typing import Any

try:
    from .generator_utils import (
        REFERENCE_DIR,
        choose_volume,
        current_timestamp,
        load_config,
        load_json,
        load_pathways,
        parse_date,
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
        parse_date,
        save_output,
        timeline_dates,
    )


MEETING_FILE = "mdt_meetings.json"
BOOKING_FILE = "mdt_bookings.json"
NOTE_FILE = "mdt_notes.json"

SITE_WEEKDAY = {
    "Breast": 1,
    "Lung": 2,
    "Colorectal": 3,
    "Prostate": 4,
    "Head & Neck": 1,
    "Upper GI": 2,
    "Haematology": 3,
    "Gynaecology": 4,
    "Skin": 0,
    "Urology": 1,
    "Brain/CNS": 2,
    "Sarcoma": 3,
}

NOTE_TEMPLATES = {
    "radiology": [
        "Patient discussed at {site} MDT. Imaging reviewed and appearances remain suspicious for malignancy. Recommend correlation with histology and proceed with next staging step.",
        "Radiology findings presented at MDT. Cross-sectional imaging demonstrates a focal lesion without definite distant disease. Consensus is to progress to definitive treatment planning.",
    ],
    "histology": [
        "Histology reviewed at MDT. Tissue confirms malignant pathology in keeping with the suspected primary site. Receptor and grading information noted for treatment planning.",
        "Pathology discussed at MDT. Microscopy supports the working diagnosis and sample adequacy was considered satisfactory. Clinical team to use result for decision to treat.",
    ],
    "outcome": [
        "MDT outcome recorded. Case accepted for onward management at {hospital}. Recommendation is to proceed to specialist clinic review and implement the agreed pathway.",
        "Formal MDT decision documented. Team consensus is for curative intent where feasible, with appropriate referral and follow-up actions allocated.",
    ],
    "general": [
        "Case reviewed at scheduled MDT. Performance status, comorbidities, and current investigations were considered. Further coordination with the booking team is required.",
        "Patient discussed in routine MDT forum. Notes reflect the agreed next step and confirm that outstanding items will be tracked before the next review.",
    ],
    "clinical_opinion": [
        "Consultant opinion at MDT favours treatment escalation given current disease burden. Surgical and oncological options were both reviewed with a preference for multidisciplinary follow-up.",
        "Clinical opinion recorded at MDT. Team advises specialist referral and timely diagnostic completion before final treatment commitment.",
    ],
}


def align_to_weekday(start_day: date, weekday: int) -> date:
    delta = (weekday - start_day.weekday()) % 7
    return start_day + timedelta(days=delta)


def meeting_datetime_for(day: date) -> str:
    hour = random.choice([8, 9, 12, 13, 16])
    minute = random.choice([0, 15, 30, 45])
    return datetime.combine(day, time(hour=hour, minute=minute)).astimezone().isoformat()


def meeting_status(meeting_day: date) -> str:
    if random.random() < 0.05:
        return "Cancelled"
    return "Completed" if meeting_day <= date.today() else "Scheduled"


def build_note_text(note_type: str, pathway: dict[str, Any]) -> str:
    template = random.choice(NOTE_TEMPLATES[note_type])
    return template.format(site=pathway["cancer_site"], hospital=pathway["hospital_site"])


def generate_mdt_entities(
    pathways: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    config = config or load_config()
    cancer_sites = load_json(REFERENCE_DIR / "cancer_sites.json")
    date_start = parse_date(config["generation"]["date_range"]["start"])
    date_end = parse_date(config["generation"]["date_range"]["end"])
    meeting_cfg = config["generation"]["volume_per_patient"]["mdt_meetings_per_site"]
    note_cfg = config["generation"]["volume_per_patient"]["mdt_notes_per_pathway"]
    source_name = config["generation"]["source_systems"]["mdt"]

    meetings: list[dict[str, Any]] = []
    bookings: list[dict[str, Any]] = []
    notes: list[dict[str, Any]] = []
    meetings_by_site: dict[str, list[dict[str, Any]]] = {}

    for site_row in cancer_sites:
        cancer_site = site_row["cancer_site"]
        weekday = SITE_WEEKDAY.get(cancer_site, 2)
        meeting_count = choose_volume(meeting_cfg)
        total_days = max(1, (date_end - date_start).days)
        step = max(7, total_days // max(meeting_count, 1))
        first_candidate = align_to_weekday(date_start + timedelta(days=random.randint(0, 6)), weekday)
        site_meetings: list[dict[str, Any]] = []
        for index in range(meeting_count):
            meeting_day = first_candidate + timedelta(days=index * step)
            if meeting_day > date_end:
                meeting_day = align_to_weekday(date_end - timedelta(days=random.randint(0, 28)), weekday)
            meeting = {
                "mdt_meeting_id": str(uuid.uuid4()),
                "cancer_site": cancer_site,
                "meeting_timestamp": meeting_datetime_for(meeting_day),
                "mdt_status": meeting_status(meeting_day),
                "source_system_name": source_name,
                "last_refreshed_at_source_timestamp": current_timestamp(),
            }
            site_meetings.append(meeting)
            meetings.append(meeting)
        site_meetings.sort(key=lambda row: row["meeting_timestamp"])
        meetings_by_site[cancer_site] = site_meetings

    for pathway in pathways:
        if not pathway["timeline_skeleton"]["scenarios"].get("has_mdt"):
            continue
        dates = timeline_dates(pathway)
        anchor = dates["diagnosis"] or dates["first_seen"] or dates["referral"]
        if anchor is None:
            continue

        matching_meetings = [
            meeting
            for meeting in meetings_by_site.get(pathway["cancer_site"], [])
            if parse_date(meeting["meeting_timestamp"][:10]) >= anchor
        ]
        if not matching_meetings:
            matching_meetings = meetings_by_site.get(pathway["cancer_site"], [])
        if not matching_meetings:
            continue

        booking_count = min(len(matching_meetings), random.randint(1, 3))
        selected_meetings = matching_meetings[:booking_count]
        pathway_booking_meetings: list[dict[str, Any]] = []

        for meeting in selected_meetings:
            bookings.append(
                {
                    "mdt_booking_id": str(uuid.uuid4()),
                    "meeting_id": meeting["mdt_meeting_id"],
                    "pathway_id": pathway["pathway_id"],
                    "cancer_site": pathway["cancer_site"],
                    "source_system_name": source_name,
                    "last_refreshed_at_source_timestamp": current_timestamp(),
                }
            )
            pathway_booking_meetings.append(meeting)

        note_count = choose_volume(note_cfg)
        if note_count <= 0:
            continue
        for _ in range(note_count):
            meeting = random.choice(pathway_booking_meetings)
            note_type = random.choice(list(NOTE_TEMPLATES.keys()))
            meeting_day = parse_date(meeting["meeting_timestamp"][:10])
            updated_at = datetime.combine(
                meeting_day + timedelta(days=random.randint(1, 3)),
                time(hour=random.randint(8, 17), minute=random.choice([0, 15, 30, 45])),
            ).astimezone()
            notes.append(
                {
                    "mdt_note_id": str(uuid.uuid4()),
                    "cancer_pathway_id": pathway["pathway_id"],
                    "meeting_id": meeting["mdt_meeting_id"],
                    "person_id": pathway["person_id"],
                    "mrn": pathway["mrn"],
                    "nhs_number": pathway["nhs_number"],
                    "note_type": note_type,
                    "mdt_note_text": build_note_text(note_type, pathway),
                    "last_updated_timestamp": updated_at.isoformat(),
                    "source_system_name": source_name,
                    "last_refreshed_at_source_timestamp": current_timestamp(),
                }
            )

    return meetings, bookings, notes


def main() -> None:
    pathways = load_pathways()
    meetings, bookings, notes = generate_mdt_entities(pathways)
    meeting_path = save_output(MEETING_FILE, meetings)
    booking_path = save_output(BOOKING_FILE, bookings)
    note_path = save_output(NOTE_FILE, notes)
    print(
        f"Generated {len(meetings)} MDT meetings, {len(bookings)} bookings, "
        f"and {len(notes)} notes for {len(pathways)} pathways -> "
        f"{meeting_path}, {booking_path}, {note_path}"
    )


if __name__ == "__main__":
    main()
