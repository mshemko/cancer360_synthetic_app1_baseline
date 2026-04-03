"""SQLAlchemy ORM models for the NHS FDP Cancer 360 Canonical Data Model."""

from __future__ import annotations
import uuid
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    String, Text, Boolean, SmallInteger, Integer, Date, Time,
    DateTime, Numeric, ForeignKey, ARRAY, CheckConstraint, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


# ─── Patient ────────────────────────────────────────────────────────────────

class Patient(Base):
    __tablename__ = "patient"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nhs_number: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    hospital_number: Mapped[Optional[str]] = mapped_column(String(20))
    prefix: Mapped[Optional[str]] = mapped_column(String(10))
    forename: Mapped[str] = mapped_column(String(100), nullable=False)
    surname: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    sex: Mapped[str] = mapped_column(String(1), nullable=False)
    ethnicity_code: Mapped[Optional[str]] = mapped_column(String(5))
    ethnicity_desc: Mapped[Optional[str]] = mapped_column(String(100))
    postcode: Mapped[Optional[str]] = mapped_column(String(10))
    lsoa_code: Mapped[Optional[str]] = mapped_column(String(15))
    imd_decile: Mapped[Optional[int]] = mapped_column(SmallInteger)
    gp_practice_code: Mapped[Optional[str]] = mapped_column(String(10))
    gp_name: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    nok_name: Mapped[Optional[str]] = mapped_column(String(200))
    nok_relationship: Mapped[Optional[str]] = mapped_column(String(50))
    deceased_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    referrals: Mapped[List[Referral]] = relationship(back_populates="patient", lazy="selectin")
    diagnoses: Mapped[List[Diagnosis]] = relationship(back_populates="patient", lazy="selectin")
    pathways: Mapped[List[CancerPathway]] = relationship(back_populates="patient", lazy="selectin")


# ─── Referral ───────────────────────────────────────────────────────────────

class Referral(Base):
    __tablename__ = "referral"

    referral_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.patient_id"), nullable=False, index=True)
    source_referral_id: Mapped[Optional[str]] = mapped_column(String(50))
    ubrn: Mapped[Optional[str]] = mapped_column(String(20))
    referral_date: Mapped[date] = mapped_column(Date, nullable=False)
    receipt_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    clock_start_date: Mapped[Optional[date]] = mapped_column(Date)
    referral_source: Mapped[Optional[str]] = mapped_column(String(50))
    referral_priority: Mapped[Optional[str]] = mapped_column(String(30))
    referred_to_specialty: Mapped[Optional[str]] = mapped_column(String(10))
    referred_to_consultant: Mapped[Optional[str]] = mapped_column(String(20))
    referring_gp_code: Mapped[Optional[str]] = mapped_column(String(20))
    referring_practice: Mapped[Optional[str]] = mapped_column(String(20))
    clinical_info: Mapped[Optional[str]] = mapped_column(Text)
    cancer_type_code: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    status: Mapped[str] = mapped_column(String(30), default="open")
    source_system: Mapped[Optional[str]] = mapped_column(String(50))
    source_message_id: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    patient: Mapped[Patient] = relationship(back_populates="referrals")


# ─── Diagnosis ──────────────────────────────────────────────────────────────

class Diagnosis(Base):
    __tablename__ = "diagnosis"

    diagnosis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.patient_id"), nullable=False, index=True)
    referral_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("referral.referral_id"))
    diagnosis_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    icd10_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    icd10_description: Mapped[Optional[str]] = mapped_column(String(500))
    morphology_code: Mapped[Optional[str]] = mapped_column(String(10))
    morphology_desc: Mapped[Optional[str]] = mapped_column(String(500))
    laterality: Mapped[Optional[str]] = mapped_column(String(1))
    basis_of_diagnosis: Mapped[Optional[str]] = mapped_column(String(5))
    source_system: Mapped[Optional[str]] = mapped_column(String(50))
    source_message_id: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    patient: Mapped[Patient] = relationship(back_populates="diagnoses")
    staging: Mapped[List[Staging]] = relationship(back_populates="diagnosis", lazy="selectin")


# ─── Staging ────────────────────────────────────────────────────────────────

