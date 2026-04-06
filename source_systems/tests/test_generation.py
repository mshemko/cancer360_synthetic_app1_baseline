"""End-to-end validation for synthetic generation and render pipeline."""

from __future__ import annotations

import json
import shutil
import unittest
import xml.etree.ElementTree as ET
import csv
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from source_systems.generators.orchestrator import run_generation_pipeline


ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUT = ROOT / "source_systems" / "output_test"
JOURNEY_DIR = TEST_OUTPUT / "journeys"


class GenerationPipelineTest(unittest.TestCase):
    summary: dict
    results_log: list[tuple[str, bool]]

    @classmethod
    def setUpClass(cls) -> None:
        if TEST_OUTPUT.exists():
            shutil.rmtree(TEST_OUTPUT)
        cls.results_log = []
        cls.summary = run_generation_pipeline(
            patients_override=50,
            output_root=TEST_OUTPUT,
            clean=True,
            seed=42,
        )
        cls.patients = cls._load("patients.json")
        cls.pathways = cls._load("pathways.json")
        cls.radiology = cls._load("radiology.json")
        cls.histology = cls._load("histology.json")
        cls.test_results = cls._load("test_results.json")
        cls.treatments = cls._load("treatments.json")
        cls.mdt_meetings = cls._load("mdt_meetings.json")
        cls.mdt_bookings = cls._load("mdt_bookings.json")
        cls.mdt_notes = cls._load("mdt_notes.json")
        cls.appointments = cls._load("appointments.json")
        cls.encounters = cls._load("encounters.json")
        cls.endoscopy = cls._load("endoscopy.json")
        cls.ipt = cls._load("ipt.json")
        cls.comments = cls._load("tracking_comments.json")

    @classmethod
    def tearDownClass(cls) -> None:
        print("\nValidation summary")
        for name, ok in cls.results_log:
            print(f"{'PASS' if ok else 'FAIL'} - {name}")
        passed = sum(1 for _, ok in cls.results_log if ok)
        total = len(cls.results_log)
        print(f"Overall: {passed}/{total} checks passed")

    @classmethod
    def _load(cls, file_name: str):
        return json.loads((JOURNEY_DIR / file_name).read_text(encoding="utf-8"))

    def check(self, name: str, condition: bool, detail: str | None = None) -> None:
        self.results_log.append((name, condition))
        print(f"{'PASS' if condition else 'FAIL'} - {name}")
        if not condition and detail:
            print(detail)
        self.assertTrue(condition, detail or name)

    def test_01_expected_journey_files_exist(self) -> None:
        expected = [
            "patients.json",
            "pathways.json",
            "diagnoses.json",
            "radiology.json",
            "histology.json",
            "test_results.json",
            "treatments.json",
            "mdt_meetings.json",
            "mdt_bookings.json",
            "mdt_notes.json",
            "appointments.json",
            "encounters.json",
            "endoscopy.json",
            "ipt.json",
            "tracking_comments.json",
        ]
        ok = all((JOURNEY_DIR / name).exists() and (JOURNEY_DIR / name).stat().st_size > 0 for name in expected)
        self.check("All expected journey JSON files exist and are non-empty", ok)

    def test_02_format_dirs_have_files(self) -> None:
        dirs = ["hl7", "csv", "xml", "json"]
        ok = all((TEST_OUTPUT / name).exists() and any((TEST_OUTPUT / name).iterdir()) for name in dirs)
        self.check("All expected output format directories have files", ok)

    def test_03_patient_count_matches(self) -> None:
        self.check("Patient count matches config override", len(self.patients) == 50, f"Found {len(self.patients)} patients")

    def test_04_relationship_validations(self) -> None:
        patient_ids = {row["person_id"] for row in self.patients}
        pathway_ids = {row["pathway_id"] for row in self.pathways}
        meeting_ids = {row["mdt_meeting_id"] for row in self.mdt_meetings}

        self.check("Every pathway has a valid person_id that exists in patients", all(row["person_id"] in patient_ids for row in self.pathways))
        self.check("Every radiology exam has a valid patient_id in patients", all(row["patient_id"] in patient_ids for row in self.radiology))
        self.check("Every histology sample has a valid person_id in patients", all(row["person_id"] in patient_ids for row in self.histology))
        self.check("Every test result has a valid person_id in patients", all(row["person_id"] in patient_ids for row in self.test_results))
        self.check("Every treatment has a valid person_id in patients", all(row["person_id"] in patient_ids for row in self.treatments))
        self.check(
            "Every MDT booking has a valid meeting_id and pathway_id",
            all(row["meeting_id"] in meeting_ids and row["pathway_id"] in pathway_ids for row in self.mdt_bookings),
        )
        self.check(
            "Every MDT note has a valid meeting_id and pathway_id",
            all(row["meeting_id"] in meeting_ids and row["cancer_pathway_id"] in pathway_ids for row in self.mdt_notes),
        )
        self.check("Every appointment has a valid person_id in patients", all(row["person_id"] in patient_ids for row in self.appointments))
        self.check("Every encounter has a valid person_id in patients", all(row["person_id"] in patient_ids for row in self.encounters))
        self.check("Every endoscopy has a valid person_id in patients", all(row["person_id"] in patient_ids for row in self.endoscopy))
        self.check(
            "Every IPT has a valid pathway_id and person_id",
            all(row["pathway_id"] in pathway_ids and row["person_id"] in patient_ids for row in self.ipt),
        )
        self.check(
            "Every tracking comment has a valid cancer_pathway_id",
            all(row["cancer_pathway_id"] in pathway_ids for row in self.comments),
        )

    def test_05_date_coherence_sample(self) -> None:
        sample = self.pathways[:10]

        def coherent(pathway: dict) -> bool:
            dates = [
                pathway["timeline_skeleton"]["key_dates"].get("referral"),
                pathway["timeline_skeleton"]["key_dates"].get("first_seen"),
                pathway["timeline_skeleton"]["key_dates"].get("diagnosis"),
                pathway["timeline_skeleton"]["key_dates"].get("dtt"),
                pathway["timeline_skeleton"]["key_dates"].get("first_treatment"),
            ]
            filtered = [value for value in dates if value]
            return filtered == sorted(filtered)

        self.check("Date coherence for sample pathways", all(coherent(pathway) for pathway in sample))

    def test_06_hl7_files_valid(self) -> None:
        hl7_files = [path for path in (TEST_OUTPUT / "hl7").glob("*.hl7") if path.name != "all_messages.hl7"]
        ok = all(path.read_text(encoding="utf-8").startswith("MSH|") for path in hl7_files[:10])
        self.check("HL7 files contain valid MSH segments", ok)

    def test_07_csv_headers_and_columns(self) -> None:
        csv_dir = TEST_OUTPUT / "csv"
        ok = True
        for path in csv_dir.glob("*.csv"):
            with path.open("r", encoding="utf-8", newline="") as handle:
                reader = list(csv.reader(handle))
            if len(reader) < 2 or len(reader[0]) != len(reader[1]):
                ok = False
                break
        self.check("CSV files have header rows and correct column counts", ok)

    def test_08_xml_valid(self) -> None:
        xml_files = list((TEST_OUTPUT / "xml").glob("*.xml"))
        ok = True
        for path in xml_files[:10]:
            try:
                ET.parse(path)
            except ET.ParseError:
                ok = False
                break
        self.check("XML files are valid XML", ok)

    def test_09_json_outputs_valid(self) -> None:
        json_files = list((TEST_OUTPUT / "json").glob("*.json"))
        ok = True
        for path in json_files[:10]:
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                ok = False
                break
        self.check("JSON output files are valid JSON", ok)


if __name__ == "__main__":
    unittest.main(verbosity=2)
