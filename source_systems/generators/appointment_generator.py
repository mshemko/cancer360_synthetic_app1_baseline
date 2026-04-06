"""Generate outpatient appointments and link attendance IDs to existing outputs."""

from __future__ import annotations

import json
import random
import uuid
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

try:
    from .generator_utils import (
        OUTPUT_DIR,
        choose_volume,
        current_timestamp,
        load_config,
        load_pathways,
        pathway_end_date,
        save_output,
        timeline_dates,
    )
except ImportError:
    from generator_utils import (
        OUTPUT_DIR,
        choose_volume,
        current_timestamp,
        load_config,
        load_pathways,
        pathway_end_date,
        save_output,
        timeline_dates,
    )


OUTPUT_FILE = "appointments.json"
OUTPUT_PATH = OUTPUT_DIR / OUTPUT_FILE
TEST_RESULTS_FILE = OUTPUT_DIR / "test_results.json"
TREATMENTS_FILE = OUTPUT_DIR / "treatments.json"

CLINIC_TYPES = {
    "Breast": ["Breast New Patient", "Breast Surgical Follow Up", "Oncology Follow Up"],
    "Lung": ["Lung Rapid Access", "Thoracic Oncology Review", "Respiratory New Patient"],
    "Colorectal": ["Colorectal Surg 2WW New", "Colorectal Telephone Follow Up", "GI Oncology Review"],
    "Prostate": ["Urology Cancer New", "Prostate Follow Up", "Oncology Review"],
    "Head & Neck": ["ENT 2WW New", "Head and Neck Oncology Clinic", "Maxillofacial Follow Up"],
    "Upper GI": ["Upper GI 2WW New", "Hepatobiliary Review", "GI Oncology Follow Up"],
    "Haematology": ["Haematology Review", "Haematology New Patient", "Systemic Therapy Follow Up"],
    "Gynaecology": ["Gynae Rapid Access New", "Gynaecology Follow Up", "Gynae Oncology Review"],
    "Skin": ["Derm Telederm New", "Skin Cancer Follow Up", "Plastic Surgery Review"],
    "Urology": ["Urology 2WW New", "Cystoscopy Review", "Urology Follow Up"],
    "Brain/CNS": ["Neuro-oncology Review", "Neurosurgery Follow Up", "Neurology Tel New"],
    "Sarcoma": ["Sarcoma MDT Clinic", "Sarcoma Follow Up", "Orthopaedic Oncology Review"],
}


def appointment_datetime(day: date) -> datetime:
    return datetime.combine(
        day,
        time(hour=random.randint(8, 17), minute=random.choice([0, 10, 20, 30, 40, 50])),
    ).astimezone()


def booking_status(start_dt: datetime) -> str:
    if start_dt.date() > date.today():
        return random.choices(
            ["Booked", "Attended", "Cancelled"],
            weights=[0.72, 0.08, 0.20],
            k=1,
        )[0]
    return random.choices(
        ["Attended", "Booked", "Did Not Attend", "Cancelled"],
        weights=[0.70, 0.15, 0.05, 0.10],
        k=1,
    )[0]


