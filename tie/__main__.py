"""CLI entry point for the native Trust Integration Engine."""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
from pathlib import Path

from tie.common import DatabaseStore
from tie.config import get_config
from tie.receivers.file_watcher import PollingFileWatcher
from tie.receivers.mllp_server import MLLPServer
from tie.router import IntegrationRouter


class TieApp:
    def __init__(self) -> None:
        self.config = get_config()
        self.store = DatabaseStore(self.config.database_url)
        self.router = IntegrationRouter(self.store)

    async def run(self) -> None:
        incoming_dirs = [self.config.incoming_root / subdir for subdir in self.config.file_subdirs]
        watcher = PollingFileWatcher(incoming_dirs, self.config.poll_seconds, self.process_file_path)
        server = MLLPServer(self.config.mllp_host, self.config.mllp_port, self.router.handle_hl7)
        print(f"TIE listening on {self.config.mllp_host}:{self.config.mllp_port} and watching {self.config.incoming_root.resolve()}")
        await asyncio.gather(server.start(), watcher.start())

    async def process_file_path(self, path: Path) -> None:
        processed_dir = path.parent / "processed"
        error_dir = path.parent / "error"
        processed_dir.mkdir(exist_ok=True)
        error_dir.mkdir(exist_ok=True)
        try:
            payload = path.read_text(encoding="utf-8")
            await self.router.handle_file_payload(path.name, payload)
            shutil.move(str(path), str(processed_dir / path.name))
            print(f"Processed {path.name}")
        except Exception as exc:
            shutil.move(str(path), str(error_dir / path.name))
            (error_dir / f"{path.name}.error.txt").write_text(str(exc), encoding="utf-8")
            print(f"Failed {path.name}: {exc}")

    async def replay(self, data_dir: str | Path) -> None:
        data_path = Path(data_dir)
        manifest = data_path / "manifest.json"
        if manifest.exists():
            events = json.loads(manifest.read_text(encoding="utf-8"))
            for event in events:
                if event["format"] == "hl7":
                    await self.router.handle_hl7(event["payload"])
                else:
                    await self.router.handle_file_payload(event["filename"], event["payload"])
            print(f"Replayed {len(events)} events from {manifest}")
            return

        hl7_files = sorted((data_path / "hl7").rglob("*.hl7"))
        csv_files = sorted((data_path / "csv").rglob("*.csv"))
        for file_path in hl7_files:
            await self.router.handle_hl7(file_path.read_text(encoding="utf-8"))
        for file_path in csv_files:
            await self.router.handle_file_payload(file_path.name, file_path.read_text(encoding="utf-8"))
        print(f"Replayed {len(hl7_files) + len(csv_files)} files from {data_path}")


async def main_async() -> None:
    parser = argparse.ArgumentParser(description="Native Trust Integration Engine")
    subparsers = parser.add_subparsers(dest="command")
    replay_parser = subparsers.add_parser("replay", help="Replay generated data directly into the database")
    replay_parser.add_argument("--data-dir", default="data", help="Directory containing manifest/hl7/csv output")
    args = parser.parse_args()

    app = TieApp()
    if args.command == "replay":
        await app.replay(args.data_dir)
    else:
        await app.run()


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
