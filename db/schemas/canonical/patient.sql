CREATE TABLE IF NOT EXISTS canonical.patient (
    person_id VARCHAR PRIMARY KEY,
    mrn VARCHAR,
    nhs_number VARCHAR,
    first_name VARCHAR,
    surname VARCHAR,
    title VARCHAR,
    date_of_birth DATE,
    date_of_death DATE,
    sex VARCHAR,
    gender_identity VARCHAR,
    address_line_1 VARCHAR,
    address_line_2 VARCHAR,
    postcode VARCHAR,
    phone_number VARCHAR,
    registered_gp VARCHAR,
    next_of_kin_name VARCHAR,
    next_of_kin_number VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    source_system_name VARCHAR,
    last_refreshed_at_source_timestamp TIMESTAMPTZ
);

COMMENT ON TABLE canonical.patient IS 'Canonical patient demographics and identity record aligned to the NNUH Cancer Product Data Specification v5.';
