"""Pydantic schemas for Cancer 360 API request and response models."""

from __future__ import annotations
from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# ─── Patient ────────────────────────────────────────────────────────────────

class PatientSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    patient_id: UUID
    nhs_number: str
    forename: str
    surname: str
    date_of_birth: date
    sex: str
    age: Optional[int] = None
    postcode: Optional[str] = None
    gp_practice_code: Optional[str] = None
    gp_name: Optional[str] = None


class PatientDetail(PatientSummary):
    prefix: Optional[str] = None
    hospital_number: Optional[str] = None
    ethnicity_code: Optional[str] = None
    ethnicity_desc: Optional[str] = None
    lsoa_code: Optional[str] = None
    imd_decile: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    nok_name: Optional[str] = None
    nok_relationship: Optional[str] = None
    deceased_date: Optional[date] = None


# ─── Referral ───────────────────────────────────────────────────────────────

class ReferralSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    referral_id: UUID
    referral_date: date
    receipt_date: date
    clock_start_date: Optional[date] = None
    referral_source: Optional[str] = None
    referral_priority: Optional[str] = None
    referred_to_specialty: Optional[str] = None
    clinical_info: Optional[str] = None
    cancer_type_code: Optional[str] = None
    status: str


# ─── Diagnosis ──────────────────────────────────────────────────────────────

class DiagnosisSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    diagnosis_id: UUID
    diagnosis_date: date
    icd10_code: str
    icd10_description: Optional[str] = None
    morphology_code: Optional[str] = None
    morphology_desc: Optional[str] = None
    laterality: Optional[str] = None
    basis_of_diagnosis: Optional[str] = None


# ─── Staging ────────────────────────────────────────────────────────────────

class StagingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    staging_id: UUID
    staging_date: date
    staging_type: Optional[str] = None
    tnm_t: Optional[str] = None
    tnm_n: Optional[str] = None
    tnm_m: Optional[str] = None
    stage_group: Optional[str] = None
    grade: Optional[str] = None
    performance_status: Optional[int] = None
    gleason_total: Optional[int] = None
    isup_grade_group: Optional[int] = None


# ─── Pathology ──────────────────────────────────────────────────────────────

class PathologyValueSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    test_code: Optional[str] = None
    test_name: Optional[str] = None
    value_type: Optional[str] = None
    numeric_value: Optional[float] = None
    text_value: Optional[str] = None
    coded_value: Optional[str] = None
    coded_display: Optional[str] = None
    unit: Optional[str] = None
    reference_range_text: Optional[str] = None
    abnormal_flag: Optional[str] = None


class HistopathSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tumour_type: Optional[str] = None
    grade: Optional[str] = None
    tumour_size_mm: Optional[float] = None
    margin_status: Optional[str] = None
    margin_closest_mm: Optional[float] = None
    lymphovascular_invasion: Optional[str] = None
    perineural_invasion: Optional[str] = None
    nodes_examined: Optional[int] = None
    nodes_positive: Optional[int] = None
    er_status: Optional[str] = None
    pr_status: Optional[str] = None
    her2_status: Optional[str] = None
    ki67_percent: Optional[float] = None
    msi_status: Optional[str] = None
    kras_status: Optional[str] = None
    braf_status: Optional[str] = None
    egfr_status: Optional[str] = None
    alk_status: Optional[str] = None
    pdl1_tps: Optional[float] = None


class PathologyResultSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    result_id: UUID
    source_accession: Optional[str] = None
    order_date: Optional[datetime] = None
    specimen_date: Optional[datetime] = None
    report_date: Optional[datetime] = None
    discipline: Optional[str] = None
    test_code: Optional[str] = None
    test_name: Optional[str] = None
    status: str
    requesting_clinician_name: Optional[str] = None
    reporting_pathologist_name: Optional[str] = None
    narrative_report: Optional[str] = None
    source_system: str
    values: List[PathologyValueSchema] = []
    histopath: Optional[HistopathSchema] = None


# ─── Radiology ──────────────────────────────────────────────────────────────

class RadiologyResultSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    result_id: UUID
    accession_number: Optional[str] = None
    exam_date: datetime
    report_date: Optional[datetime] = None
    modality: Optional[str] = None
    body_part: Optional[str] = None
    exam_description: Optional[str] = None
    clinical_indication: Optional[str] = None
    report_text: Optional[str] = None
    conclusion: Optional[str] = None
    reporting_radiologist_name: Optional[str] = None
    status: str
    source_system: str


# ─── SACT ───────────────────────────────────────────────────────────────────

class SACTDrugSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    drug_name: str
    dose_mg: Optional[float] = None
    dose_per_m2: Optional[float] = None
    actual_dose_pct: int = 100
    route: Optional[str] = None
    administration_date: Optional[date] = None


class SACTCycleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cycle_id: UUID
    cycle_number: int
    start_date: date
    bsa_m2: Optional[float] = None
    performance_status: Optional[int] = None
    cycle_outcome: Optional[str] = None
    delay_days: int = 0
    dose_reduction_pct: int = 0
    toxicity_grade: Optional[int] = None
    toxicity_type: Optional[str] = None
    drugs: List[SACTDrugSchema] = []


class SACTCourseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    course_id: UUID
    regimen_name: Optional[str] = None
    regimen_intent: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_cycles: Optional[int] = None
    completed_cycles: int = 0
    course_status: str
    consultant_name: Optional[str] = None
    cycles: List[SACTCycleSchema] = []


