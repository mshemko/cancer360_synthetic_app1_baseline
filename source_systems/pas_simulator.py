"""PAS/Cerner simulator that emits ADT and SIU HL7 messages."""

from __future__ import annotations

from datetime import datetime, time

from source_systems.common import build_pas_adt_message, build_pas_siu_message, parse_iso_date


def generate_events(journeys: list[dict]) -> list[dict]:
    events: list[dict] = []
    for journey in journeys:
        patient = journey["patient"]
        for appointment in journey["pas"]["appointments"]:
            appt_dt = datetime.fromisoformat(f"{appointment['date']}T{appointment['time']}")
            events.append({"timestamp": appt_dt.isoformat(), "source": "pas", "format": "hl7", "filename": f"{appt_dt.strftime('%Y%m%d%H%M%S')}_pas_a04_{appointment['source_appt_id']}.hl7", "payload": build_pas_adt_message(patient, appointment, "ADT^A04", f"{journey['journey_id']}-A04")})
            booked_dt = appt_dt.replace(hour=max(7, appt_dt.hour - 1))
            events.append({"timestamp": booked_dt.isoformat(), "source": "pas", "format": "hl7", "filename": f"{booked_dt.strftime('%Y%m%d%H%M%S')}_pas_s12_{appointment['source_appt_id']}.hl7", "payload": build_pas_siu_message(patient, appointment, "S12", f"{journey['journey_id']}-S12-{appointment['source_appt_id']}")})
            if appointment["attendance_status"] == "attended":
                attended_dt = appt_dt.replace(hour=min(17, appt_dt.hour + 1))
                events.append({"timestamp": attended_dt.isoformat(), "source": "pas", "format": "hl7", "filename": f"{attended_dt.strftime('%Y%m%d%H%M%S')}_pas_s14_{appointment['source_appt_id']}.hl7", "payload": build_pas_siu_message(patient, appointment, "S14", f"{journey['journey_id']}-S14-{appointment['source_appt_id']}")})

        for admission in journey["pas"]["admissions"]:
            admit_dt = datetime.combine(parse_iso_date(admission["admission_date"]), time(7, 30))
            discharge_dt = datetime.combine(parse_iso_date(admission["discharge_date"]), time(11, 0))
            pseudo_appt = {"date": admission["admission_date"], "time": "07:30", "clinic_code": admission["ward_name"][:8].upper(), "clinic_name": admission["ward_name"], "appointment_type": "inpatient", "attendance_status": "attended", "consultant_name": admission["consultant_name"], "source_appt_id": admission["episode_id"]}
            events.append({"timestamp": admit_dt.isoformat(), "source": "pas", "format": "hl7", "filename": f"{admit_dt.strftime('%Y%m%d%H%M%S')}_pas_a01_{admission['episode_id']}.hl7", "payload": build_pas_adt_message(patient, pseudo_appt, "ADT^A01", f"{journey['journey_id']}-A01")})
            events.append({"timestamp": discharge_dt.isoformat(), "source": "pas", "format": "hl7", "filename": f"{discharge_dt.strftime('%Y%m%d%H%M%S')}_pas_a03_{admission['episode_id']}.hl7", "payload": build_pas_adt_message(patient, pseudo_appt, "ADT^A03", f"{journey['journey_id']}-A03")})
    return sorted(events, key=lambda item: item["timestamp"])
