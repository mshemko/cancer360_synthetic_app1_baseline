"""Message Replay Engine — loads synthetic data files and replays them through the integration pipeline.

This enables loading the complete synthetic dataset into the CDM store without
running live TCP/file-watch receivers. It processes all message types in
chronological order, simulating a realistic data flow.
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from orchestrator import IntegrationOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class TimedMessage:
    timestamp: datetime
    source: str
    format: str  # hl7, csv, xml, json
    file_type: str
    content: str
    filename: str = ""


class MessageReplayEngine:
    """Replays synthetic data files through the integration pipeline in chronological order."""

    def __init__(self, data_dir: str, orchestrator: IntegrationOrchestrator):
        self.data_dir = Path(data_dir)
        self.orchestrator = orchestrator

    def load_hl7_messages(self, filepath: Path, source: str) -> List[TimedMessage]:
        """Load HL7 messages from a text file (one message per MSH...segment block)."""
        messages = []
        if not filepath.exists():
            logger.warning(f"HL7 file not found: {filepath}")
            return messages

        content = filepath.read_text(encoding="utf-8", errors="replace")

        # Split on MSH segment boundaries
        raw_messages = []
        current = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("MSH|") and current:
                raw_messages.append("\r".join(current))
                current = [line]
            elif line:
                current.append(line)
        if current:
            raw_messages.append("\r".join(current))

        for raw in raw_messages:
            # Extract timestamp from MSH-7
            try:
                fields = raw.split("\r")[0].split("|")
                ts_str = fields[6] if len(fields) > 6 else ""
                ts = self._parse_timestamp(ts_str)
            except (IndexError, ValueError):
                ts = datetime.now()

            messages.append(TimedMessage(
                timestamp=ts,
                source=source,
                format="hl7",
                file_type=f"{source}_hl7",
                content=raw,
                filename=filepath.name,
            ))

        logger.info(f"Loaded {len(messages)} HL7 messages from {filepath}")
        return messages

    def load_csv_file(self, filepath: Path, file_type: str) -> List[TimedMessage]:
        """Load a CSV file as a single message."""
        if not filepath.exists():
            logger.warning(f"CSV file not found: {filepath}")
            return []

        content = filepath.read_text(encoding="utf-8-sig", errors="replace")
        return [TimedMessage(
            timestamp=datetime.now(),
            source=file_type,
            format="csv",
            file_type=file_type,
            content=content,
            filename=filepath.name,
        )]

    def load_xml_file(self, filepath: Path) -> List[TimedMessage]:
        """Load an XML file as a single message."""
        if not filepath.exists():
            logger.warning(f"XML file not found: {filepath}")
            return []

        content = filepath.read_text(encoding="utf-8", errors="replace")
        return [TimedMessage(
            timestamp=datetime.now(),
            source="SOMERSET",
            format="xml",
            file_type="somerset_xml",
            content=content,
            filename=filepath.name,
        )]

    def load_json_file(self, filepath: Path, file_type: str) -> List[TimedMessage]:
        """Load a JSON file as messages."""
        if not filepath.exists():
            logger.warning(f"JSON file not found: {filepath}")
            return []

        content = filepath.read_text(encoding="utf-8", errors="replace")
        return [TimedMessage(
            timestamp=datetime.now(),
            source=file_type.upper(),
            format="json",
            file_type=file_type,
            content=content,
            filename=filepath.name,
        )]

    async def replay_all(self):
        """Load and replay all synthetic data files."""
        logger.info(f"Starting replay from {self.data_dir}")
        messages = []

        # HL7 messages
        msg_dir = self.data_dir / "messages"
        if msg_dir.exists():
            for f in msg_dir.glob("*_hl7.txt"):
                source = "ICE" if "ice" in f.name.lower() else "RIS" if "ris" in f.name.lower() else "UNKNOWN"
                messages.extend(self.load_hl7_messages(f, source))

        # CSV files
        export_dir = self.data_dir / "exports"
        if export_dir.exists():
            for f in export_dir.glob("sact_*.csv"):
                messages.extend(self.load_csv_file(f, "sact_csv"))
            for f in export_dir.glob("rtds_*.csv"):
                messages.extend(self.load_csv_file(f, "rtds_csv"))
            for f in export_dir.glob("cds_*.csv"):
                messages.extend(self.load_csv_file(f, "cds_csv"))

        # XML files
        if msg_dir.exists():
            for f in msg_dir.glob("somerset_*.xml"):
                messages.extend(self.load_xml_file(f))

        # JSON files
        raw_dir = self.data_dir / "raw"
        if raw_dir.exists():
            for f in raw_dir.glob("mdt_*.json"):
                messages.extend(self.load_json_file(f, "mdt"))
            for f in raw_dir.glob("ers_*.json"):
                messages.extend(self.load_json_file(f, "ers"))

        # Parquet-based raw data (convert to process)
        if raw_dir.exists():
            for f in raw_dir.glob("*.parquet"):
                logger.info(f"Skipping parquet file (use notebook to convert): {f.name}")

        if not messages:
            logger.warning("No synthetic data files found. Generate data using notebooks first.")
            return

        # Sort by timestamp
        messages.sort(key=lambda m: m.timestamp)
        logger.info(f"Loaded {len(messages)} messages for replay")

        # Process each message
        processed = 0
        errors = 0

        for i, msg in enumerate(messages):
            try:
                if msg.format == "hl7":
                    await self.orchestrator.process_hl7_message(msg.content)
                elif msg.format in ("csv", "xml"):
                    await self.orchestrator.process_csv_file(msg.filename, msg.content, msg.file_type)
                elif msg.format == "json":
                    try:
                        records = json.loads(msg.content)
                        if isinstance(records, list):
                            await self.orchestrator.process_json_records(records, msg.file_type)
                        elif isinstance(records, dict):
                            await self.orchestrator.process_json_records([records], msg.file_type)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error in {msg.filename}: {e}")

                processed += 1
                if processed % 100 == 0:
                    stats = self.orchestrator.get_stats()
                    logger.info(
                        f"Progress: {processed}/{len(messages)} messages "
                        f"({stats['messages_processed']} entities stored)"
                    )

            except Exception as e:
                errors += 1
                logger.error(f"Error replaying message {i} ({msg.source}/{msg.format}): {e}")

        stats = self.orchestrator.get_stats()
        logger.info(
            f"Replay complete: {processed} messages processed, {errors} errors. "
            f"CDM store: {stats['messages_processed']} entities, "
            f"{stats['patient_cache_size']} patients cached."
        )

    @staticmethod
    def _parse_timestamp(ts_str: str) -> datetime:
        for fmt in ("%Y%m%d%H%M%S", "%Y%m%d%H%M", "%Y%m%d"):
            try:
                return datetime.strptime(ts_str[:len(fmt.replace("%", ""))], fmt)
            except (ValueError, IndexError):
                continue
        return datetime.now()


async def main():
    """Entry point for running the replay engine."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    database_url = os.environ.get(
        "DATABASE_URL", "postgresql+asyncpg://cancer360:localdev@localhost:5432/cancer360"
    )
    data_dir = os.environ.get("DATA_DIR", "./data")

    orchestrator = IntegrationOrchestrator(database_url)
    replay = MessageReplayEngine(data_dir, orchestrator)
    await replay.replay_all()


if __name__ == "__main__":
    asyncio.run(main())
