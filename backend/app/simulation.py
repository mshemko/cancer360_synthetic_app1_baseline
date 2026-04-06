"""In-process simulation runner and state store for the operator studio."""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, text

from app.config import get_settings
from app.database import async_session_factory
from app.models import (
    Appointment,
    CancerAction,
    CancerPathway,
    Diagnosis,
    Episode,
    MDTDiscussion,
    PathologyResult,
    Patient,
    RadiologyResult,
    RadiotherapyCourse,
    Referral,
    SACTCourse,
)
from app.schemas import (
    SimulationApiCheck,
    SimulationCatalogResponse,
    SimulationCreatedPatient,
    SimulationDatabaseDelta,
    SimulationRunDetail,
    SimulationRunRequest,
    SimulationRunSummary,
    SimulationStreamEvent,
)
from app.services import PTLService

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from source_systems import (  # noqa: E402
    aria_simulator,
    endoscopy_simulator,
    ice_simulator,
    pas_simulator,
    ris_simulator,
    somerset_simulator,
)
from source_systems.common import build_journeys, write_json  # noqa: E402
from source_systems.run_all import write_events  # noqa: E402
from tie.common import deterministic_uuid, parse_hl7, read_csv_rows  # noqa: E402
from tie.router import IntegrationRouter  # noqa: E402
from tie.common import DatabaseStore  # noqa: E402


SOURCE_PRODUCERS = {
    "pas": pas_simulator.generate_events,
    "ice": ice_simulator.generate_events,
    "ris": ris_simulator.generate_events,
    "somerset": somerset_simulator.generate_events,
    "aria": aria_simulator.generate_events,
    "endoscopy": endoscopy_simulator.generate_events,
}

SOURCE_LABELS = {
    "pas": "PAS / Cerner",
    "ice": "ICE / WinPath",
    "ris": "RIS / CRIS",
    "somerset": "Somerset Cancer Register",
    "aria": "Aria OIS",
    "endoscopy": "Endoscopy",
}

IMPACT_TABLES = {
    "pas": ["patient", "appointment", "episode"],
    "ice": ["patient", "pathology_result", "pathology_result_value", "histopath_structured"],
    "ris": ["patient", "radiology_result"],
    "somerset": ["referral", "diagnosis", "staging", "cancer_pathway", "cancer_action", "mdt_discussion"],
    "aria": ["appointment", "sact_course", "sact_cycle", "sact_drug", "radiotherapy_course", "radiotherapy_fraction"],
    "endoscopy": ["appointment", "cancer_action"],
}

TABLE_COUNT_QUERIES = {
    "patient": select(func.count()).select_from(Patient),
    "referral": select(func.count()).select_from(Referral),
    "diagnosis": select(func.count()).select_from(Diagnosis),
    "appointment": select(func.count()).select_from(Appointment),
    "episode": select(func.count()).select_from(Episode),
    "pathology_result": select(func.count()).select_from(PathologyResult),
    "radiology_result": select(func.count()).select_from(RadiologyResult),
    "cancer_pathway": select(func.count()).select_from(CancerPathway),
    "cancer_action": select(func.count()).select_from(CancerAction),
    "mdt_discussion": select(func.count()).select_from(MDTDiscussion),
    "sact_course": select(func.count()).select_from(SACTCourse),
    "radiotherapy_course": select(func.count()).select_from(RadiotherapyCourse),
}


@dataclass
class SimulationRunState:
    run_id: str
    request: SimulationRunRequest
    status: str = "queued"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    journeys_generated: int = 0
    total_events: int = 0
    processed_events: int = 0
    failed_events: int = 0
    source_event_counts: dict[str, int] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    created_patients: list[SimulationCreatedPatient] = field(default_factory=list)
    database_deltas: list[SimulationDatabaseDelta] = field(default_factory=list)
    api_checks: list[SimulationApiCheck] = field(default_factory=list)
    stream: list[SimulationStreamEvent] = field(default_factory=list)

    def to_summary(self) -> SimulationRunSummary:
        return SimulationRunSummary(
            run_id=self.run_id,
            status=self.status,
            started_at=self.started_at,
            completed_at=self.completed_at,
            patient_count=self.request.patient_count,
            journeys_generated=self.journeys_generated,
            total_events=self.total_events,
            processed_events=self.processed_events,
            failed_events=self.failed_events,
            source_systems=self.request.source_systems,
            source_event_counts=self.source_event_counts,
        )

    def to_detail(self) -> SimulationRunDetail:
        return SimulationRunDetail(
            **self.to_summary().model_dump(),
            artifacts=self.artifacts,
            database_deltas=self.database_deltas,
            created_patients=self.created_patients,
            api_checks=self.api_checks,
            stream=self.stream,
        )


