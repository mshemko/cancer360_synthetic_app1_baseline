INSERT INTO ref.cancer_site (cancer_site_id, cancer_site, cancer_subsite) VALUES
    ('BREAST', 'Breast', ARRAY['Breast']),
    ('LUNG', 'Lung', ARRAY['Lung']),
    ('COLORECTAL', 'Colorectal', ARRAY['Colon', 'Rectum', 'Colorectal NOS']),
    ('PROSTATE', 'Prostate', ARRAY['Prostate']),
    ('HEAD_NECK', 'Head & Neck', ARRAY['Larynx', 'Oral Cavity', 'Oropharynx', 'Thyroid', 'Salivary Gland']),
    ('UPPER_GI', 'Upper GI', ARRAY['Oesophagus', 'Stomach', 'Hepatobiliary', 'Pancreas']),
    ('HAEMATOLOGY', 'Haematology', ARRAY['Lymphoma', 'Leukaemia', 'Myeloma']),
    ('GYNAECOLOGY', 'Gynaecology', ARRAY['Ovary', 'Cervix', 'Endometrial', 'Vulva']),
    ('SKIN', 'Skin', ARRAY['Melanoma', 'Non-Melanoma']),
    ('UROLOGY', 'Urology', ARRAY['Bladder', 'Renal', 'Testicular']),
    ('BRAIN_CNS', 'Brain/CNS', ARRAY['Brain', 'CNS']),
    ('SARCOMA', 'Sarcoma', ARRAY['Bone Sarcoma', 'Soft Tissue Sarcoma'])
ON CONFLICT DO NOTHING;

INSERT INTO ref.hospital_site (hospital_site_id, hospital_site) VALUES
    ('NNUH', 'NNUH — Norfolk and Norwich University Hospital'),
    ('JPH', 'JPH — James Paget Hospital'),
    ('QEH', 'QEH — Queen Elizabeth Hospital King''s Lynn')
ON CONFLICT DO NOTHING;
