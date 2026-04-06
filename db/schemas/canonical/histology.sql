CREATE TABLE IF NOT EXISTS canonical.histology (
    histology_id VARCHAR PRIMARY KEY,
    person_id VARCHAR REFERENCES canonical.patient(person_id),
    histology_type VARCHAR,
    priority VARCHAR,
    histology_status VARCHAR,
    sample_taken_date DATE,
    received_at_lab_date DATE,
    sample_prepared_date DATE,
    report_prepared_date DATE,
    report_authorised_date DATE,
    is_reported BOOLEAN,
    histology_report_text VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    source_system_name VARCHAR,
    last_refreshed_at_source_timestamp TIMESTAMPTZ
);

COMMENT ON TABLE canonical.histology IS 'Canonical histology and cytology specimens, processing milestones, and authorised reports.';