class Staging(Base):
    __tablename__ = "staging"

    staging_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.patient_id"), nullable=False, index=True)
    diagnosis_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("diagnosis.diagnosis_id"), index=True)
    staging_date: Mapped[date] = mapped_column(Date, nullable=False)
    staging_type: Mapped[Optional[str]] = mapped_column(String(20))
    tnm_t: Mapped[Optional[str]] = mapped_column(String(10))
    tnm_n: Mapped[Optional[str]] = mapped_column(String(10))
    tnm_m: Mapped[Optional[str]] = mapped_column(String(10))
    stage_group: Mapped[Optional[str]] = mapped_column(String(20))
    grade: Mapped[Optional[str]] = mapped_column(String(10))
    performance_status: Mapped[Optional[int]] = mapped_column(SmallInteger)
    staging_system: Mapped[str] = mapped_column(String(50), default="AJCC 8th")
    figo_stage: Mapped[Optional[str]] = mapped_column(String(20))
    dukes_stage: Mapped[Optional[str]] = mapped_column(String(5))
    gleason_primary: Mapped[Optional[int]] = mapped_column(SmallInteger)
    gleason_secondary: Mapped[Optional[int]] = mapped_column(SmallInteger)
    gleason_total: Mapped[Optional[int]] = mapped_column(SmallInteger)
    isup_grade_group: Mapped[Optional[int]] = mapped_column(SmallInteger)
    source_system: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    diagnosis: Mapped[Optional[Diagnosis]] = relationship(back_populates="staging")


# ─── Episode ────────────────────────────────────────────────────────────────

class Episode(Base):
    __tablename__ = "episode"

    episode_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.patient_id"), nullable=False, index=True)
    source_spell_id: Mapped[Optional[str]] = mapped_column(String(50))
    source_episode_id: Mapped[Optional[str]] = mapped_column(String(50))
    episode_type: Mapped[Optional[str]] = mapped_column(String(20))
    admission_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    admission_time: Mapped[Optional[time]] = mapped_column(Time)
    admission_method: Mapped[Optional[str]] = mapped_column(String(10))
    discharge_date: Mapped[Optional[date]] = mapped_column(Date)
    discharge_time: Mapped[Optional[time]] = mapped_column(Time)
    discharge_method: Mapped[Optional[str]] = mapped_column(String(10))
    specialty_code: Mapped[Optional[str]] = mapped_column(String(10))
    specialty_name: Mapped[Optional[str]] = mapped_column(String(200))
    consultant_code: Mapped[Optional[str]] = mapped_column(String(20))
    consultant_name: Mapped[Optional[str]] = mapped_column(String(200))
    ward_code: Mapped[Optional[str]] = mapped_column(String(20))
    ward_name: Mapped[Optional[str]] = mapped_column(String(100))
    primary_diagnosis: Mapped[Optional[str]] = mapped_column(String(10))
    primary_procedure: Mapped[Optional[str]] = mapped_column(String(10))
    primary_procedure_desc: Mapped[Optional[str]] = mapped_column(String(500))
    procedure_date: Mapped[Optional[date]] = mapped_column(Date)
    hrg_code: Mapped[Optional[str]] = mapped_column(String(10))
    los_days: Mapped[Optional[int]] = mapped_column(SmallInteger)
    source_system: Mapped[Optional[str]] = mapped_column(String(50))
    source_message_id: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# ─── Appointment ────────────────────────────────────────────────────────────

class Appointment(Base):
    __tablename__ = "appointment"

    appointment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.patient_id"), nullable=False, index=True)
    referral_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("referral.referral_id"))
    source_appt_id: Mapped[Optional[str]] = mapped_column(String(50))
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    appointment_time: Mapped[Optional[time]] = mapped_column(Time)
    clinic_code: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    clinic_name: Mapped[Optional[str]] = mapped_column(String(200))
    specialty_code: Mapped[Optional[str]] = mapped_column(String(10))
    consultant_code: Mapped[Optional[str]] = mapped_column(String(20))
    consultant_name: Mapped[Optional[str]] = mapped_column(String(200))
    appointment_type: Mapped[Optional[str]] = mapped_column(String(30))
    attendance_status: Mapped[Optional[str]] = mapped_column(String(10))
    outcome_code: Mapped[Optional[str]] = mapped_column(String(10))
    session_type: Mapped[str] = mapped_column(String(30), default="face_to_face")
    location: Mapped[Optional[str]] = mapped_column(String(200))
    source_system: Mapped[Optional[str]] = mapped_column(String(50))
    source_message_id: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# ─── Pathology Result ───────────────────────────────────────────────────────

