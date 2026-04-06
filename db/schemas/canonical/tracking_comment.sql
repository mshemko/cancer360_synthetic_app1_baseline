CREATE TABLE IF NOT EXISTS canonical.tracking_comment (
    cancer_tracking_comment_id VARCHAR PRIMARY KEY,
    cancer_pathway_id VARCHAR REFERENCES canonical.cancer_pathway(pathway_id),
    comment_title VARCHAR,
    comment_text VARCHAR,
    created_by VARCHAR,
    created_at_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    source_system_name VARCHAR,
    last_refreshed_at_source_timestamp TIMESTAMPTZ
);

COMMENT ON TABLE canonical.tracking_comment IS 'Canonical tracking comments attached to cancer pathways for operational and clinical follow-up.';
