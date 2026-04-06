CREATE TABLE IF NOT EXISTS canonical.radiology (
    radiology_exam_id VARCHAR PRIMARY KEY,
    person_id VARCHAR REFERENCES canonical.patient(person_id),
    radiology_exam_type VARCHAR,
    modality VARCHAR,
    radiology_priority VARCHAR,
    exam_status VARCHAR,
    ordered_date DATE,
    scheduled_date DATE,
    attendance_date DATE,
    report_authorised_date DATE,
    is_reported BOOLEAN,
    radiology_report_text VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    source_system_name VARCHAR,
    last_refreshed_at_source_timestamp TIMESTAMPTZ
);

COMMENT ON TABLE canonical.radiology IS 'Canonical radiology imaging exams, attendance, and reporting outcomes.';
