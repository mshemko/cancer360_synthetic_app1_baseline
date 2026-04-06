"""Shared scenario and payload builders for the native Windows simulation."""

from __future__ import annotations

import csv
import io
import json
import random
from copy import deepcopy
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from src.synth_utils import (
    add_working_days,
    build_hl7_msh,
    build_hl7_obr,
    build_hl7_obx,
    build_hl7_pid,
    calculate_breach_risk,
    calculate_bsa,
    generate_nhs_number,
    next_working_day,
    random_time,
    stage_to_tnm,
)

FORENAMES_F = [
    "Amelia", "Ava", "Charlotte", "Claire", "Emily", "Emma", "Grace", "Hannah",
    "Helen", "Jessica", "Julia", "Laura", "Louise", "Mary", "Rachel", "Sarah",
    "Sophie", "Susan", "Victoria", "Zoe",
]
FORENAMES_M = [
    "Adam", "Andrew", "Benjamin", "Charles", "Daniel", "David", "Edward", "George",
    "Harry", "James", "John", "Leo", "Mark", "Matthew", "Michael", "Oliver",
    "Paul", "Peter", "Robert", "Thomas",
]
SURNAMES = [
    "Brown", "Campbell", "Clarke", "Cooper", "Davies", "Evans", "Green", "Hall",
    "Harrison", "Hughes", "Jackson", "Johnson", "Jones", "King", "Lewis", "Martin",
    "Patel", "Roberts", "Smith", "Taylor", "Thomas", "Walker", "White", "Williams",
]

TEAMS = {
    "breast": "Breast MDT",
    "colorectal": "Colorectal MDT",
    "lung": "Lung MDT",
    "prostate": "Urology MDT",
    "gynae": "Gynaecology MDT",
    "upper_gi": "Upper GI MDT",
    "urology": "Urology MDT",
    "haem": "Haematology MDT",
    "head_neck": "Head & Neck MDT",
    "melanoma": "Skin MDT",
}

