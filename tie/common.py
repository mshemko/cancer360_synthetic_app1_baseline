"""Shared parsing and database helpers for the native TIE."""

from __future__ import annotations

import csv
import hashlib
import io
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def deterministic_uuid(namespace: str, value: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"cancer360:{namespace}:{value}")


def clean_nhs(value: str | None) -> str | None:
    if not value:
        return None
    return value.replace(" ", "").replace("-", "").strip()[:10]


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt, length in (
        ("%Y-%m-%d", 10),
        ("%Y%m%d", 8),
        ("%d/%m/%Y", 10),
        ("%Y-%m-%dT%H:%M:%S", 19),
        ("%Y-%m-%dT%H:%M:%S.%f", 26),
    ):
        try:
            return datetime.strptime(value[:length], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt, length in (
        ("%Y%m%d%H%M%S", 14),
        ("%Y%m%d%H%M", 12),
        ("%Y%m%d", 8),
        ("%Y-%m-%dT%H:%M:%S", 19),
        ("%Y-%m-%d %H:%M:%S", 19),
    ):
        try:
            return datetime.strptime(value[:length], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "t", "y", "yes", "open", "attended"}


def read_csv_rows(payload: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload)))


def payload_hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()


def parse_hl7(raw: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {"segments": {}, "observations": []}
    segments = [segment for segment in raw.strip().split("\r") if segment.strip()]
    for segment in segments:
        fields = segment.split("|")
        name = fields[0]
        parsed["segments"].setdefault(name, []).append(fields)
        if name == "MSH":
            parsed["message_type"] = fields[8]
            parsed["message_id"] = fields[9]
            parsed["sending_app"] = fields[2]
            parsed["sending_facility"] = fields[3]
            parsed["timestamp"] = parse_datetime(fields[6])
        elif name == "PID":
            ids = fields[3].split("~") if len(fields) > 3 else []
            nhs = None
            mrn = None
            for pid_value in ids:
                parts = pid_value.split("^")
                if len(parts) > 4 and parts[4] == "NH":
                    nhs = parts[0]
                elif len(parts) > 4 and parts[4] == "MR":
                    mrn = parts[0]
            name_parts = fields[5].split("^") if len(fields) > 5 else []
            parsed["patient"] = {
                "nhs_number": clean_nhs(nhs or (ids[0].split("^")[0] if ids else None)),
                "hospital_number": mrn,
                "surname": name_parts[0] if name_parts else None,
                "forename": name_parts[1] if len(name_parts) > 1 else None,
                "prefix": name_parts[4] if len(name_parts) > 4 else None,
                "date_of_birth": parse_date(fields[7]) if len(fields) > 7 else None,
                "sex": fields[8] if len(fields) > 8 else None,
                "postcode": fields[11].split("^")[4] if len(fields) > 11 and "^" in fields[11] else None,
                "phone": fields[13] if len(fields) > 13 else None,
            }
        elif name == "PV1":
            parsed["visit"] = {"location": fields[3] if len(fields) > 3 else None}
        elif name == "SCH":
            parsed["schedule"] = {
                "appointment_id": fields[1] if len(fields) > 1 else None,
                "appointment_type": fields[6] if len(fields) > 6 else None,
                "clinic_name": fields[7] if len(fields) > 7 else None,
                "start_datetime": parse_datetime(fields[10]) if len(fields) > 10 else None,
                "status": fields[11] if len(fields) > 11 else None,
                "consultant_name": fields[15] if len(fields) > 15 else None,
            }
        elif name == "OBR":
            test_parts = fields[4].split("^") if len(fields) > 4 else []
            clinician = fields[16].split("^") if len(fields) > 16 else []
            parsed["order"] = {
                "order_id": fields[2] if len(fields) > 2 else None,
                "accession": fields[3] if len(fields) > 3 else None,
                "test_code": test_parts[0] if test_parts else None,
                "test_name": test_parts[1] if len(test_parts) > 1 else None,
                "order_datetime": parse_datetime(fields[7]) if len(fields) > 7 else None,
                "specimen_datetime": parse_datetime(fields[14]) if len(fields) > 14 else None,
                "result_datetime": parse_datetime(fields[22]) if len(fields) > 22 else None,
                "status": fields[25] if len(fields) > 25 else None,
                "clinician_name": " ".join(part for part in clinician[1:3] if part).strip() if clinician else None,
            }
        elif name == "OBX":
            obs_parts = fields[3].split("^") if len(fields) > 3 else []
            parsed["observations"].append({
                "set_id": fields[1] if len(fields) > 1 else None,
                "value_type": fields[2] if len(fields) > 2 else None,
                "code": obs_parts[0] if obs_parts else None,
                "name": obs_parts[1] if len(obs_parts) > 1 else None,
                "value": fields[5] if len(fields) > 5 else None,
                "units": fields[6] if len(fields) > 6 else None,
                "range": fields[7] if len(fields) > 7 else None,
                "flag": fields[8] if len(fields) > 8 else None,
            })
    return parsed


def build_ack(raw: str, code: str = "AA", error: str = "") -> str:
    parsed = parse_hl7(raw)
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    return (
        f"MSH|^~\\&|C360|FDP|{parsed.get('sending_app','SRC')}|{parsed.get('sending_facility','SRC')}|{now}||ACK|ACK-{parsed.get('message_id','UNKNOWN')}|P|2.4\r"
        f"MSA|{code}|{parsed.get('message_id','UNKNOWN')}|{error}\r"
    )


class DatabaseStore:
    conflict_columns = {
        "patient": "nhs_number",
        "referral": "referral_id",
        "diagnosis": "diagnosis_id",
        "staging": "staging_id",
        "appointment": "appointment_id",
        "episode": "episode_id",
        "pathology_result": "result_id",
        "pathology_result_value": "value_id",
        "histopath_structured": "histopath_id",
        "radiology_result": "result_id",
        "sact_course": "course_id",
        "sact_cycle": "cycle_id",
        "sact_drug": "drug_id",
        "radiotherapy_course": "course_id",
        "radiotherapy_fraction": "fraction_id",
        "mdt_discussion": "mdt_id",
        "cancer_action": "action_id",
        "cancer_pathway": "pathway_id",
        "integration_audit_log": "log_id",
        "dead_letter_queue": "dlq_id",
    }

    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, future=True, echo=False)
        self.session_factory = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def resolve_patient_id(self, session: AsyncSession, nhs_number: str | None) -> Any:
        if not nhs_number:
            return None
        result = await session.execute(text("SELECT patient_id FROM patient WHERE nhs_number = :nhs"), {"nhs": clean_nhs(nhs_number)})
        row = result.first()
        return row[0] if row else None

    async def fetch_pathway_context(self, session: AsyncSession, pathway_id: uuid.UUID) -> dict[str, Any] | None:
        result = await session.execute(text("SELECT patient_id, referral_id, diagnosis_id, staging_id FROM cancer_pathway WHERE pathway_id = :pathway_id"), {"pathway_id": pathway_id})
        row = result.first()
        return {"patient_id": row[0], "referral_id": row[1], "diagnosis_id": row[2], "staging_id": row[3]} if row else None

    async def upsert(self, session: AsyncSession, table: str, payload: dict[str, Any]) -> None:
        conflict = self.conflict_columns[table]
        columns = list(payload.keys())
        assignments = [f"{column} = EXCLUDED.{column}" for column in columns if column != conflict]
        sql = (
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(':' + column for column in columns)}) "
            f"ON CONFLICT ({conflict}) DO UPDATE SET {', '.join(assignments) if assignments else f'{conflict} = EXCLUDED.{conflict}'}"
        )
        await session.execute(text(sql), payload)

    async def audit(self, session: AsyncSession, correlation_id: uuid.UUID, source_system: str, message_type: str, message_id: str, entity_type: str, entity_id: uuid.UUID | None, status: str, raw_payload: str, processing_time_ms: int, error_message: str | None = None) -> None:
        await self.upsert(session, "integration_audit_log", {
            "log_id": uuid.uuid4(),
            "correlation_id": correlation_id,
            "event_type": "processed" if status == "success" else "error",
            "source_system": source_system,
            "message_type": message_type,
            "message_id": message_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "status": status,
            "error_message": error_message,
            "raw_payload_hash": payload_hash(raw_payload),
            "processing_time_ms": processing_time_ms,
        })

    async def dead_letter(self, session: AsyncSession, correlation_id: uuid.UUID, source_system: str, message_format: str, raw_payload: str, error_message: str) -> None:
        await self.upsert(session, "dead_letter_queue", {
            "dlq_id": uuid.uuid4(),
            "correlation_id": correlation_id,
            "source_system": source_system,
            "message_format": message_format,
            "raw_payload": raw_payload,
            "error_message": error_message,
            "status": "pending",
        })