class PathologyResult(Base):
    __tablename__ = "pathology_result"

    result_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.patient_id"), nullable=False, index=True)
    source_accession: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(50))
    order_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    specimen_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    report_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    discipline: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    test_code: Mapped[Optional[str]] = mapped_column(String(50))
    test_name: Mapped[Optional[str]] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="final")
    requesting_clinician_code: Mapped[Optional[str]] = mapped_column(String(20))
    requesting_clinician_name: Mapped[Optional[str]] = mapped_column(String(200))
    reporting_pathologist_code: Mapped[Optional[str]] = mapped_column(String(20))
    reporting_pathologist_name: Mapped[Optional[str]] = mapped_column(String(200))
    narrative_report: Mapped[Optional[str]] = mapped_column(Text)
    source_system: Mapped[str] = mapped_column(String(50), default="ICE")
    source_message_id: Mapped[Optional[str]] = mapped_column(String(100))
    raw_hl7: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    values: Mapped[List[PathologyResultValue]] = relationship(back_populates="result", lazy="selectin")
    histopath: Mapped[Optional[HistopathStructured]] = relationship(back_populates="result", uselist=False, lazy="selectin")


class PathologyResultValue(Base):
    __tablename__ = "pathology_result_value"

    value_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pathology_result.result_id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_number: Mapped[Optional[int]] = mapped_column(SmallInteger)
    test_code: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    test_name: Mapped[Optional[str]] = mapped_column(String(200))
    value_type: Mapped[Optional[str]] = mapped_column(String(10))
    numeric_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    text_value: Mapped[Optional[str]] = mapped_column(Text)
    coded_value: Mapped[Optional[str]] = mapped_column(String(50))
    coded_display: Mapped[Optional[str]] = mapped_column(String(200))
    coding_system: Mapped[Optional[str]] = mapped_column(String(50))
    unit: Mapped[Optional[str]] = mapped_column(String(50))
    reference_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    reference_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    reference_range_text: Mapped[Optional[str]] = mapped_column(String(100))
    abnormal_flag: Mapped[Optional[str]] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    result: Mapped[PathologyResult] = relationship(back_populates="values")


class HistopathStructured(Base):
    __tablename__ = "histopath_structured"

    histopath_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pathology_result.result_id", ondelete="CASCADE"), unique=True, nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.patient_id"), nullable=False, index=True)
    tumour_type: Mapped[Optional[str]] = mapped_column(String(200))
    grade: Mapped[Optional[str]] = mapped_column(String(10))
    tumour_size_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 1))
    margin_status: Mapped[Optional[str]] = mapped_column(String(50))
    margin_closest_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 1))
    lymphovascular_invasion: Mapped[Optional[str]] = mapped_column(String(20))
    perineural_invasion: Mapped[Optional[str]] = mapped_column(String(20))
    nodes_examined: Mapped[Optional[int]] = mapped_column(SmallInteger)
    nodes_positive: Mapped[Optional[int]] = mapped_column(SmallInteger)
    er_status: Mapped[Optional[str]] = mapped_column(String(20))
    er_allred: Mapped[Optional[str]] = mapped_column(String(10))
    pr_status: Mapped[Optional[str]] = mapped_column(String(20))
    pr_allred: Mapped[Optional[str]] = mapped_column(String(10))
    her2_status: Mapped[Optional[str]] = mapped_column(String(20))
    her2_ihc_score: Mapped[Optional[str]] = mapped_column(String(10))
    ki67_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
    msi_status: Mapped[Optional[str]] = mapped_column(String(30))
    mmr_status: Mapped[Optional[str]] = mapped_column(String(100))
    kras_status: Mapped[Optional[str]] = mapped_column(String(30))
    braf_status: Mapped[Optional[str]] = mapped_column(String(30))
    egfr_status: Mapped[Optional[str]] = mapped_column(String(30))
    alk_status: Mapped[Optional[str]] = mapped_column(String(30))
    pdl1_tps: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    result: Mapped[PathologyResult] = relationship(back_populates="histopath")


# ─── Radiology Result ───────────────────────────────────────────────────────

class RadiologyResult(Base):
    __tablename__ = "radiology_result"

    result_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.patient_id"), nullable=False, index=True)
    accession_number: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(50))
    exam_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    report_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    modality: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    body_part: Mapped[Optional[str]] = mapped_column(String(100))
    exam_code: Mapped[Optional[str]] = mapped_column(String(50))
    exam_description: Mapped[Optional[str]] = mapped_column(String(500))
    clinical_indication: Mapped[Optional[str]] = mapped_column(Text)
    report_text: Mapped[Optional[str]] = mapped_column(Text)
    conclusion: Mapped[Optional[str]] = mapped_column(Text)
    addendum: Mapped[Optional[str]] = mapped_column(Text)
    requesting_clinician_code: Mapped[Optional[str]] = mapped_column(String(20))
    requesting_clinician_name: Mapped[Optional[str]] = mapped_column(String(200))
    reporting_radiologist_code: Mapped[Optional[str]] = mapped_column(String(20))
    reporting_radiologist_name: Mapped[Optional[str]] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="verified")
    urgency: Mapped[Optional[str]] = mapped_column(String(20))
    source_system: Mapped[str] = mapped_column(String(50), default="RIS")
    source_message_id: Mapped[Optional[str]] = mapped_column(String(100))
    raw_hl7: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# ─── SACT ───────────────────────────────────────────────────────────────────

