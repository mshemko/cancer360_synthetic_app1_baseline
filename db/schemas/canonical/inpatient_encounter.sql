CREATE TABLE IF NOT EXISTS canonical.inpatient_encounter (
    encounter_id VARCHAR PRIMARY KEY,
    person_id VARCHAR REFERENCES canonical.patient(person_id),
    title VARCHAR,
    tci_status VARCHAR,
    surgical_order_date DATE,
    admission_offer_timestamp DATE,
    attendance_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    source_system_name VARCHAR,
    last_refreshed_at_source_timestamp TIMESTAMPTZ
);

COMMENT ON TABLE canonical.inpatient_encounter IS 'Canonical inpatient encounter and inpatient procedure milestones for Cancer 360.';
