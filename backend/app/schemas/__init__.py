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
    operation: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    assigned_team: Optional[str] = None
    assigned_user: Optional[str] = None
    notes: Optional[str] = None
    comment_title: Optional[str] = None
    comment_text: Optional[str] = None


class ActionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    action_id: UUID
    patient_id: UUID
    pathway_id: Optional[UUID] = None
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
    source_system: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── Cancer Pathway / PTL ───────────────────────────────────────────────────

class PTLRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    pathway_id: UUID
    patient_id: UUID
    nhs_number: str
    patient_name: str
    hospital_number: Optional[str] = None
    date_of_birth: date
    sex: str
    age: Optional[int] = None
    cancer_type_code: Optional[str] = None
    cancer_type_desc: Optional[str] = None
    cancer_site: Optional[str] = None
    cancer_sub_site: Optional[str] = None
    hospital_site: Optional[str] = None
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
    open_action_count: int = 0
    latest_action: Optional[str] = None
    recent_action_update: bool = False
    latest_tracking_comment: Optional[str] = None
    breach_date_28: Optional[date] = None
    breach_date_31: Optional[date] = None
    breach_date_62: Optional[date] = None
    first_outpatient_attended_date: Optional[date] = None
    next_outpatient_attended_date: Optional[date] = None
    latest_histology_attended_date: Optional[date] = None
    latest_radiology_attended_date: Optional[date] = None
    latest_inpatient_encounter_tci_date: Optional[date] = None
    latest_mdt_status: Optional[str] = None
    latest_ipt_date: Optional[date] = None
    tags: List[str] = Field(default_factory=list)
    watchlist_reason: Optional[str] = None


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
    navigation_actions: List[ActionSchema] = []


class DrawerSectionCount(BaseModel):
    key: str
    label: str
    count: int


class PathwayDrawerDetail(BaseModel):
    pathway_status: str
    pathway_type: str
    days_since_adjusted_pathway_start: Optional[int] = None
    cancer_site: Optional[str] = None
    cancer_sub_site: Optional[str] = None
    hospital_site: Optional[str] = None
    full_name: str
    nhs_number: str
    mrn: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: date
    adjusted_pathway_start_date: Optional[date] = None
    original_pathway_start_date: Optional[date] = None
    pathway_closed_date: Optional[date] = None
    breach_date_28: Optional[date] = None
    breach_date_31: Optional[date] = None
    breach_date_62: Optional[date] = None
    watchlist_reason: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class PathwayDrawerHistoryItem(BaseModel):
    timestamp: datetime
    event_type: str
    title: str
    detail: Optional[str] = None
    actor: Optional[str] = None
    tone: str = "neutral"


class PathwayDrawerAction(BaseModel):
    action_id: UUID
    title: str
    due_date: Optional[date] = None
    status: str
    detail: Optional[str] = None
    owner: Optional[str] = None
    priority: str
    source_system: Optional[str] = None
    history: List[PathwayDrawerHistoryItem] = Field(default_factory=list)


class PathwayDrawerAppointment(BaseModel):
    record_id: str
    name: str
    status: Optional[str] = None
    ordered_date: Optional[date] = None
    scheduled_date: Optional[date] = None
    attended_date: Optional[date] = None
    specialty_name: Optional[str] = None
    consultant_name: Optional[str] = None
    source_system: Optional[str] = None


class PathwayDrawerProcedure(BaseModel):
    record_id: str
    name: str
    status: Optional[str] = None
    ordered_date: Optional[date] = None
    scheduled_date: Optional[date] = None
    attended_date: Optional[date] = None
    specialty_name: Optional[str] = None
    consultant_name: Optional[str] = None
    ward_name: Optional[str] = None
    source_system: Optional[str] = None


class PathwayDrawerReport(BaseModel):
    record_id: str
    name: str
    status: str
    priority: Optional[str] = None
    ordered_date: Optional[date] = None
    report_date: Optional[date] = None
    summary: Optional[str] = None
    report_text: Optional[str] = None
    author_name: Optional[str] = None
    clinical_question: Optional[str] = None
    reference_number: Optional[str] = None
    hospital_name: Optional[str] = None
    source_system: Optional[str] = None


