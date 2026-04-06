"""Somerset Cancer Register simulator producing the six CSV extracts."""

from __future__ import annotations

from datetime import datetime, time, timedelta

from source_systems.common import render_csv

PATHWAY_FIELDS = ["pathway_id", "mrn", "nhs_number", "person_id", "first_name", "full_name", "surname", "original_pathway_start_date", "pathway_closed_date", "waiting_time_adjustment_days", "adjusted_pathway_start_date", "cancer_site", "cancer_sub_site", "hospital_site", "hospital_site_id", "pathway_status", "pathway_referral_route", "first_seen_site", "first_seen_site_ods_code", "28_day_breach_date", "31_day_breach_date", "62_day_breach_date", "patient_informed_date", "referral_received_date", "upgrade_date", "date_of_birth", "date_of_death", "decision_to_treat_date", "diagnosis", "diagnosis_icd_10_code", "diagnosis_date", "first_seen_date", "first_treatment_date", "first_treatment_type", "organisation_site_treatment", "treatment_site_ods_code", "treatment_site", "referral_source", "is_benign", "is_62_day_pathway_open", "is_31_day_pathway_open", "is_28_day_pathway_open", "is_any_pathway_type_open", "source_system_name", "last_refreshed_at_source_timestamp"]
TRACKING_FIELDS = ["cancer_tracking_comment_id", "cancer_pathway_id", "comment_text", "comment_title", "created_by", "created_at_timestamp", "source_system_name", "last_refreshed_at_source_timestamp"]
MEETING_FIELDS = ["mdt_meeting_id", "meeting_timestamp", "mdt_status", "source_system_name", "last_refreshed_at_source_timestamp"]
BOOKING_FIELDS = ["meeting_id", "pathway_id", "source_system_name", "last_refreshed_at_source_timestamp"]
NOTE_FIELDS = ["mdt_note_id", "mdt_note_text", "cancer_pathway_id", "meeting_id", "note_type", "last_updated_timestamp", "source_system_names", "last_refreshed_at_source_timestamp"]
IPT_FIELDS = ["tertiary_id", "pathway_id", "person_id", "nhs_number", "mrn", "tertiary_referral_type", "tertiary_reason_code", "tertiary_reason", "tertiary_sent_date", "tertiary_received_date", "tertiary_returned_date", "tertiary_sending_comment", "tertiary_return_comment", "sending_org_id", "sending_org_name", "receiving_org_id", "receiving_org_name", "is_sent", "is_received", "is_returned", "source_system_name", "last_refreshed_at_source_timestamp"]