SCENARIO_TEMPLATES = [
    {"name": "breast_surgery_adjuvant_rt", "cancer_type": "breast", "cancer_type_code": "101", "cancer_type_desc": "Breast", "sex_bias": "F", "icd10": "C50.4", "morphology": "8500/3", "stage_group": "IIA", "grade": "2", "treatment_modality": "Surgery + Radiotherapy", "first_treatment_type": "Surgery", "status": "on_treatment", "aria_mode": "rt", "needs_surgery_episode": True, "radiology_modality": "CT"},
    {"name": "lung_chemo", "cancer_type": "lung", "cancer_type_code": "103", "cancer_type_desc": "Lung", "sex_bias": None, "icd10": "C34.1", "morphology": "8140/3", "stage_group": "IIIB", "grade": "3", "treatment_modality": "Chemotherapy", "first_treatment_type": "Chemotherapy", "status": "awaiting_treatment", "aria_mode": "sact", "radiology_modality": "CT"},
    {"name": "colorectal_endoscopy_pathway", "cancer_type": "colorectal", "cancer_type_code": "102", "cancer_type_desc": "Colorectal", "sex_bias": None, "icd10": "C18.7", "morphology": "8140/3", "stage_group": "IIA", "grade": "2", "treatment_modality": "Surgery", "first_treatment_type": "Surgery", "status": "awaiting_mdt", "aria_mode": None, "needs_endoscopy": True, "needs_surgery_episode": True, "radiology_modality": "CT"},
    {"name": "prostate_radiotherapy_completed", "cancer_type": "prostate", "cancer_type_code": "104", "cancer_type_desc": "Prostate", "sex_bias": "M", "icd10": "C61", "morphology": "8140/3", "stage_group": "IIB", "grade": "2", "treatment_modality": "Radiotherapy", "first_treatment_type": "Radiotherapy", "status": "completed", "aria_mode": "rt", "radiology_modality": "MRI"},
    {"name": "gynae_combo", "cancer_type": "gynae", "cancer_type_code": "105", "cancer_type_desc": "Gynaecological", "sex_bias": "F", "icd10": "C56", "morphology": "8441/3", "stage_group": "IIIC", "grade": "3", "treatment_modality": "Chemotherapy", "first_treatment_type": "Chemotherapy", "status": "on_treatment", "aria_mode": "sact", "radiology_modality": "CT"},
    {"name": "upper_gi_ipt", "cancer_type": "upper_gi", "cancer_type_code": "106", "cancer_type_desc": "Upper GI", "sex_bias": None, "icd10": "C16.0", "morphology": "8140/3", "stage_group": "IIIA", "grade": "3", "treatment_modality": "Surgery", "first_treatment_type": "Surgery", "status": "awaiting_treatment", "aria_mode": None, "needs_ipt": True, "needs_endoscopy": True, "radiology_modality": "CT"},
    {"name": "urology_surgery", "cancer_type": "urology", "cancer_type_code": "107", "cancer_type_desc": "Urological", "sex_bias": None, "icd10": "C67.9", "morphology": "8120/3", "stage_group": "IIB", "grade": "2", "treatment_modality": "Surgery", "first_treatment_type": "Surgery", "status": "awaiting_diagnostics", "aria_mode": None, "needs_surgery_episode": True, "radiology_modality": "CT"},
    {"name": "haem_immunotherapy", "cancer_type": "haem", "cancer_type_code": "108", "cancer_type_desc": "Haematological", "sex_bias": None, "icd10": "C83.3", "morphology": "9680/3", "stage_group": "IIIB", "grade": "3", "treatment_modality": "Immunotherapy", "first_treatment_type": "Immunotherapy", "status": "on_treatment", "aria_mode": "immunotherapy", "radiology_modality": "PET-CT"},
    {"name": "head_neck_chemoradiotherapy", "cancer_type": "head_neck", "cancer_type_code": "109", "cancer_type_desc": "Head & Neck", "sex_bias": None, "icd10": "C10.0", "morphology": "8070/3", "stage_group": "IV", "grade": "3", "treatment_modality": "Chemoradiotherapy", "first_treatment_type": "Chemoradiotherapy", "status": "awaiting_treatment", "aria_mode": "combo", "radiology_modality": "MRI"},
    {"name": "melanoma_surveillance", "cancer_type": "melanoma", "cancer_type_code": "110", "cancer_type_desc": "Skin/Melanoma", "sex_bias": None, "icd10": "C43.6", "morphology": "8720/3", "stage_group": "IB", "grade": "2", "treatment_modality": "Surgery", "first_treatment_type": "Surgery", "status": "active_monitoring", "aria_mode": None, "needs_surgery_episode": True, "radiology_modality": "CT"},
]


def ensure_dir(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def write_json(path: str | Path, payload: Any) -> Path:
    target = Path(path)
    ensure_dir(target.parent)
    target.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")
    return target


def render_csv(rows: list[dict[str, Any]], fieldnames: list[str]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _stringify_csv(row.get(key)) for key in fieldnames})
    return buffer.getvalue()


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value[:10])


