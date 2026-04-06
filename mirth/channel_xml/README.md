# Mirth Channel XML Skeletons

This folder contains one XML scaffold per Cancer 360 Mirth channel.

These files are intentionally lightweight channel skeletons rather than raw Mirth export XML from a running Mirth instance. They are designed to help you build the channels consistently in Mirth Administrator by providing:

- channel metadata
- source connector settings
- routing and filtering rules
- transformer script references
- destination order and intent
- required code templates and SQL property keys

Files:

- `01_PAS_ADT.xml`
- `02_PAS_SIU.xml`
- `03_ICE_ORU.xml`
- `04_RIS_ORU.xml`
- `05_ARIA_SIU.xml`
- `06_SOMERSET_PATHWAYS.xml`
- `07_SOMERSET_TRACKING.xml`
- `08_SOMERSET_MDT.xml`
- `09_SOMERSET_IPT.xml`
- `10_ARIA_TREATMENT.xml`
- `11_ENDOSCOPY.xml`

Use these alongside:

- [../CHANNEL_BLUEPRINT.md](/c:/Users/MS234/Desktop/cancer360/mirth/CHANNEL_BLUEPRINT.md)
- [../code_templates/README.md](/c:/Users/MS234/Desktop/cancer360/mirth/code_templates/README.md)
- [../sql/README.md](/c:/Users/MS234/Desktop/cancer360/mirth/sql/README.md)
- [../channels/channel_manifest.json](/c:/Users/MS234/Desktop/cancer360/mirth/channels/channel_manifest.json)
