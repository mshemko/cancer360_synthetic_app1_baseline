"""Generate synthetic Somerset tracking comments."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, time
from typing import Any

try:
    from .generator_utils import (
        choose_volume,
        current_timestamp,
        load_config,
        load_pathways,
        pathway_end_date,
        save_output,
        sorted_event_dates,
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
        sorted_event_dates,
        timeline_dates,
    )


OUTPUT_FILE = "tracking_comments.json"
STAFF_POOL = [
    "Emma Dawson",
    "Megan Fuller",
    "Olivia Barker",
    "Sophie Barrett",
    "Holly Pearson",
    "Chloe Warren",
    "Grace Turner",
    "Jessica Watts",
    "Hannah Moore",
    "Isla Palmer",
    "Lewis Harper",
    "Daniel Solomon",
    "Will Carroll",
    "Elia Benhamou",
    "Sarah Collins",
    "Amy Johnson",
    "Rachel Abbott",
    "Lauren Scott",
]

COMMENT_LIBRARY = {
    "Chasing histology": "Histology results remain outstanding following biopsy. Laboratory contacted for update and report expected shortly.",
    "MDT outcome": "Case discussed at MDT and outcome documented. Agreed action is to progress to the next stage of pathway management.",
    "Patient contacted": "Patient contacted by telephone and updated regarding current plan. They understand the next steps and will await appointment confirmation.",
    "Awaiting scan date": "Radiology booking remains pending. Request escalated to secure the earliest available slot within pathway targets.",
    "Referral to oncology": "Referral sent to oncology team for review and treatment planning. Booking team asked to prioritise the appointment.",
    "Appointment booked": "Relevant appointment has now been booked and patient notified. Admin team to monitor attendance outcome.",
    "Results reviewed": "Available results have been reviewed by the clinical team. No immediate change to current management plan required.",
}


def generate_comments(pathways: list[dict[str, Any]], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    config = config or load_config()
    volume_cfg = config["generation"]["volume_per_patient"]["tracking_comments"]
    source_name = config["generation"]["source_systems"]["pathway"]
    records: list[dict[str, Any]] = []
    titles = list(COMMENT_LIBRARY.keys())

    for pathway in pathways:
        if not pathway["timeline_skeleton"]["scenarios"].get("has_tracking_comments"):
            continue
        count = choose_volume(volume_cfg)
        if count <= 0:
            continue
        dates = timeline_dates(pathway)
        timeline_end = pathway_end_date(pathway)
        comment_days = sorted_event_dates(
            dates["referral"] or timeline_end,
            timeline_end,
            count,
            min_spacing_days=3,
        )
        for comment_day in comment_days:
            title = random.choice(titles)
            created_at = datetime.combine(
                comment_day,
                time(hour=random.randint(8, 17), minute=random.choice([0, 10, 15, 20, 30, 40, 45, 50])),
            ).astimezone()
            records.append(
                {
                    "cancer_tracking_comment_id": str(uuid.uuid4()),
                    "cancer_pathway_id": pathway["pathway_id"],
                    "person_id": pathway["person_id"],
                    "mrn": pathway["mrn"],
                    "nhs_number": pathway["nhs_number"],
                    "comment_title": title,
                    "comment_text": COMMENT_LIBRARY[title],
                    "created_by": random.choice(STAFF_POOL),
                    "created_at_timestamp": created_at.isoformat(),
                    "source_system_name": source_name,
                    "last_refreshed_at_source_timestamp": current_timestamp(),
                }
            )

    return records


def main() -> None:
    pathways = load_pathways()
    records = generate_comments(pathways)
    output_path = save_output(OUTPUT_FILE, records)
    print(f"Generated {len(records)} tracking comments for {len(pathways)} pathways -> {output_path}")


if __name__ == "__main__":
    main()
