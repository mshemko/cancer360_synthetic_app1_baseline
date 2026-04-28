"""Load parsed payloads into staging tables."""

from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from pprint import pprint
from typing import Any

from integration_engine import config
from integration_engine.parsers.csv_parser import parse_csv_file


_SCHEMA_READY = False


def ensure_staging_schema(connection) -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    migration_file = config.MIGRATIONS_DIR / "add_staging_columns.sql"
    if migration_file.exists():
        sql_text = migration_file.read_text(encoding="utf-8")
        with connection.cursor() as cursor:
            cursor.execute(sql_text)
        connection.commit()
    _SCHEMA_READY = True


def _record_exists(table: str, key_field: str, key_value: str, connection) -> bool:
    if not key_value:
        return False
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT 1 FROM {table} WHERE {key_field} = %s LIMIT 1", (key_value,))
        return cursor.fetchone() is not None


def _insert_rows_with_status(table: str, rows: list[dict[str, Any]], connection) -> int:
    inserted = 0
    for row in rows:
        columns = list(row.keys())
        query = (
            f"INSERT INTO {table} ({', '.join(columns)}, processed_at, mapping_status) "
            f"VALUES ({', '.join(['%s'] * len(columns))}, NOW(), %s)"
        )
        with connection.cursor() as cursor:
            cursor.execute(query, [row[column] for column in columns] + ["staged"])
        inserted += 1
    connection.commit()
    return inserted


def load_staging_patient(records: list[dict], correlation_id: str, connection) -> int:
    ensure_staging_schema(connection)
    rows = []
    for record in records:
        if _record_exists("staging.pas_patient", "person_id", record.get("person_id", ""), connection):
            continue
        rows.append(
            {
                "correlation_id": correlation_id,
                "person_id": record.get("person_id"),
                "mrn": record.get("mrn"),
                "nhs_number": record.get("nhs_number"),
                "first_name": record.get("first_name"),
                "surname": record.get("surname"),
                "date_of_birth": record.get("date_of_birth"),
                "date_of_death": record.get("date_of_death"),
                "sex": record.get("sex"),
                "title": record.get("title"),
                "gender_identity": record.get("gender_identity"),
                "address_line_1": record.get("address_line_1"),
                "address_line_2": record.get("address_line_2"),
                "postcode": record.get("postcode"),
                "phone_number": record.get("phone_number"),
                "registered_gp": record.get("registered_gp"),
                "next_of_kin_name": record.get("next_of_kin_name"),
                "next_of_kin_number": record.get("next_of_kin_number"),
                "source_system_name": record.get("source_system_name"),
                "last_refreshed_at_source_timestamp": record.get("last_refreshed_at_source_timestamp"),
            }
        )
    return _insert_rows_with_status("staging.pas_patient", rows, connection) if rows else 0


def load_staging_pathway(records: list[dict], correlation_id: str, connection) -> int:
    ensure_staging_schema(connection)
    rows = []
    for record in records:
        if _record_exists("staging.somerset_pathway", "pathway_id", record.get("pathway_id", ""), connection):
            continue
        rows.append(
            {
                "correlation_id": correlation_id,
                "pathway_id": record.get("pathway_id"),
                "person_id": record.get("person_id"),
                "patient_nhs_number": record.get("nhs_number"),
                "mrn": record.get("mrn"),
                "first_name": record.get("first_name"),
                "surname": record.get("surname"),
                "date_of_birth": record.get("date_of_birth"),
                "cancer_site": record.get("cancer_site"),
                "cancer_sub_site": record.get("cancer_sub_site"),
                "pathway_start_date": record.get("adjusted_start_date"),
                "original_start_date": record.get("original_start_date"),
                "adjusted_start_date": record.get("adjusted_start_date"),
                "referral_route": record.get("referral_route"),
                "referral_source": record.get("referral_source"),
                "first_seen_date": record.get("first_seen_date"),
                "diagnosis_date": record.get("diagnosis_date"),
                "decision_to_treat_date": record.get("decision_to_treat_date"),
                "treatment_start_date": record.get("first_treatment_date"),
                "first_treatment_date": record.get("first_treatment_date"),
                "closed_date": record.get("closed_date"),
                "diagnosis": record.get("diagnosis"),
                "diagnosis_icd_10": record.get("diagnosis_icd_10"),
                "is_benign": record.get("is_benign"),
                "hospital_site_id": record.get("hospital_site_id"),
                "hospital_site_name": record.get("hospital_site_name"),
                "pathway_status": record.get("pathway_status"),
                "source_system_name": record.get("source_system"),
                "last_refreshed_at_source_timestamp": record.get("last_refreshed"),
            }
        )
    return _insert_rows_with_status("staging.somerset_pathway", rows, connection) if rows else 0