class SACTCourse(Base):
    __tablename__ = "sact_course"

    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.patient_id"), nullable=False, index=True)
    diagnosis_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("diagnosis.diagnosis_id"))
    source_sact_id: Mapped[Optional[str]] = mapped_column(String(50))
    regimen_name: Mapped[Optional[str]] = mapped_column(String(100))
    regimen_code: Mapped[Optional[str]] = mapped_column(String(50))
    regimen_intent: Mapped[Optional[str]] = mapped_column(String(50))
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    max_cycles: Mapped[Optional[int]] = mapped_column(SmallInteger)
    completed_cycles: Mapped[int] = mapped_column(SmallInteger, default=0)
    course_status: Mapped[str] = mapped_column(String(30), default="active")
    consultant_code: Mapped[Optional[str]] = mapped_column(String(20))
    consultant_name: Mapped[Optional[str]] = mapped_column(String(200))
    organisation_code: Mapped[Optional[str]] = mapped_column(String(20))
    source_system: Mapped[str] = mapped_column(String(50), default="CHEMOCARE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    cycles: Mapped[List[SACTCycle]] = relationship(back_populates="course", lazy="selectin")


class SACTCycle(Base):
    __tablename__ = "sact_cycle"

    cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sact_course.course_id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.patient_id"), nullable=False, index=True)
    cycle_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    height_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
    weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
    bsa_m2: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    performance_status: Mapped[Optional[int]] = mapped_column(SmallInteger)
    cycle_outcome: Mapped[Optional[str]] = mapped_column(String(50))
    delay_days: Mapped[int] = mapped_column(SmallInteger, default=0)
    dose_reduction_pct: Mapped[int] = mapped_column(SmallInteger, default=0)
    toxicity_grade: Mapped[Optional[int]] = mapped_column(SmallInteger)
    toxicity_type: Mapped[Optional[str]] = mapped_column(String(100))
    source_system: Mapped[str] = mapped_column(String(50), default="CHEMOCARE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    course: Mapped[SACTCourse] = relationship(back_populates="cycles")
    drugs: Mapped[List[SACTDrug]] = relationship(back_populates="cycle", lazy="selectin")


class SACTDrug(Base):
    __tablename__ = "sact_drug"

    drug_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sact_cycle.cycle_id", ondelete="CASCADE"), nullable=False, index=True)
    drug_name: Mapped[str] = mapped_column(String(100), nullable=False)
    drug_code: Mapped[Optional[str]] = mapped_column(String(50))
    dose_mg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    dose_per_m2: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    actual_dose_pct: Mapped[int] = mapped_column(SmallInteger, default=100)
    route: Mapped[Optional[str]] = mapped_column(String(20))
    administration_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    cycle: Mapped[SACTCycle] = relationship(back_populates="drugs")


# ─── Radiotherapy ───────────────────────────────────────────────────────────

class RadiotherapyCourse(Base):
    __tablename__ = "radiotherapy_course"

    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.patient_id"), nullable=False, index=True)
    diagnosis_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("diagnosis.diagnosis_id"))
    source_course_id: Mapped[Optional[str]] = mapped_column(String(50))
    treatment_intent: Mapped[Optional[str]] = mapped_column(String(50))
    treatment_site: Mapped[Optional[str]] = mapped_column(String(200))
    technique: Mapped[Optional[str]] = mapped_column(String(50))
    total_dose_gy: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    fractions_prescribed: Mapped[Optional[int]] = mapped_column(SmallInteger)
    dose_per_fraction_gy: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    first_fraction_date: Mapped[Optional[date]] = mapped_column(Date)
    last_fraction_date: Mapped[Optional[date]] = mapped_column(Date)
    planning_ct_date: Mapped[Optional[date]] = mapped_column(Date)
    machine_id: Mapped[Optional[str]] = mapped_column(String(20))
    concurrent_sact: Mapped[bool] = mapped_column(Boolean, default=False)
    course_status: Mapped[str] = mapped_column(String(30), default="active")
    consultant_code: Mapped[Optional[str]] = mapped_column(String(20))
    consultant_name: Mapped[Optional[str]] = mapped_column(String(200))
    source_system: Mapped[str] = mapped_column(String(50), default="MOSAIQ")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    fractions: Mapped[List[RadiotherapyFraction]] = relationship(back_populates="course", lazy="selectin")


class RadiotherapyFraction(Base):
    __tablename__ = "radiotherapy_fraction"

    fraction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("radiotherapy_course.course_id", ondelete="CASCADE"), nullable=False, index=True)
    fraction_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    scheduled_date: Mapped[Optional[date]] = mapped_column(Date)
    delivered_date: Mapped[Optional[date]] = mapped_column(Date)
    delivered_time: Mapped[Optional[time]] = mapped_column(Time)
    dose_gy: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    machine_id: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    course: Mapped[RadiotherapyCourse] = relationship(back_populates="fractions")


