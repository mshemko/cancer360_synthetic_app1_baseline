CREATE TABLE IF NOT EXISTS canonical.cancer_treatment (
    cancer_treatment_id VARCHAR PRIMARY KEY,
    person_id VARCHAR REFERENCES canonical.patient(person_id),
    treatment_type VARCHAR,
    treatment_description VARCHAR,
    treatment_status VARCHAR,
    attendance_date DATE,
    ordered_date DATE,
    scheduled_date DATE,
    poa_attendance_id VARCHAR REFERENCES canonical.outpatient_appointment(attendance_id),
    poa_booking_status VARCHAR,
    prescription_status VARCHAR,
    is_prescription_prepared BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    source_system_name VARCHAR,
    last_refreshed_at_source_timestamp TIMESTAMPTZ
);

COMMENT ON TABLE canonical.cancer_treatment IS 'Canonical cancer treatment activity spanning surgery, systemic anti-cancer therapy, radiotherapy, and other first-treatment events.';
