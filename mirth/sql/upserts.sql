-- PostgreSQL upsert templates for Mirth Connect
-- These statements align to the live schema in init.sql.

-- patient
INSERT INTO patient (
    patient_id, nhs_number, hospital_number, prefix, forename, surname,
    date_of_birth, sex, postcode, gp_practice_code, gp_name, phone
) VALUES (
    :patient_id, :nhs_number, :hospital_number, :prefix, :forename, :surname,
    :date_of_birth, :sex, :postcode, :gp_practice_code, :gp_name, :phone
)
ON CONFLICT (nhs_number) DO UPDATE SET
    hospital_number = EXCLUDED.hospital_number,
    prefix = EXCLUDED.prefix,
    forename = EXCLUDED.forename,
    surname = EXCLUDED.surname,
    date_of_birth = EXCLUDED.date_of_birth,
    sex = EXCLUDED.sex,
    postcode = EXCLUDED.postcode,
    gp_practice_code = EXCLUDED.gp_practice_code,
    gp_name = EXCLUDED.gp_name,
    phone = EXCLUDED.phone,
    updated_at = now();

-- referral
INSERT INTO referral (
    referral_id, patient_id, source_referral_id, referral_date, receipt_date,
    clock_start_date, referral_source, referral_priority, cancer_type_code,
    status, source_system
) VALUES (
    :referral_id, :patient_id, :source_referral_id, :referral_date, :receipt_date,
    :clock_start_date, :referral_source, :referral_priority, :cancer_type_code,
    :status, :source_system
)
ON CONFLICT (referral_id) DO UPDATE SET
    patient_id = EXCLUDED.patient_id,
    referral_date = EXCLUDED.referral_date,
    receipt_date = EXCLUDED.receipt_date,
    clock_start_date = EXCLUDED.clock_start_date,
    referral_source = EXCLUDED.referral_source,
    referral_priority = EXCLUDED.referral_priority,
    cancer_type_code = EXCLUDED.cancer_type_code,
    status = EXCLUDED.status,
    source_system = EXCLUDED.source_system,
    updated_at = now();

-- diagnosis
INSERT INTO diagnosis (
    diagnosis_id, patient_id, referral_id, diagnosis_date, icd10_code,
    icd10_description, morphology_code, laterality, basis_of_diagnosis, source_system
) VALUES (
    :diagnosis_id, :patient_id, :referral_id, :diagnosis_date, :icd10_code,
    :icd10_description, :morphology_code, :laterality, :basis_of_diagnosis, :source_system
)
ON CONFLICT (diagnosis_id) DO UPDATE SET
    patient_id = EXCLUDED.patient_id,
    referral_id = EXCLUDED.referral_id,
    diagnosis_date = EXCLUDED.diagnosis_date,
    icd10_code = EXCLUDED.icd10_code,
    icd10_description = EXCLUDED.icd10_description,
    morphology_code = EXCLUDED.morphology_code,
    laterality = EXCLUDED.laterality,
    basis_of_diagnosis = EXCLUDED.basis_of_diagnosis,
    source_system = EXCLUDED.source_system,
    updated_at = now();

-- staging
INSERT INTO staging (
    staging_id, patient_id, diagnosis_id, staging_date, staging_type,
    tnm_t, tnm_n, tnm_m, stage_group, grade, performance_status, source_system
) VALUES (
    :staging_id, :patient_id, :diagnosis_id, :staging_date, :staging_type,
    :tnm_t, :tnm_n, :tnm_m, :stage_group, :grade, :performance_status, :source_system
)
ON CONFLICT (staging_id) DO UPDATE SET
    patient_id = EXCLUDED.patient_id,
    diagnosis_id = EXCLUDED.diagnosis_id,
    staging_date = EXCLUDED.staging_date,
    staging_type = EXCLUDED.staging_type,
    tnm_t = EXCLUDED.tnm_t,
    tnm_n = EXCLUDED.tnm_n,
    tnm_m = EXCLUDED.tnm_m,
    stage_group = EXCLUDED.stage_group,
    grade = EXCLUDED.grade,
    performance_status = EXCLUDED.performance_status,
    source_system = EXCLUDED.source_system,
    updated_at = now();

