CREATE TABLE IF NOT EXISTS ref.cancer_site (
    cancer_site_id VARCHAR PRIMARY KEY,
    cancer_site VARCHAR NOT NULL,
    cancer_subsite TEXT[] NOT NULL
);

CREATE TABLE IF NOT EXISTS ref.hospital_site (
    hospital_site_id VARCHAR PRIMARY KEY,
    hospital_site VARCHAR NOT NULL
);
