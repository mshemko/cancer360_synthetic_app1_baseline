CREATE TABLE IF NOT EXISTS canonical.endoscopy (
    endoscopy_id VARCHAR PRIMARY KEY,
    person_id VARCHAR REFERENCES canonical.patient(person_id),
    endoscopy_type VARCHAR,
    modality VARCHAR,
    endoscopy_priority VARCHAR,
    exam_status VARCHAR,
    ordered_date DATE,
    scheduled_date DATE,
    attendance_date DATE,
    report_prepared_date DATE,
    report_authorised_date DATE,
    is_reported BOOLEAN,
    endoscopy_report_text VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    source_system_name VARCHAR,
    last_refreshed_at_source_timestamp TIMESTAMPTZ
);

COMMENT ON TABLE canonical.endoscopy IS 'Canonical endoscopy events including booking, attendance, and reporting status.';
