"""Map Somerset staging rows into canonical cancer pathway rows."""

from __future__ import annotations

from typing import Any

from .mapper_utils import current_timestamp, full_name, parse_bool, parse_date, safe_date_plus


def map_pathway(staged_record: dict[str, Any]) -> dict[str, Any]:
    original_start_date = parse_date(staged_record.get("original_start_date"))
    adjusted_start_date = parse_date(staged_record.get("adjusted_start_date")) or parse_date(
        staged_record.get("pathway_start_date")
    )
    decision_to_treat_date = parse_date(staged_record.get("decision_to_treat_date"))
    first_treatment_date = parse_date(staged_record.get("first_treatment_date")) or parse_date(
        staged_record.get("treatment_start_date")
    )
    pathway_closed_date = parse_date(staged_record.get("closed_date"))
    diagnosis_date = parse_date(staged_record.get("diagnosis_date"))
    is_benign = parse_bool(staged_record.get("is_benign"))
    diagnosis_icd_10_code = staged_record.get("diagnosis_icd_10") or staged_record.get("diagnosis_icd10_code")
    if is_benign is None and diagnosis_icd_10_code:
        is_benign = str(diagnosis_icd_10_code).upper().startswith("D")
    waiting_time_adjustment_days = None
    if original_start_date and adjusted_start_date:
        waiting_time_adjustment_days = (adjusted_start_date - original_start_date).days

    pathway_status = staged_record.get("pathway_status")
    is_open = str(pathway_status or "").lower() == "open"
    breach_28 = safe_date_plus(adjusted_start_date, 28)
    breach_31 = safe_date_plus(decision_to_treat_date, 31)
    breach_62 = safe_date_plus(adjusted_start_date, 62)
    is_28_open = bool(is_open and adjusted_start_date and diagnosis_date is None)
    is_31_open = bool(is_open and decision_to_treat_date and first_treatment_date is None)
    is_62_open = bool(is_open and first_treatment_date is None)

    return {
        "pathway_id": staged_record.get("pathway_id"),
        "person_id": staged_record.get("person_id"),
        "mrn": staged_record.get("mrn"),
        "nhs_number": staged_record.get("patient_nhs_number") or staged_record.get("nhs_number"),
        "first_name": staged_record.get("first_name"),
        "surname": staged_record.get("surname"),
        "full_name": full_name(staged_record.get("first_name"), staged_record.get("surname")),
        "original_pathway_start_date": original_start_date,
        "pathway_closed_date": pathway_closed_date,
        "waiting_time_adjustment_days": waiting_time_adjustment_days,
        "adjusted_pathway_start_date": adjusted_start_date,
        "cancer_site": staged_record.get("cancer_site"),
        "cancer_sub_site": staged_record.get("cancer_sub_site"),
        "hospital_site": staged_record.get("hospital_site_name") or staged_record.get("hospital_site"),
        "hospital_site_id": staged_record.get("hospital_site_id"),
        "pathway_status": pathway_status,
        "pathway_referral_route": staged_record.get("referral_route"),
        "first_seen_site": None,
        "first_seen_site_ods_code": None,
        "28_day_breach_date": breach_28,
        "31_day_breach_date": breach_31,
        "62_day_breach_date": breach_62,
        "patient_informed_date": None,
        "referral_received_date": parse_date(staged_record.get("referral_received_date"))
        or original_start_date,
        "upgrade_date": None,
        "date_of_birth": parse_date(staged_record.get("date_of_birth")),
        "date_of_death": None,
        "decision_to_treat_date": decision_to_treat_date,
        "diagnosis": staged_record.get("diagnosis"),
        "diagnosis_icd_10_code": diagnosis_icd_10_code,
        "diagnosis_date": diagnosis_date,
        "first_seen_date": parse_date(staged_record.get("first_seen_date")),
        "first_treatment_date": first_treatment_date,
        "first_treatment_type": None,
        "organisation_site_treatment": None,
        "treatment_site_ods_code": None,
        "treatment_site": None,
        "referral_source": staged_record.get("referral_source"),
        "is_benign": is_benign,
        "is_62_day_pathway_open": is_62_open,
        "is_31_day_pathway_open": is_31_open,
        "is_28_day_pathway_open": is_28_open,
        "is_any_pathway_type_open": bool(is_28_open or is_31_open or is_62_open),
        "source_system_name": "Somerset",
        "last_refreshed_at_source_timestamp": current_timestamp(),
    }


def map_pathways(staged_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [map_pathway(record) for record in staged_records]
