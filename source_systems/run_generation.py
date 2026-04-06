"""CLI entry point for end-to-end Cancer 360 synthetic generation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from source_systems.generators.orchestrator import print_summary, run_generation_pipeline


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Cancer 360 synthetic data generation and rendering")
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "generation_params.yaml"),
        help="Path to generation_params.yaml",
    )
    parser.add_argument(
        "--patients",
        type=int,
        default=None,
        help="Override number of patients to generate",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "source_systems" / "output"),
        help="Override output directory root",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete existing output files before generating",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        summary = run_generation_pipeline(
            config_path=Path(args.config).resolve(),
            patients_override=args.patients,
            output_root=Path(args.output).resolve(),
            clean=args.clean,
            seed=args.seed,
        )
    except FileNotFoundError as exc:
        print(f"Generation failed: missing file -> {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1

    print_summary(summary)
    print(f"Output root: {summary['output_root']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