def build_journeys(
    patient_count: int,
    seed: int = 360,
    anchor_date: date | None = None,
    start_index: int = 1,
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    today = anchor_date or date.today()
    journeys: list[dict[str, Any]] = []
    for idx in range(start_index, start_index + patient_count):
        template = deepcopy(SCENARIO_TEMPLATES[(idx - 1) % len(SCENARIO_TEMPLATES)])
        journeys.append(_build_journey(idx, template, today, rng))
    return journeys


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return str(value)


def _stringify_csv(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bool):
        return "True" if value else "False"
    return str(value)


def _build_journey(idx: int, template: dict[str, Any], today: date, rng: random.Random) -> dict[str, Any]:
    sex = template["sex_bias"] or rng.choice(["F", "M"])
    forename = rng.choice(FORENAMES_F if sex == "F" else FORENAMES_M)
    surname = rng.choice(SURNAMES)
    age = rng.randint(41, 84)
    dob = date(today.year - age, rng.randint(1, 12), rng.randint(1, 28))
    nhs_number = generate_nhs_number(idx)
    hospital_number = f"H{200000 + idx}"
    prefix = "Ms" if sex == "F" else "Mr"
    team = TEAMS[template["cancer_type"]]
    stage_for_tnm = template["stage_group"] if template["stage_group"] in {"IA", "IB", "IIA", "IIB", "IIIA", "IIIB", "IIIC", "IV"} else "IV"
    tnm = stage_to_tnm(stage_for_tnm)

    status = template["status"]
    if status == "awaiting_diagnostics":
        referral_received = today - timedelta(days=rng.randint(14, 24))
    elif status == "awaiting_mdt":
        referral_received = today - timedelta(days=rng.randint(25, 38))
    elif status == "awaiting_treatment":
        referral_received = today - timedelta(days=rng.randint(40, 68))
    elif status == "on_treatment":
        referral_received = today - timedelta(days=rng.randint(50, 88))
    else:
        referral_received = today - timedelta(days=rng.randint(70, 120))

    referral_received = next_working_day(referral_received)
    first_seen = add_working_days(referral_received, rng.randint(4, 8))
    biopsy_date = add_working_days(first_seen, rng.randint(2, 6))
    diagnosis_date = add_working_days(biopsy_date, rng.randint(3, 6))
    mdt_date = add_working_days(diagnosis_date, rng.randint(2, 5))
    dtt_date = add_working_days(mdt_date, 1)
    first_treatment = add_working_days(dtt_date, rng.randint(7, 15))

    if status == "awaiting_diagnostics":
        diagnosis_date = None
        mdt_date = None
        dtt_date = None
        first_treatment = None
    elif status == "awaiting_mdt":
        mdt_date = None
        dtt_date = None
        first_treatment = None
    elif status == "awaiting_treatment":
        first_treatment = None

    cancer_desc = template["cancer_type_desc"]
    pathway_id = f"PATH-{idx:05d}"
    meeting_id = f"MTG-{team.replace(' ', '').upper()}-{(mdt_date or today).strftime('%Y%m%d')}"
    stage_label = f"{tnm[0]} {tnm[1]} {tnm[2]} - Stage {template['stage_group']}" if diagnosis_date else "Awaiting diagnosis"

    weight = round(rng.uniform(55, 98), 1)
    height = round(rng.uniform(154, 188), 1)
    bsa = round(calculate_bsa(height, weight), 2)

    patient = {
        "nhs_number": nhs_number,
        "hospital_number": hospital_number,
        "prefix": prefix,
        "forename": forename,
        "surname": surname,
        "full_name": f"{surname}, {forename}",
        "date_of_birth": dob.isoformat(),
        "sex": sex,
        "postcode": f"SW{rng.randint(1, 20)} {rng.randint(1, 9)}AB",
        "phone": f"07{rng.randint(100000000, 999999999)}",
        "gp_name": f"Dr {rng.choice(SURNAMES)}",
        "gp_practice_code": f"A{rng.randint(10000, 99999)}",
    }
    clinical = {
        "cancer_type": template["cancer_type"],
        "cancer_type_code": template["cancer_type_code"],
        "cancer_type_desc": cancer_desc,
        "team": team,
        "icd10": template["icd10"],
        "morphology": template["morphology"],
        "stage_group": template["stage_group"],
        "grade": template["grade"],
        "tnm_t": tnm[0],
        "tnm_n": tnm[1],
        "tnm_m": tnm[2],
        "treatment_modality": template["treatment_modality"],
        "first_treatment_type": template["first_treatment_type"],
        "status": status,
        "current_stage_label": stage_label,
        "breach_risk": calculate_breach_risk(referral_received, diagnosis_date, first_treatment),
        "pathway_id": pathway_id,
        "somerset_person_id": f"SCRP{idx:05d}",
        "referral_source": "GP" if idx % 4 else "Screening",
        "referral_priority": "2WW",
    }
    dates = {
        "referral_received": referral_received.isoformat(),
        "first_seen": first_seen.isoformat(),
        "biopsy_date": biopsy_date.isoformat(),
        "diagnosis_date": diagnosis_date.isoformat() if diagnosis_date else None,
        "mdt_date": mdt_date.isoformat() if mdt_date else None,
        "decision_to_treat": dtt_date.isoformat() if dtt_date else None,
        "first_treatment": first_treatment.isoformat() if first_treatment else None,
    }
    metrics = {
        "days_to_first_seen": (first_seen - referral_received).days,
        "days_to_diagnosis": (diagnosis_date - referral_received).days if diagnosis_date else None,
        "days_to_treatment": (first_treatment - referral_received).days if first_treatment else None,
        "fds_28day_met": diagnosis_date is not None and (diagnosis_date - referral_received).days <= 28,
        "standard_62day_met": first_treatment is not None and (first_treatment - referral_received).days <= 62,
        "standard_31day_met": first_treatment is not None and dtt_date is not None and (first_treatment - dtt_date).days <= 31,
    }
    somerset = {
        "pathway_id": pathway_id,
        "meeting_id": meeting_id,
        "tracking_comments": _tracking_comments(status, cancer_desc, referral_received, mdt_date, first_treatment),
        "ipt": _ipt_record(idx, template, referral_received, nhs_number, hospital_number),
    }
    return {
        "journey_id": f"J{idx:05d}",
        "scenario": template["name"],
        "patient": patient,
        "clinical": clinical,
        "dates": dates,
        "metrics": metrics,
        "somerset": somerset,
        "pas": {"specialty_code": template["cancer_type_code"], "appointments": _pas_appointments(idx, team, first_seen, mdt_date, first_treatment, status), "admissions": _pas_admissions(idx, template, first_treatment)},
        "pathology": _pathology_payload(idx, template, biopsy_date, diagnosis_date or add_working_days(biopsy_date, 3), patient),
        "radiology": _radiology_payload(idx, template, add_working_days(first_seen, 4), add_working_days(first_seen, 6), patient),
        "mdt": {
            "meeting_id": meeting_id,
            "meeting_timestamp": datetime.combine(mdt_date, time(8, 0)).isoformat() if mdt_date else None,
            "status": "completed" if mdt_date else "booked",
            "note_text": _mdt_note(cancer_desc, template["stage_group"], template["first_treatment_type"], forename, surname, nhs_number),
        },
        "aria": _aria_payload(idx, template, first_treatment, dtt_date, nhs_number, team, bsa, weight, height),
        "endoscopy": _endoscopy_payload(idx, template, nhs_number, first_seen),
    }


def _tracking_comments(status: str, cancer_desc: str, referral_received: date, mdt_date: date | None, first_treatment: date | None) -> list[dict[str, str]]:
    comments = [{"title": "Referral received", "text": f"2WW referral received for suspected {cancer_desc.lower()} cancer. Navigation started.", "created_by": "Cancer Navigator", "created_at": datetime.combine(referral_received, time(9, 15)).isoformat()}]
    if status in {"awaiting_mdt", "awaiting_treatment", "on_treatment", "completed", "active_monitoring"}:
        comments.append({"title": "Diagnostics", "text": "Histology authorised and uploaded. Case ready for MDT discussion.", "created_by": "MDT Coordinator", "created_at": datetime.combine(add_working_days(referral_received, 12), time(11, 0)).isoformat()})
    if mdt_date:
        comments.append({"title": "MDT outcome", "text": "MDT agreed definitive management plan and asked team to proceed to booking.", "created_by": "MDT Coordinator", "created_at": datetime.combine(mdt_date, time(14, 0)).isoformat()})
    if first_treatment:
        comments.append({"title": "Treatment", "text": "First definitive treatment recorded in Somerset and clock stopped.", "created_by": "Cancer Navigator", "created_at": datetime.combine(first_treatment, time(16, 15)).isoformat()})
    return comments


def _ipt_record(idx: int, template: dict[str, Any], referral_received: date, nhs_number: str, hospital_number: str) -> dict[str, Any] | None:
    if not template.get("needs_ipt"):
        return None
    sent = add_working_days(referral_received, 22)
    received = add_working_days(sent, 3)
    return {"tertiary_id": f"IPT-{idx:05d}", "tertiary_referral_type": "Sent", "tertiary_reason_code": "TREAT", "tertiary_reason": "Specialist surgery", "tertiary_sent_date": sent.isoformat(), "tertiary_received_date": received.isoformat(), "tertiary_returned_date": None, "tertiary_sending_comment": "Referred to tertiary centre for specialist opinion and theatre capacity.", "tertiary_return_comment": None, "sending_org_id": "RYJ", "sending_org_name": "Cancer 360 Demo Trust", "receiving_org_id": "RAL", "receiving_org_name": "Addenbrooke's Hospital", "nhs_number": nhs_number, "mrn": hospital_number}


def _pas_appointments(idx: int, team: str, first_seen: date, mdt_date: date | None, first_treatment: date | None, status: str) -> list[dict[str, Any]]:
    appointments = [{"source_appt_id": f"OPA-{idx:05d}-FS", "date": first_seen.isoformat(), "time": random_time(8, 12), "clinic_code": team.replace(' MDT', '').replace(' ', '')[:8].upper(), "clinic_name": f"{team} New Patient Clinic", "appointment_type": "new", "attendance_status": "attended", "consultant_name": "Dr Sarah Jones"}]
    if mdt_date:
        appointments.append({"source_appt_id": f"OPA-{idx:05d}-MDT", "date": add_working_days(mdt_date, 1).isoformat(), "time": "09:00", "clinic_code": "POSTMDT", "clinic_name": "Post-MDT Review", "appointment_type": "follow_up", "attendance_status": "attended", "consultant_name": "Dr Amit Patel"})
    if status in {"awaiting_treatment", "on_treatment", "completed", "active_monitoring"} and first_treatment:
        appointments.append({"source_appt_id": f"OPA-{idx:05d}-PREOP", "date": add_working_days(first_treatment, -3).isoformat(), "time": "14:00", "clinic_code": "PREOP", "clinic_name": "Pre-operative Assessment", "appointment_type": "pre_op", "attendance_status": "attended", "consultant_name": "Nurse Lisa Brown"})
    return appointments


def _pas_admissions(idx: int, template: dict[str, Any], first_treatment: date | None) -> list[dict[str, Any]]:
    if not template.get("needs_surgery_episode") or not first_treatment:
        return []
    discharge = add_working_days(first_treatment, 2)
    return [{"spell_id": f"SPELL-{idx:05d}", "episode_id": f"EP-{idx:05d}", "admission_date": first_treatment.isoformat(), "discharge_date": discharge.isoformat(), "specialty_code": template["cancer_type_code"], "consultant_code": "CONS001", "consultant_name": "Mr Alex Carter", "ward_name": "Surgical Oncology", "primary_procedure": "OPCS4-X99", "primary_procedure_desc": f"{template['first_treatment_type']} for {template['cancer_type_desc'].lower()} cancer"}]


def _pathology_payload(idx: int, template: dict[str, Any], biopsy_date: date, report_date: date, patient: dict[str, Any]) -> dict[str, Any]:
    narrative, markers = _histology_narrative(template)
    return {
        "histology": {"message_id": f"ICE-HIST-{idx:05d}", "order_id": f"ORD-HIST-{idx:05d}", "accession": f"ACC-HIST-{idx:05d}", "test_code": "HISTO", "test_name": "Histopathology", "order_datetime": datetime.combine(biopsy_date, time(10, 30)).isoformat(), "specimen_datetime": datetime.combine(biopsy_date, time(10, 45)).isoformat(), "result_datetime": datetime.combine(report_date, time(16, 0)).isoformat(), "nhs_number": patient["nhs_number"], "hospital_number": patient["hospital_number"], "forename": patient["forename"], "surname": patient["surname"], "date_of_birth": patient["date_of_birth"], "sex": patient["sex"], "narrative": narrative, "markers": markers},
        "bloods": {"message_id": f"ICE-FBC-{idx:05d}", "order_id": f"ORD-FBC-{idx:05d}", "accession": f"ACC-FBC-{idx:05d}", "test_code": "FBC", "test_name": "Full Blood Count", "order_datetime": datetime.combine(add_working_days(biopsy_date, -1), time(8, 15)).isoformat(), "result_datetime": datetime.combine(add_working_days(biopsy_date, -1), time(12, 30)).isoformat(), "nhs_number": patient["nhs_number"], "hospital_number": patient["hospital_number"], "forename": patient["forename"], "surname": patient["surname"], "date_of_birth": patient["date_of_birth"], "sex": patient["sex"], "results": [{"code": "HB", "name": "Haemoglobin", "value": "124", "units": "g/L", "range": "120-160", "flag": "N"}, {"code": "WBC", "name": "White Cell Count", "value": "6.1", "units": "10*9/L", "range": "4.0-11.0", "flag": "N"}, {"code": "PLT", "name": "Platelets", "value": "275", "units": "10*9/L", "range": "150-400", "flag": "N"}]},
    }


def _histology_narrative(template: dict[str, Any]) -> tuple[str, list[dict[str, str]]]:
    cancer_type = template["cancer_type"]
    if cancer_type == "breast":
        return "Core biopsy confirms invasive ductal carcinoma grade 2. ER positive, PR positive, HER2 negative, Ki-67 18%. No lymphovascular invasion identified.", [{"code": "ER", "name": "Oestrogen Receptor", "value_type": "CE", "value": "POS^Positive^LOCAL"}, {"code": "PR", "name": "Progesterone Receptor", "value_type": "CE", "value": "POS^Positive^LOCAL"}, {"code": "HER2", "name": "HER2", "value_type": "CE", "value": "NEG^Negative^LOCAL"}, {"code": "KI67", "name": "Ki-67", "value_type": "NM", "value": "18", "units": "%"}]
    if cancer_type == "colorectal":
        return "Biopsies show moderately differentiated adenocarcinoma. MMR proteins retained. KRAS mutation not detected. BRAF wild type.", [{"code": "MMR", "name": "MMR status", "value_type": "CE", "value": "INTACT^Retained^LOCAL"}, {"code": "KRAS", "name": "KRAS", "value_type": "CE", "value": "WT^Wild type^LOCAL"}, {"code": "BRAF", "name": "BRAF", "value_type": "CE", "value": "WT^Wild type^LOCAL"}]
    if cancer_type == "lung":
        return "Bronchial biopsy confirms adenocarcinoma. PD-L1 TPS 40%. EGFR negative. ALK negative.", [{"code": "PDL1", "name": "PD-L1 TPS", "value_type": "NM", "value": "40", "units": "%"}, {"code": "EGFR", "name": "EGFR", "value_type": "CE", "value": "NEG^Negative^LOCAL"}, {"code": "ALK", "name": "ALK", "value_type": "CE", "value": "NEG^Negative^LOCAL"}]
    if cancer_type == "prostate":
        return "Prostate biopsies show adenocarcinoma, Gleason 3+4=7, ISUP grade group 2.", [{"code": "GLEASON", "name": "Gleason Score", "value_type": "ST", "value": "3+4=7"}]
    return f"Biopsy confirms {template['cancer_type_desc'].lower()} malignancy, grade {template['grade']}.", []


def _radiology_payload(idx: int, template: dict[str, Any], exam_date: date, report_date: date, patient: dict[str, Any]) -> dict[str, Any]:
    conclusion = "No evidence of distant metastatic disease." if template["stage_group"] not in {"IIIB", "IIIC", "IVA", "IV"} else "Locoregionally advanced disease without confirmed distant metastases."
    return {"message_id": f"RIS-{idx:05d}", "order_id": f"RAD-ORD-{idx:05d}", "accession": f"RAD-ACC-{idx:05d}", "test_code": template["radiology_modality"], "test_name": f"{template['radiology_modality']} staging study", "order_datetime": datetime.combine(exam_date, time(9, 0)).isoformat(), "result_datetime": datetime.combine(report_date, time(15, 30)).isoformat(), "nhs_number": patient["nhs_number"], "hospital_number": patient["hospital_number"], "forename": patient["forename"], "surname": patient["surname"], "date_of_birth": patient["date_of_birth"], "sex": patient["sex"], "observations": [{"code": "REPORT", "name": "Report Text", "value_type": "FT", "value": f"Staging {template['radiology_modality']} completed. {conclusion}"}, {"code": "CONCLUSION", "name": "Conclusion", "value_type": "FT", "value": conclusion}]}


def _mdt_note(cancer_desc: str, stage_group: str, treatment: str, forename: str, surname: str, nhs_number: str) -> str:
    return f"{cancer_desc} MDT discussion for {surname}, {forename} (NHS {nhs_number}). Stage {stage_group}. Consensus recommendation: proceed to {treatment.lower()}."


def _aria_payload(idx: int, template: dict[str, Any], first_treatment: date | None, dtt_date: date | None, nhs_number: str, team: str, bsa: float, weight: float, height: float) -> dict[str, Any]:
    if not template.get("aria_mode") or not first_treatment:
        return {"appointments": [], "treatments": []}
    treatments: list[dict[str, Any]] = []
    appointments: list[dict[str, Any]] = []
    aria_mode = template["aria_mode"]
    if aria_mode in {"sact", "immunotherapy", "combo"}:
        regimen = {"lung": "Carboplatin/Pemetrexed", "gynae": "Carboplatin/Paclitaxel", "haem": "R-CHOP", "head_neck": "Cisplatin"}.get(template["cancer_type"], "Pembrolizumab" if aria_mode == "immunotherapy" else "FEC-T")
        cycle_count = 3 if template["status"] == "on_treatment" else 1
        for cycle in range(1, cycle_count + 1):
            cycle_date = add_working_days(first_treatment, (cycle - 1) * 15)
            treatments.append({"cancer_treatment_id": f"ARIA-SACT-{idx:05d}-C{cycle}", "nhs_number": nhs_number, "treatment_group_id": f"ARIA-SACT-{idx:05d}", "attendance_date": cycle_date.isoformat(), "ordered_date": (dtt_date or first_treatment).isoformat(), "scheduled_date": cycle_date.isoformat(), "treatment_description": f"{regimen} cycle {cycle}", "treatment_type": "Immunotherapy" if aria_mode == "immunotherapy" else "Chemotherapy", "treatment_status": "Attended" if cycle_date <= date.today() else "Booked", "regimen_name": regimen, "cycle_number": cycle, "max_cycles": 6, "drug_name": regimen.split('/')[0], "dose_mg": round(100 * bsa, 1), "dose_unit": "mg", "route": "IV", "bsa_m2": bsa, "weight_kg": weight, "height_cm": height, "consultant_name": "Dr Sarah Jones", "source_system_name": "Aria OIS", "last_refreshed_at_source_timestamp": datetime.now().isoformat()})
            appointments.append({"appointment_id": f"ARIA-APT-{idx:05d}-C{cycle}", "start_datetime": datetime.combine(cycle_date, time(9, 0)).isoformat(), "status": "BOOKED" if cycle_date > date.today() else "ATTENDED", "clinic_name": f"{team} Day Unit", "consultant_name": "Dr Sarah Jones", "reason": regimen})
    if aria_mode in {"rt", "combo"}:
        fractions = 15 if template["cancer_type"] in {"breast", "prostate"} else 20
        first_fraction = first_treatment if aria_mode == "rt" else add_working_days(first_treatment, 3)
        for fraction in range(1, min(fractions, 10) + 1):
            fx_date = add_working_days(first_fraction, fraction - 1)
            treatments.append({"cancer_treatment_id": f"ARIA-RT-{idx:05d}-F{fraction}", "nhs_number": nhs_number, "treatment_group_id": f"ARIA-RT-{idx:05d}", "attendance_date": fx_date.isoformat(), "ordered_date": (dtt_date or first_fraction).isoformat(), "scheduled_date": fx_date.isoformat(), "treatment_description": f"Radiotherapy fraction {fraction}", "treatment_type": "Radiotherapy", "treatment_status": "Attended" if fx_date <= date.today() else "Booked", "treatment_site": template["cancer_type_desc"], "fractions_prescribed": fractions, "fraction_number": fraction, "total_dose_gy": 40 if template["cancer_type"] == "breast" else 60, "dose_per_fraction_gy": round((40 if template["cancer_type"] == "breast" else 60) / fractions, 2), "machine_id": "LINAC-01", "consultant_name": "Dr Amit Patel", "source_system_name": "Aria OIS", "last_refreshed_at_source_timestamp": datetime.now().isoformat()})
            appointments.append({"appointment_id": f"ARIA-APT-{idx:05d}-RT-{fraction}", "start_datetime": datetime.combine(fx_date, time(8, 30)).isoformat(), "status": "BOOKED" if fx_date > date.today() else "ATTENDED", "clinic_name": "Radiotherapy Unit", "consultant_name": "Dr Amit Patel", "reason": f"Fraction {fraction}"})
    return {"appointments": appointments, "treatments": treatments}


def _endoscopy_payload(idx: int, template: dict[str, Any], nhs_number: str, first_seen: date) -> dict[str, Any] | None:
    if not template.get("needs_endoscopy"):
        return None
    attendance = add_working_days(first_seen, 1)
    return {"endoscopy_id": f"ENDO-{idx:05d}", "nhs_number": nhs_number, "is_reported": True, "ordered_date": first_seen.isoformat(), "scheduled_date": attendance.isoformat(), "attendance_date": attendance.isoformat(), "report_authorised_date": add_working_days(attendance, 2).isoformat(), "report_prepared_date": add_working_days(attendance, 1).isoformat(), "exam_status": "Completed", "modality": "Endoscopy", "endoscopy_type": "Colonoscopy" if template["cancer_type"] == "colorectal" else "Gastroscopy", "endoscopy_priority": "Urgent", "endoscopy_report_text": "Suspicious malignant lesion visualised and biopsied. Images and report sent to MDT coordinator.", "source_system_name": "Solus Endoscopy", "last_refreshed_at_source_timestamp": datetime.now().isoformat()}


def build_pas_adt_message(patient: dict[str, Any], appointment: dict[str, Any], message_type: str, message_id: str) -> str:
    appt_dt = datetime.fromisoformat(f"{appointment['date']}T{appointment['time']}")
    return "\r".join([build_hl7_msh("CERNER", "PAS", "C360", "FDP", message_type, message_id, appt_dt), build_hl7_pid(patient["nhs_number"], patient["hospital_number"], patient["surname"], patient["forename"], date.fromisoformat(patient["date_of_birth"]), patient["sex"], postcode=patient["postcode"], phone=patient["phone"], prefix=patient["prefix"]), f"PV1|1|O|{appointment['clinic_code']}^^^C360||||CONS001^{appointment['consultant_name'].replace(' ', '^')}"]) + "\r"


def build_pas_siu_message(patient: dict[str, Any], appointment: dict[str, Any], event_code: str, message_id: str) -> str:
    appt_dt = datetime.fromisoformat(f"{appointment['date']}T{appointment['time']}")
    sch = f"SCH|{appointment['source_appt_id']}|||||{appointment['appointment_type']}|{appointment['clinic_name']}|||{appt_dt.strftime('%Y%m%d%H%M%S')}|{appointment['attendance_status'].upper()}||||{appointment['consultant_name']}"
    return "\r".join([build_hl7_msh("CERNER", "PAS", "C360", "FDP", f"SIU^{event_code}", message_id, appt_dt), build_hl7_pid(patient["nhs_number"], patient["hospital_number"], patient["surname"], patient["forename"], date.fromisoformat(patient["date_of_birth"]), patient["sex"], postcode=patient["postcode"], phone=patient["phone"], prefix=patient["prefix"]), sch]) + "\r"


def build_aria_siu_message(patient: dict[str, Any], appointment: dict[str, Any], event_code: str, message_id: str) -> str:
    appt_dt = datetime.fromisoformat(appointment["start_datetime"])
    sch = f"SCH|{appointment['appointment_id']}|||||{appointment['reason']}|{appointment['clinic_name']}|||{appt_dt.strftime('%Y%m%d%H%M%S')}|{appointment['status']}||||{appointment['consultant_name']}"
    return "\r".join([build_hl7_msh("ARIA", "ONC", "C360", "FDP", f"SIU^{event_code}", message_id, appt_dt), build_hl7_pid(patient["nhs_number"], patient["hospital_number"], patient["surname"], patient["forename"], date.fromisoformat(patient["date_of_birth"]), patient["sex"], postcode=patient["postcode"], phone=patient["phone"], prefix=patient["prefix"]), sch]) + "\r"


def build_oru_message(source_app: str, source_facility: str, patient: dict[str, Any], payload: dict[str, Any], message_type: str = "ORU^R01") -> str:
    order_dt = datetime.fromisoformat(payload["order_datetime"])
    result_dt = datetime.fromisoformat(payload["result_datetime"])
    segments = [build_hl7_msh(source_app, source_facility, "C360", "FDP", message_type, payload["message_id"], result_dt), build_hl7_pid(payload["nhs_number"], payload["hospital_number"], payload["surname"], payload["forename"], date.fromisoformat(payload["date_of_birth"]), payload["sex"], postcode=patient["postcode"], phone=patient["phone"], prefix=patient["prefix"]), build_hl7_obr(payload["order_id"], payload["accession"], payload["test_code"], payload["test_name"], order_dt, result_dt, provider_code="CONS001", provider_name="Dr Sarah Jones")]
    observations = payload.get("markers") or payload.get("results") or payload.get("observations") or []
    if payload.get("narrative"):
        observations = [{"code": "REPORT", "name": "Narrative Report", "value_type": "FT", "value": payload["narrative"]}] + observations
    for idx, obs in enumerate(observations, start=1):
        segments.append(build_hl7_obx(idx, obs.get("value_type", "FT"), obs["code"], obs["name"], obs["value"], obs.get("units", ""), obs.get("range", ""), obs.get("flag", "")))
    return "\r".join(segments) + "\r"
