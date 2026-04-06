"""RIS/CRIS simulator for radiology ORU messages."""

from __future__ import annotations

from source_systems.common import build_oru_message


def generate_events(journeys: list[dict]) -> list[dict]:
    events: list[dict] = []
    for journey in journeys:
        patient = journey["patient"]
        payload = journey["radiology"]
        stamp = payload["result_datetime"].replace(":", "").replace("-", "")[:14]
        events.append({"timestamp": payload["result_datetime"], "source": "ris", "format": "hl7", "filename": f"{stamp}_ris_oru_{journey['journey_id']}.hl7", "payload": build_oru_message("CRIS", "RIS", patient, payload)})
    return sorted(events, key=lambda item: item["timestamp"])
