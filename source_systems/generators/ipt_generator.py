"""Generate synthetic inter-provider transfer records."""

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


OUTPUT_FILE = "ipt.json"
REASONS = [
    ("Specialist opinion", "SPEC_OP"),
    ("Treatment", "TREAT"),
    ("Diagnostics", "DIAG"),
    ("Shared care", "SHARE"),
    ("Surgery", "SURG"),
]


def short_comment(reason: str) -> tuple[str, str | None]:
    sending = {
        "Specialist opinion": "Referral for specialist opinion on complex cancer pathway management.",
        "Treatment": "Referral for tertiary treatment delivery at partner organisation.",
        "Diagnostics": "Transfer initiated for specialist diagnostics not available locally.",
        "Shared care": "Shared-care referral agreed between trusts for ongoing pathway management.",
        "Surgery": "Referral for specialist surgical review and intervention.",
    }[reason]
    returned = None
    if random.random() < 0.5:
        returned = {
            "Specialist opinion": "Patient reviewed. Specialist advice returned to referring trust for onward management.",
            "Treatment": "Patient assessed and treatment plan agreed. Continue pathway in line with specialist recommendation.",
            "Diagnostics": "Diagnostic work-up completed and results sent back to referring team.",
            "Shared care": "Shared care accepted and return communication sent with next steps.",
            "Surgery": "Patient reviewed. Recommend proceeding with surgery at referring trust or booked tertiary intervention.",
        }[reason]
    return sending, returned


def generate_ipt(pathways: list[dict[str, Any]], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    config = config or load_config()
    hospitals = load_json(REFERENCE_DIR / "hospital_sites.json")
    volume_cfg = config["generation"]["volume_per_patient"]["ipt_per_pathway"]
    source_name = config["generation"]["source_systems"]["pathway"]
    records: list[dict[str, Any]] = []

    hospital_lookup = {row["hospital_site_id"]: row for row in hospitals}

    for pathway in pathways:
        if not pathway["timeline_skeleton"]["scenarios"].get("has_ipt"):
            continue
        dates = timeline_dates(pathway)
        timeline_end = pathway_end_date(pathway)
        count = max(1, choose_volume(volume_cfg))
        event_days = sorted_event_dates(
            dates["diagnosis"] or dates["first_seen"] or dates["referral"] or timeline_end,
            timeline_end,
            count,
            min_spacing_days=7,
        )
        pathway_hospital = hospital_lookup.get(pathway["hospital_site_id"], hospitals[0])

        for event_day in event_days:
            reason, reason_code = random.choice(REASONS)
            referral_type = random.choice(["Sent", "Received"])
            other_hospital = random.choice(
                [row for row in hospitals if row["hospital_site_id"] != pathway_hospital["hospital_site_id"]]
            )
            if referral_type == "Sent":
                sending_org = pathway_hospital
                receiving_org = other_hospital
            else:
                sending_org = other_hospital
                receiving_org = pathway_hospital

            sent_date = event_day
            received_date = min(timeline_end, sent_date + timedelta(days=random.randint(1, 5)))
            sending_comment, return_comment = short_comment(reason)
            returned_date = None
            if return_comment:
                returned_date = min(timeline_end, received_date + timedelta(days=random.randint(7, 60)))

            records.append(
                {
                    "tertiary_id": str(uuid.uuid4()),
                    "pathway_id": pathway["pathway_id"],
                    "person_id": pathway["person_id"],
                    "nhs_number": pathway["nhs_number"],
                    "mrn": pathway["mrn"],
                    "tertiary_referral_type": referral_type,
                    "tertiary_reason": reason,
                    "tertiary_reason_code": reason_code,
                    "sending_org_id": sending_org["hospital_site_id"],
                    "sending_org_name": sending_org["hospital_site"],
                    "receiving_org_id": receiving_org["hospital_site_id"],
                    "receiving_org_name": receiving_org["hospital_site"],
                    "tertiary_sent_date": sent_date.isoformat(),
                    "tertiary_received_date": received_date.isoformat(),
                    "tertiary_returned_date": returned_date.isoformat() if returned_date else None,
                    "tertiary_sending_comment": sending_comment,
                    "tertiary_return_comment": return_comment,
                    "is_sent": referral_type == "Sent",
                    "is_received": referral_type == "Received",
                    "is_returned": returned_date is not None,
                    "source_system_name": source_name,
                    "last_refreshed_at_source_timestamp": current_timestamp(),
                }
            )

    return records


def main() -> None:
    pathways = load_pathways()
    records = generate_ipt(pathways)
    output_path = save_output(OUTPUT_FILE, records)
    print(f"Generated {len(records)} IPT records for {len(pathways)} pathways -> {output_path}")


if __name__ == "__main__":
    main()