-- appointment
INSERT INTO appointment (
    appointment_id, patient_id, referral_id, source_appt_id, appointment_date,
    appointment_time, clinic_code, clinic_name, appointment_type, attendance_status,
    outcome_code, consultant_name, location, source_system, source_message_id
) VALUES (
    :appointment_id, :patient_id, :referral_id, :source_appt_id, :appointment_date,
    :appointment_time, :clinic_code, :clinic_name, :appointment_type, :attendance_status,
    :outcome_code, :consultant_name, :location, :source_system, :source_message_id
)
ON CONFLICT (appointment_id) DO UPDATE SET
    patient_id = EXCLUDED.patient_id,
    referral_id = EXCLUDED.referral_id,
    source_appt_id = EXCLUDED.source_appt_id,
    appointment_date = EXCLUDED.appointment_date,
    appointment_time = EXCLUDED.appointment_time,
    clinic_code = EXCLUDED.clinic_code,
    clinic_name = EXCLUDED.clinic_name,
    appointment_type = EXCLUDED.appointment_type,
    attendance_status = EXCLUDED.attendance_status,
    outcome_code = EXCLUDED.outcome_code,
    consultant_name = EXCLUDED.consultant_name,
    location = EXCLUDED.location,
    source_system = EXCLUDED.source_system,
    source_message_id = EXCLUDED.source_message_id,
    updated_at = now();

-- episode
INSERT INTO episode (
    episode_id, patient_id, source_spell_id, source_episode_id, episode_type,
    admission_date, discharge_date, specialty_name, ward_name,
    primary_procedure, primary_procedure_desc, source_system, source_message_id
) VALUES (
    :episode_id, :patient_id, :source_spell_id, :source_episode_id, :episode_type,
    :admission_date, :discharge_date, :specialty_name, :ward_name,
    :primary_procedure, :primary_procedure_desc, :source_system, :source_message_id
)
ON CONFLICT (episode_id) DO UPDATE SET
    patient_id = EXCLUDED.patient_id,
    source_spell_id = EXCLUDED.source_spell_id,
    source_episode_id = EXCLUDED.source_episode_id,
    episode_type = EXCLUDED.episode_type,
    admission_date = EXCLUDED.admission_date,
    discharge_date = EXCLUDED.discharge_date,
    specialty_name = EXCLUDED.specialty_name,
    ward_name = EXCLUDED.ward_name,
    primary_procedure = EXCLUDED.primary_procedure,
    primary_procedure_desc = EXCLUDED.primary_procedure_desc,
    source_system = EXCLUDED.source_system,
    source_message_id = EXCLUDED.source_message_id,
    updated_at = now();

-- pathology_result
INSERT INTO pathology_result (
    result_id, patient_id, source_accession, order_id, order_date, specimen_date,
    report_date, discipline, test_code, test_name, status,
    requesting_clinician_name, narrative_report, source_system, source_message_id, raw_hl7
) VALUES (
    :result_id, :patient_id, :source_accession, :order_id, :order_date, :specimen_date,
    :report_date, :discipline, :test_code, :test_name, :status,
    :requesting_clinician_name, :narrative_report, :source_system, :source_message_id, :raw_hl7
)
ON CONFLICT (result_id) DO UPDATE SET
    patient_id = EXCLUDED.patient_id,
    source_accession = EXCLUDED.source_accession,
    order_id = EXCLUDED.order_id,
    order_date = EXCLUDED.order_date,
    specimen_date = EXCLUDED.specimen_date,
    report_date = EXCLUDED.report_date,
    discipline = EXCLUDED.discipline,
    test_code = EXCLUDED.test_code,
    test_name = EXCLUDED.test_name,
    status = EXCLUDED.status,
    requesting_clinician_name = EXCLUDED.requesting_clinician_name,
    narrative_report = EXCLUDED.narrative_report,
    source_system = EXCLUDED.source_system,
    source_message_id = EXCLUDED.source_message_id,
    raw_hl7 = EXCLUDED.raw_hl7,
    updated_at = now();

