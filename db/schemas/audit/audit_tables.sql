CREATE TABLE IF NOT EXISTS audit.load_log (
    id SERIAL PRIMARY KEY,
    source_system VARCHAR,
    source_file VARCHAR,
    table_target VARCHAR,
    rows_loaded INTEGER,
    rows_failed INTEGER,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    status VARCHAR,
    error_summary TEXT
);

CREATE TABLE IF NOT EXISTS audit.error_log (
    id SERIAL PRIMARY KEY,
    source_system VARCHAR,
    correlation_id VARCHAR,
    error_type VARCHAR,
    error_message TEXT,
    payload_snippet TEXT,
    occurred_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit.refresh_status (
    table_name VARCHAR PRIMARY KEY,
    last_refresh_at TIMESTAMPTZ,
    rows_in_last_refresh INTEGER,
    source_system VARCHAR,
    status VARCHAR
);
