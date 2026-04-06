"""Orchestrate all source-system simulators and optionally replay them into the TIE."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from source_systems import aria_simulator, endoscopy_simulator, ice_simulator, pas_simulator, ris_simulator, somerset_simulator
from source_systems.common import ensure_dir, write_json

MLLP_START = b"\x0b"
MLLP_END = b"\x1c\x0d"


async def send_hl7(host: str, port: int, payload: str) -> str:
    reader, writer = await asyncio.open_connection(host, port)
    try:
        writer.write(MLLP_START + payload.encode("utf-8") + MLLP_END)
        await writer.drain()
        buffer = b""
        while MLLP_END not in buffer:
            chunk = await reader.read(4096)
            if not chunk:
                break
            buffer += chunk
        if MLLP_START in buffer and MLLP_END in buffer:
            start = buffer.index(MLLP_START) + 1
            end = buffer.index(MLLP_END)
            return buffer[start:end].decode("utf-8", errors="replace")
        return ""
    finally:
        writer.close()
        await writer.wait_closed()


def load_journeys(path: str | Path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_events(journeys: list[dict]) -> list[dict]:
    events = []
    for producer in (
        pas_simulator.generate_events,
        ice_simulator.generate_events,
        ris_simulator.generate_events,
        somerset_simulator.generate_events,
        aria_simulator.generate_events,
        endoscopy_simulator.generate_events,
    ):
        events.extend(producer(journeys))
    events.sort(key=lambda item: item["timestamp"])
    return events


def write_events(events: list[dict], output_dir: str | Path) -> None:
    base = ensure_dir(output_dir)
    hl7_dir = ensure_dir(base / "hl7")
    csv_dir = ensure_dir(base / "csv")
    for event in events:
        target_root = hl7_dir / event["source"] if event["format"] == "hl7" else csv_dir / event["subdir"]
        target = ensure_dir(target_root) / event["filename"]
        target.write_text(event["payload"], encoding="utf-8")
    write_json(base / "manifest.json", events)


async def dispatch_events(events: list[dict], host: str | None, port: int, file_drop_dir: str | None, mode: str, speed: float) -> None:
    last_ts: datetime | None = None
    for event in events:
        current = datetime.fromisoformat(event["timestamp"])
        if mode == "live" and last_ts is not None:
            await asyncio.sleep(min(max(0.0, (current - last_ts).total_seconds() / max(speed, 1.0)), 2.0))
        elif mode == "replay":
            await asyncio.sleep(0.02)
        last_ts = current

        if event["format"] == "hl7" and host:
            ack = await send_hl7(host, port, event["payload"])
            print(f"HL7 {event['filename']} -> {ack.split(chr(13))[1] if ack else 'NO_ACK'}")
        elif event["format"] == "file" and file_drop_dir:
            target = ensure_dir(Path(file_drop_dir) / event["subdir"]) / event["filename"]
            target.write_text(event["payload"], encoding="utf-8")
            print(f"FILE {target}")


async def main_async() -> None:
    parser = argparse.ArgumentParser(description="Generate and optionally replay all source-system payloads.")
    parser.add_argument("--scenarios", required=True, help="Path to journeys.json from scenario_engine.")
    parser.add_argument("--output-dir", default="data", help="Directory for generated hl7/csv payloads.")
    parser.add_argument("--mode", choices=["generate", "replay", "live"], default="generate")
    parser.add_argument("--mllp-host", default=None, help="Host for live HL7 dispatch.")
    parser.add_argument("--mllp-port", type=int, default=2575, help="MLLP port.")
    parser.add_argument("--file-drop-dir", default=None, help="Incoming directory root for file-drop sources.")
    parser.add_argument("--speed", type=float, default=120.0, help="Time compression factor for live mode.")
    args = parser.parse_args()

    journeys = load_journeys(args.scenarios)
    events = build_events(journeys)
    write_events(events, args.output_dir)
    print(f"Generated {len(events)} payload events under {Path(args.output_dir).resolve()}")

    if args.mode != "generate":
        await dispatch_events(events, args.mllp_host, args.mllp_port, args.file_drop_dir, args.mode, args.speed)


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