-- pathology_result_value
INSERT INTO pathology_result_value (
    value_id, result_id, sequence_number, test_code, test_name, value_type,
    numeric_value, text_value, coded_value, coded_display, unit,
    reference_range_text, abnormal_flag
) VALUES (
    :value_id, :result_id, :sequence_number, :test_code, :test_name, :value_type,
    :numeric_value, :text_value, :coded_value, :coded_display, :unit,
    :reference_range_text, :abnormal_flag
)
ON CONFLICT (value_id) DO UPDATE SET
    result_id = EXCLUDED.result_id,
    sequence_number = EXCLUDED.sequence_number,
    test_code = EXCLUDED.test_code,
    test_name = EXCLUDED.test_name,
    value_type = EXCLUDED.value_type,
    numeric_value = EXCLUDED.numeric_value,
    text_value = EXCLUDED.text_value,
    coded_value = EXCLUDED.coded_value,
    coded_display = EXCLUDED.coded_display,
    unit = EXCLUDED.unit,
    reference_range_text = EXCLUDED.reference_range_text,
    abnormal_flag = EXCLUDED.abnormal_flag;

-- histopath_structured
INSERT INTO histopath_structured (
    histopath_id, result_id, patient_id, tumour_type, grade,
    er_status, pr_status, her2_status, ki67_percent, lymphovascular_invasion
) VALUES (
    :histopath_id, :result_id, :patient_id, :tumour_type, :grade,
    :er_status, :pr_status, :her2_status, :ki67_percent, :lymphovascular_invasion
)
ON CONFLICT (histopath_id) DO UPDATE SET
    result_id = EXCLUDED.result_id,
    patient_id = EXCLUDED.patient_id,
    tumour_type = EXCLUDED.tumour_type,
    grade = EXCLUDED.grade,
    er_status = EXCLUDED.er_status,
    pr_status = EXCLUDED.pr_status,
    her2_status = EXCLUDED.her2_status,
    ki67_percent = EXCLUDED.ki67_percent,
    lymphovascular_invasion = EXCLUDED.lymphovascular_invasion;

-- radiology_result
INSERT INTO radiology_result (
    result_id, patient_id, accession_number, order_id, exam_date, report_date,
    modality, exam_code, exam_description, report_text, conclusion,
    requesting_clinician_name, status, source_system, source_message_id, raw_hl7
) VALUES (
    :result_id, :patient_id, :accession_number, :order_id, :exam_date, :report_date,
    :modality, :exam_code, :exam_description, :report_text, :conclusion,
    :requesting_clinician_name, :status, :source_system, :source_message_id, :raw_hl7
)
ON CONFLICT (result_id) DO UPDATE SET
    patient_id = EXCLUDED.patient_id,
    accession_number = EXCLUDED.accession_number,
    order_id = EXCLUDED.order_id,
    exam_date = EXCLUDED.exam_date,
    report_date = EXCLUDED.report_date,
    modality = EXCLUDED.modality,
    exam_code = EXCLUDED.exam_code,
    exam_description = EXCLUDED.exam_description,
    report_text = EXCLUDED.report_text,
    conclusion = EXCLUDED.conclusion,
    requesting_clinician_name = EXCLUDED.requesting_clinician_name,
    status = EXCLUDED.status,
    source_system = EXCLUDED.source_system,
    source_message_id = EXCLUDED.source_message_id,
    raw_hl7 = EXCLUDED.raw_hl7;

-- sact_course
INSERT INTO sact_course (
    course_id, patient_id, diagnosis_id, source_sact_id, regimen_name,
    regimen_code, regimen_intent, start_date, end_date, max_cycles,
    completed_cycles, course_status, discontinuation_reason,
    consultant_code, consultant_name, organisation_code, source_system
) VALUES (
    :course_id, :patient_id, :diagnosis_id, :source_sact_id, :regimen_name,
    :regimen_code, :regimen_intent, :start_date, :end_date, :max_cycles,
    :completed_cycles, :course_status, :discontinuation_reason,
    :consultant_code, :consultant_name, :organisation_code, :source_system
)
ON CONFLICT (course_id) DO UPDATE SET
    patient_id = EXCLUDED.patient_id,
    diagnosis_id = EXCLUDED.diagnosis_id,
    source_sact_id = EXCLUDED.source_sact_id,
    regimen_name = EXCLUDED.regimen_name,
    regimen_code = EXCLUDED.regimen_code,
    regimen_intent = EXCLUDED.regimen_intent,
    start_date = EXCLUDED.start_date,
    end_date = EXCLUDED.end_date,
    max_cycles = EXCLUDED.max_cycles,
    completed_cycles = EXCLUDED.completed_cycles,
    course_status = EXCLUDED.course_status,
    discontinuation_reason = EXCLUDED.discontinuation_reason,
    consultant_code = EXCLUDED.consultant_code,
    consultant_name = EXCLUDED.consultant_name,
    organisation_code = EXCLUDED.organisation_code,
    source_system = EXCLUDED.source_system,
    updated_at = now();

