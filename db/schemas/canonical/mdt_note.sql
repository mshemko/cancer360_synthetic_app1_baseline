CREATE TABLE IF NOT EXISTS canonical.mdt_note (
    mdt_note_id VARCHAR PRIMARY KEY,
    cancer_pathway_id VARCHAR REFERENCES canonical.cancer_pathway(pathway_id),
    meeting_id VARCHAR REFERENCES canonical.mdt_meeting(mdt_meeting_id),
    note_type VARCHAR,
    mdt_note_text VARCHAR,
    last_updated_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    source_system_name VARCHAR,
    last_refreshed_at_source_timestamp TIMESTAMPTZ
);

COMMENT ON TABLE canonical.mdt_note IS 'Canonical MDT notes recorded against a patient pathway and MDT meeting.';
