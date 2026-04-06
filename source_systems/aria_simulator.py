"""Varian Aria simulator emitting treatment CSV extracts and SIU messages."""

from __future__ import annotations

from datetime import datetime, timedelta

from source_systems.common import build_aria_siu_message, render_csv

ARIA_FIELDS = ["cancer_treatment_id", "nhs_number", "treatment_group_id", "attendance_date", "ordered_date", "scheduled_date", "treatment_description", "treatment_type", "treatment_status", "regimen_name", "cycle_number", "max_cycles", "drug_name", "dose_mg", "dose_unit", "route", "bsa_m2", "weight_kg", "height_cm", "consultant_name", "treatment_site", "fractions_prescribed", "fraction_number", "total_dose_gy", "dose_per_fraction_gy", "machine_id", "source_system_name", "last_refreshed_at_source_timestamp"]


def generate_events(journeys: list[dict]) -> list[dict]:
    csv_rows, hl7_events = [], []
    for journey in journeys:
        patient = journey["patient"]
        aria = journey["aria"]
        csv_rows.extend(aria["treatments"])
        for index, appointment in enumerate(aria["appointments"], start=1):
            start_dt = datetime.fromisoformat(appointment["start_datetime"])
            booked_dt = start_dt - timedelta(hours=1)
            hl7_events.append({"timestamp": booked_dt.isoformat(), "source": "aria", "format": "hl7", "filename": f"{booked_dt.strftime('%Y%m%d%H%M%S')}_aria_s12_{appointment['appointment_id']}.hl7", "payload": build_aria_siu_message(patient, appointment, "S12", f"{journey['journey_id']}-ARIA-S12-{index}")})
            if appointment["status"] == "ATTENDED":
                hl7_events.append({"timestamp": start_dt.isoformat(), "source": "aria", "format": "hl7", "filename": f"{start_dt.strftime('%Y%m%d%H%M%S')}_aria_s14_{appointment['appointment_id']}.hl7", "payload": build_aria_siu_message(patient, appointment, "S14", f"{journey['journey_id']}-ARIA-S14-{index}")})

    extract_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    csv_event = {"timestamp": extract_time.isoformat(), "source": "aria", "format": "file", "subdir": "aria", "filename": f"aria_treatment_{extract_time.strftime('%Y%m%d%H%M%S')}.csv", "payload": render_csv(csv_rows, ARIA_FIELDS)}
    return [csv_event] + sorted(hl7_events, key=lambda item: item["timestamp"])