-- sact_cycle
INSERT INTO sact_cycle (
    cycle_id, course_id, patient_id, cycle_number, start_date,
    end_date, height_cm, weight_kg, bsa_m2, performance_status,
    cycle_outcome, delay_days, dose_reduction_pct, toxicity_grade,
    toxicity_type, source_system
) VALUES (
    :cycle_id, :course_id, :patient_id, :cycle_number, :start_date,
    :end_date, :height_cm, :weight_kg, :bsa_m2, :performance_status,
    :cycle_outcome, :delay_days, :dose_reduction_pct, :toxicity_grade,
    :toxicity_type, :source_system
)
ON CONFLICT (cycle_id) DO UPDATE SET
    course_id = EXCLUDED.course_id,
    patient_id = EXCLUDED.patient_id,
    cycle_number = EXCLUDED.cycle_number,
    start_date = EXCLUDED.start_date,
    end_date = EXCLUDED.end_date,
    height_cm = EXCLUDED.height_cm,
    weight_kg = EXCLUDED.weight_kg,
    bsa_m2 = EXCLUDED.bsa_m2,
    performance_status = EXCLUDED.performance_status,
    cycle_outcome = EXCLUDED.cycle_outcome,
    delay_days = EXCLUDED.delay_days,
    dose_reduction_pct = EXCLUDED.dose_reduction_pct,
    toxicity_grade = EXCLUDED.toxicity_grade,
    toxicity_type = EXCLUDED.toxicity_type,
    source_system = EXCLUDED.source_system;

-- sact_drug
INSERT INTO sact_drug (
    drug_id, cycle_id, drug_name, drug_code, dose_mg,
    dose_per_m2, dose_band, actual_dose_pct, route,
    administration_date, infusion_duration_mins
) VALUES (
    :drug_id, :cycle_id, :drug_name, :drug_code, :dose_mg,
    :dose_per_m2, :dose_band, :actual_dose_pct, :route,
    :administration_date, :infusion_duration_mins
)
ON CONFLICT (drug_id) DO UPDATE SET
    cycle_id = EXCLUDED.cycle_id,
    drug_name = EXCLUDED.drug_name,
    drug_code = EXCLUDED.drug_code,
    dose_mg = EXCLUDED.dose_mg,
    dose_per_m2 = EXCLUDED.dose_per_m2,
    dose_band = EXCLUDED.dose_band,
    actual_dose_pct = EXCLUDED.actual_dose_pct,
    route = EXCLUDED.route,
    administration_date = EXCLUDED.administration_date,
    infusion_duration_mins = EXCLUDED.infusion_duration_mins;

