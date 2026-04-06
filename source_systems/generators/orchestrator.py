"""Orchestrate end-to-end journey generation and source-format rendering."""

from __future__ import annotations

import json
import random
import shutil
from pathlib import Path
from typing import Any

import yaml

from source_systems.generators import (
    appointment_generator,
    comment_generator,
    diagnosis_generator,
    encounter_generator,
    endoscopy_generator,
    histology_generator,
    ipt_generator,
    mdt_generator,
    patient_generator,
    pathway_generator,
    radiology_generator,
    test_result_generator,
    treatment_generator,
)
from source_systems.renderers import (
    render_csv_outputs,
    render_hl7_messages,
    render_mdt_json,
    render_pathway_xml,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = ROOT / "config" / "generation_params.yaml"
DEFAULT_OUTPUT_ROOT = ROOT / "source_systems" / "output"


def load_config(config_path: Path) -> dict[str, Any]:
    return yaml.safe_load(config_path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def clean_output_root(output_root: Path) -> None:
    if output_root.exists():
        shutil.rmtree(output_root)


def merge_diagnoses_into_pathways(
    pathways: list[dict[str, Any]],
    diagnoses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    diagnosis_lookup = {row["pathway_id"]: row for row in diagnoses}
    merged: list[dict[str, Any]] = []
    for pathway in pathways:
        diagnosis = diagnosis_lookup.get(pathway["pathway_id"])
        if diagnosis:
            pathway = {
                **pathway,
                "diagnosis": diagnosis.get("diagnosis"),
                "diagnosis_icd_10_code": diagnosis.get("diagnosis_icd_10_code"),
                "diagnosis_date": diagnosis.get("diagnosis_date"),
                "is_benign": diagnosis.get("is_benign"),
                "staging_t": diagnosis.get("staging_t"),
                "staging_n": diagnosis.get("staging_n"),
                "staging_m": diagnosis.get("staging_m"),
                "overall_stage": diagnosis.get("overall_stage"),
            }
        merged.append(pathway)
    return merged


def run_generation_pipeline(
    config_path: Path | None = None,
    patients_override: int | None = None,
    output_root: Path | None = None,
    clean: bool = False,
    seed: int | None = None,
) -> dict[str, Any]:
    config_path = config_path or DEFAULT_CONFIG_PATH
    output_root = output_root or DEFAULT_OUTPUT_ROOT
    journey_dir = output_root / "journeys"

    if clean:
        clean_output_root(output_root)

    if seed is not None:
        random.seed(seed)

    config = load_config(config_path)
    if patients_override is not None:
        config["generation"]["patients"] = int(patients_override)

    journey_dir.mkdir(parents=True, exist_ok=True)

    patients = patient_generator.generate_patients(config)
    write_json(journey_dir / "patients.json", patients)

    pathways = pathway_generator.generate_pathways(patients, config)
    write_json(journey_dir / "pathways.json", pathways)

    diagnoses = diagnosis_generator.generate_diagnoses(pathways, config)
    write_json(journey_dir / "diagnoses.json", diagnoses)

    pathways = merge_diagnoses_into_pathways(pathways, diagnoses)
    write_json(journey_dir / "pathways.json", pathways)

    radiology = radiology_generator.generate_radiology(pathways, config)
    write_json(journey_dir / "radiology.json", radiology)

    histology = histology_generator.generate_histology(pathways, config)
    write_json(journey_dir / "histology.json", histology)

    test_results = test_result_generator.generate_test_results(pathways, config)
    write_json(journey_dir / "test_results.json", test_results)

    treatments = treatment_generator.generate_treatments(pathways, config)
    write_json(journey_dir / "treatments.json", treatments)

    mdt_meetings, mdt_bookings, mdt_notes = mdt_generator.generate_mdt_entities(pathways, config)
    write_json(journey_dir / "mdt_meetings.json", mdt_meetings)
    write_json(journey_dir / "mdt_bookings.json", mdt_bookings)
    write_json(journey_dir / "mdt_notes.json", mdt_notes)

    appointments = appointment_generator.generate_appointments(pathways, config)
    write_json(journey_dir / "appointments.json", appointments)
    link_summary = appointment_generator.link_attendance_ids(
        appointments,
        appointment_output_path=journey_dir / "appointments.json",
        test_results_file=journey_dir / "test_results.json",
        treatments_file=journey_dir / "treatments.json",
    )
    appointments = json.loads((journey_dir / "appointments.json").read_text(encoding="utf-8"))
    test_results = json.loads((journey_dir / "test_results.json").read_text(encoding="utf-8"))
    treatments = json.loads((journey_dir / "treatments.json").read_text(encoding="utf-8"))

    encounters = encounter_generator.generate_encounters(pathways, config)
    write_json(journey_dir / "encounters.json", encounters)

    endoscopy = endoscopy_generator.generate_endoscopy(pathways, config)
    write_json(journey_dir / "endoscopy.json", endoscopy)

    ipt = ipt_generator.generate_ipt(pathways, config)
    write_json(journey_dir / "ipt.json", ipt)

    comments = comment_generator.generate_comments(pathways, config)
    write_json(journey_dir / "tracking_comments.json", comments)

    hl7_summary = render_hl7_messages(journey_dir=journey_dir, output_dir=output_root / "hl7")
    csv_summary = render_csv_outputs(journey_dir=journey_dir, output_dir=output_root / "csv")
    xml_summary = render_pathway_xml(journey_dir=journey_dir, output_dir=output_root / "xml")
    json_summary = render_mdt_json(journey_dir=journey_dir, output_dir=output_root / "json")

    summary = {
        "patients_generated": len(patients),
        "pathways_generated": len(pathways),
        "diagnoses_generated": len(diagnoses),
        "radiology_exams": len(radiology),
        "histology_samples": len(histology),
        "test_results": len(test_results),
        "treatments": len(treatments),
        "mdt_meetings": len(mdt_meetings),
        "mdt_bookings": len(mdt_bookings),
        "mdt_notes": len(mdt_notes),
        "appointments": len(appointments),
        "encounters": len(encounters),
        "endoscopy_exams": len(endoscopy),
        "ipt_records": len(ipt),
        "tracking_comments": len(comments),
        "hl7_files_written": hl7_summary["message_files"] + hl7_summary["combined_files"],
        "csv_files_written": len(csv_summary),
        "xml_files_written": xml_summary["pathway_files"] + xml_summary["combined_files"],
        "json_files_written": json_summary["meeting_files"] + json_summary["combined_files"],
        "attendance_linking": link_summary,
        "output_root": str(output_root),
        "journey_dir": str(journey_dir),
    }
    return summary


def print_summary(summary: dict[str, Any]) -> None:
    print("Generation and rendering complete")
    print(f"Patients generated: {summary['patients_generated']}")
    print(f"Pathways generated: {summary['pathways_generated']}")
    print(f"Radiology exams: {summary['radiology_exams']}")
    print(f"Histology samples: {summary['histology_samples']}")
    print(f"Test results: {summary['test_results']}")
    print(f"Treatments: {summary['treatments']}")
    print(f"MDT meetings: {summary['mdt_meetings']}")
    print(f"MDT bookings: {summary['mdt_bookings']}")
    print(f"MDT notes: {summary['mdt_notes']}")
    print(f"Appointments: {summary['appointments']}")
    print(f"Encounters: {summary['encounters']}")
    print(f"Endoscopy exams: {summary['endoscopy_exams']}")
    print(f"IPT records: {summary['ipt_records']}")
    print(f"Tracking comments: {summary['tracking_comments']}")
    print(f"HL7 files written: {summary['hl7_files_written']}")
    print(f"CSV files written: {summary['csv_files_written']}")
    print(f"XML files written: {summary['xml_files_written']}")
    print(f"JSON files written: {summary['json_files_written']}")


def main() -> None:
    summary = run_generation_pipeline()
    print_summary(summary)


if __name__ == "__main__":
    main()
