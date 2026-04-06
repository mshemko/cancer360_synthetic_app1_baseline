CREATE TABLE IF NOT EXISTS canonical.test_result (
    test_result_id VARCHAR PRIMARY KEY,
    person_id VARCHAR REFERENCES canonical.patient(person_id),
    attendance_id VARCHAR REFERENCES canonical.outpatient_appointment(attendance_id),
    test_name VARCHAR,
    test_id_code VARCHAR,
    test_date_time TIMESTAMPTZ,
    test_ordered_timestamp TIMESTAMPTZ,
    value VARCHAR,
    value_double DOUBLE PRECISION,
    test_value_type VARCHAR,
    unit VARCHAR,
    ordering_specialty_name VARCHAR,
    expiry_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    source_system_name VARCHAR,
    last_refreshed_at_source_timestamp TIMESTAMPTZ
);

COMMENT ON TABLE canonical.test_result IS 'Canonical laboratory and pathology-linked test result observations.';