-- radiotherapy_course
INSERT INTO radiotherapy_course (
    course_id, patient_id, diagnosis_id, source_course_id, treatment_intent,
    treatment_site, technique, total_dose_gy, fractions_prescribed,
    dose_per_fraction_gy, first_fraction_date, last_fraction_date,
    planning_ct_date, plan_approved_date, plan_approved_by, machine_id,
    energy_mv, concurrent_sact, course_status, consultant_code,
    consultant_name, organisation_code, source_system
) VALUES (
    :course_id, :patient_id, :diagnosis_id, :source_course_id, :treatment_intent,
    :treatment_site, :technique, :total_dose_gy, :fractions_prescribed,
    :dose_per_fraction_gy, :first_fraction_date, :last_fraction_date,
    :planning_ct_date, :plan_approved_date, :plan_approved_by, :machine_id,
    :energy_mv, :concurrent_sact, :course_status, :consultant_code,
    :consultant_name, :organisation_code, :source_system
)
ON CONFLICT (course_id) DO UPDATE SET
    patient_id = EXCLUDED.patient_id,
    diagnosis_id = EXCLUDED.diagnosis_id,
    source_course_id = EXCLUDED.source_course_id,
    treatment_intent = EXCLUDED.treatment_intent,
    treatment_site = EXCLUDED.treatment_site,
    technique = EXCLUDED.technique,
    total_dose_gy = EXCLUDED.total_dose_gy,
    fractions_prescribed = EXCLUDED.fractions_prescribed,
    dose_per_fraction_gy = EXCLUDED.dose_per_fraction_gy,
    first_fraction_date = EXCLUDED.first_fraction_date,
    last_fraction_date = EXCLUDED.last_fraction_date,
    planning_ct_date = EXCLUDED.planning_ct_date,
    plan_approved_date = EXCLUDED.plan_approved_date,
    plan_approved_by = EXCLUDED.plan_approved_by,
    machine_id = EXCLUDED.machine_id,
    energy_mv = EXCLUDED.energy_mv,
    concurrent_sact = EXCLUDED.concurrent_sact,
    course_status = EXCLUDED.course_status,
    consultant_code = EXCLUDED.consultant_code,
    consultant_name = EXCLUDED.consultant_name,
    organisation_code = EXCLUDED.organisation_code,
    source_system = EXCLUDED.source_system,
    updated_at = now();

-- radiotherapy_fraction
INSERT INTO radiotherapy_fraction (
    fraction_id, course_id, fraction_number, scheduled_date, delivered_date,
    delivered_time, dose_gy, status, machine_id, notes
) VALUES (
    :fraction_id, :course_id, :fraction_number, :scheduled_date, :delivered_date,
    :delivered_time, :dose_gy, :status, :machine_id, :notes
)
ON CONFLICT (fraction_id) DO UPDATE SET
    course_id = EXCLUDED.course_id,
    fraction_number = EXCLUDED.fraction_number,
    scheduled_date = EXCLUDED.scheduled_date,
    delivered_date = EXCLUDED.delivered_date,
    delivered_time = EXCLUDED.delivered_time,
    dose_gy = EXCLUDED.dose_gy,
    status = EXCLUDED.status,
    machine_id = EXCLUDED.machine_id,
    notes = EXCLUDED.notes;

-- cancer_pathway
INSERT INTO cancer_pathway (
    pathway_id, patient_id, referral_id, diagnosis_id, staging_id,
    cancer_type_code, cancer_type_desc, date_referral_received, date_first_seen,
    date_diagnosis, date_mdt, date_decision_to_treat, date_first_treatment,
    days_to_first_seen, days_to_diagnosis, days_to_treatment,
    fds_28day_met, standard_62day_met, standard_31day_met,
    treatment_modality, first_treatment_type, pathway_status,
    current_stage_label, next_action, next_action_date,
    assigned_team, assigned_user, breach_risk, notes
) VALUES (
    :pathway_id, :patient_id, :referral_id, :diagnosis_id, :staging_id,
    :cancer_type_code, :cancer_type_desc, :date_referral_received, :date_first_seen,
    :date_diagnosis, :date_mdt, :date_decision_to_treat, :date_first_treatment,
    :days_to_first_seen, :days_to_diagnosis, :days_to_treatment,
    :fds_28day_met, :standard_62day_met, :standard_31day_met,
    :treatment_modality, :first_treatment_type, :pathway_status,
    :current_stage_label, :next_action, :next_action_date,
    :assigned_team, :assigned_user, :breach_risk, :notes
)
ON CONFLICT (pathway_id) DO UPDATE SET
    patient_id = EXCLUDED.patient_id,
    referral_id = EXCLUDED.referral_id,
    diagnosis_id = EXCLUDED.diagnosis_id,
    staging_id = EXCLUDED.staging_id,
    cancer_type_code = EXCLUDED.cancer_type_code,
    cancer_type_desc = EXCLUDED.cancer_type_desc,
    date_referral_received = EXCLUDED.date_referral_received,
    date_first_seen = EXCLUDED.date_first_seen,
    date_diagnosis = EXCLUDED.date_diagnosis,
    date_mdt = EXCLUDED.date_mdt,
    date_decision_to_treat = EXCLUDED.date_decision_to_treat,
    date_first_treatment = EXCLUDED.date_first_treatment,
    days_to_first_seen = EXCLUDED.days_to_first_seen,
    days_to_diagnosis = EXCLUDED.days_to_diagnosis,
    days_to_treatment = EXCLUDED.days_to_treatment,
    fds_28day_met = EXCLUDED.fds_28day_met,
    standard_62day_met = EXCLUDED.standard_62day_met,
    standard_31day_met = EXCLUDED.standard_31day_met,
    treatment_modality = EXCLUDED.treatment_modality,
    first_treatment_type = EXCLUDED.first_treatment_type,
    pathway_status = EXCLUDED.pathway_status,
    current_stage_label = EXCLUDED.current_stage_label,
    next_action = EXCLUDED.next_action,
    next_action_date = EXCLUDED.next_action_date,
    assigned_team = EXCLUDED.assigned_team,
    assigned_user = EXCLUDED.assigned_user,
    breach_risk = EXCLUDED.breach_risk,
    notes = EXCLUDED.notes,
    updated_at = now();

