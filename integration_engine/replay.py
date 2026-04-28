"""CLI wrapper for replaying rendered source payloads through raw and staging."""

from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[1]))

import argparse

from integration_engine.orchestrator import run_replay


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay rendered source payloads into raw and staging schemas.")
    parser.add_argument(
        "--source-dir",
        default=None,
        help="Optional override for the source_systems/output directory.",
    )
    args = parser.parse_args()
    run_replay(args.source_dir)


if __name__ == "__main__":
    main()
