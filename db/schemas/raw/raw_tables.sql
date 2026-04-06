CREATE TABLE IF NOT EXISTS raw.hl7_message (
    id SERIAL PRIMARY KEY,
    source_system VARCHAR,
    message_type VARCHAR,
    payload_text TEXT,
    file_name VARCHAR,
    received_at TIMESTAMPTZ DEFAULT NOW(),
    correlation_id VARCHAR,
    processing_status VARCHAR DEFAULT 'received',
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS raw.csv_extract (
    id SERIAL PRIMARY KEY,
    source_system VARCHAR,
    message_type VARCHAR,
    payload_text TEXT,
    file_name VARCHAR,
    received_at TIMESTAMPTZ DEFAULT NOW(),
    correlation_id VARCHAR,
    processing_status VARCHAR DEFAULT 'received',
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS raw.xml_payload (
    id SERIAL PRIMARY KEY,
    source_system VARCHAR,
    message_type VARCHAR,
    payload_text TEXT,
    file_name VARCHAR,
    received_at TIMESTAMPTZ DEFAULT NOW(),
    correlation_id VARCHAR,
    processing_status VARCHAR DEFAULT 'received',
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS raw.json_payload (
    id SERIAL PRIMARY KEY,
    source_system VARCHAR,
    message_type VARCHAR,
    payload_text TEXT,
    file_name VARCHAR,
    received_at TIMESTAMPTZ DEFAULT NOW(),
    correlation_id VARCHAR,
    processing_status VARCHAR DEFAULT 'received',
    error_message TEXT
);