def load_staging_radiology(records: list[dict], correlation_id: str, connection) -> int:
    ensure_staging_schema(connection)
    rows = []
    for record in records:
        obr = record.get("OBR", {})
        pid = record.get("PID", {})
        if _record_exists(
            "staging.radiology_hl7",
            "message_control_id",
            record.get("MSH", {}).get("message_control_id", ""),
            connection,
        ):
            continue
        report_text = " ".join(obs.get("value", "") for obs in record.get("OBX", []) if obs.get("value"))
        rows.append(
            {
                "correlation_id": correlation_id,
                "message_control_id": record.get("MSH", {}).get("message_control_id"),
                "patient_nhs_number": pid.get("nhs_number"),
                "mrn": pid.get("mrn"),
                "person_id": "",
                "pathway_id": "",
                "result_id": obr.get("order_number"),
                "exam_type": obr.get("exam_type"),
                "report_text": report_text,
                "observed_at": obr.get("ordered_datetime"),
                "reported_at": record.get("MSH", {}).get("timestamp"),
                "modality": "",
                "priority": "",
                "scheduled_date": "",
                "attendance_date": "",
                "exam_status": obr.get("result_status"),
                "source_system_name": record.get("MSH", {}).get("sending_application"),
                "last_refreshed_at_source_timestamp": record.get("MSH", {}).get("timestamp"),
            }
        )
    return _insert_rows_with_status("staging.radiology_hl7", rows, connection) if rows else 0


def load_staging_histology(records: list[dict], correlation_id: str, connection) -> int:
    ensure_staging_schema(connection)
    rows = []
    for record in records:
        obr = record.get("OBR", {})
        pid = record.get("PID", {})
        if _record_exists(
            "staging.pathology_hl7",
            "message_control_id",
            record.get("MSH", {}).get("message_control_id", ""),
            connection,
        ):
            continue
        report_text = " ".join(obs.get("value", "") for obs in record.get("OBX", []) if obs.get("value"))
        rows.append(
            {
                "correlation_id": correlation_id,
                "message_control_id": record.get("MSH", {}).get("message_control_id"),
                "patient_nhs_number": pid.get("nhs_number"),
                "mrn": pid.get("mrn"),
                "person_id": "",
                "pathway_id": "",
                "result_id": obr.get("order_number"),
                "test_name": obr.get("exam_type"),
                "result_text": report_text,
                "result_value": "",
                "unit": "",
                "observed_at": obr.get("ordered_datetime"),
                "reported_at": record.get("MSH", {}).get("timestamp"),
                "source_system_name": record.get("MSH", {}).get("sending_application"),
                "last_refreshed_at_source_timestamp": record.get("MSH", {}).get("timestamp"),
            }
        )
    return _insert_rows_with_status("staging.pathology_hl7", rows, connection) if rows else 0


