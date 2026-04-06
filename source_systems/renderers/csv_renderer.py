"""Render journey JSON into CSV extracts representing source-system exports."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
JOURNEY_DIR = ROOT / "source_systems" / "output" / "journeys"
OUTPUT_DIR = ROOT / "source_systems" / "output" / "csv"


def load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column) for column in columns})


def flatten_patients(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for row in rows:
        flattened.append(
            {
                "person_id": row.get("person_id"),
                "mrn": row.get("mrn"),
                "nhs_number": row.get("nhs_number"),
                "first_name": row.get("first_name"),
                "surname": row.get("surname"),
                "title": row.get("title"),
                "date_of_birth": row.get("date_of_birth"),
                "date_of_death": row.get("date_of_death"),
                "sex": row.get("sex"),
                "gender_identity": row.get("gender_identity"),
                "address_line_1": row.get("address_line_1"),
                "address_line_2": row.get("address_line_2"),
                "postcode": row.get("postcode"),
                "phone_number": row.get("phone_number"),
                "registered_gp": row.get("registered_gp", {}).get("name")
                if isinstance(row.get("registered_gp"), dict)
                else row.get("registered_gp"),
                "next_of_kin_name": row.get("next_of_kin_name"),
                "next_of_kin_number": row.get("next_of_kin_number"),
                "created_at": row.get("last_refreshed_at_source_timestamp"),
                "updated_at": row.get("last_refreshed_at_source_timestamp"),
                "source_system_name": row.get("source_system_name"),
                "last_refreshed_at_source_timestamp": row.get("last_refreshed_at_source_timestamp"),
            }
        )
    return flattened


def render_csv_outputs(
    journey_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, int]:
    journey_dir = journey_dir or JOURNEY_DIR
    output_dir = output_dir or OUTPUT_DIR

    patients = flatten_patients(load_json(journey_dir / "patients.json"))
    appointments = load_json(journey_dir / "appointments.json")
    encounters = load_json(journey_dir / "encounters.json")
    treatments = load_json(journey_dir / "treatments.json")
    endoscopy = load_json(journey_dir / "endoscopy.json")
    ipt = load_json(journey_dir / "ipt.json")
    comments = load_json(journey_dir / "tracking_comments.json")

    csv_specs = [
        (
            "pas_patients.csv",
            [
                "person_id",
                "mrn",
                "nhs_number",
                "first_name",
                "surname",
                "title",
                "date_of_birth",
                "date_of_death",
                "sex",
                "gender_identity",
                "address_line_1",
                "address_line_2",
                "postcode",
                "phone_number",
                "registered_gp",
                "next_of_kin_name",
                "next_of_kin_number",
                "created_at",
                "updated_at",
                "source_system_name",
                "last_refreshed_at_source_timestamp",
            ],
            patients,
        ),
        (
            "pas_appointments.csv",
            [
                "attendance_id",
                "person_id",
                "type",
                "booking_status",
                "start_date_time",
                "ordered_date",
                "date_time_booked",
                "created_at",
                "updated_at",
                "source_system_name",
                "last_refreshed_at_source_timestamp",
            ],
            appointments,
        ),
        (
            "pas_encounters.csv",
            [
                "encounter_id",
                "person_id",
                "title",
                "tci_status",
                "surgical_order_date",
                "admission_offer_timestamp",
                "attendance_date",
                "created_at",
                "updated_at",
                "source_system_name",
                "last_refreshed_at_source_timestamp",
            ],
            encounters,
        ),
        (
            "sact_treatments.csv",
            [
                "cancer_treatment_id",
                "person_id",
                "treatment_type",
                "treatment_description",
                "treatment_status",
                "attendance_date",
                "ordered_date",
                "scheduled_date",
                "poa_attendance_id",
                "poa_booking_status",
                "prescription_status",
                "is_prescription_prepared",
                "created_at",
                "updated_at",
                "source_system_name",
                "last_refreshed_at_source_timestamp",
            ],
            treatments,
        ),
        (
            "endoscopy_exams.csv",
            [
                "endoscopy_id",
                "person_id",
                "endoscopy_type",
                "modality",
                "endoscopy_priority",
                "exam_status",
                "ordered_date",
                "scheduled_date",
                "attendance_date",
                "report_prepared_date",
                "report_authorised_date",
                "is_reported",
                "endoscopy_report_text",
                "created_at",
                "updated_at",
                "source_system_name",
                "last_refreshed_at_source_timestamp",
            ],
            endoscopy,
        ),
        (
            "ipt_referrals.csv",
            [
                "tertiary_id",
                "pathway_id",
                "person_id",
                "nhs_number",
                "mrn",
                "tertiary_referral_type",
                "tertiary_reason",
                "tertiary_reason_code",
                "sending_org_id",
                "sending_org_name",
                "receiving_org_id",
                "receiving_org_name",
                "tertiary_sent_date",
                "tertiary_received_date",
                "tertiary_returned_date",
                "tertiary_sending_comment",
                "tertiary_return_comment",
                "is_sent",
                "is_received",
                "is_returned",
                "created_at",
                "updated_at",
                "source_system_name",
                "last_refreshed_at_source_timestamp",
            ],
            ipt,
        ),
        (
            "tracking_comments.csv",
            [
                "cancer_tracking_comment_id",
                "cancer_pathway_id",
                "comment_title",
                "comment_text",
                "created_by",
                "created_at_timestamp",
                "created_at",
                "updated_at",
                "source_system_name",
                "last_refreshed_at_source_timestamp",
            ],
            comments,
        ),
    ]

    for file_name, columns, rows in csv_specs:
        write_csv(output_dir / file_name, columns, rows)

    return {file_name: len(rows) for file_name, _, rows in csv_specs}


def main() -> None:
    summary = render_csv_outputs()
    print(f"Wrote {len(summary)} CSV extract files to {OUTPUT_DIR}")
    for file_name, count in summary.items():
        print(f"  - {file_name}: {count} rows")


if __name__ == "__main__":
    main()