-- cancer_action
INSERT INTO cancer_action (
    action_id, patient_id, pathway_id, action_type, action_description,
    priority, status, due_date, assigned_team, assigned_user,
    created_by, notes, source_system
) VALUES (
    :action_id, :patient_id, :pathway_id, :action_type, :action_description,
    :priority, :status, :due_date, :assigned_team, :assigned_user,
    :created_by, :notes, :source_system
)
ON CONFLICT (action_id) DO UPDATE SET
    patient_id = EXCLUDED.patient_id,
    pathway_id = EXCLUDED.pathway_id,
    action_type = EXCLUDED.action_type,
    action_description = EXCLUDED.action_description,
    priority = EXCLUDED.priority,
    status = EXCLUDED.status,
    due_date = EXCLUDED.due_date,
    assigned_team = EXCLUDED.assigned_team,
    assigned_user = EXCLUDED.assigned_user,
    created_by = EXCLUDED.created_by,
    notes = EXCLUDED.notes,
    source_system = EXCLUDED.source_system,
    updated_at = now();

-- mdt_discussion
INSERT INTO mdt_discussion (
    mdt_id, patient_id, diagnosis_id, mdt_date, mdt_site,
    mdt_type, quorate, clinical_summary, staging_presented,
    decision, treatment_intent, source_system, source_message_id
) VALUES (
    :mdt_id, :patient_id, :diagnosis_id, :mdt_date, :mdt_site,
    :mdt_type, :quorate, :clinical_summary, :staging_presented,
    :decision, :treatment_intent, :source_system, :source_message_id
)
ON CONFLICT (mdt_id) DO UPDATE SET
    patient_id = EXCLUDED.patient_id,
    diagnosis_id = EXCLUDED.diagnosis_id,
    mdt_date = EXCLUDED.mdt_date,
    mdt_site = EXCLUDED.mdt_site,
    mdt_type = EXCLUDED.mdt_type,
    quorate = EXCLUDED.quorate,
    clinical_summary = EXCLUDED.clinical_summary,
    staging_presented = EXCLUDED.staging_presented,
    decision = EXCLUDED.decision,
    treatment_intent = EXCLUDED.treatment_intent,
    source_system = EXCLUDED.source_system,
    source_message_id = EXCLUDED.source_message_id,
    updated_at = now();

-- integration_audit_log
INSERT INTO integration_audit_log (
    log_id, correlation_id, event_type, source_system, message_type,
    message_id, entity_type, entity_id, status, error_message,
    raw_payload_hash, processing_time_ms
) VALUES (
    :log_id, :correlation_id, :event_type, :source_system, :message_type,
    :message_id, :entity_type, :entity_id, :status, :error_message,
    :raw_payload_hash, :processing_time_ms
);

-- dead_letter_queue
INSERT INTO dead_letter_queue (
    dlq_id, correlation_id, source_system, message_format,
    raw_payload, error_message, error_detail, status
) VALUES (
    :dlq_id, :correlation_id, :source_system, :message_format,
    :raw_payload, :error_message, :error_detail, :status
);