def generate_events(journeys: list[dict]) -> list[dict]:
    extract_ts = datetime.now().strftime("%Y%m%d%H%M%S")
    exported_at = datetime.now().isoformat()
    pathways, tracking, meetings, bookings, notes, ipt_rows = [], [], [], [], [], []

    for journey in journeys:
        patient = journey["patient"]
        clinical = journey["clinical"]
        dates = journey["dates"]
        somerset = journey["somerset"]
        first_treatment = dates["first_treatment"]
        dtt = dates["decision_to_treat"]
        referral = dates["referral_received"]
        diagnosis = dates["diagnosis_date"]
        pathways.append({
            "pathway_id": somerset["pathway_id"], "mrn": patient["hospital_number"], "nhs_number": patient["nhs_number"], "person_id": clinical["somerset_person_id"], "first_name": patient["forename"], "full_name": patient["full_name"], "surname": patient["surname"], "original_pathway_start_date": referral, "pathway_closed_date": first_treatment if clinical["status"] in {"completed", "active_monitoring"} else None, "waiting_time_adjustment_days": 0, "adjusted_pathway_start_date": referral, "cancer_site": clinical["cancer_type_desc"], "cancer_sub_site": clinical["cancer_type_desc"], "hospital_site": "Cancer Centre", "hospital_site_id": "SITE01", "pathway_status": "Closed" if clinical["status"] in {"completed", "active_monitoring"} else "Open", "pathway_referral_route": clinical["referral_priority"], "first_seen_site": "RYJ", "first_seen_site_ods_code": "RYJ", "28_day_breach_date": _plus_days(referral, 28), "31_day_breach_date": _plus_days(dtt, 31) if dtt else None, "62_day_breach_date": _plus_days(referral, 62), "patient_informed_date": diagnosis, "referral_received_date": referral, "upgrade_date": None, "date_of_birth": patient["date_of_birth"], "date_of_death": None, "decision_to_treat_date": dtt, "diagnosis": f"{clinical['cancer_type_desc']} malignancy", "diagnosis_icd_10_code": clinical["icd10"], "diagnosis_date": diagnosis, "first_seen_date": dates["first_seen"], "first_treatment_date": first_treatment, "first_treatment_type": clinical["first_treatment_type"], "organisation_site_treatment": "RYJ", "treatment_site_ods_code": "RYJ", "treatment_site": "Cancer Centre", "referral_source": clinical["referral_source"], "is_benign": False, "is_62_day_pathway_open": first_treatment is None, "is_31_day_pathway_open": dtt is not None and first_treatment is None, "is_28_day_pathway_open": diagnosis is None, "is_any_pathway_type_open": clinical["status"] not in {"completed", "active_monitoring"}, "source_system_name": "Somerset Cancer Register", "last_refreshed_at_source_timestamp": exported_at,
        })
        for index, comment in enumerate(somerset["tracking_comments"], start=1):
            tracking.append({"cancer_tracking_comment_id": f"{somerset['pathway_id']}-C{index}", "cancer_pathway_id": somerset["pathway_id"], "comment_text": comment["text"], "comment_title": comment["title"], "created_by": comment["created_by"], "created_at_timestamp": comment["created_at"], "source_system_name": "Somerset Cancer Register", "last_refreshed_at_source_timestamp": exported_at})
        meetings.append({"mdt_meeting_id": journey["mdt"]["meeting_id"], "meeting_timestamp": journey["mdt"]["meeting_timestamp"] or datetime.now().isoformat(), "mdt_status": journey["mdt"]["status"], "source_system_name": "Somerset Cancer Register", "last_refreshed_at_source_timestamp": exported_at})
        bookings.append({"meeting_id": journey["mdt"]["meeting_id"], "pathway_id": somerset["pathway_id"], "source_system_name": "Somerset Cancer Register", "last_refreshed_at_source_timestamp": exported_at})
        notes.append({"mdt_note_id": f"{journey['mdt']['meeting_id']}-{somerset['pathway_id']}", "mdt_note_text": journey["mdt"]["note_text"], "cancer_pathway_id": somerset["pathway_id"], "meeting_id": journey["mdt"]["meeting_id"], "note_type": "outcome", "last_updated_timestamp": journey["mdt"]["meeting_timestamp"] or datetime.now().isoformat(), "source_system_names": "Somerset Cancer Register", "last_refreshed_at_source_timestamp": exported_at})
        if somerset["ipt"]:
            ipt_rows.append({"pathway_id": somerset["pathway_id"], "person_id": clinical["somerset_person_id"], "source_system_name": "Somerset Cancer Register", "last_refreshed_at_source_timestamp": exported_at, "is_sent": True, "is_received": False, "is_returned": False, **somerset["ipt"]})

    file_specs = [("somerset_pathways", PATHWAY_FIELDS, pathways, datetime.combine(datetime.now().date(), time(8, 0))), ("somerset_tracking", TRACKING_FIELDS, tracking, datetime.combine(datetime.now().date(), time(8, 5))), ("somerset_mdt_meetings", MEETING_FIELDS, meetings, datetime.combine(datetime.now().date(), time(8, 10))), ("somerset_mdt_bookings", BOOKING_FIELDS, bookings, datetime.combine(datetime.now().date(), time(8, 12))), ("somerset_mdt_notes", NOTE_FIELDS, notes, datetime.combine(datetime.now().date(), time(8, 15))), ("somerset_ipt", IPT_FIELDS, ipt_rows, datetime.combine(datetime.now().date(), time(8, 18)))]
    return [{"timestamp": event_time.isoformat(), "source": "somerset", "format": "file", "subdir": "somerset", "filename": f"{prefix}_{extract_ts}.csv", "payload": render_csv(rows, fieldnames)} for prefix, fieldnames, rows, event_time in file_specs]


def _plus_days(value: str | None, days: int) -> str | None:
    if not value:
        return None
    return (datetime.fromisoformat(value).date() + timedelta(days=days)).isoformat()