def load_staging_test_result(records: list[dict], correlation_id: str, connection) -> int:
    ensure_staging_schema(connection)
    rows = []
    for record in records:
        obr = record.get("OBR", {})
        pid = record.get("PID", {})
        if _record_exists(
            "staging.pathology_hl7",
            "message_control_id",
            record.get("MSH", {}).get("message_control_id", ""),
            connection,
        ):
            continue
        first_obx = record.get("OBX", [{}])[0] if record.get("OBX") else {}
        rows.append(
            {
                "correlation_id": correlation_id,
                "message_control_id": record.get("MSH", {}).get("message_control_id"),
                "patient_nhs_number": pid.get("nhs_number"),
                "mrn": pid.get("mrn"),
                "person_id": "",
                "pathway_id": "",
                "result_id": obr.get("order_number"),
                "test_name": obr.get("exam_type"),
                "result_text": "",
                "result_value": first_obx.get("value"),
                "unit": first_obx.get("unit"),
                "observed_at": obr.get("ordered_datetime"),
                "reported_at": record.get("MSH", {}).get("timestamp"),
                "source_system_name": record.get("MSH", {}).get("sending_application"),
                "last_refreshed_at_source_timestamp": record.get("MSH", {}).get("timestamp"),
            }
        )
    return _insert_rows_with_status("staging.pathology_hl7", rows, connection) if rows else 0


def load_staging_treatment(records: list[dict], correlation_id: str, connection) -> int:
    ensure_staging_schema(connection)
    rows = []
    for record in records:
        course_id = record.get("cancer_treatment_id", "")
        if _record_exists("staging.sact_treatment", "treatment_id", course_id, connection):
            continue
        rows.append(
            {
                "correlation_id": correlation_id,
                "nhs_number": record.get("nhs_number"),
                "mrn": record.get("mrn"),
                "person_id": record.get("person_id"),
                "pathway_id": record.get("pathway_id"),
                "treatment_id": course_id,
                "treatment_type": record.get("treatment_type"),
                "regimen_name": record.get("treatment_description"),
                "ordered_date": record.get("ordered_date"),
                "scheduled_date": record.get("scheduled_date"),
                "attendance_date": record.get("attendance_date"),
                "poa_attendance_id": record.get("poa_attendance_id"),
                "treatment_status": record.get("treatment_status"),
                "prescription_status": record.get("prescription_status"),
                "is_prescription_prepared": str(record.get("is_prescription_prepared")),
                "source_system_name": record.get("source_system_name"),
                "last_refreshed_at_source_timestamp": record.get("last_refreshed_at_source_timestamp"),
            }
        )
    return _insert_rows_with_status("staging.sact_treatment", rows, connection) if rows else 0


def load_staging_mdt(meetings: list[dict], bookings: list[dict], notes: list[dict], correlation_id: str, connection) -> dict:
    ensure_staging_schema(connection)
    summary = {"meetings": 0, "bookings": 0, "notes": 0}

    meeting_rows = []
    for meeting in meetings:
        if _record_exists("staging.mdt_source", "meeting_id", meeting.get("meeting_id", ""), connection):
            continue
        meeting_rows.append(
            {
                "correlation_id": correlation_id,
                "record_type": "meeting",
                "meeting_id": meeting.get("meeting_id"),
                "pathway_id": "",
                "patient_nhs_number": "",
                "patient_name": "",
                "patient_mrn": "",
                "patient_person_id": "",
                "note_type": "",
                "note_text": "",
                "meeting_timestamp": meeting.get("meeting_timestamp"),
                "mdt_status": meeting.get("mdt_status"),
                "last_updated_timestamp": "",
                "source_system_name": meeting.get("source_system", "Infoflex"),
                "last_refreshed_at_source_timestamp": meeting.get("last_refreshed"),
            }
        )
    if meeting_rows:
        summary["meetings"] = _insert_rows_with_status("staging.mdt_source", meeting_rows, connection)

    booking_rows = []
    for booking in bookings:
        booking_id = f"{booking.get('meeting_id')}::{booking.get('pathway_id')}"
        if _record_exists("staging.mdt_source", "mdt_booking_id", booking_id, connection):
            continue
        booking_rows.append(
            {
                "correlation_id": correlation_id,
                "record_type": "booking",
                "meeting_id": booking.get("meeting_id"),
                "mdt_booking_id": booking_id,
                "pathway_id": booking.get("pathway_id"),
                "patient_nhs_number": booking.get("patient_nhs_number"),
                "patient_name": booking.get("patient_name"),
                "patient_mrn": "",
                "patient_person_id": "",
                "note_type": "",
                "note_text": "",
                "meeting_timestamp": "",
                "mdt_status": "",
                "last_updated_timestamp": "",
                "source_system_name": "Infoflex",
                "last_refreshed_at_source_timestamp": "",
            }
        )
    if booking_rows:
        summary["bookings"] = _insert_rows_with_status("staging.mdt_source", booking_rows, connection)

    note_rows = []
    for note in notes:
        if _record_exists("staging.mdt_source", "mdt_note_id", note.get("note_id", ""), connection):
            continue
        note_rows.append(
            {
                "correlation_id": correlation_id,
                "record_type": "note",
                "meeting_id": note.get("meeting_id"),
                "mdt_note_id": note.get("note_id"),
                "pathway_id": note.get("pathway_id"),
                "patient_nhs_number": "",
                "patient_name": "",
                "patient_mrn": "",
                "patient_person_id": "",
                "note_type": note.get("note_type"),
                "note_text": note.get("note_text"),
                "meeting_timestamp": "",
                "mdt_status": "",
                "last_updated_timestamp": note.get("last_updated"),
                "source_system_name": "Infoflex",
                "last_refreshed_at_source_timestamp": "",
            }
        )
    if note_rows:
        summary["notes"] = _insert_rows_with_status("staging.mdt_source", note_rows, connection)

    return summary


