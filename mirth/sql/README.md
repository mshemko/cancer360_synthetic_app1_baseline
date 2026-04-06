# Mirth SQL Property Keys

The transformer scripts under `mirth/channels/transformers/` expect these SQL statements to be available through Mirth properties or maps using the exact keys below:

- `sql.patient.upsert`
- `sql.referral.upsert`
- `sql.diagnosis.upsert`
- `sql.staging.upsert`
- `sql.appointment.upsert`
- `sql.episode.upsert`
- `sql.pathology_result.upsert`
- `sql.pathology_result_value.upsert`
- `sql.histopath_structured.upsert`
- `sql.radiology_result.upsert`
- `sql.sact_course.upsert`
- `sql.sact_cycle.upsert`
- `sql.sact_drug.upsert`
- `sql.radiotherapy_course.upsert`
- `sql.radiotherapy_fraction.upsert`
- `sql.cancer_pathway.upsert`
- `sql.cancer_action.upsert`
- `sql.mdt_discussion.upsert`

Use [upserts.sql](/c:/Users/MS234/Desktop/cancer360/mirth/sql/upserts.sql) as the source for the statement bodies.
