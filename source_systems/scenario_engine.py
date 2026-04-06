"""Generate clinically coherent patient journeys for the integration simulation."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from source_systems.common import build_journeys, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Cancer 360 scenario journeys.")
    parser.add_argument("--patients", type=int, default=50, help="Number of patient journeys to create.")
    parser.add_argument("--seed", type=int, default=360, help="Random seed for reproducible output.")
    parser.add_argument("--output", default="data/scenarios/journeys.json", help="Output JSON path.")
    parser.add_argument("--anchor-date", default=None, help="Anchor date in YYYY-MM-DD format.")
    args = parser.parse_args()

    anchor = date.fromisoformat(args.anchor_date) if args.anchor_date else None
    journeys = build_journeys(args.patients, seed=args.seed, anchor_date=anchor)
    output_path = write_json(Path(args.output), journeys)
    print(f"Generated {len(journeys)} journeys -> {output_path}")


if __name__ == "__main__":
    main()