# ─── MDT Discussion ─────────────────────────────────────────────────────────

class MDTDiscussion(Base):
    __tablename__ = "mdt_discussion"

    mdt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.patient_id"), nullable=False, index=True)
    diagnosis_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("diagnosis.diagnosis_id"))
    mdt_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    mdt_site: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    mdt_type: Mapped[Optional[str]] = mapped_column(String(50))
    meeting_venue: Mapped[Optional[str]] = mapped_column(String(200))
    chair_code: Mapped[Optional[str]] = mapped_column(String(20))
    chair_name: Mapped[Optional[str]] = mapped_column(String(200))
    quorate: Mapped[bool] = mapped_column(Boolean, default=True)
    clinical_summary: Mapped[Optional[str]] = mapped_column(Text)
    staging_presented: Mapped[Optional[str]] = mapped_column(String(100))
    decision: Mapped[Optional[str]] = mapped_column(Text)
    treatment_intent: Mapped[Optional[str]] = mapped_column(String(50))
    patient_informed_date: Mapped[Optional[date]] = mapped_column(Date)
    source_system: Mapped[str] = mapped_column(String(50), default="INFOFLEX")
    source_message_id: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# ─── Cancer Action (worklist) ───────────────────────────────────────────────

class CancerAction(Base):
    __tablename__ = "cancer_action"

    action_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.patient_id"), nullable=False, index=True)
    pathway_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_description: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    assigned_team: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    assigned_user: Mapped[Optional[str]] = mapped_column(String(200))
    created_by: Mapped[Optional[str]] = mapped_column(String(200))
    completed_by: Mapped[Optional[str]] = mapped_column(String(200))
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    source_system: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# ─── Cancer Pathway (derived) ───────────────────────────────────────────────

class CancerPathway(Base):
    __tablename__ = "cancer_pathway"

    pathway_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient.patient_id"), nullable=False, index=True)
    referral_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("referral.referral_id"), index=True)
    diagnosis_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("diagnosis.diagnosis_id"))
    staging_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("staging.staging_id"))
    cancer_type_code: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    cancer_type_desc: Mapped[Optional[str]] = mapped_column(String(100))
    date_referral_received: Mapped[Optional[date]] = mapped_column(Date)
    date_first_seen: Mapped[Optional[date]] = mapped_column(Date)
    date_diagnosis: Mapped[Optional[date]] = mapped_column(Date)
    date_mdt: Mapped[Optional[date]] = mapped_column(Date)
    date_decision_to_treat: Mapped[Optional[date]] = mapped_column(Date)
    date_first_treatment: Mapped[Optional[date]] = mapped_column(Date)
    days_to_first_seen: Mapped[Optional[int]] = mapped_column(SmallInteger)
    days_to_diagnosis: Mapped[Optional[int]] = mapped_column(SmallInteger)
    days_to_treatment: Mapped[Optional[int]] = mapped_column(SmallInteger)
    fds_28day_met: Mapped[Optional[bool]] = mapped_column(Boolean)
    standard_62day_met: Mapped[Optional[bool]] = mapped_column(Boolean)
    standard_31day_met: Mapped[Optional[bool]] = mapped_column(Boolean)
    treatment_modality: Mapped[Optional[str]] = mapped_column(String(100))
    first_treatment_type: Mapped[Optional[str]] = mapped_column(String(50))
    pathway_status: Mapped[str] = mapped_column(String(50), default="open", index=True)
    current_stage_label: Mapped[Optional[str]] = mapped_column(String(200))
    next_action: Mapped[Optional[str]] = mapped_column(Text)
    next_action_date: Mapped[Optional[date]] = mapped_column(Date)
    assigned_team: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    assigned_user: Mapped[Optional[str]] = mapped_column(String(200))
    breach_risk: Mapped[str] = mapped_column(String(20), default="none", index=True)
    clock_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    clock_pause_reason: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    patient: Mapped[Patient] = relationship(back_populates="pathways")