def load_staging_endoscopy(records: list[dict], correlation_id: str, connection) -> int:
    ensure_staging_schema(connection)
    rows = []
    for record in records:
        procedure_id = record.get("endoscopy_id", "")
        if _record_exists("staging.endoscopy_source", "procedure_id", procedure_id, connection):
            continue
        rows.append(
            {
                "correlation_id": correlation_id,
                "nhs_number": record.get("nhs_number"),
                "mrn": record.get("mrn"),
                "person_id": record.get("person_id"),
                "pathway_id": record.get("pathway_id"),
                "procedure_id": procedure_id,
                "procedure_type": record.get("endoscopy_type"),
                "report_text": record.get("endoscopy_report_text"),
                "procedure_date": record.get("attendance_date"),
                "status": record.get("exam_status"),
                "modality": record.get("modality"),
                "priority": record.get("endoscopy_priority"),
                "ordered_date": record.get("ordered_date"),
                "scheduled_date": record.get("scheduled_date"),
                "attendance_date": record.get("attendance_date"),
                "report_prepared_date": record.get("report_prepared_date"),
                "report_authorised_date": record.get("report_authorised_date"),
                "is_reported": str(record.get("is_reported")),
                "source_system_name": record.get("source_system_name"),
                "last_refreshed_at_source_timestamp": record.get("last_refreshed_at_source_timestamp"),
            }
        )
    return _insert_rows_with_status("staging.endoscopy_source", rows, connection) if rows else 0


def load_staging_appointment(records: list[dict], correlation_id: str, connection) -> int:
    ensure_staging_schema(connection)
    rows = []
    for record in records:
        if _record_exists("staging.pas_appointment", "attendance_id", record.get("attendance_id", ""), connection):
            continue
        rows.append(
            {
                "correlation_id": correlation_id,
                "attendance_id": record.get("attendance_id"),
                "person_id": record.get("person_id"),
                "pathway_id": record.get("pathway_id"),
                "patient_nhs_number": record.get("nhs_number"),
                "mrn": record.get("mrn"),
                "appointment_type": record.get("type"),
                "booking_status": record.get("booking_status"),
                "start_date_time": record.get("start_date_time"),
                "ordered_date": record.get("ordered_date"),
                "date_time_booked": record.get("date_time_booked"),
                "source_system_name": record.get("source_system_name"),
                "last_refreshed_at_source_timestamp": record.get("last_refreshed_at_source_timestamp"),
            }
        )
    return _insert_rows_with_status("staging.pas_appointment", rows, connection) if rows else 0


