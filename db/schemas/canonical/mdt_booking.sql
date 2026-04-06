CREATE TABLE IF NOT EXISTS canonical.mdt_booking (
    meeting_id VARCHAR REFERENCES canonical.mdt_meeting(mdt_meeting_id),
    pathway_id VARCHAR REFERENCES canonical.cancer_pathway(pathway_id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    source_system_name VARCHAR,
    last_refreshed_at_source_timestamp TIMESTAMPTZ,
    PRIMARY KEY (meeting_id, pathway_id)
);

COMMENT ON TABLE canonical.mdt_booking IS 'Canonical link table joining cancer pathways to MDT meetings they were booked into.';
