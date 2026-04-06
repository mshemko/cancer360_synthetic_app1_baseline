"""Shared helpers for Phase 2 synthetic journey generators."""

from __future__ import annotations

import json
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "generation_params.yaml"
REFERENCE_DIR = ROOT / "source_systems" / "config" / "reference_data"
OUTPUT_DIR = ROOT / "source_systems" / "output" / "journeys"
PATHWAY_OUTPUT = OUTPUT_DIR / "pathways.json"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_config() -> dict[str, Any]:
    return load_yaml(CONFIG_PATH)


def load_pathways() -> list[dict[str, Any]]:
    return load_json(PATHWAY_OUTPUT)


def save_output(file_name: str, records: list[dict[str, Any]]) -> Path:
    output_path = OUTPUT_DIR / file_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return output_path


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def current_timestamp() -> str:
    return datetime.now().astimezone().isoformat()


def random_date_between(start: date, end: date) -> date:
    if end <= start:
        return start
    return start + timedelta(days=random.randint(0, (end - start).days))


def random_datetime_on(day: date) -> str:
    hour = random.randint(7, 18)
    minute = random.choice([0, 10, 15, 20, 30, 40, 45, 50])
    return datetime.combine(day, time(hour=hour, minute=minute)).astimezone().isoformat()


def timeline_dates(pathway: dict[str, Any]) -> dict[str, date | None]:
    key_dates = pathway["timeline_skeleton"]["key_dates"]
    return {
        "referral": parse_date(key_dates.get("referral")),
        "first_seen": parse_date(key_dates.get("first_seen")),
        "diagnosis": parse_date(key_dates.get("diagnosis")),
        "dtt": parse_date(key_dates.get("dtt")),
        "first_treatment": parse_date(key_dates.get("first_treatment")),
        "closed": parse_date(key_dates.get("closed")),
    }


def pathway_end_date(pathway: dict[str, Any]) -> date:
    dates = timeline_dates(pathway)
    if dates["closed"]:
        return dates["closed"]
    candidates = [value for value in dates.values() if value is not None]
    latest = max(candidates) if candidates else date.today()
    return min(date.today(), latest + timedelta(days=180))


def sorted_event_dates(
    window_start: date,
    window_end: date,
    count: int,
    min_spacing_days: int = 0,
) -> list[date]:
    if count <= 0:
        return []
    if window_end < window_start:
        window_end = window_start
    dates: list[date] = []
    current_start = window_start
    for remaining in range(count, 0, -1):
        latest_start = window_end - timedelta(days=min_spacing_days * (remaining - 1))
        if latest_start < current_start:
            latest_start = current_start
        chosen = random_date_between(current_start, latest_start)
        dates.append(chosen)
        current_start = chosen + timedelta(days=min_spacing_days)
    return dates


def choose_volume(volume_cfg: dict[str, int]) -> int:
    return random.randint(int(volume_cfg["min"]), int(volume_cfg["max"]))

