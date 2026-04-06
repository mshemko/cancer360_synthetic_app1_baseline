CREATE TABLE IF NOT EXISTS canonical.mdt_meeting (
    mdt_meeting_id VARCHAR PRIMARY KEY,
    meeting_timestamp TIMESTAMPTZ,
    mdt_status VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    source_system_name VARCHAR,
    last_refreshed_at_source_timestamp TIMESTAMPTZ
);

COMMENT ON TABLE canonical.mdt_meeting IS 'Canonical multidisciplinary team meeting events.';
