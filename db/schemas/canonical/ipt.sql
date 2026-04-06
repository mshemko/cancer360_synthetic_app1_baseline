CREATE TABLE IF NOT EXISTS canonical.ipt (
    tertiary_id VARCHAR PRIMARY KEY,
    pathway_id VARCHAR REFERENCES canonical.cancer_pathway(pathway_id),
    person_id VARCHAR REFERENCES canonical.patient(person_id),
    nhs_number VARCHAR,
    mrn VARCHAR,
    tertiary_referral_type VARCHAR,
    tertiary_reason VARCHAR,
    tertiary_reason_code VARCHAR,
    sending_org_id VARCHAR,
    sending_org_name VARCHAR,
    receiving_org_id VARCHAR,
    receiving_org_name VARCHAR,
    tertiary_sent_date DATE,
    tertiary_received_date DATE,
    tertiary_returned_date DATE,
    tertiary_sending_comment VARCHAR,
    tertiary_return_comment VARCHAR,
    is_sent BOOLEAN,
    is_received BOOLEAN,
    is_returned BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    source_system_name VARCHAR,
    last_refreshed_at_source_timestamp TIMESTAMPTZ
);

COMMENT ON TABLE canonical.ipt IS 'Canonical inter-provider transfer events associated with a patient and pathway.';