def load_staging_encounter(records: list[dict], correlation_id: str, connection) -> int:
    ensure_staging_schema(connection)
    rows = []
    for record in records:
        if _record_exists("staging.pas_encounter", "encounter_id", record.get("encounter_id", ""), connection):
            continue
        rows.append(
            {
                "correlation_id": correlation_id,
                "encounter_id": record.get("encounter_id"),
                "person_id": record.get("person_id"),
                "pathway_id": record.get("pathway_id"),
                "patient_nhs_number": record.get("nhs_number"),
                "mrn": record.get("mrn"),
                "title": record.get("title"),
                "tci_status": record.get("tci_status"),
                "surgical_order_date": record.get("surgical_order_date"),
                "admission_offer_timestamp": record.get("admission_offer_timestamp"),
                "attendance_date": record.get("attendance_date"),
                "source_system_name": record.get("source_system_name"),
                "last_refreshed_at_source_timestamp": record.get("last_refreshed_at_source_timestamp"),
            }
        )
    return _insert_rows_with_status("staging.pas_encounter", rows, connection) if rows else 0


def load_staging_ipt(records: list[dict], correlation_id: str, connection) -> int:
    ensure_staging_schema(connection)
    rows = []
    for record in records:
        if _record_exists("staging.ipt_source", "tertiary_id", record.get("tertiary_id", ""), connection):
            continue
        rows.append(
            {
                "correlation_id": correlation_id,
                "tertiary_id": record.get("tertiary_id"),
                "pathway_id": record.get("pathway_id"),
                "person_id": record.get("person_id"),
                "nhs_number": record.get("nhs_number"),
                "mrn": record.get("mrn"),
                "tertiary_referral_type": record.get("tertiary_referral_type"),
                "tertiary_reason": record.get("tertiary_reason"),
                "tertiary_reason_code": record.get("tertiary_reason_code"),
                "sending_org_id": record.get("sending_org_id"),
                "sending_org_name": record.get("sending_org_name"),
                "receiving_org_id": record.get("receiving_org_id"),
                "receiving_org_name": record.get("receiving_org_name"),
                "tertiary_sent_date": record.get("tertiary_sent_date"),
                "tertiary_received_date": record.get("tertiary_received_date"),
                "tertiary_returned_date": record.get("tertiary_returned_date"),
                "tertiary_sending_comment": record.get("tertiary_sending_comment"),
                "tertiary_return_comment": record.get("tertiary_return_comment"),
                "is_sent": str(record.get("is_sent")),
                "is_received": str(record.get("is_received")),
                "is_returned": str(record.get("is_returned")),
                "source_system_name": record.get("source_system_name"),
                "last_refreshed_at_source_timestamp": record.get("last_refreshed_at_source_timestamp"),
            }
        )
    return _insert_rows_with_status("staging.ipt_source", rows, connection) if rows else 0


def load_staging_comment(records: list[dict], correlation_id: str, connection) -> int:
    ensure_staging_schema(connection)
    rows = []
    for record in records:
        if _record_exists(
            "staging.comment_source",
            "cancer_tracking_comment_id",
            record.get("cancer_tracking_comment_id", ""),
            connection,
        ):
            continue
        rows.append(
            {
                "correlation_id": correlation_id,
                "cancer_tracking_comment_id": record.get("cancer_tracking_comment_id"),
                "cancer_pathway_id": record.get("cancer_pathway_id"),
                "person_id": record.get("person_id"),
                "nhs_number": record.get("nhs_number"),
                "mrn": record.get("mrn"),
                "comment_title": record.get("comment_title"),
                "comment_text": record.get("comment_text"),
                "created_by": record.get("created_by"),
                "created_at_timestamp": record.get("created_at_timestamp"),
                "source_system_name": record.get("source_system_name"),
                "last_refreshed_at_source_timestamp": record.get("last_refreshed_at_source_timestamp"),
            }
        )
    return _insert_rows_with_status("staging.comment_source", rows, connection) if rows else 0


def main() -> None:
    connection = config.get_connection()
    try:
        sample = config.CSV_DIR / "pas_patients.csv"
        if not sample.exists():
            print("No sample CSV file found.")
            return
        records = parse_csv_file(str(sample))
        inserted = load_staging_patient(records[:5], "demo-correlation", connection)
        print(f"Loaded {inserted} patient rows into staging.pas_patient")
        pprint(records[:1])
    finally:
        connection.close()


if __name__ == "__main__":
    main()