class PathwayDrawerMdtNote(BaseModel):
    note_type: str
    created_at: datetime
    text: str


class PathwayDrawerMdtMeeting(BaseModel):
    meeting_id: UUID
    meeting_date: date
    status: str
    note_count: int
    mdt_site: Optional[str] = None
    source_system: Optional[str] = None
    notes: List[PathwayDrawerMdtNote] = Field(default_factory=list)


class PathwayDrawerTestResult(BaseModel):
    record_id: str
    test_name: str
    test_date: Optional[date] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    value_type: Optional[str] = None
    abnormal_flag: Optional[str] = None


class PathwayDrawerIPT(BaseModel):
    record_id: str
    reason_for_ipt: str
    sent_or_received: str
    ipt_date: Optional[date] = None
    ipt_on_day: Optional[int] = None
    sending_org_name: Optional[str] = None
    receiving_org_name: Optional[str] = None
    source_system: Optional[str] = None


class PathwayDrawerTrackingComment(BaseModel):
    record_id: str
    created_at: datetime
    created_by: Optional[str] = None
    title: Optional[str] = None
    comment_text: str
    source_system: Optional[str] = None


class PathwayDrawerResponse(BaseModel):
    pathway: PTLRow
    last_updated: datetime
    section_counts: List[DrawerSectionCount]
    details: PathwayDrawerDetail
    milestones: List[PathwayTimelineEvent] = Field(default_factory=list)
    actions: List[PathwayDrawerAction] = Field(default_factory=list)
    outpatient_appointments: List[PathwayDrawerAppointment] = Field(default_factory=list)
    inpatient_procedures: List[PathwayDrawerProcedure] = Field(default_factory=list)
    histology: List[PathwayDrawerReport] = Field(default_factory=list)
    radiology: List[PathwayDrawerReport] = Field(default_factory=list)
    mdt_notes: List[PathwayDrawerMdtMeeting] = Field(default_factory=list)
    test_results: List[PathwayDrawerTestResult] = Field(default_factory=list)
    ipt: List[PathwayDrawerIPT] = Field(default_factory=list)
    tracking_comments: List[PathwayDrawerTrackingComment] = Field(default_factory=list)
    patient_360: Patient360Response


class ActionWorklistRow(BaseModel):
    action_id: UUID
    pathway_id: Optional[UUID] = None
    patient_id: UUID
    due_date: Optional[date] = None
    title: str
    priority: str
    action_detail_summary: Optional[str] = None
    action_status: str
    action_status_tone: str
    pathway_day: Optional[int] = None
    patient_name: str
    cancer_site: Optional[str] = None
    hospital_site: Optional[str] = None
    mrn: Optional[str] = None
    nhs_number: str
    owner: Optional[str] = None
    team_name: Optional[str] = None
    days_open: int
    pathway_is_open: bool
    pathway_status: Optional[str] = None
    latest_action_comment: Optional[str] = None
    latest_comment_at: Optional[datetime] = None
    latest_comment_by: Optional[str] = None
    breach_date_28: Optional[date] = None
    breach_date_31: Optional[date] = None
    breach_date_62: Optional[date] = None
    first_op_appt_attended_date: Optional[date] = None
    next_op_appt_attended_date: Optional[date] = None
    latest_radiology_attended_date: Optional[date] = None
    latest_histology_attended_date: Optional[date] = None
    latest_ip_procedure_tci_date: Optional[date] = None
    watchlist_reason: Optional[str] = None
    is_watchlist: bool = False
    last_updated: Optional[datetime] = None
    last_updated_by: Optional[str] = None


class ActionsKpiSummary(BaseModel):
    my_actions: int
    team_actions: int
    awaiting_assignment: int
    escalated_team_actions: int
    all_actions: int
    watchlist_only: int


class ActionWorklistResponse(BaseModel):
    items: List[ActionWorklistRow]
    summary: ActionsKpiSummary


