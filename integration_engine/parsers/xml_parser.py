"""Parse Somerset XML payloads into flat dictionaries."""

from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from datetime import date, datetime
from pprint import pprint
import xml.etree.ElementTree as ET

from integration_engine import config


def parse_xml_date(date_str: str) -> date | None:
    if not date_str or date_str in {"None", "null"}:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def _text(element: ET.Element, tag: str) -> str:
    child = element.find(tag)
    return child.text.strip() if child is not None and child.text else ""


def _parse_pathway_element(pathway: ET.Element) -> dict:
    patient = pathway.find("Patient") or ET.Element("Patient")
    referral = pathway.find("ReferralDetails") or ET.Element("ReferralDetails")
    pathway_dates = pathway.find("PathwayDates") or ET.Element("PathwayDates")
    cancer = pathway.find("CancerDetails") or ET.Element("CancerDetails")
    hospital = pathway.find("HospitalSite") or ET.Element("HospitalSite")

    return {
        "pathway_id": _text(pathway, "PathwayID"),
        "person_id": _text(patient, "PersonID"),
        "nhs_number": _text(patient, "NHSNumber"),
        "mrn": _text(patient, "MRN"),
        "first_name": _text(patient, "FirstName"),
        "surname": _text(patient, "Surname"),
        "date_of_birth": _text(patient, "DateOfBirth"),
        "referral_received_date": _text(referral, "ReferralReceivedDate"),
        "referral_route": _text(referral, "ReferralRoute"),
        "referral_source": _text(referral, "ReferralSource"),
        "original_start_date": _text(pathway_dates, "OriginalStartDate"),
        "adjusted_start_date": _text(pathway_dates, "AdjustedStartDate"),
        "first_seen_date": _text(pathway_dates, "FirstSeenDate"),
        "diagnosis_date": _text(pathway_dates, "DiagnosisDate"),
        "decision_to_treat_date": _text(pathway_dates, "DecisionToTreatDate"),
        "first_treatment_date": _text(pathway_dates, "FirstTreatmentDate"),
        "closed_date": _text(pathway_dates, "ClosedDate"),
        "cancer_site": _text(cancer, "CancerSite"),
        "cancer_sub_site": _text(cancer, "CancerSubSite"),
        "diagnosis": _text(cancer, "Diagnosis"),
        "diagnosis_icd_10": _text(cancer, "DiagnosisICD10"),
        "is_benign": _text(cancer, "IsBenign"),
        "hospital_site_id": _text(hospital, "SiteID"),
        "hospital_site_name": _text(hospital, "SiteName"),
        "pathway_status": _text(pathway, "PathwayStatus"),
        "source_system": _text(pathway, "SourceSystem") or "Somerset",
        "last_refreshed": _text(pathway, "LastRefreshed"),
    }


def parse_somerset_xml(xml_text: str) -> dict:
    root = ET.fromstring(xml_text)
    if root.tag == "SomersetPathway":
        return _parse_pathway_element(root)
    if root.tag == "SomersetExport":
        first = root.find("SomersetPathway")
        if first is None:
            raise ValueError("SomersetExport contains no SomersetPathway elements")
        return _parse_pathway_element(first)
    raise ValueError(f"Unexpected XML root: {root.tag}")


def parse_xml_file(filepath: str) -> list[dict]:
    root = ET.parse(filepath).getroot()
    if root.tag == "SomersetPathway":
        return [_parse_pathway_element(root)]
    if root.tag == "SomersetExport":
        return [_parse_pathway_element(element) for element in root.findall("SomersetPathway")]
    raise ValueError(f"Unexpected XML root: {root.tag}")


def main() -> None:
    sample = next(
        (path for path in config.XML_DIR.glob("*.xml") if path.name != "all_pathways.xml"),
        None,
    )
    if not sample:
        print("No sample XML file found.")
        return

    parsed = parse_xml_file(str(sample))
    print(f"Sample file: {sample.name}")
    pprint(parsed[0])


if __name__ == "__main__":
    main()
