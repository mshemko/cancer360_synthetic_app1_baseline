"""Integration Orchestrator — coordinates message flow from receivers through parsers to CDM store.

This is the central pipeline controller. It receives raw messages from adapters,
routes them to the correct parser, transforms via CDM mappers, resolves patient
identity, and persists to PostgreSQL.
"""

import asyncio
import hashlib
import logging
import time
import uuid
from typing import Optional, Dict, Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from parsers import HL7Parser, SACTParser, RTDSParser, CDSParser, SomersetXMLParser
from mappers import (
    PathologyMapper, RadiologyMapper, SomersetMapper,
    SACTMapper, RadiotherapyMapper, MDTMapper, AdmissionMapper,
)

logger = logging.getLogger(__name__)


class CDMStore:
    """Persists CDM entities to PostgreSQL, handling patient resolution and upserts."""

    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, pool_size=10, echo=False)
        self.session_factory = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self._patient_cache: Dict[str, str] = {}  # nhs_number → patient_id

    async def resolve_patient_id(self, session: AsyncSession, nhs_number: str) -> Optional[str]:
        """Resolve NHS number to patient_id UUID. Returns None if patient not found."""
        if not nhs_number:
            return None

        nhs_clean = nhs_number.replace(" ", "").strip()

        # Check cache first
        if nhs_clean in self._patient_cache:
            return self._patient_cache[nhs_clean]

        # Query database
        result = await session.execute(
            text("SELECT patient_id FROM patient WHERE nhs_number = :nhs"),
            {"nhs": nhs_clean},
        )
        row = result.fetchone()
        if row:
            pid = str(row[0])
            self._patient_cache[nhs_clean] = pid
            return pid

        return None

    async def upsert_entity(self, session: AsyncSession, table: str, data: Dict[str, Any]) -> Optional[str]:
        """Insert or update a CDM entity. Returns the entity ID."""

        # Resolve patient_id from _nhs_number if present
        nhs_number = data.pop("_nhs_number", None)
        # Remove any other private fields
        private_keys = [k for k in data if k.startswith("_")]
        for k in private_keys:
            data.pop(k)

        if nhs_number and "patient_id" not in data:
            patient_id = await self.resolve_patient_id(session, nhs_number)
            if patient_id:
                data["patient_id"] = patient_id
            else:
                logger.warning(f"Patient not found for NHS number {nhs_number}, skipping {table}")
                return None

        # Build INSERT statement dynamically
        columns = list(data.keys())
        placeholders = [f":{col}" for col in columns]

        sql = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            ON CONFLICT DO NOTHING
        """

        try:
            await session.execute(text(sql), data)
            entity_id = data.get(f"{table.split('_')[0]}_id") or data.get("result_id") or data.get("course_id")
            return str(entity_id) if entity_id else None
        except Exception as e:
            logger.error(f"Error upserting to {table}: {e}")
            raise

    async def persist_entities(self, entities: list) -> int:
        """Persist a list of mapped entities within a single transaction."""
        count = 0
        async with self.session_factory() as session:
            async with session.begin():
                for entity in entities:
                    table = entity["table"]
                    data = entity["data"]
                    result = await self.upsert_entity(session, table, data)
                    if result:
                        count += 1
        return count


class AuditLogger:
    """Log integration pipeline events for audit and debugging."""

    def __init__(self, store: CDMStore):
        self.store = store

    async def log(self, correlation_id: str, event_type: str, source: str = "",
                  message_type: str = "", message_id: str = "", entity_type: str = "",
                  entity_id: str = "", status: str = "success", error: str = "",
                  processing_time_ms: int = 0):
        try:
            async with self.store.session_factory() as session:
                async with session.begin():
                    await session.execute(
                        text("""
                            INSERT INTO integration_audit_log
                            (log_id, correlation_id, event_type, source_system, message_type,
                             message_id, entity_type, entity_id, status, error_message, processing_time_ms)
                            VALUES (:lid, :cid, :et, :ss, :mt, :mid, :ety, :eid, :st, :err, :pt)
                        """),
                        {
                            "lid": str(uuid.uuid4()), "cid": correlation_id,
                            "et": event_type, "ss": source, "mt": message_type,
                            "mid": message_id, "ety": entity_type, "eid": entity_id or "",
                            "st": status, "err": error, "pt": processing_time_ms,
                        },
                    )
        except Exception as e:
            logger.error(f"Audit log error: {e}")


class IntegrationOrchestrator:
    """Main pipeline controller — routes messages from adapters through parsers and mappers to the CDM store."""

    def __init__(self, database_url: str):
        self.store = CDMStore(database_url)
        self.audit = AuditLogger(self.store)

        # Parsers
        self.hl7_parser = HL7Parser()
        self.sact_parser = SACTParser()
        self.rtds_parser = RTDSParser()
        self.cds_parser = CDSParser()
        self.somerset_parser = SomersetXMLParser()

        # Mappers
        self.pathology_mapper = PathologyMapper()
        self.radiology_mapper = RadiologyMapper()
        self.somerset_mapper = SomersetMapper()
        self.sact_mapper = SACTMapper()
        self.rt_mapper = RadiotherapyMapper()
        self.mdt_mapper = MDTMapper()
        self.admission_mapper = AdmissionMapper()

        # Counters
        self.messages_processed = 0
        self.messages_failed = 0

    async def process_hl7_message(self, raw: str) -> str:
        """Process a single HL7 message end-to-end. Returns ACK message."""
        correlation_id = str(uuid.uuid4())
        start = time.monotonic()

        try:
            # Parse
            parsed = self.hl7_parser.parse(raw)
            source = HL7Parser.determine_source_system(parsed)
            category = HL7Parser.determine_message_category(parsed)

            await self.audit.log(correlation_id, "received", source, parsed.message_type, parsed.message_id)

            # Select mapper
            if category == "pathology_result":
                mapper = self.pathology_mapper
            elif category == "radiology_result":
                mapper = self.radiology_mapper
            else:
                logger.info(f"Skipping {category} message (not yet mapped)")
                return self.hl7_parser._build_ack_from_parsed(parsed, "AA")

            # Map
            entities = mapper.map_to_entities(parsed)

            # Persist
            count = await self.store.persist_entities(entities)

            elapsed = int((time.monotonic() - start) * 1000)
            await self.audit.log(
                correlation_id, "completed", source, parsed.message_type,
                parsed.message_id, category, "", "success", "", elapsed,
            )

            self.messages_processed += 1
            logger.info(f"Processed {category} from {source}: {count} entities ({elapsed}ms)")

            return HL7Parser._build_ack(raw, "AA")

        except Exception as e:
            self.messages_failed += 1
            elapsed = int((time.monotonic() - start) * 1000)
            await self.audit.log(
                correlation_id, "error", "", "", "", "", "", "error", str(e), elapsed,
            )
            logger.error(f"Pipeline error: {e}")
            return HL7Parser._build_ack(raw, "AE", str(e)[:200])

    async def process_csv_file(self, filepath, content: str, file_type: str):
        """Process a CSV/XML file through the appropriate parser and mapper."""
        correlation_id = str(uuid.uuid4())
        start = time.monotonic()

        try:
            # Parse
            if file_type == "sact_csv":
                parsed = self.sact_parser.parse(content, str(filepath))
                mapper = self.sact_mapper
            elif file_type == "rtds_csv":
                parsed = self.rtds_parser.parse(content, str(filepath))
                mapper = self.rt_mapper
            elif file_type == "cds_csv":
                parsed = self.cds_parser.parse(content, str(filepath))
                mapper = self.admission_mapper
            elif file_type == "somerset_xml":
                parsed = self.somerset_parser.parse(content, str(filepath))
                mapper = self.somerset_mapper
            else:
                logger.warning(f"Unknown file type: {file_type}")
                return

            await self.audit.log(correlation_id, "file_received", file_type, file_type, str(filepath))

            # Map and persist each record
            total_entities = 0
            for record in parsed.records:
                try:
                    entities = mapper.map_to_entities(record)
                    count = await self.store.persist_entities(entities)
                    total_entities += count
                except Exception as e:
                    logger.error(f"Error mapping record {record.row_number}: {e}")

            elapsed = int((time.monotonic() - start) * 1000)
            await self.audit.log(
                correlation_id, "file_completed", file_type, file_type,
                str(filepath), "", "", "success", "", elapsed,
            )
            self.messages_processed += parsed.parsed_rows
            logger.info(
                f"Processed {file_type}: {parsed.parsed_rows} records → {total_entities} entities ({elapsed}ms)"
            )

            if parsed.errors:
                for err in parsed.errors[:10]:
                    logger.warning(f"  Parse error: {err}")

        except Exception as e:
            self.messages_failed += 1
            logger.error(f"File processing error ({file_type}): {e}")
            await self.audit.log(correlation_id, "file_error", file_type, "", str(filepath), "", "", "error", str(e))

    async def process_json_records(self, records: list, record_type: str):
        """Process a list of JSON records (MDT, e-RS, etc.)."""
        correlation_id = str(uuid.uuid4())

        if record_type == "mdt":
            mapper = self.mdt_mapper
        else:
            logger.warning(f"Unknown JSON record type: {record_type}")
            return

        total = 0
        for record in records:
            try:
                entities = mapper.map_to_entities(record)
                count = await self.store.persist_entities(entities)
                total += count
            except Exception as e:
                logger.error(f"Error processing JSON record: {e}")

        logger.info(f"Processed {len(records)} {record_type} JSON records → {total} entities")

    def get_stats(self) -> dict:
        return {
            "messages_processed": self.messages_processed,
            "messages_failed": self.messages_failed,
            "patient_cache_size": len(self.store._patient_cache),
        }
