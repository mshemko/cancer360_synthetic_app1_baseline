-- ============================================================================
-- NHS FDP Cancer 360 — Canonical Data Model Schema
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── Core identity ─────────────────────────────────────────────────────────

CREATE TABLE patient (
    patient_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nhs_number          CHAR(10) UNIQUE NOT NULL,
    hospital_number     VARCHAR(20),
    prefix              VARCHAR(10),
    forename            VARCHAR(100) NOT NULL,
    surname             VARCHAR(100) NOT NULL,
    date_of_birth       DATE NOT NULL,
    sex                 CHAR(1) NOT NULL CHECK (sex IN ('M','F','I','X')),
    ethnicity_code      VARCHAR(5),
    ethnicity_desc      VARCHAR(100),
    postcode            VARCHAR(10),
    lsoa_code           VARCHAR(15),
    imd_decile          SMALLINT,
    gp_practice_code    VARCHAR(10),
    gp_name             VARCHAR(200),
    phone               VARCHAR(20),
    email               VARCHAR(200),
    nok_name            VARCHAR(200),
    nok_relationship    VARCHAR(50),
    deceased_date       DATE,
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_patient_nhs ON patient(nhs_number);
CREATE INDEX idx_patient_surname ON patient(surname);
CREATE INDEX idx_patient_gp ON patient(gp_practice_code);

-- ─── Cancer referral ───────────────────────────────────────────────────────

CREATE TABLE referral (
    referral_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          UUID NOT NULL REFERENCES patient(patient_id),
    source_referral_id  VARCHAR(50),
    ubrn                VARCHAR(20),
    referral_date       DATE NOT NULL,
    receipt_date        DATE NOT NULL,
    clock_start_date    DATE,
    referral_source     VARCHAR(50),
    referral_priority   VARCHAR(30),
    referred_to_specialty VARCHAR(10),
    referred_to_consultant VARCHAR(20),
    referring_gp_code   VARCHAR(20),
    referring_practice  VARCHAR(20),
    clinical_info       TEXT,
    cancer_type_code    VARCHAR(10),
    status              VARCHAR(30) DEFAULT 'open',
    source_system       VARCHAR(50),
    source_message_id   VARCHAR(100),
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_referral_patient ON referral(patient_id);
CREATE INDEX idx_referral_status ON referral(status);
CREATE INDEX idx_referral_date ON referral(receipt_date);
CREATE INDEX idx_referral_cancer_type ON referral(cancer_type_code);

-- ─── Cancer diagnosis ──────────────────────────────────────────────────────

CREATE TABLE diagnosis (
    diagnosis_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          UUID NOT NULL REFERENCES patient(patient_id),
    referral_id         UUID REFERENCES referral(referral_id),
    diagnosis_date      DATE NOT NULL,
    icd10_code          VARCHAR(10) NOT NULL,
    icd10_description   VARCHAR(500),
    morphology_code     VARCHAR(10),
    morphology_desc     VARCHAR(500),
    laterality          CHAR(1),
    basis_of_diagnosis  VARCHAR(5),
    source_system       VARCHAR(50),
    source_message_id   VARCHAR(100),
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_diagnosis_patient ON diagnosis(patient_id);
CREATE INDEX idx_diagnosis_icd10 ON diagnosis(icd10_code);
CREATE INDEX idx_diagnosis_date ON diagnosis(diagnosis_date);

-- ─── TNM staging ───────────────────────────────────────────────────────────

CREATE TABLE staging (
    staging_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          UUID NOT NULL REFERENCES patient(patient_id),
    diagnosis_id        UUID REFERENCES diagnosis(diagnosis_id),
    staging_date        DATE NOT NULL,
    staging_type        VARCHAR(20) CHECK (staging_type IN ('clinical','pathological','post_neoadjuvant')),
    tnm_t               VARCHAR(10),
    tnm_n               VARCHAR(10),
    tnm_m               VARCHAR(10),
    stage_group         VARCHAR(20),
    grade               VARCHAR(10),
    performance_status  SMALLINT CHECK (performance_status BETWEEN 0 AND 4),
    staging_system      VARCHAR(50) DEFAULT 'AJCC 8th',
    figo_stage          VARCHAR(20),
    dukes_stage         VARCHAR(5),
    gleason_primary     SMALLINT,
    gleason_secondary   SMALLINT,
    gleason_total       SMALLINT,
    isup_grade_group    SMALLINT,
    source_system       VARCHAR(50),
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_staging_patient ON staging(patient_id);
CREATE INDEX idx_staging_diagnosis ON staging(diagnosis_id);

-- ─── Episodes (inpatient/outpatient/day case) ──────────────────────────────

CREATE TABLE episode (
    episode_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          UUID NOT NULL REFERENCES patient(patient_id),
    source_spell_id     VARCHAR(50),
    source_episode_id   VARCHAR(50),
    episode_type        VARCHAR(20) CHECK (episode_type IN ('inpatient','outpatient','day_case','emergency')),
    admission_date      DATE,
    admission_time      TIME,
    admission_method    VARCHAR(10),
    discharge_date      DATE,
    discharge_time      TIME,
    discharge_method    VARCHAR(10),
    specialty_code      VARCHAR(10),
    specialty_name      VARCHAR(200),
    consultant_code     VARCHAR(20),
    consultant_name     VARCHAR(200),
    ward_code           VARCHAR(20),
    ward_name           VARCHAR(100),
    primary_diagnosis   VARCHAR(10),
    secondary_diagnoses TEXT[],
    primary_procedure   VARCHAR(10),
    primary_procedure_desc VARCHAR(500),
    procedure_date      DATE,
    secondary_procedures TEXT[],
    hrg_code            VARCHAR(10),
    los_days            SMALLINT,
    source_system       VARCHAR(50),
    source_message_id   VARCHAR(100),
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_episode_patient ON episode(patient_id);
CREATE INDEX idx_episode_type ON episode(episode_type);
CREATE INDEX idx_episode_admission ON episode(admission_date);

-- ─── Appointments ──────────────────────────────────────────────────────────

CREATE TABLE appointment (
    appointment_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          UUID NOT NULL REFERENCES patient(patient_id),
    referral_id         UUID REFERENCES referral(referral_id),
    source_appt_id      VARCHAR(50),
    appointment_date    DATE NOT NULL,
    appointment_time    TIME,
    clinic_code         VARCHAR(20),
    clinic_name         VARCHAR(200),
    specialty_code      VARCHAR(10),
    consultant_code     VARCHAR(20),
    consultant_name     VARCHAR(200),
    appointment_type    VARCHAR(30),
    attendance_status   VARCHAR(10),
    outcome_code        VARCHAR(10),
    session_type        VARCHAR(30) DEFAULT 'face_to_face',
    location            VARCHAR(200),
    source_system       VARCHAR(50),
    source_message_id   VARCHAR(100),
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_appointment_patient ON appointment(patient_id);
CREATE INDEX idx_appointment_date ON appointment(appointment_date);
CREATE INDEX idx_appointment_clinic ON appointment(clinic_code);

-- ─── Pathology results ─────────────────────────────────────────────────────

CREATE TABLE pathology_result (
    result_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          UUID NOT NULL REFERENCES patient(patient_id),
    source_accession    VARCHAR(50),
    order_id            VARCHAR(50),
    order_date          TIMESTAMPTZ,
    specimen_date       TIMESTAMPTZ,
    report_date         TIMESTAMPTZ,
    discipline          VARCHAR(50),
    test_code           VARCHAR(50),
    test_name           VARCHAR(200),
    status              VARCHAR(20) DEFAULT 'final',
    requesting_clinician_code VARCHAR(20),
    requesting_clinician_name VARCHAR(200),
    reporting_pathologist_code VARCHAR(20),
    reporting_pathologist_name VARCHAR(200),
    narrative_report    TEXT,
    source_system       VARCHAR(50) DEFAULT 'ICE',
    source_message_id   VARCHAR(100),
    raw_hl7             TEXT,
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_pathology_patient ON pathology_result(patient_id);
CREATE INDEX idx_pathology_discipline ON pathology_result(discipline);
CREATE INDEX idx_pathology_date ON pathology_result(report_date);
CREATE INDEX idx_pathology_accession ON pathology_result(source_accession);

-- ─── Individual result values (child of pathology_result) ──────────────────

CREATE TABLE pathology_result_value (
    value_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    result_id           UUID NOT NULL REFERENCES pathology_result(result_id) ON DELETE CASCADE,
    sequence_number     SMALLINT,
    test_code           VARCHAR(50),
    test_name           VARCHAR(200),
    value_type          VARCHAR(10) CHECK (value_type IN ('numeric','coded','text')),
    numeric_value       DECIMAL(12,4),
    text_value          TEXT,
    coded_value         VARCHAR(50),
    coded_display       VARCHAR(200),
    coding_system       VARCHAR(50),
    unit                VARCHAR(50),
    reference_low       DECIMAL(12,4),
    reference_high      DECIMAL(12,4),
    reference_range_text VARCHAR(100),
    abnormal_flag       VARCHAR(10),
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_pathvalue_result ON pathology_result_value(result_id);
CREATE INDEX idx_pathvalue_test ON pathology_result_value(test_code);

-- ─── Structured histopathology (extracted from narrative) ──────────────────

CREATE TABLE histopath_structured (
    histopath_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    result_id           UUID UNIQUE NOT NULL REFERENCES pathology_result(result_id) ON DELETE CASCADE,
    patient_id          UUID NOT NULL REFERENCES patient(patient_id),
    tumour_type         VARCHAR(200),
    tumour_type_snomed  VARCHAR(20),
    grade               VARCHAR(10),
    tubules_score       SMALLINT,
    nuclei_score        SMALLINT,
    mitoses_score       SMALLINT,
    total_grade_score   SMALLINT,
    tumour_size_mm      DECIMAL(6,1),
    margin_status       VARCHAR(50),
    margin_closest_mm   DECIMAL(6,1),
    lymphovascular_invasion VARCHAR(20),
    perineural_invasion VARCHAR(20),
    nodes_examined      SMALLINT,
    nodes_positive      SMALLINT,
    extranodal_extension VARCHAR(20),
    er_status           VARCHAR(20),
    er_allred           VARCHAR(10),
    er_percentage       DECIMAL(5,1),
    pr_status           VARCHAR(20),
    pr_allred           VARCHAR(10),
    pr_percentage       DECIMAL(5,1),
    her2_status         VARCHAR(20),
    her2_ihc_score      VARCHAR(10),
    her2_fish_ratio     DECIMAL(4,2),
    ki67_percent        DECIMAL(5,1),
    msi_status          VARCHAR(30),
    mmr_status          VARCHAR(100),
    mmr_mlh1            VARCHAR(20),
    mmr_pms2            VARCHAR(20),
    mmr_msh2            VARCHAR(20),
    mmr_msh6            VARCHAR(20),
    kras_status         VARCHAR(30),
    kras_mutation       VARCHAR(100),
    nras_status         VARCHAR(30),
    braf_status         VARCHAR(30),
    braf_mutation       VARCHAR(100),
    egfr_status         VARCHAR(30),
    egfr_mutation       VARCHAR(100),
    alk_status          VARCHAR(30),
    ros1_status         VARCHAR(30),
    pdl1_tps            DECIMAL(5,1),
    pdl1_clone          VARCHAR(20),
    oncotype_score      SMALLINT,
    crm_mm              DECIMAL(6,1),
    emvi_status         VARCHAR(20),
    tumour_budding      VARCHAR(20),
    pt_stage            VARCHAR(10),
    pn_stage            VARCHAR(10),
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_histopath_patient ON histopath_structured(patient_id);
CREATE INDEX idx_histopath_result ON histopath_structured(result_id);

-- ─── Radiology results ─────────────────────────────────────────────────────

CREATE TABLE radiology_result (
    result_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          UUID NOT NULL REFERENCES patient(patient_id),
    accession_number    VARCHAR(50),
    order_id            VARCHAR(50),
    exam_date           TIMESTAMPTZ NOT NULL,
    report_date         TIMESTAMPTZ,
    modality            VARCHAR(20),
    body_part           VARCHAR(100),
    exam_code           VARCHAR(50),
    exam_description    VARCHAR(500),
    clinical_indication TEXT,
    report_text         TEXT,
    conclusion          TEXT,
    addendum            TEXT,
    requesting_clinician_code VARCHAR(20),
    requesting_clinician_name VARCHAR(200),
    reporting_radiologist_code VARCHAR(20),
    reporting_radiologist_name VARCHAR(200),
    status              VARCHAR(20) DEFAULT 'verified',
    urgency             VARCHAR(20),
    source_system       VARCHAR(50) DEFAULT 'RIS',
    source_message_id   VARCHAR(100),
    raw_hl7             TEXT,
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_radiology_patient ON radiology_result(patient_id);
CREATE INDEX idx_radiology_modality ON radiology_result(modality);
CREATE INDEX idx_radiology_date ON radiology_result(exam_date);
CREATE INDEX idx_radiology_accession ON radiology_result(accession_number);

-- ─── SACT chemotherapy courses ─────────────────────────────────────────────

CREATE TABLE sact_course (
    course_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          UUID NOT NULL REFERENCES patient(patient_id),
    diagnosis_id        UUID REFERENCES diagnosis(diagnosis_id),
    source_sact_id      VARCHAR(50),
    regimen_name        VARCHAR(100),
    regimen_code        VARCHAR(50),
    regimen_intent      VARCHAR(50),
    start_date          DATE,
    end_date            DATE,
    max_cycles          SMALLINT,
    completed_cycles    SMALLINT DEFAULT 0,
    course_status       VARCHAR(30) DEFAULT 'active',
    discontinuation_reason VARCHAR(200),
    consultant_code     VARCHAR(20),
    consultant_name     VARCHAR(200),
    organisation_code   VARCHAR(20),
    source_system       VARCHAR(50) DEFAULT 'CHEMOCARE',
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_sact_course_patient ON sact_course(patient_id);

-- ─── SACT chemotherapy cycles ──────────────────────────────────────────────

CREATE TABLE sact_cycle (
    cycle_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id           UUID NOT NULL REFERENCES sact_course(course_id) ON DELETE CASCADE,
    patient_id          UUID NOT NULL REFERENCES patient(patient_id),
    cycle_number        SMALLINT NOT NULL,
    start_date          DATE NOT NULL,
    end_date            DATE,
    height_cm           DECIMAL(5,1),
    weight_kg           DECIMAL(5,1),
    bsa_m2              DECIMAL(4,2),
    performance_status  SMALLINT,
    cycle_outcome       VARCHAR(50),
    delay_days          SMALLINT DEFAULT 0,
    dose_reduction_pct  SMALLINT DEFAULT 0,
    toxicity_grade      SMALLINT,
    toxicity_type       VARCHAR(100),
    source_system       VARCHAR(50) DEFAULT 'CHEMOCARE',
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_sact_cycle_patient ON sact_cycle(patient_id);
CREATE INDEX idx_sact_cycle_course ON sact_cycle(course_id);

-- ─── SACT drug administrations (child of sact_cycle) ───────────────────────

CREATE TABLE sact_drug (
    drug_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id            UUID NOT NULL REFERENCES sact_cycle(cycle_id) ON DELETE CASCADE,
    drug_name           VARCHAR(100) NOT NULL,
    drug_code           VARCHAR(50),
    dose_mg             DECIMAL(10,2),
    dose_per_m2         DECIMAL(10,2),
    dose_band           VARCHAR(50),
    actual_dose_pct     SMALLINT DEFAULT 100,
    route               VARCHAR(20),
    administration_date DATE,
    infusion_duration_mins SMALLINT,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_sact_drug_cycle ON sact_drug(cycle_id);

-- ─── Radiotherapy courses ──────────────────────────────────────────────────

CREATE TABLE radiotherapy_course (
    course_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          UUID NOT NULL REFERENCES patient(patient_id),
    diagnosis_id        UUID REFERENCES diagnosis(diagnosis_id),
    source_course_id    VARCHAR(50),
    treatment_intent    VARCHAR(50),
    treatment_site      VARCHAR(200),
    technique           VARCHAR(50),
    total_dose_gy       DECIMAL(6,2),
    fractions_prescribed SMALLINT,
    dose_per_fraction_gy DECIMAL(6,2),
    first_fraction_date DATE,
    last_fraction_date  DATE,
    planning_ct_date    DATE,
    plan_approved_date  DATE,
    plan_approved_by    VARCHAR(200),
    machine_id          VARCHAR(20),
    energy_mv           SMALLINT,
    concurrent_sact     BOOLEAN DEFAULT false,
    course_status       VARCHAR(30) DEFAULT 'active',
    consultant_code     VARCHAR(20),
    consultant_name     VARCHAR(200),
    organisation_code   VARCHAR(20),
    source_system       VARCHAR(50) DEFAULT 'MOSAIQ',
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_rt_course_patient ON radiotherapy_course(patient_id);

-- ─── Radiotherapy fractions ────────────────────────────────────────────────

CREATE TABLE radiotherapy_fraction (
    fraction_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id           UUID NOT NULL REFERENCES radiotherapy_course(course_id) ON DELETE CASCADE,
    fraction_number     SMALLINT NOT NULL,
    scheduled_date      DATE,
    delivered_date      DATE,
    delivered_time      TIME,
    dose_gy             DECIMAL(6,2),
    status              VARCHAR(20) DEFAULT 'scheduled',
    machine_id          VARCHAR(20),
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_rt_fraction_course ON radiotherapy_fraction(course_id);

-- ─── Radiotherapy on-treatment reviews ─────────────────────────────────────

CREATE TABLE radiotherapy_review (
    review_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id           UUID NOT NULL REFERENCES radiotherapy_course(course_id) ON DELETE CASCADE,
    review_date         DATE NOT NULL,
    week_number         SMALLINT,
    toxicity_description TEXT,
    ctcae_grade         SMALLINT,
    action_taken        TEXT,
    reviewer_code       VARCHAR(20),
    reviewer_name       VARCHAR(200),
    created_at          TIMESTAMPTZ DEFAULT now()
);

-- ─── MDT discussions ───────────────────────────────────────────────────────

CREATE TABLE mdt_discussion (
    mdt_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          UUID NOT NULL REFERENCES patient(patient_id),
    diagnosis_id        UUID REFERENCES diagnosis(diagnosis_id),
    mdt_date            DATE NOT NULL,
    mdt_site            VARCHAR(50),
    mdt_type            VARCHAR(50),
    meeting_venue       VARCHAR(200),
    chair_code          VARCHAR(20),
    chair_name          VARCHAR(200),
    quorate             BOOLEAN DEFAULT true,
    clinical_summary    TEXT,
    staging_presented   VARCHAR(100),
    investigations_reviewed TEXT[],
    discussion_points   TEXT[],
    decision            TEXT,
    treatment_intent    VARCHAR(50),
    additional_actions  TEXT[],
    patient_informed_date DATE,
    patient_consent     VARCHAR(30),
    source_system       VARCHAR(50) DEFAULT 'INFOFLEX',
    source_message_id   VARCHAR(100),
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_mdt_patient ON mdt_discussion(patient_id);
CREATE INDEX idx_mdt_date ON mdt_discussion(mdt_date);
CREATE INDEX idx_mdt_site ON mdt_discussion(mdt_site);

-- ─── MDT attendees ─────────────────────────────────────────────────────────

CREATE TABLE mdt_attendee (
    attendee_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mdt_id              UUID NOT NULL REFERENCES mdt_discussion(mdt_id) ON DELETE CASCADE,
    role                VARCHAR(50),
    name                VARCHAR(200),
    gmc_code            VARCHAR(20),
    present             BOOLEAN DEFAULT true
);

CREATE INDEX idx_mdt_attendee_mdt ON mdt_attendee(mdt_id);

-- ─── Cancer actions (worklist) ─────────────────────────────────────────────

CREATE TABLE cancer_action (
    action_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          UUID NOT NULL REFERENCES patient(patient_id),
    pathway_id          UUID,
    action_type         VARCHAR(100) NOT NULL,
    action_description  TEXT,
    priority            VARCHAR(20) DEFAULT 'normal',
    status              VARCHAR(30) DEFAULT 'open',
    due_date            DATE,
    assigned_team       VARCHAR(100),
    assigned_user       VARCHAR(200),
    created_by          VARCHAR(200),
    completed_by        VARCHAR(200),
    completed_date      TIMESTAMPTZ,
    notes               TEXT,
    source_system       VARCHAR(50),
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_action_patient ON cancer_action(patient_id);
CREATE INDEX idx_action_status ON cancer_action(status);
CREATE INDEX idx_action_due ON cancer_action(due_date);
CREATE INDEX idx_action_team ON cancer_action(assigned_team);

-- ─── Derived: Cancer pathway ───────────────────────────────────────────────

CREATE TABLE cancer_pathway (
    pathway_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          UUID NOT NULL REFERENCES patient(patient_id),
    referral_id         UUID REFERENCES referral(referral_id),
    diagnosis_id        UUID REFERENCES diagnosis(diagnosis_id),
    staging_id          UUID REFERENCES staging(staging_id),
    cancer_type_code    VARCHAR(10),
    cancer_type_desc    VARCHAR(100),
    date_referral_received DATE,
    date_first_seen     DATE,
    date_diagnosis      DATE,
    date_mdt            DATE,
    date_decision_to_treat DATE,
    date_first_treatment DATE,
    days_to_first_seen  SMALLINT,
    days_to_diagnosis   SMALLINT,
    days_to_treatment   SMALLINT,
    fds_28day_met       BOOLEAN,
    standard_62day_met  BOOLEAN,
    standard_31day_met  BOOLEAN,
    treatment_modality  VARCHAR(100),
    first_treatment_type VARCHAR(50),
    pathway_status      VARCHAR(50) DEFAULT 'open',
    current_stage_label VARCHAR(200),
    next_action         TEXT,
    next_action_date    DATE,
    assigned_team       VARCHAR(100),
    assigned_user       VARCHAR(200),
    breach_risk         VARCHAR(20) DEFAULT 'none',
    clock_paused        BOOLEAN DEFAULT false,
    clock_pause_reason  TEXT,
    clock_pause_date    DATE,
    notes               TEXT,
    updated_at          TIMESTAMPTZ DEFAULT now(),
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_pathway_patient ON cancer_pathway(patient_id);
CREATE INDEX idx_pathway_status ON cancer_pathway(pathway_status);
CREATE INDEX idx_pathway_breach ON cancer_pathway(breach_risk);
CREATE INDEX idx_pathway_cancer_type ON cancer_pathway(cancer_type_code);
CREATE INDEX idx_pathway_team ON cancer_pathway(assigned_team);
CREATE INDEX idx_pathway_referral ON cancer_pathway(referral_id);

-- ─── Audit log ─────────────────────────────────────────────────────────────

CREATE TABLE integration_audit_log (
    log_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correlation_id      UUID NOT NULL,
    event_type          VARCHAR(50) NOT NULL,
    source_system       VARCHAR(50),
    message_type        VARCHAR(50),
    message_id          VARCHAR(100),
    entity_type         VARCHAR(50),
    entity_id           UUID,
    status              VARCHAR(20),
    error_message       TEXT,
    raw_payload_hash    VARCHAR(64),
    processing_time_ms  INTEGER,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_audit_correlation ON integration_audit_log(correlation_id);
CREATE INDEX idx_audit_created ON integration_audit_log(created_at);
CREATE INDEX idx_audit_source ON integration_audit_log(source_system);

-- ─── Dead letter queue ─────────────────────────────────────────────────────

CREATE TABLE dead_letter_queue (
    dlq_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correlation_id      UUID,
    source_system       VARCHAR(50),
    message_format      VARCHAR(20),
    raw_payload         TEXT,
    error_message       TEXT,
    error_detail        TEXT,
    retry_count         SMALLINT DEFAULT 0,
    max_retries         SMALLINT DEFAULT 3,
    status              VARCHAR(20) DEFAULT 'pending',
    created_at          TIMESTAMPTZ DEFAULT now(),
    processed_at        TIMESTAMPTZ
);

CREATE INDEX idx_dlq_status ON dead_letter_queue(status);

-- ─── Application users (for RBAC) ─────────────────────────────────────────

CREATE TABLE app_user (
    user_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username            VARCHAR(100) UNIQUE NOT NULL,
    password_hash       VARCHAR(200) NOT NULL,
    full_name           VARCHAR(200) NOT NULL,
    email               VARCHAR(200),
    role                VARCHAR(50) NOT NULL CHECK (role IN ('admin','clinician','cancer_nurse','mdt_coordinator','manager','readonly')),
    team                VARCHAR(100),
    active              BOOLEAN DEFAULT true,
    created_at          TIMESTAMPTZ DEFAULT now()
);

-- Seed default users
INSERT INTO app_user (username, password_hash, full_name, role, team) VALUES
('admin', '$2b$12$LJ3m4ys5O8JzK7K9V0hYjO0vE7U3W8N1D5s2T9R6Y4Q1P8M3K6J0G', 'System Admin', 'admin', NULL),
('s.jones', '$2b$12$LJ3m4ys5O8JzK7K9V0hYjO0vE7U3W8N1D5s2T9R6Y4Q1P8M3K6J0G', 'Ms Sarah Jones', 'clinician', 'Breast MDT'),
('a.patel', '$2b$12$LJ3m4ys5O8JzK7K9V0hYjO0vE7U3W8N1D5s2T9R6Y4Q1P8M3K6J0G', 'Dr Amit Patel', 'clinician', 'Colorectal MDT'),
('l.brown', '$2b$12$LJ3m4ys5O8JzK7K9V0hYjO0vE7U3W8N1D5s2T9R6Y4Q1P8M3K6J0G', 'Nurse Lisa Brown', 'cancer_nurse', 'Breast MDT'),
('j.smith', '$2b$12$LJ3m4ys5O8JzK7K9V0hYjO0vE7U3W8N1D5s2T9R6Y4Q1P8M3K6J0G', 'Jane Smith', 'mdt_coordinator', NULL);