class SimulationHub:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._runs: dict[str, SimulationRunState] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    def get_catalog(self) -> SimulationCatalogResponse:
        return SimulationCatalogResponse(
            available_sources=list(SOURCE_PRODUCERS.keys()),
            default_sources=list(SOURCE_PRODUCERS.keys()),
            default_patient_count=6,
            recommended_seed=360,
        )

    async def list_runs(self) -> list[SimulationRunSummary]:
        async with self._lock:
            runs = sorted(
                self._runs.values(),
                key=lambda run: run.started_at or datetime.min.replace(tzinfo=UTC),
                reverse=True,
            )
            return [run.to_summary() for run in runs[:20]]

    async def get_run(self, run_id: str) -> SimulationRunDetail | None:
        async with self._lock:
            run = self._runs.get(run_id)
            return run.to_detail() if run else None

    async def start_run(self, request: SimulationRunRequest) -> SimulationRunDetail:
        run_id = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
        state = SimulationRunState(run_id=run_id, request=request)
        async with self._lock:
            self._runs[run_id] = state
            self._tasks[run_id] = asyncio.create_task(self._execute_run(run_id))
        return state.to_detail()

    async def _execute_run(self, run_id: str) -> None:
        async with self._lock:
            run = self._runs[run_id]
            run.status = "running"
            run.started_at = datetime.now(UTC)

        router_store = DatabaseStore(self.settings.database_url)
        router = IntegrationRouter(router_store)
        try:
            artifact_root = REPO_ROOT / ".tmp" / "studio_runs" / run_id
            start_index = await self._next_start_index()
            journeys = build_journeys(
                run.request.patient_count,
                seed=run.request.seed,
                anchor_date=run.request.anchor_date,
                start_index=start_index,
            )
            run.journeys_generated = len(journeys)
            run.created_patients = self._build_created_patients(journeys)

            scenario_path = write_json(artifact_root / "journeys.json", journeys)
            self._append_event(
                run,
                layer="source",
                component="Scenario Engine",
                title=f"Generated {len(journeys)} synthetic patient journeys",
                detail="Each journey contains clinically coherent demographics, pathway dates, and source-system payload context.",
                impact_tables=[],
            )

            events: list[dict[str, Any]] = []
            for source in run.request.source_systems:
                producer = SOURCE_PRODUCERS[source]
                produced = producer(journeys)
                run.source_event_counts[source] = len(produced)
                events.extend(produced)
                self._append_event(
                    run,
                    layer="source",
                    component=SOURCE_LABELS[source],
                    title=f"Prepared {len(produced)} payload events from {SOURCE_LABELS[source]}",
                    detail=self._describe_generated_batch(source, produced),
                    source_system=source,
                    impact_tables=IMPACT_TABLES[source],
                )

            events.sort(key=lambda item: item["timestamp"])
            run.total_events = len(events)
            write_events(events, artifact_root / "payloads")
            write_json(artifact_root / "manifest.json", events)
            run.artifacts = {
                "journeys": str(scenario_path),
                "payload_root": str((artifact_root / "payloads").resolve()),
                "manifest": str((artifact_root / "payloads" / "manifest.json").resolve()),
            }

            before_counts = await self._collect_table_counts()
            self._append_event(
                run,
                layer="integration",
                component="Mirth / TIE Lane",
                title="Starting replay through the integration layer",
                detail="This demo replays events through the native TIE. In production, Mirth would occupy this same orchestration lane.",
                impact_tables=[],
            )

            for event in events:
                await self._process_event(run, router, event)

            after_counts = await self._collect_table_counts()
            run.database_deltas = [
                SimulationDatabaseDelta(
                    table_name=table_name,
                    before_count=before_counts[table_name],
                    after_count=after_counts[table_name],
                    delta=after_counts[table_name] - before_counts[table_name],
                )
                for table_name in TABLE_COUNT_QUERIES
            ]
            self._append_event(
                run,
                layer="database",
                component="PostgreSQL CDM",
                title="Database snapshot captured after replay",
                detail=self._format_database_delta_summary(run.database_deltas),
                impact_tables=[delta.table_name for delta in run.database_deltas if delta.delta > 0],
            )

            run.api_checks = await self._run_api_checks(run.created_patients)
            for check in run.api_checks:
                self._append_event(
                    run,
                    layer="api",
                    component="FastAPI",
                    title=check.name,
                    detail=check.detail,
                    status=check.status,
                    impact_tables=[],
                )

            self._append_event(
                run,
                layer="app",
                component="Cancer 360 Operator Console",
                title="Run complete and ready to inspect",
                detail="Use the patient cards below to open 360 views and confirm the replayed records are visible through the live API.",
                impact_tables=[],
            )
            run.status = "completed"
            run.completed_at = datetime.now(UTC)
        except Exception as exc:
            run.failed_events += 1
            run.status = "failed"
            run.completed_at = datetime.now(UTC)
            self._append_event(
                run,
                layer="integration",
                component="Simulation Runner",
                title="Run failed",
                detail=str(exc),
                status="error",
                impact_tables=[],
            )
        finally:
            await router_store.engine.dispose()

    def _build_created_patients(self, journeys: list[dict[str, Any]]) -> list[SimulationCreatedPatient]:
        patients: list[SimulationCreatedPatient] = []
        for journey in journeys:
            patient = journey["patient"]
            patients.append(
                SimulationCreatedPatient(
                    nhs_number=patient["nhs_number"],
                    patient_name=patient["full_name"],
                    scenario=journey["scenario"],
                    source_pathway_id=journey["somerset"]["pathway_id"],
                    pathway_id=deterministic_uuid("somerset-pathway", journey["somerset"]["pathway_id"]),
                )
            )
        return patients

    def _append_event(
        self,
        run: SimulationRunState,
        *,
        layer: str,
        component: str,
        title: str,
        detail: str,
        status: str = "success",
        source_system: str | None = None,
        message_type: str | None = None,
        file_name: str | None = None,
        payload_preview: str | None = None,
        impact_tables: list[str] | None = None,
    ) -> None:
        run.stream.append(
            SimulationStreamEvent(
                timestamp=datetime.now(UTC),
                layer=layer,
                component=component,
                title=title,
                detail=detail,
                status=status,
                source_system=source_system,
                message_type=message_type,
                file_name=file_name,
                payload_preview=payload_preview,
                impact_tables=impact_tables or [],
            )
        )

    def _describe_generated_batch(self, source: str, events: list[dict[str, Any]]) -> str:
        if not events:
            return "No payloads were generated for this source because the selected journeys did not need it."
        formats = {}
        for event in events:
            formats[event["format"]] = formats.get(event["format"], 0) + 1
        fragments = [f"{count} {fmt.upper()}" for fmt, count in formats.items()]
        return f"Generated {' and '.join(fragments)} payloads that will flow into the integration layer and then the Cancer 360 database."

    async def _process_event(self, run: SimulationRunState, router: IntegrationRouter, event: dict[str, Any]) -> None:
        title, detail, message_type, payload_preview = self._describe_payload(event)
        self._append_event(
            run,
            layer="source",
            component=SOURCE_LABELS.get(event["source"], event["source"].upper()),
            title=title,
            detail=detail,
            source_system=event["source"],
            message_type=message_type,
            file_name=event["filename"],
            payload_preview=payload_preview,
            impact_tables=IMPACT_TABLES.get(event["source"], []),
        )
        if event["format"] == "hl7":
            ack = await router.handle_hl7(event["payload"])
            run.processed_events += 1
            self._append_event(
                run,
                layer="integration",
                component="Native TIE / Mirth-equivalent",
                title=f"Accepted {message_type or 'HL7'} from {SOURCE_LABELS.get(event['source'], event['source'])}",
                detail=f"The integration layer parsed `{event['filename']}` and returned ACK `{ack.split(chr(13))[1] if ack else 'NO_ACK'}` before writing the target rows.",
                source_system=event["source"],
                message_type=message_type,
                file_name=event["filename"],
                payload_preview=payload_preview,
                impact_tables=IMPACT_TABLES.get(event["source"], []),
            )
        else:
            await router.handle_file_payload(event["filename"], event["payload"])
            run.processed_events += 1
            self._append_event(
                run,
                layer="integration",
                component="Native TIE / Mirth-equivalent",
                title=f"Processed file drop from {SOURCE_LABELS.get(event['source'], event['source'])}",
                detail=f"The integration layer consumed `{event['filename']}` as a watched-file payload and upserted the corresponding CDM entities.",
                source_system=event["source"],
                file_name=event["filename"],
                payload_preview=payload_preview,
                impact_tables=IMPACT_TABLES.get(event["source"], []),
            )
        self._append_event(
            run,
            layer="database",
            component="PostgreSQL CDM",
            title=f"Applied upserts for {SOURCE_LABELS.get(event['source'], event['source'])}",
            detail=f"Rows were written or updated in {', '.join(IMPACT_TABLES.get(event['source'], []))}. These records are now available to the API and patient views.",
            source_system=event["source"],
            message_type=message_type,
            file_name=event["filename"],
            payload_preview=payload_preview,
            impact_tables=IMPACT_TABLES.get(event["source"], []),
        )

    def _describe_payload(self, event: dict[str, Any]) -> tuple[str, str, str | None, str]:
        if event["format"] == "hl7":
            parsed = parse_hl7(event["payload"])
            patient = parsed.get("patient", {})
            message_type = parsed.get("message_type")
            patient_text = patient.get("nhs_number") or "unknown patient"
            preview = self._preview_hl7(event["payload"])
            return (
                f"Emitted {message_type} for NHS {patient_text}",
                f"`{event['filename']}` left {SOURCE_LABELS.get(event['source'], event['source'])} and entered the integration lane carrying a real-looking HL7 message.",
                message_type,
                preview,
            )

        rows = read_csv_rows(event["payload"])
        if rows and "nhs_number" in rows[0]:
            sample = ", ".join(row.get("nhs_number", "") for row in rows[:3] if row.get("nhs_number"))
            detail = f"`{event['filename']}` contains {len(rows)} rows. Sample NHS numbers: {sample or 'not present in this extract'}."
        else:
            detail = f"`{event['filename']}` contains {len(rows)} rows and is ready for watched-folder ingestion."
        preview = self._preview_csv(event["payload"])
        return (
            f"Prepared file extract `{event['filename']}`",
            detail,
            None,
            preview,
        )

    def _preview_hl7(self, payload: str) -> str:
        segments = [segment for segment in payload.split("\r") if segment][:8]
        return "\n".join(segments)

    def _preview_csv(self, payload: str) -> str:
        lines = [line for line in payload.splitlines() if line][:4]
        return "\n".join(lines)

    async def _collect_table_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        async with async_session_factory() as session:
            for table_name, query in TABLE_COUNT_QUERIES.items():
                counts[table_name] = int(await session.scalar(query) or 0)
        return counts

    async def _next_start_index(self) -> int:
        async with async_session_factory() as session:
            total_patients = int(await session.scalar(select(func.count()).select_from(Patient)) or 0)
        return total_patients + 1

    def _format_database_delta_summary(self, deltas: list[SimulationDatabaseDelta]) -> str:
        changed = [f"{delta.table_name}: +{delta.delta}" for delta in deltas if delta.delta > 0]
        return ", ".join(changed) if changed else "No table counts changed during this run."

    async def _run_api_checks(self, patients: list[SimulationCreatedPatient]) -> list[SimulationApiCheck]:
        checks: list[SimulationApiCheck] = []
        async with async_session_factory() as session:
            svc = PTLService(session)
            dashboard = await svc.get_dashboard()
            checks.append(
                SimulationApiCheck(
                    name="Dashboard metrics refreshed",
                    status="success",
                    detail=f"Dashboard now reports {dashboard.total_pathways} total pathways and {dashboard.active_pathways} active pathways.",
                )
            )
            integration = await svc.get_integration_status()
            checks.append(
                SimulationApiCheck(
                    name="Integration status available",
                    status="success",
                    detail=f"Audit log now contains {integration.audit_total} processed integration events with {integration.dlq_pending} pending DLQ rows.",
                )
            )
            if patients:
                patient_360 = await svc.get_patient_360(patients[0].nhs_number)
                if patient_360:
                    checks.append(
                        SimulationApiCheck(
                            name=f"Patient 360 available for {patients[0].nhs_number}",
                            status="success",
                            detail=f"Patient 360 returned {len(patient_360.timeline)} timeline events, {len(patient_360.pathology_results)} pathology results, and {len(patient_360.actions)} actions.",
                        )
                    )
                else:
                    checks.append(
                        SimulationApiCheck(
                            name=f"Patient 360 missing for {patients[0].nhs_number}",
                            status="error",
                            detail="The synthetic patient could not be read back through the API layer.",
                        )
                    )
        return checks


simulation_hub = SimulationHub()
