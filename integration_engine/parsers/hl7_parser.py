"""Parse HL7 v2.4 ORU messages into structured dictionaries."""

from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

import json
import re
from datetime import datetime
from pprint import pprint

from integration_engine import config


def parse_hl7_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    date_str = date_str.strip()
    for fmt, length in (
        ("%Y%m%d%H%M%S", 14),
        ("%Y%m%d%H%M", 12),
        ("%Y%m%d", 8),
    ):
        try:
            return datetime.strptime(date_str[:length], fmt)
        except ValueError:
            continue
    return None


def _segments(hl7_text: str) -> list[list[str]]:
    raw_segments = [line.strip() for line in re.split(r"[\r\n]+", hl7_text) if line.strip()]
    return [segment.split("|") for segment in raw_segments]


def parse_msh(msh_segment: list[str]) -> dict:
    return {
        "sending_application": msh_segment[2] if len(msh_segment) > 2 else "",
        "receiving_application": msh_segment[4] if len(msh_segment) > 4 else "",
        "message_type": msh_segment[8] if len(msh_segment) > 8 else "",
        "message_control_id": msh_segment[9] if len(msh_segment) > 9 else "",
        "timestamp": msh_segment[6] if len(msh_segment) > 6 else "",
        "parsed_timestamp": parse_hl7_date(msh_segment[6] if len(msh_segment) > 6 else ""),
    }


def parse_pid(pid_segment: list[str]) -> dict:
    identifiers = pid_segment[3] if len(pid_segment) > 3 else ""
    nhs_number = ""
    mrn = ""
    for identifier in identifiers.split("~"):
        parts = identifier.split("^")
        value = parts[0].strip() if parts else ""
        authority = parts[3].strip().upper() if len(parts) > 3 else ""
        if authority == "NHS":
            nhs_number = value
        elif authority == "MRN":
            mrn = value
        elif not nhs_number:
            nhs_number = value

    patient_name = pid_segment[5] if len(pid_segment) > 5 else ""
    name_parts = patient_name.split("^")
    surname = name_parts[0].strip() if name_parts else ""
    first_name = name_parts[1].strip() if len(name_parts) > 1 else ""

    address = pid_segment[11] if len(pid_segment) > 11 else ""
    address_parts = address.split("^")

    return {
        "nhs_number": nhs_number,
        "mrn": mrn,
        "patient_name": patient_name,
        "first_name": first_name,
        "surname": surname,
        "dob": pid_segment[7] if len(pid_segment) > 7 else "",
        "parsed_dob": parse_hl7_date(pid_segment[7] if len(pid_segment) > 7 else ""),
        "sex": pid_segment[8] if len(pid_segment) > 8 else "",
        "address": address,
        "address_line_1": address_parts[0].strip() if address_parts else "",
        "address_line_2": address_parts[2].strip() if len(address_parts) > 2 else "",
        "phone": pid_segment[13] if len(pid_segment) > 13 else "",
    }


def parse_obr(obr_segment: list[str]) -> dict:
    identifier = obr_segment[4] if len(obr_segment) > 4 else ""
    identifier_parts = identifier.split("^")
    result_status = ""
    for value in reversed(obr_segment):
        if value:
            result_status = value
            break

    return {
        "order_number": obr_segment[2] if len(obr_segment) > 2 else "",
        "observation_identifier": identifier_parts[0].strip() if identifier_parts else "",
        "exam_type": identifier_parts[1].strip() if len(identifier_parts) > 1 else identifier,
        "ordered_datetime": obr_segment[6] if len(obr_segment) > 6 else "",
        "parsed_ordered_datetime": parse_hl7_date(obr_segment[6] if len(obr_segment) > 6 else ""),
        "result_status": result_status,
    }


def parse_obx(obx_segments: list[list[str]]) -> list[dict]:
    observations: list[dict] = []
    for segment in obx_segments:
        observations.append(
            {
                "value_type": segment[2] if len(segment) > 2 else "",
                "observation_identifier": segment[3] if len(segment) > 3 else "",
                "value": segment[5] if len(segment) > 5 else "",
                "unit": segment[6] if len(segment) > 6 else "",
                "status": segment[11] if len(segment) > 11 else "",
            }
        )
    return observations


def parse_message(hl7_text: str) -> dict:
    segments = _segments(hl7_text)
    parsed: dict[str, object] = {"raw_message": hl7_text}
    obx_segments: list[list[str]] = []

    for segment in segments:
        name = segment[0]
        if name == "MSH":
            parsed["MSH"] = parse_msh(segment)
        elif name == "PID":
            parsed["PID"] = parse_pid(segment)
        elif name == "PV1":
            parsed["PV1"] = {
                "patient_class": segment[2] if len(segment) > 2 else "",
                "attending_doctor": segment[7] if len(segment) > 7 else "",
            }
        elif name == "OBR":
            parsed["OBR"] = parse_obr(segment)
        elif name == "OBX":
            obx_segments.append(segment)

    parsed["OBX"] = parse_obx(obx_segments)
    return parsed


def classify_message(parsed: dict) -> str:
    msh = parsed.get("MSH", {})
    obr = parsed.get("OBR", {})
    obx = parsed.get("OBX", [])

    sending_application = str(msh.get("sending_application", "")).upper()
    observation_identifier = str(obr.get("observation_identifier", "")).upper()
    exam_type = str(obr.get("exam_type", "")).lower()

    if sending_application == "CRIS":
        return "radiology"

    if sending_application == "ICE":
        if observation_identifier == "HIST_REPORT":
            return "histology"
        if any(str(obs.get("value_type", "")).upper() == "NM" for obs in obx):
            return "test_result"
        histology_keywords = ("hist", "biopsy", "cytology", "tissue", "fna", "excision")
        if any(keyword in exam_type for keyword in histology_keywords):
            return "histology"
        return "test_result"

    return "test_result"


def main() -> None:
    sample = next(
        (path for path in config.HL7_DIR.glob("*.hl7") if path.name != "all_messages.hl7"),
        None,
    )
    if not sample:
        print("No sample HL7 file found.")
        return

    parsed = parse_message(sample.read_text(encoding="utf-8"))
    print(f"Sample file: {sample.name}")
    print(f"Classification: {classify_message(parsed)}")
    pprint(json.loads(json.dumps(parsed, default=str)))


if __name__ == "__main__":
    main()
