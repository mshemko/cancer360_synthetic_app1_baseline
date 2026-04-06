# Mirth Connect Implementation Pack

This folder contains the production-style replacement plan for the Python `tie` layer using Mirth Connect as the integration engine.

Files:

- [CHANNEL_BLUEPRINT.md](/c:/Users/MS234/Desktop/cancer360/mirth/CHANNEL_BLUEPRINT.md): channel-by-channel design, connectors, routing, transformer logic, and operational guidance
- [sql/upserts.sql](/c:/Users/MS234/Desktop/cancer360/mirth/sql/upserts.sql): PostgreSQL upsert templates aligned to the live Cancer 360 schema in `init.sql`
- [sql/README.md](/c:/Users/MS234/Desktop/cancer360/mirth/sql/README.md): expected `sql.*.upsert` property names used by the transformer scripts
- [code_templates/README.md](/c:/Users/MS234/Desktop/cancer360/mirth/code_templates/README.md): global code-template library to load into Mirth
- [channels/channel_manifest.json](/c:/Users/MS234/Desktop/cancer360/mirth/channels/channel_manifest.json): channel inventory with connector type, routing hints, and target tables
- [channels/README.md](/c:/Users/MS234/Desktop/cancer360/mirth/channels/README.md): transformer script inventory and usage notes
- [channel_xml/README.md](/c:/Users/MS234/Desktop/cancer360/mirth/channel_xml/README.md): one XML skeleton per channel for Mirth Administrator build-out
- [DEPLOYMENT_CHECKLIST.md](/c:/Users/MS234/Desktop/cancer360/mirth/DEPLOYMENT_CHECKLIST.md): Windows-oriented deployment and validation checklist

This design assumes:

- source simulators in [source_systems](/c:/Users/MS234/Desktop/cancer360/source_systems) remain in place
- Mirth replaces the Python `tie` package
- PostgreSQL remains the canonical store
- the FastAPI backend in [backend](/c:/Users/MS234/Desktop/cancer360/backend) remains unchanged
