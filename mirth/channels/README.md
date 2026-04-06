# Mirth Channel Assets

This folder contains:

- [channel_manifest.json](/c:/Users/MS234/Desktop/cancer360/mirth/channels/channel_manifest.json): channel inventory, connectors, routes, and destination intent
- one JavaScript transformer per channel under `transformers/`

Included transformer scripts:

- `PAS_ADT.js`
- `PAS_SIU.js`
- `ICE_ORU.js`
- `RIS_ORU.js`
- `ARIA_SIU.js`
- `SOMERSET_PATHWAYS.js`
- `SOMERSET_TRACKING.js`
- `SOMERSET_MDT.js`
- `SOMERSET_IPT.js`
- `ARIA_TREATMENT.js`
- `ENDOSCOPY.js`

These are not raw Mirth export XML files. They are build-ready assets intended to be pasted into Mirth channel transformers and connector settings.

The CSV-driven channels expect the global code templates from `mirth/code_templates/`, especially `csv_helpers.js`, and the SQL statement properties referenced as `sql.*.upsert`.
