"""ICE/WinPath simulator for pathology ORU messages."""

from __future__ import annotations

from source_systems.common import build_oru_message


def generate_events(journeys: list[dict]) -> list[dict]:
    events: list[dict] = []
    for journey in journeys:
        patient = journey["patient"]
        for key in ("histology", "bloods"):
            payload = journey["pathology"][key]
            stamp = payload["result_datetime"].replace(":", "").replace("-", "")[:14]
            events.append({"timestamp": payload["result_datetime"], "source": "ice", "format": "hl7", "filename": f"{stamp}_ice_{key}_{journey['journey_id']}.hl7", "payload": build_oru_message("WINPATH", "PATH", patient, payload)})
    return sorted(events, key=lambda item: item["timestamp"])
