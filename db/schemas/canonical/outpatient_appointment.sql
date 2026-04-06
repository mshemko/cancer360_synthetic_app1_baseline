CREATE TABLE IF NOT EXISTS canonical.outpatient_appointment (
    attendance_id VARCHAR PRIMARY KEY,
    person_id VARCHAR REFERENCES canonical.patient(person_id),
    type VARCHAR,
    booking_status VARCHAR,
    start_date_time DATE,
    ordered_date DATE,
    date_time_booked DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    source_system_name VARCHAR,
    last_refreshed_at_source_timestamp TIMESTAMPTZ
);

COMMENT ON TABLE canonical.outpatient_appointment IS 'Canonical outpatient appointment records for first and follow-up outpatient activity.';
