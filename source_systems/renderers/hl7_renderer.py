"""Render radiology, histology, and test results into HL7 ORU^R01 messages."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
JOURNEY_DIR = ROOT / "source_systems" / "output" / "journeys"
OUTPUT_DIR = ROOT / "source_systems" / "output" / "hl7"

PATIENTS_FILE = JOURNEY_DIR / "patients.json"
RADIOLOGY_FILE = JOURNEY_DIR / "radiology.json"
HISTOLOGY_FILE = JOURNEY_DIR / "histology.json"
TEST_RESULTS_FILE = JOURNEY_DIR / "test_results.json"

ATTENDING_DOCTORS = [
    "Dr Amelia Clarke",
    "Dr James Thompson",
    "Dr Priya Shah",
    "Dr Benjamin Carter",
    "Dr Hannah Lewis",
    "Dr Oliver Green",
]


def load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def hl7_ts(value: str | None) -> str:
    if not value:
        return ""
    try:
        if "T" in value:
            dt = datetime.fromisoformat(value)
        else:
            dt = datetime.fromisoformat(f"{value}T09:00:00")
    except ValueError:
        return value
    return dt.strftime("%Y%m%d%H%M%S")


def clean_text(value: str | None) -> str:
    return (value or "").replace("\r", " ").replace("\n", " ").strip()


def sex_code(patient: dict[str, Any]) -> str:
    value = (patient.get("sex") or "").strip().lower()
    if value.startswith("m"):
        return "M"
    if value.startswith("f"):
        return "F"
    return "U"


def pid_segment(patient: dict[str, Any]) -> str:
    identifier = f"{patient.get('nhs_number','')}^^^NHS~{patient.get('mrn','')}^^^MRN"
    name = f"{patient.get('surname','')}^{patient.get('first_name','')}"
    address = f"{patient.get('address_line_1','')}^^{patient.get('address_line_2','')}^^{patient.get('postcode','')}"
    return "|".join(
        [
            "PID",
            "1",
            "",
            identifier,
            "",
            name,
            "",
            hl7_ts(patient.get("date_of_birth")),
            sex_code(patient),
            "",
            "",
            address,
            "",
            patient.get("phone_number", ""),
        ]
    )


def build_message(
    sending_app: str,
    patient: dict[str, Any],
    order_id: str,
    order_text: str,
    ordered_at: str | None,
    status: str | None,
    observation_type: str,
    observation_id: str,
    observation_value: str,
    observation_unit: str = "",
) -> str:
    control_id = str(uuid.uuid4())
    timestamp = hl7_ts(datetime.now().astimezone().isoformat())
    msh = "|".join(
        [
            "MSH",
            "^~\\&",
            sending_app,
            "",
            "TIE",
            "",
            timestamp,
            "",
            "ORU^R01",
            control_id,
            "P",
            "2.4",
        ]
    )
    pv1 = "|".join(["PV1", "1", "O", "", "", "", "", f"{ATTENDING_DOCTORS[hash(order_id) % len(ATTENDING_DOCTORS)]}"])
    obr = "|".join(
        [
            "OBR",
            "1",
            order_id,
            "",
            f"{observation_id}^{clean_text(order_text)}",
            "",
            hl7_ts(ordered_at),
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            clean_text(status),
        ]
    )
    obx = "|".join(
        [
            "OBX",
            "1",
            observation_type,
            observation_id,
            "",
            clean_text(observation_value),
            observation_unit,
            "",
            "",
            "",
            "F",
        ]
    )
    return "\r".join([msh, pid_segment(patient), pv1, obr, obx])


def write_message(source: str, identifier: str, message: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{source}_ORU_R01_{identifier}.hl7"
    file_path.write_text(message, encoding="utf-8")
    return file_path


def render_hl7_messages(
    journey_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, int]:
    journey_dir = journey_dir or JOURNEY_DIR
    output_dir = output_dir or OUTPUT_DIR

    patients = {row["person_id"]: row for row in load_json(journey_dir / "patients.json")}
    radiology = load_json(journey_dir / "radiology.json")
    histology = load_json(journey_dir / "histology.json")
    test_results = load_json(journey_dir / "test_results.json")

    messages: list[str] = []
    file_count = 0

    for exam in radiology:
        patient = patients.get(exam["person_id"])
        if not patient:
            continue
        message = build_message(
            sending_app=exam["source_system_name"],
            patient=patient,
            order_id=exam["radiology_exam_id"],
            order_text=exam["radiology_exam_type"],
            ordered_at=exam.get("ordered_date"),
            status=exam.get("exam_status"),
            observation_type="TX",
            observation_id="RAD_REPORT",
            observation_value=exam.get("radiology_report_text", ""),
        )
        write_message(exam["source_system_name"], exam["radiology_exam_id"], message, output_dir)
        messages.append(message)
        file_count += 1

    for sample in histology:
        patient = patients.get(sample["person_id"])
        if not patient:
            continue
        message = build_message(
            sending_app=sample["source_system_name"],
            patient=patient,
            order_id=sample["histology_id"],
            order_text=sample["histology_type"],
            ordered_at=sample.get("sample_taken_date"),
            status=sample.get("histology_status"),
            observation_type="TX",
            observation_id="HIST_REPORT",
            observation_value=sample.get("histology_report_text", ""),
        )
        write_message(sample["source_system_name"], sample["histology_id"], message, output_dir)
        messages.append(message)
        file_count += 1

    for result in test_results:
        patient = patients.get(result["person_id"])
        if not patient:
            continue
        observation_type = "NM" if result.get("test_value_type") == "Numeric" else "TX"
        message = build_message(
            sending_app=result["source_system_name"],
            patient=patient,
            order_id=result["test_result_id"],
            order_text=result["test_name"],
            ordered_at=result.get("test_ordered_timestamp"),
            status="Final",
            observation_type=observation_type,
            observation_id=result.get("test_name", "TEST"),
            observation_value=str(result.get("value", "")),
            observation_unit=result.get("unit", "") or "",
        )
        write_message(result["source_system_name"], result["test_result_id"], message, output_dir)
        messages.append(message)
        file_count += 1

    combined_path = output_dir / "all_messages.hl7"
    output_dir.mkdir(parents=True, exist_ok=True)
    combined_path.write_text("\n\n".join(messages), encoding="utf-8")
    return {
        "message_files": file_count,
        "combined_files": 1,
        "total_messages": len(messages),
    }


def main() -> None:
    summary = render_hl7_messages()
    print(
        f"Wrote {summary['message_files']} HL7 message files and {summary['combined_files']} combined file "
        f"to {OUTPUT_DIR} ({summary['total_messages']} messages)"
    )


if __name__ == "__main__":
    main()
