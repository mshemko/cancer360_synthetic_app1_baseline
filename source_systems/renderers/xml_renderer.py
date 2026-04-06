"""Render pathway journeys into Somerset-style XML exports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
JOURNEY_DIR = ROOT / "source_systems" / "output" / "journeys"
OUTPUT_DIR = ROOT / "source_systems" / "output" / "xml"

PATHWAYS_FILE = JOURNEY_DIR / "pathways.json"
PATIENTS_FILE = JOURNEY_DIR / "patients.json"
DIAGNOSES_FILE = JOURNEY_DIR / "diagnoses.json"


def load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def format_bool(value: Any) -> str:
    return "true" if bool(value) else "false"


def add_text(parent: ET.Element, tag: str, value: Any) -> ET.Element:
    child = ET.SubElement(parent, tag)
    child.text = "" if value is None else str(value)
    return child


def build_pathway_element(
    pathway: dict[str, Any],
    patient_lookup: dict[str, dict[str, Any]],
    diagnosis_lookup: dict[str, dict[str, Any]],
) -> ET.Element:
    patient = patient_lookup.get(pathway["person_id"], {})
    diagnosis = diagnosis_lookup.get(pathway["pathway_id"], {})

    root = ET.Element("SomersetPathway")
    add_text(root, "PathwayID", pathway.get("pathway_id"))

    patient_el = ET.SubElement(root, "Patient")
    add_text(patient_el, "PersonID", pathway.get("person_id"))
    add_text(patient_el, "NHSNumber", pathway.get("nhs_number"))
    add_text(patient_el, "MRN", pathway.get("mrn"))
    add_text(patient_el, "FirstName", pathway.get("first_name"))
    add_text(patient_el, "Surname", pathway.get("surname"))
    add_text(
        patient_el,
        "DateOfBirth",
        patient.get("date_of_birth") or pathway.get("date_of_birth"),
    )

    referral_el = ET.SubElement(root, "ReferralDetails")
    add_text(referral_el, "ReferralReceivedDate", pathway.get("referral_received_date"))
    add_text(referral_el, "ReferralRoute", pathway.get("pathway_referral_route"))
    add_text(referral_el, "ReferralSource", pathway.get("referral_source"))

    dates_el = ET.SubElement(root, "PathwayDates")
    add_text(dates_el, "OriginalStartDate", pathway.get("original_pathway_start_date"))
    add_text(dates_el, "AdjustedStartDate", pathway.get("adjusted_pathway_start_date"))
    add_text(dates_el, "FirstSeenDate", pathway.get("first_seen_date"))
    add_text(
        dates_el,
        "DiagnosisDate",
        diagnosis.get("diagnosis_date") or pathway.get("diagnosis_date"),
    )
    add_text(dates_el, "DecisionToTreatDate", pathway.get("decision_to_treat_date"))
    add_text(dates_el, "FirstTreatmentDate", pathway.get("first_treatment_date"))
    add_text(dates_el, "ClosedDate", pathway.get("pathway_closed_date"))

    cancer_el = ET.SubElement(root, "CancerDetails")
    add_text(cancer_el, "CancerSite", pathway.get("cancer_site"))
    add_text(cancer_el, "CancerSubSite", pathway.get("cancer_sub_site"))
    add_text(cancer_el, "Diagnosis", diagnosis.get("diagnosis") or pathway.get("diagnosis"))
    add_text(
        cancer_el,
        "DiagnosisICD10",
        diagnosis.get("diagnosis_icd_10_code") or pathway.get("diagnosis_icd_10_code"),
    )
    add_text(
        cancer_el,
        "IsBenign",
        format_bool(
            diagnosis.get("is_benign")
            if "is_benign" in diagnosis
            else pathway.get("is_benign")
        ),
    )

    hospital_el = ET.SubElement(root, "HospitalSite")
    add_text(hospital_el, "SiteID", pathway.get("hospital_site_id"))
    add_text(hospital_el, "SiteName", pathway.get("hospital_site"))

    add_text(root, "PathwayStatus", pathway.get("pathway_status"))
    add_text(root, "SourceSystem", pathway.get("source_system_name", "Somerset"))
    add_text(root, "LastRefreshed", pathway.get("last_refreshed_at_source_timestamp"))
    return root


def write_xml(path: Path, element: ET.Element) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(element)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def render_pathway_xml(
    journey_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, int]:
    journey_dir = journey_dir or JOURNEY_DIR
    output_dir = output_dir or OUTPUT_DIR

    pathways = load_json(journey_dir / "pathways.json")
    patients = {row["person_id"]: row for row in load_json(journey_dir / "patients.json")}
    diagnoses = {row["pathway_id"]: row for row in load_json(journey_dir / "diagnoses.json")}

    per_file_count = 0
    combined_root = ET.Element("SomersetExport")

    for pathway in pathways:
        element = build_pathway_element(pathway, patients, diagnoses)
        pathway_id = pathway["pathway_id"]
        write_xml(output_dir / f"somerset_pathway_{pathway_id}.xml", element)
        combined_root.append(build_pathway_element(pathway, patients, diagnoses))
        per_file_count += 1

    write_xml(output_dir / "all_pathways.xml", combined_root)
    return {
        "pathway_files": per_file_count,
        "combined_files": 1,
        "total_pathways": len(pathways),
    }


def main() -> None:
    summary = render_pathway_xml()
    print(
        f"Wrote {summary['pathway_files']} pathway XML files and {summary['combined_files']} combined file "
        f"to {OUTPUT_DIR} ({summary['total_pathways']} pathways)"
    )


if __name__ == "__main__":
    main()