def generate_appointments(pathways: list[dict[str, Any]], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    config = config or load_config()
    volume_cfg = config["generation"]["volume_per_patient"]["outpatient_appointments"]
    source_name = config["generation"]["source_systems"]["appointments"]
    records: list[dict[str, Any]] = []

    for pathway in pathways:
        if not pathway["timeline_skeleton"]["scenarios"].get("has_outpatient"):
            continue

        dates = timeline_dates(pathway)
        first_seen = dates["first_seen"] or dates["referral"]
        if first_seen is None:
            continue
        timeline_end = pathway_end_date(pathway)
        count = choose_volume(volume_cfg)
        clinic_types = CLINIC_TYPES.get(pathway["cancer_site"], ["Oncology New Patient", "Oncology Follow Up"])
        appointment_days: list[date] = [first_seen]
        current_day = first_seen

        for _ in range(1, count):
            current_day = min(timeline_end, current_day + timedelta(days=random.randint(14, 42)))
            appointment_days.append(current_day)

        for index, appointment_day in enumerate(appointment_days):
            start_dt = appointment_datetime(appointment_day)
            ordered_date = max(
                dates["referral"] or appointment_day,
                appointment_day - timedelta(days=random.randint(1, 14)),
            )
            booked_dt = datetime.combine(
                max(ordered_date, appointment_day - timedelta(days=random.randint(0, 10))),
                time(hour=random.randint(8, 17), minute=random.choice([0, 15, 30, 45])),
            ).astimezone()
            if booked_dt > start_dt:
                booked_dt = start_dt - timedelta(hours=random.randint(1, 48))
            status = booking_status(start_dt)
            clinic_type = clinic_types[0] if index == 0 else random.choice(clinic_types)
            records.append(
                {
                    "attendance_id": str(uuid.uuid4()),
                    "pathway_id": pathway["pathway_id"],
                    "person_id": pathway["person_id"],
                    "mrn": pathway["mrn"],
                    "nhs_number": pathway["nhs_number"],
                    "type": clinic_type,
                    "booking_status": status,
                    "start_date_time": start_dt.isoformat(),
                    "ordered_date": ordered_date.isoformat(),
                    "date_time_booked": booked_dt.isoformat(),
                    "source_system_name": source_name,
                    "last_refreshed_at_source_timestamp": current_timestamp(),
                }
            )

    return records


def load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_records(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")


def build_linked_appointment(
    row: dict[str, Any],
    start_dt: datetime,
    appointment_type: str,
) -> dict[str, Any]:
    ordered_date = (start_dt.date() - timedelta(days=1)).isoformat()
    booked_dt = (start_dt - timedelta(hours=2)).isoformat()
    return {
        "attendance_id": str(uuid.uuid4()),
        "pathway_id": row.get("pathway_id"),
        "person_id": row["person_id"],
        "mrn": row.get("mrn"),
        "nhs_number": row.get("nhs_number"),
        "type": appointment_type,
        "booking_status": "Attended",
        "start_date_time": start_dt.isoformat(),
        "ordered_date": ordered_date,
        "date_time_booked": booked_dt,
        "source_system_name": "PAS",
        "last_refreshed_at_source_timestamp": current_timestamp(),
    }


def link_attendance_ids(
    appointments: list[dict[str, Any]],
    appointment_output_path: Path | None = None,
    test_results_file: Path | None = None,
    treatments_file: Path | None = None,
) -> dict[str, int]:
    appointment_output_path = appointment_output_path or OUTPUT_PATH
    test_results_file = test_results_file or TEST_RESULTS_FILE
    treatments_file = treatments_file or TREATMENTS_FILE

    appointments_by_person: dict[str, list[dict[str, Any]]] = {}
    for appointment in appointments:
        appointments_by_person.setdefault(appointment["person_id"], []).append(appointment)
    for rows in appointments_by_person.values():
        rows.sort(key=lambda row: row["start_date_time"])

    linked_test_results = 0
    linked_treatments = 0
    created_fallback_appointments = 0

    test_results = load_records(test_results_file)
    for row in test_results:
        candidates = appointments_by_person.get(row["person_id"], [])
        target = datetime.fromisoformat(row["test_date_time"])
        if not candidates:
            fallback = build_linked_appointment(row, target, "Linked Diagnostic Review")
            appointments.append(fallback)
            appointments_by_person.setdefault(row["person_id"], []).append(fallback)
            candidates = appointments_by_person[row["person_id"]]
            created_fallback_appointments += 1
        best = min(
            candidates,
            key=lambda candidate: abs(datetime.fromisoformat(candidate["start_date_time"]) - target),
        )
        row["attendance_id"] = best["attendance_id"]
        linked_test_results += 1
    if test_results:
        save_records(test_results_file, test_results)

    treatments = load_records(treatments_file)
    for row in treatments:
        candidates = appointments_by_person.get(row["person_id"], [])
        target = datetime.combine(date.fromisoformat(row["attendance_date"]), time(hour=9)).astimezone()
        if not candidates:
            fallback = build_linked_appointment(row, target, "Pre-Treatment Assessment")
            appointments.append(fallback)
            appointments_by_person.setdefault(row["person_id"], []).append(fallback)
            candidates = appointments_by_person[row["person_id"]]
            created_fallback_appointments += 1
        best = min(
            candidates,
            key=lambda candidate: abs(datetime.fromisoformat(candidate["start_date_time"]) - target),
        )
        row["poa_attendance_id"] = best["attendance_id"]
        linked_treatments += 1
    if treatments:
        save_records(treatments_file, treatments)
    save_records(appointment_output_path, appointments)

    return {
        "test_results_linked": linked_test_results,
        "treatments_linked": linked_treatments,
        "fallback_appointments_created": created_fallback_appointments,
    }


def main() -> None:
    pathways = load_pathways()
    appointments = generate_appointments(pathways)
    output_path = save_output(OUTPUT_FILE, appointments)
    linked = link_attendance_ids(appointments)
    print(
        f"Generated {len(appointments)} outpatient appointments for {len(pathways)} pathways -> {output_path} "
        f"(linked {linked['test_results_linked']} test results and {linked['treatments_linked']} treatments; "
        f"created {linked['fallback_appointments_created']} linked appointments)"
    )


if __name__ == "__main__":
    main()