class ActionDetailResponse(BaseModel):
    action: ActionWorklistRow
    history: List[PathwayDrawerHistoryItem] = Field(default_factory=list)
    data_provenance: dict[str, str] = Field(default_factory=dict)


class ActionUpdateItem(BaseModel):
    update_id: str
    action_id: UUID
    update_type: str
    update_tone: str
    title: str
    timestamp: datetime
    actor: Optional[str] = None
    comment_title: Optional[str] = None
    comment_text: Optional[str] = None
    action_detail: ActionDetailResponse


class ActionUpdatesResponse(BaseModel):
    items: List[ActionUpdateItem]
    total: int
    page: int
    per_page: int


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


class ServiceOverviewTrendingResponse(BaseModel):
    trending_ptl_size: List[dict]
    trending_close_day: List[dict]
    trending_action_volume: List[dict]
    current_open_pathways_mean_age: int
    mean_close_day_last_month: int
    provenance: dict[str, str] = {}


class ServiceOverviewTeamResponse(BaseModel):
    actions_by_type: List[dict]
    actions_by_team: List[dict]
    total_open_actions: int
    provenance: dict[str, str] = {}


class ServiceOverviewResponse(BaseModel):
    filters: dict[str, List[str]]
    ptl_size: dict[str, int]
    by_cancer_site: List[dict]
    trending_ptl_size: List[dict]
    by_tag: List[dict]
    by_pathway_type: List[dict]
    actions_by_type: List[dict]
    actions_by_team: List[dict]
    trending_close_day: List[dict]
    trending_action_volume: List[dict]
    current_open_pathways_mean_age: int
    mean_close_day_last_month: int
    total_open_actions: int
    provenance: dict[str, str] = {}


class IntegrationSourceStatus(BaseModel):
    source_system: str
    success_count: int
    error_count: int
    last_event_at: Optional[datetime] = None


class IntegrationIssue(BaseModel):
    source_system: Optional[str] = None
    message_type: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime


class IntegrationStatusResponse(BaseModel):
    audit_total: int
    audit_success: int
    audit_error: int
    dlq_pending: int
    dlq_total: int
    source_status: List[IntegrationSourceStatus]
    recent_errors: List[IntegrationIssue]


class SimulationStreamEvent(BaseModel):
    timestamp: datetime
    layer: str
    component: str
    title: str
    detail: str
    status: str = "success"
    source_system: Optional[str] = None
    message_type: Optional[str] = None
    file_name: Optional[str] = None
    payload_preview: Optional[str] = None
    impact_tables: List[str] = []


class SimulationDatabaseDelta(BaseModel):
    table_name: str
    before_count: int
    after_count: int
    delta: int


class SimulationCreatedPatient(BaseModel):
    nhs_number: str
    patient_name: str
    scenario: str
    source_pathway_id: str
    pathway_id: UUID


class SimulationApiCheck(BaseModel):
    name: str
    status: str
    detail: str


class SimulationRunRequest(BaseModel):
    patient_count: int = Field(default=6, ge=1, le=100)
    seed: int = 360
    anchor_date: Optional[date] = None
    source_systems: List[str] = Field(default_factory=lambda: ["pas", "ice", "ris", "somerset", "aria", "endoscopy"])


class SimulationRunSummary(BaseModel):
    run_id: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    patient_count: int
    journeys_generated: int = 0
    total_events: int = 0
    processed_events: int = 0
    failed_events: int = 0
    source_systems: List[str] = []
    source_event_counts: dict[str, int] = {}


class SimulationRunDetail(SimulationRunSummary):
    artifacts: dict[str, str] = {}
    database_deltas: List[SimulationDatabaseDelta] = []
    created_patients: List[SimulationCreatedPatient] = []
    api_checks: List[SimulationApiCheck] = []
    stream: List[SimulationStreamEvent] = []


class SimulationCatalogResponse(BaseModel):
    available_sources: List[str]
    default_sources: List[str]
    default_patient_count: int
    recommended_seed: int


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