# ─── Radiotherapy ───────────────────────────────────────────────────────────

class RTFractionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    fraction_number: int
    scheduled_date: Optional[date] = None
    delivered_date: Optional[date] = None
    dose_gy: Optional[float] = None
    status: str


class RTCourseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    course_id: UUID
    treatment_intent: Optional[str] = None
    treatment_site: Optional[str] = None
    technique: Optional[str] = None
    total_dose_gy: Optional[float] = None
    fractions_prescribed: Optional[int] = None
    dose_per_fraction_gy: Optional[float] = None
    first_fraction_date: Optional[date] = None
    last_fraction_date: Optional[date] = None
    machine_id: Optional[str] = None
    concurrent_sact: bool = False
    course_status: str
    fractions: List[RTFractionSchema] = []


# ─── MDT ────────────────────────────────────────────────────────────────────

class MDTDiscussionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    mdt_id: UUID
    mdt_date: date
    mdt_site: Optional[str] = None
    mdt_type: Optional[str] = None
    chair_name: Optional[str] = None
    quorate: bool
    clinical_summary: Optional[str] = None
    staging_presented: Optional[str] = None
    decision: Optional[str] = None
    treatment_intent: Optional[str] = None
    patient_informed_date: Optional[date] = None


# ─── Cancer Action ──────────────────────────────────────────────────────────

class ActionCreate(BaseModel):
    patient_id: UUID
    pathway_id: Optional[UUID] = None
    action_type: str
    action_description: Optional[str] = None
    priority: str = "normal"
    due_date: Optional[date] = None
    assigned_team: Optional[str] = None
    assigned_user: Optional[str] = None
    notes: Optional[str] = None


class ActionUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    assigned_team: Optional[str] = None
    assigned_user: Optional[str] = None
    notes: Optional[str] = None


class ActionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    action_id: UUID
    patient_id: UUID
    action_type: str
    action_description: Optional[str] = None
    priority: str
    status: str
    due_date: Optional[date] = None
    assigned_team: Optional[str] = None
    assigned_user: Optional[str] = None
    created_by: Optional[str] = None
    completed_by: Optional[str] = None
    completed_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime


# ─── Cancer Pathway / PTL ───────────────────────────────────────────────────

class PTLRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    pathway_id: UUID
    patient_id: UUID
    nhs_number: str
    patient_name: str
    date_of_birth: date
    sex: str
    cancer_type_code: Optional[str] = None
    cancer_type_desc: Optional[str] = None
    stage_group: Optional[str] = None
    grade: Optional[str] = None
    date_referral_received: Optional[date] = None
    days_on_pathway: Optional[int] = None
    date_diagnosis: Optional[date] = None
    days_to_diagnosis: Optional[int] = None
    fds_28day_met: Optional[bool] = None
    date_first_treatment: Optional[date] = None
    days_to_treatment: Optional[int] = None
    standard_62day_met: Optional[bool] = None
    pathway_status: str
    current_stage_label: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[date] = None
    assigned_team: Optional[str] = None
    breach_risk: str
    treatment_modality: Optional[str] = None


class PTLSummary(BaseModel):
    total: int
    breached: int
    high_risk: int
    medium_risk: int
    awaiting_diagnostics: int
    awaiting_mdt: int
    awaiting_treatment: int
    on_treatment: int
    active_monitoring: int
    completed: int
    fds_28d_performance: Optional[float] = None
    rtt_62d_performance: Optional[float] = None


class PTLResponse(BaseModel):
    items: List[PTLRow]
    total: int
    page: int
    per_page: int
    summary: PTLSummary


# ─── Patient 360 View ──────────────────────────────────────────────────────

class PathwayTimelineEvent(BaseModel):
    event_date: date
    event_type: str
    label: str
    detail: Optional[str] = None
    source_system: Optional[str] = None


class Patient360Response(BaseModel):
    patient: PatientDetail
    referral: Optional[ReferralSchema] = None
    diagnosis: Optional[DiagnosisSchema] = None
    staging: Optional[StagingSchema] = None
    pathway: Optional[PTLRow] = None
    timeline: List[PathwayTimelineEvent] = []
    pathology_results: List[PathologyResultSchema] = []
    radiology_results: List[RadiologyResultSchema] = []
    sact_courses: List[SACTCourseSchema] = []
    rt_courses: List[RTCourseSchema] = []
    mdt_discussions: List[MDTDiscussionSchema] = []
    actions: List[ActionSchema] = []


# ─── Dashboard ──────────────────────────────────────────────────────────────

class DashboardMetrics(BaseModel):
    total_pathways: int
    active_pathways: int
    fds_28d_numerator: int
    fds_28d_denominator: int
    fds_28d_performance: Optional[float] = None
    rtt_62d_numerator: int
    rtt_62d_denominator: int
    rtt_62d_performance: Optional[float] = None
    by_cancer_type: List[dict]
    by_breach_risk: List[dict]
    by_status: List[dict]


# ─── Search ─────────────────────────────────────────────────────────────────

class SearchResult(BaseModel):
    patient_id: UUID
    nhs_number: str
    forename: str
    surname: str
    date_of_birth: date
    sex: str
    cancer_type: Optional[str] = None
    pathway_status: Optional[str] = None


# ─── Auth ───────────────────────────────────────────────────────────────────

class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
