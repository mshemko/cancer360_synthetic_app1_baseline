"""Patient Tracking List service — core query logic for Cancer 360."""

from collections import defaultdict
import json
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy import select, func, case, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    CancerPathway, Patient, Referral, Diagnosis, Staging,
    PathologyResult, RadiologyResult, SACTCourse, SACTCycle, RadiotherapyCourse,
    MDTDiscussion, CancerAction, Episode, Appointment,
)
from app.schemas import (
    PTLRow, PTLSummary, PTLResponse, Patient360Response,
    PatientDetail, ReferralSchema, DiagnosisSchema, StagingSchema,
    PathologyResultSchema, RadiologyResultSchema, SACTCourseSchema,
    RTCourseSchema, MDTDiscussionSchema, ActionSchema,
    PathwayTimelineEvent, DashboardMetrics, SearchResult,
    ServiceOverviewResponse, ServiceOverviewTeamResponse, ServiceOverviewTrendingResponse,
    IntegrationStatusResponse, IntegrationSourceStatus, IntegrationIssue,
    DrawerSectionCount, PathwayDrawerAction, PathwayDrawerAppointment,
    PathwayDrawerDetail, PathwayDrawerHistoryItem, PathwayDrawerIPT,
    PathwayDrawerMdtMeeting, PathwayDrawerMdtNote, PathwayDrawerProcedure,
    PathwayDrawerReport, PathwayDrawerResponse, PathwayDrawerTestResult,
    PathwayDrawerTrackingComment,
    ActionDetailResponse, ActionsKpiSummary, ActionUpdateItem,
    ActionUpdatesResponse, ActionWorklistResponse, ActionWorklistRow,
)

CANCER_SUB_SITE_MAP = {
    "breast": "Breast",
    "colorectal": "Colon",
    "gynae": "Ovarian",
    "haem": "Lymphoma",
    "haematology": "Lymphoma",
    "lung": "Lung",
    "prostate": "Prostate",
    "skin": "Melanoma",
    "upper_gi": "Oesophagus",
    "urology": "Bladder",
}

HOSPITAL_SITE_MAP = {
    "1": "Site 1",
    "3": "Site 1",
    "5": "Site 1",
    "7": "Site 1",
    "9": "Site 1",
    "0": "Site 2",
    "2": "Site 2",
    "4": "Site 2",
    "6": "Site 2",
    "8": "Site 2",
}

ACTION_EVENT_MARKER = "[[C360_EVENT]]"


class PTLService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_ptl(
        self,
        cancer_type: Optional[str] = None,
        pathway_status: Optional[str] = None,
        breach_risk: Optional[str] = None,
        assigned_team: Optional[str] = None,
        hospital_site: Optional[str] = None,
        pathway_type: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "breach_risk",
        page: int = 1,
        per_page: int = 50,
    ) -> PTLResponse:
        """Query the cancer patient tracking list with filters and pagination."""

        query = (
            select(CancerPathway)
            .join(Patient, CancerPathway.patient_id == Patient.patient_id)
            .options(selectinload(CancerPathway.patient))
        )

        # Apply filters
        if cancer_type:
            query = query.where(CancerPathway.cancer_type_code == cancer_type)
        if pathway_status:
            query = query.where(CancerPathway.pathway_status == pathway_status)
        if breach_risk:
            query = query.where(CancerPathway.breach_risk == breach_risk)
        if assigned_team:
            query = query.where(CancerPathway.assigned_team == assigned_team)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Patient.surname.ilike(search_term),
                    Patient.forename.ilike(search_term),
                    Patient.nhs_number.like(search_term),
                    Patient.hospital_number.ilike(search_term),
                )
            )

        results = await self.db.execute(query)
        pathways = results.scalars().all()
        related = await self._load_related_context(pathways)
        items = [self._build_ptl_row(pathway, pathway.patient, related) for pathway in pathways]

        if hospital_site:
            hospital_site_normalized = hospital_site.strip().lower()
            items = [
                item for item in items
                if (item.hospital_site or "").lower() == hospital_site_normalized
            ]

        if pathway_type:
            pathway_type_normalized = pathway_type.strip().lower()
            items = [
                item for item in items
                if self._derive_pathway_type_from_row(item).lower() == pathway_type_normalized
            ]

        items = self._sort_ptl_rows(items, sort_by)
        total = len(items)
        start = max((page - 1) * per_page, 0)
        items = items[start:start + per_page]

        summary = await self._get_summary(cancer_type, assigned_team)

        return PTLResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            summary=summary,
        )

    async def _load_related_context(self, pathways: list[CancerPathway]) -> dict:
        if not pathways:
            return {
                "actions_by_pathway": defaultdict(list),
                "actions_by_patient": defaultdict(list),
                "appointments_by_patient": defaultdict(list),
                "episodes_by_patient": defaultdict(list),
                "pathology_by_patient": defaultdict(list),
                "radiology_by_patient": defaultdict(list),
                "mdt_by_patient": defaultdict(list),
            }

        patient_ids = [pathway.patient_id for pathway in pathways]
        pathway_ids = [pathway.pathway_id for pathway in pathways]

        action_result = await self.db.execute(
            select(CancerAction)
            .where(
                or_(
                    CancerAction.pathway_id.in_(pathway_ids),
                    and_(
                        CancerAction.pathway_id.is_(None),
                        CancerAction.patient_id.in_(patient_ids),
                    ),
                )
            )
            .order_by(CancerAction.updated_at.desc(), CancerAction.created_at.desc())
        )
        appointment_result = await self.db.execute(
            select(Appointment)
            .where(Appointment.patient_id.in_(patient_ids))
            .order_by(Appointment.appointment_date.desc())
        )
        episode_result = await self.db.execute(
            select(Episode)
            .where(Episode.patient_id.in_(patient_ids))
            .order_by(Episode.procedure_date.desc(), Episode.admission_date.desc())
        )
        pathology_result = await self.db.execute(
            select(PathologyResult)
            .options(selectinload(PathologyResult.values), selectinload(PathologyResult.histopath))
            .where(PathologyResult.patient_id.in_(patient_ids))
            .order_by(PathologyResult.report_date.desc())
        )
        radiology_result = await self.db.execute(
            select(RadiologyResult)
            .where(RadiologyResult.patient_id.in_(patient_ids))
            .order_by(RadiologyResult.exam_date.desc())
        )
        mdt_result = await self.db.execute(
            select(MDTDiscussion)
            .where(MDTDiscussion.patient_id.in_(patient_ids))
            .order_by(MDTDiscussion.mdt_date.desc())
        )

        actions_by_pathway = defaultdict(list)
        actions_by_patient = defaultdict(list)
        for action in action_result.scalars().all():
            actions_by_patient[action.patient_id].append(action)
            if action.pathway_id:
                actions_by_pathway[action.pathway_id].append(action)

        appointments_by_patient = defaultdict(list)
        for appointment in appointment_result.scalars().all():
            appointments_by_patient[appointment.patient_id].append(appointment)

        episodes_by_patient = defaultdict(list)
        for episode in episode_result.scalars().all():
            episodes_by_patient[episode.patient_id].append(episode)

        pathology_by_patient = defaultdict(list)
        for result in pathology_result.scalars().all():
            pathology_by_patient[result.patient_id].append(result)

        radiology_by_patient = defaultdict(list)
        for result in radiology_result.scalars().all():
            radiology_by_patient[result.patient_id].append(result)

        mdt_by_patient = defaultdict(list)
        for discussion in mdt_result.scalars().all():
            mdt_by_patient[discussion.patient_id].append(discussion)

        return {
            "actions_by_pathway": actions_by_pathway,
            "actions_by_patient": actions_by_patient,
            "appointments_by_patient": appointments_by_patient,
            "episodes_by_patient": episodes_by_patient,
            "pathology_by_patient": pathology_by_patient,
            "radiology_by_patient": radiology_by_patient,
            "mdt_by_patient": mdt_by_patient,
        }

    def _build_ptl_row(self, pathway: CancerPathway, patient: Patient, related: dict) -> PTLRow:
        actions = self._select_actions_for_pathway(pathway, related)
        appointments = related["appointments_by_patient"].get(pathway.patient_id, [])
        episodes = related["episodes_by_patient"].get(pathway.patient_id, [])
        pathology = related["pathology_by_patient"].get(pathway.patient_id, [])
        radiology = related["radiology_by_patient"].get(pathway.patient_id, [])
        mdt_discussions = related["mdt_by_patient"].get(pathway.patient_id, [])
        navigation_actions = [
            action for action in actions
            if (action.source_system or "").lower() in {"somerset", "endoscopy"}
        ]
        ipt_actions = [
            action for action in navigation_actions
            if "inter-provider" in (action.action_type or "").lower()
            or "ipt" in ((action.notes or "") + " " + (action.action_description or "")).lower()
        ]
        latest_action = actions[0] if actions else None
        recent_action_update = self._is_recent_action(latest_action)
        tags = self._build_pathway_tags(pathway, actions, pathology)

        return PTLRow(
            pathway_id=pathway.pathway_id,
            patient_id=pathway.patient_id,
            nhs_number=patient.nhs_number,
            patient_name=f"{patient.surname}, {patient.forename}",
            hospital_number=patient.hospital_number,
            date_of_birth=patient.date_of_birth,
            sex=patient.sex,
            age=self._calculate_age(patient.date_of_birth),
            cancer_type_code=pathway.cancer_type_code,
            cancer_type_desc=pathway.cancer_type_desc,
            cancer_site=pathway.cancer_type_desc or pathway.cancer_type_code,
            cancer_sub_site=self._derive_cancer_sub_site(pathway),
            hospital_site=self._derive_hospital_site(patient),
            stage_group=None,
            grade=None,
            date_referral_received=pathway.date_referral_received,
            days_on_pathway=self._days_since(pathway.date_referral_received),
            date_diagnosis=pathway.date_diagnosis,
            days_to_diagnosis=pathway.days_to_diagnosis,
            fds_28day_met=pathway.fds_28day_met,
            date_first_treatment=pathway.date_first_treatment,
            days_to_treatment=pathway.days_to_treatment,
            standard_62day_met=pathway.standard_62day_met,
            pathway_status=pathway.pathway_status,
            current_stage_label=pathway.current_stage_label,
            next_action=pathway.next_action,
            next_action_date=pathway.next_action_date,
            assigned_team=pathway.assigned_team,
            breach_risk=pathway.breach_risk,
            treatment_modality=pathway.treatment_modality,
            open_action_count=len([action for action in actions if (action.status or "").lower() != "completed"]),
            latest_action=(latest_action.action_type if latest_action else pathway.next_action),
            recent_action_update=recent_action_update,
            latest_tracking_comment=self._latest_tracking_comment(navigation_actions, latest_action, pathway),
            breach_date_28=self._offset_date(pathway.date_referral_received, 28),
            breach_date_31=self._offset_date(pathway.date_referral_received, 31),
            breach_date_62=self._offset_date(pathway.date_referral_received, 62),
            first_outpatient_attended_date=self._first_appointment_date(appointments),
            next_outpatient_attended_date=self._next_appointment_date(appointments),
            latest_histology_attended_date=self._latest_histology_date(pathology),
            latest_radiology_attended_date=self._latest_radiology_date(radiology),
            latest_inpatient_encounter_tci_date=self._latest_episode_date(episodes),
            latest_mdt_status=self._latest_mdt_status(mdt_discussions),
            latest_ipt_date=self._latest_ipt_date(ipt_actions),
            tags=tags,
            watchlist_reason=self._watchlist_reason(pathway, tags),
        )

    def _sort_ptl_rows(self, rows: list[PTLRow], sort_by: str) -> list[PTLRow]:
        breach_rank = {"breached": 0, "high": 1, "medium": 2, "low": 3, "none": 4}
        if sort_by == "name":
            return sorted(rows, key=lambda row: row.patient_name)
        if sort_by == "days":
            return sorted(rows, key=lambda row: row.days_on_pathway or -1, reverse=True)
        return sorted(
            rows,
            key=lambda row: (
                breach_rank.get((row.breach_risk or "").lower(), 99),
                -(row.days_on_pathway or 0),
                row.patient_name,
            ),
        )

    def _select_actions_for_pathway(self, pathway: CancerPathway, related: dict) -> list[CancerAction]:
        pathway_actions = related["actions_by_pathway"].get(pathway.pathway_id, [])
        return pathway_actions or related["actions_by_patient"].get(pathway.patient_id, [])

    def _calculate_age(self, dob: date) -> int:
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def _days_since(self, value: Optional[date]) -> Optional[int]:
        if not value:
            return None
        return (date.today() - value).days

    def _offset_date(self, value: Optional[date], days: int) -> Optional[date]:
        if not value:
            return None
        return date.fromordinal(value.toordinal() + days)

    def _derive_cancer_sub_site(self, pathway: CancerPathway) -> Optional[str]:
        code = (pathway.cancer_type_code or pathway.cancer_type_desc or "").lower()
        return CANCER_SUB_SITE_MAP.get(code, pathway.cancer_type_desc)

    def _derive_hospital_site(self, patient: Patient) -> str:
        return HOSPITAL_SITE_MAP.get(patient.nhs_number[-1], "Site 1")

    def _derive_pathway_type_from_row(self, row: PTLRow) -> str:
        if row.standard_62day_met is not None or row.date_first_treatment or row.days_to_treatment is not None:
            return "62 Day"
        if row.fds_28day_met is not None:
            return "28 Day"
        return "31 Day"

    def _is_recent_action(self, action: Optional[CancerAction]) -> bool:
        if not action or not action.updated_at:
            return False
        return (datetime.utcnow() - action.updated_at.replace(tzinfo=None)).days <= 2

    def _first_appointment_date(self, appointments: list[Appointment]) -> Optional[date]:
        dates = [appointment.appointment_date for appointment in appointments if appointment.appointment_date]
        return min(dates) if dates else None

    def _next_appointment_date(self, appointments: list[Appointment]) -> Optional[date]:
        today = date.today()
        future_dates = [
            appointment.appointment_date
            for appointment in appointments
            if appointment.appointment_date and appointment.appointment_date >= today
        ]
        return min(future_dates) if future_dates else None

    def _latest_histology_date(self, pathology: list[PathologyResult]) -> Optional[date]:
        dates = [
            self._as_date(result.report_date) or self._as_date(result.specimen_date)
            for result in pathology
            if "histo" in (result.discipline or "").lower() or "cyto" in (result.discipline or "").lower()
        ]
        dates = [value for value in dates if value]
        return max(dates) if dates else None

    def _latest_radiology_date(self, radiology: list[RadiologyResult]) -> Optional[date]:
        dates = [self._as_date(result.exam_date) for result in radiology if result.exam_date]
        dates = [value for value in dates if value]
        return max(dates) if dates else None

    def _latest_episode_date(self, episodes: list[Episode]) -> Optional[date]:
        dates = [
            episode.procedure_date or episode.admission_date
            for episode in episodes
            if episode.procedure_date or episode.admission_date
        ]
        return max(dates) if dates else None

    def _latest_mdt_status(self, discussions: list[MDTDiscussion]) -> Optional[str]:
        if not discussions:
            return None
        return "MDT Booked" if discussions[0].mdt_date and discussions[0].mdt_date > date.today() else "MDT Attended"

    def _latest_ipt_date(self, ipt_actions: list[CancerAction]) -> Optional[date]:
        dates = [
            action.due_date or self._as_date(action.created_at)
            for action in ipt_actions
            if action.due_date or action.created_at
        ]
        dates = [value for value in dates if value]
        return max(dates) if dates else None

    def _latest_tracking_comment(
        self,
        navigation_actions: list[CancerAction],
        latest_action: Optional[CancerAction],
        pathway: CancerPathway,
    ) -> Optional[str]:
        comment_source = navigation_actions[0] if navigation_actions else latest_action
        if comment_source:
            return comment_source.notes or comment_source.action_description or comment_source.action_type
        return pathway.next_action

    def _build_pathway_tags(
        self,
        pathway: CancerPathway,
        actions: list[CancerAction],
        pathology: list[PathologyResult],
    ) -> list[str]:
        tags = []
        if any(
            (action.status or "").lower() != "completed"
            and action.due_date
            and (date.today() - action.due_date).days > 5
            for action in actions
        ):
            tags.append("Open actions > 5 days")
        if self._is_recent_action(actions[0] if actions else None):
            tags.append("Actions updated in the last 48h")
        has_histology = any(
            "histo" in (result.discipline or "").lower() or "cyto" in (result.discipline or "").lower()
            for result in pathology
        )
        if not has_histology and (self._days_since(pathway.date_referral_received) or 0) > 12:
            tags.append("Unreported Histology On >12 Day Old Pathway")
        return tags

    def _watchlist_reason(self, pathway: CancerPathway, tags: list[str]) -> Optional[str]:
        days_on = self._days_since(pathway.date_referral_received) or 0
        if days_on >= 105:
            return "105+ day pathway"
        if pathway.breach_risk in {"high", "breached"}:
            return f"{pathway.breach_risk.title()} breach risk"
        if tags:
            return tags[0]
        return None

    def _as_date(self, value) -> Optional[date]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        return value

    async def _get_summary(
        self,
        cancer_type: Optional[str] = None,
        assigned_team: Optional[str] = None,
    ) -> PTLSummary:
        """Compute aggregate summary statistics for the PTL."""
        base = select(CancerPathway)
        if cancer_type:
            base = base.where(CancerPathway.cancer_type_code == cancer_type)
        if assigned_team:
            base = base.where(CancerPathway.assigned_team == assigned_team)

        sub = base.subquery()

        total = await self.db.scalar(select(func.count()).select_from(sub)) or 0
        breached = await self.db.scalar(
            select(func.count()).select_from(sub).where(sub.c.breach_risk == "breached")
        ) or 0
        high = await self.db.scalar(
            select(func.count()).select_from(sub).where(sub.c.breach_risk == "high")
        ) or 0
        medium = await self.db.scalar(
            select(func.count()).select_from(sub).where(sub.c.breach_risk == "medium")
        ) or 0

        status_counts = {}
        for s in ["awaiting_diagnostics", "awaiting_mdt", "awaiting_treatment",
                   "on_treatment", "active_monitoring", "completed"]:
            status_counts[s] = await self.db.scalar(
                select(func.count()).select_from(sub).where(sub.c.pathway_status == s)
            ) or 0

        # Performance calculations
        fds_denom = await self.db.scalar(
            select(func.count()).select_from(sub).where(sub.c.date_diagnosis.isnot(None))
        ) or 0
        fds_num = await self.db.scalar(
            select(func.count()).select_from(sub).where(
                and_(sub.c.date_diagnosis.isnot(None), sub.c.fds_28day_met == True)
            )
        ) or 0
        rtt_denom = await self.db.scalar(
            select(func.count()).select_from(sub).where(sub.c.date_first_treatment.isnot(None))
        ) or 0
        rtt_num = await self.db.scalar(
            select(func.count()).select_from(sub).where(
                and_(sub.c.date_first_treatment.isnot(None), sub.c.standard_62day_met == True)
            )
        ) or 0

        return PTLSummary(
            total=total,
            breached=breached,
            high_risk=high,
            medium_risk=medium,
            awaiting_diagnostics=status_counts.get("awaiting_diagnostics", 0),
            awaiting_mdt=status_counts.get("awaiting_mdt", 0),
            awaiting_treatment=status_counts.get("awaiting_treatment", 0),
            on_treatment=status_counts.get("on_treatment", 0),
            active_monitoring=status_counts.get("active_monitoring", 0),
            completed=status_counts.get("completed", 0),
            fds_28d_performance=round(fds_num / fds_denom * 100, 1) if fds_denom > 0 else None,
            rtt_62d_performance=round(rtt_num / rtt_denom * 100, 1) if rtt_denom > 0 else None,
        )

    async def get_patient_360(self, nhs_number: str) -> Optional[Patient360Response]:
        """Get the full 360° view for a single patient."""

        # Patient
        result = await self.db.execute(
            select(Patient).where(Patient.nhs_number == nhs_number.replace(" ", ""))
        )
        patient = result.scalar_one_or_none()
        if not patient:
            return None

        pid = patient.patient_id

        # Referral
        ref_result = await self.db.execute(
            select(Referral).where(Referral.patient_id == pid).order_by(Referral.receipt_date.desc()).limit(1)
        )
        referral = ref_result.scalar_one_or_none()

        # Diagnosis
        diag_result = await self.db.execute(
            select(Diagnosis).where(Diagnosis.patient_id == pid).order_by(Diagnosis.diagnosis_date.desc()).limit(1)
        )
        diagnosis = diag_result.scalar_one_or_none()

        # Staging
        staging = None
        if diagnosis:
            stg_result = await self.db.execute(
                select(Staging).where(Staging.diagnosis_id == diagnosis.diagnosis_id).order_by(Staging.staging_date.desc()).limit(1)
            )
            staging = stg_result.scalar_one_or_none()

        # Pathway
        pw_result = await self.db.execute(
            select(CancerPathway).where(CancerPathway.patient_id == pid).order_by(CancerPathway.created_at.desc()).limit(1)
        )
        pathway = pw_result.scalar_one_or_none()

        # Pathology
        path_result = await self.db.execute(
            select(PathologyResult)
            .options(selectinload(PathologyResult.values), selectinload(PathologyResult.histopath))
            .where(PathologyResult.patient_id == pid)
            .order_by(PathologyResult.report_date.desc())
        )
        pathology_results = path_result.scalars().all()

        # Radiology
        rad_result = await self.db.execute(
            select(RadiologyResult).where(RadiologyResult.patient_id == pid).order_by(RadiologyResult.exam_date.desc())
        )
        radiology_results = rad_result.scalars().all()

        # SACT
        sact_result = await self.db.execute(
            select(SACTCourse)
            .options(selectinload(SACTCourse.cycles).selectinload(SACTCycle.drugs))
            .where(SACTCourse.patient_id == pid)
            .order_by(SACTCourse.start_date.desc())
        )
        sact_courses = sact_result.scalars().all()

        # RT
        rt_result = await self.db.execute(
            select(RadiotherapyCourse)
            .options(selectinload(RadiotherapyCourse.fractions))
            .where(RadiotherapyCourse.patient_id == pid)
            .order_by(RadiotherapyCourse.first_fraction_date.desc())
        )
        rt_courses = rt_result.scalars().all()

        # MDT
        mdt_result = await self.db.execute(
            select(MDTDiscussion).where(MDTDiscussion.patient_id == pid).order_by(MDTDiscussion.mdt_date.desc())
        )
        mdt_discussions = mdt_result.scalars().all()

        # Actions
        act_result = await self.db.execute(
            select(CancerAction).where(CancerAction.patient_id == pid).order_by(CancerAction.created_at.desc())
        )
        actions = act_result.scalars().all()
        navigation_actions = [a for a in actions if (a.source_system or "").lower() in {"somerset", "endoscopy"}]

        # Build timeline
        timeline = self._build_timeline(pathway, referral, diagnosis, pathology_results, radiology_results, mdt_discussions, sact_courses, rt_courses)

        # Calculate age
        today = date.today()
        age = today.year - patient.date_of_birth.year - (
            (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
        )

        patient_detail = PatientDetail.model_validate(patient)
        patient_detail.age = age

        return Patient360Response(
            patient=patient_detail,
            referral=ReferralSchema.model_validate(referral) if referral else None,
            diagnosis=DiagnosisSchema.model_validate(diagnosis) if diagnosis else None,
            staging=StagingSchema.model_validate(staging) if staging else None,
            pathway=self._pathway_to_row(pathway, patient) if pathway else None,
            timeline=timeline,
            pathology_results=[PathologyResultSchema.model_validate(r) for r in pathology_results],
            radiology_results=[RadiologyResultSchema.model_validate(r) for r in radiology_results],
            sact_courses=[SACTCourseSchema.model_validate(c) for c in sact_courses],
            rt_courses=[RTCourseSchema.model_validate(c) for c in rt_courses],
            mdt_discussions=[MDTDiscussionSchema.model_validate(m) for m in mdt_discussions],
            actions=[ActionSchema.model_validate(a) for a in actions],
            navigation_actions=[ActionSchema.model_validate(a) for a in navigation_actions],
        )

    async def get_pathway_drawer(self, pathway_id: UUID) -> Optional[PathwayDrawerResponse]:
        pathway_result = await self.db.execute(
            select(CancerPathway)
            .join(Patient, CancerPathway.patient_id == Patient.patient_id)
            .options(selectinload(CancerPathway.patient))
            .where(CancerPathway.pathway_id == pathway_id)
        )
        pathway = pathway_result.scalar_one_or_none()
        if not pathway:
            return None

        patient = pathway.patient
        related = await self._load_related_context([pathway])
        pathway_row = self._build_ptl_row(pathway, patient, related)
        patient_360 = await self.get_patient_360(patient.nhs_number)
        if not patient_360:
            return None

        actions = self._select_actions_for_pathway(pathway, related)
        appointments = related["appointments_by_patient"].get(pathway.patient_id, [])
        episodes = related["episodes_by_patient"].get(pathway.patient_id, [])
        pathology = related["pathology_by_patient"].get(pathway.patient_id, [])
        radiology = related["radiology_by_patient"].get(pathway.patient_id, [])
        mdt_discussions = related["mdt_by_patient"].get(pathway.patient_id, [])
        navigation_actions = [
            action for action in actions
            if (action.source_system or "").lower() in {"somerset", "endoscopy"}
        ]
        ipt_actions = [
            action for action in navigation_actions
            if "inter-provider" in (action.action_type or "").lower()
            or "ipt" in ((action.notes or "") + " " + (action.action_description or "")).lower()
        ]
        tracking_actions = [
            action for action in navigation_actions
            if action not in ipt_actions
        ]

        drawer_actions = [self._build_drawer_action(action) for action in actions]
        outpatient = [self._build_drawer_appointment(pathway, appointment) for appointment in appointments]
        inpatient = [self._build_drawer_procedure(episode) for episode in episodes]
        histology = [self._build_drawer_histology_report(result) for result in pathology if self._is_histology_result(result)]
        radiology_reports = [self._build_drawer_radiology_report(result) for result in radiology]
        mdt_notes = [self._build_drawer_mdt_meeting(discussion) for discussion in mdt_discussions]
        test_results = self._build_drawer_test_results(pathology)
        ipt = [self._build_drawer_ipt(action, pathway_row.days_on_pathway) for action in ipt_actions]
        tracking_comments = self._build_tracking_comments(tracking_actions, actions)

        section_counts = [
            DrawerSectionCount(key="pathway-details", label="Pathway Details", count=1),
            DrawerSectionCount(key="actions", label="Actions", count=len(drawer_actions)),
            DrawerSectionCount(key="outpatient", label="Outpatient Appointments", count=len(outpatient)),
            DrawerSectionCount(key="inpatient", label="Inpatient Procedures", count=len(inpatient)),
            DrawerSectionCount(key="histology", label="Histology", count=len(histology)),
            DrawerSectionCount(key="radiology", label="Radiology", count=len(radiology_reports)),
            DrawerSectionCount(key="mdt", label="MDT Notes", count=len(mdt_notes)),
            DrawerSectionCount(key="tests", label="Test Results", count=len(test_results)),
            DrawerSectionCount(key="ipt", label="IPT", count=len(ipt)),
            DrawerSectionCount(key="tracking", label="Tracking Comments", count=len(tracking_comments)),
            DrawerSectionCount(key="patient", label="Patient", count=1),
        ]

        return PathwayDrawerResponse(
            pathway=pathway_row,
            last_updated=pathway.updated_at or patient.updated_at or datetime.utcnow(),
            section_counts=section_counts,
            details=PathwayDrawerDetail(
                pathway_status="Benign" if pathway.pathway_status in {"completed", "active_monitoring"} else "Suspected",
                pathway_type=self._derive_pathway_type_from_row(pathway_row),
                days_since_adjusted_pathway_start=pathway_row.days_on_pathway,
                cancer_site=pathway_row.cancer_site,
                cancer_sub_site=pathway_row.cancer_sub_site,
                hospital_site=pathway_row.hospital_site,
                full_name=pathway_row.patient_name,
                nhs_number=pathway_row.nhs_number,
                mrn=pathway_row.hospital_number,
                phone_number=patient.phone,
                date_of_birth=patient.date_of_birth,
                adjusted_pathway_start_date=pathway.date_referral_received,
                original_pathway_start_date=pathway.date_referral_received,
                pathway_closed_date=pathway.date_first_treatment if pathway.pathway_status == "completed" else None,
                breach_date_28=pathway_row.breach_date_28,
                breach_date_31=pathway_row.breach_date_31,
                breach_date_62=pathway_row.breach_date_62,
                watchlist_reason=pathway_row.watchlist_reason,
                tags=pathway_row.tags,
            ),
            milestones=patient_360.timeline,
            actions=drawer_actions,
            outpatient_appointments=outpatient,
            inpatient_procedures=inpatient,
            histology=histology,
            radiology=radiology_reports,
            mdt_notes=mdt_notes,
            test_results=test_results,
            ipt=ipt,
            tracking_comments=tracking_comments,
            patient_360=patient_360,
        )

    def _build_drawer_action(self, action: CancerAction) -> PathwayDrawerAction:
        history = [
            PathwayDrawerHistoryItem(
                timestamp=action.created_at,
                event_type="CREATE ACTION",
                title=action.action_type,
                detail=action.action_description or action.notes,
                actor=action.created_by,
                tone="success",
            )
        ]
        if action.notes:
            history.append(
                PathwayDrawerHistoryItem(
                    timestamp=action.updated_at or action.created_at,
                    event_type="COMMENT",
                    title="General Comment",
                    detail=action.notes,
                    actor=action.created_by,
                    tone="comment",
                )
            )
        if action.assigned_user:
            history.append(
                PathwayDrawerHistoryItem(
                    timestamp=action.updated_at or action.created_at,
                    event_type="ASSIGN TO USER",
                    title="Assignment updated",
                    detail=f"Assigned to {action.assigned_user}",
                    actor=action.created_by,
                    tone="info",
                )
            )
        if action.completed_date:
            history.append(
                PathwayDrawerHistoryItem(
                    timestamp=action.completed_date,
                    event_type="COMPLETE ACTION",
                    title="Action completed",
                    detail=action.notes,
                    actor=action.completed_by,
                    tone="success",
                )
            )
        history.sort(key=lambda item: item.timestamp, reverse=True)
        return PathwayDrawerAction(
            action_id=action.action_id,
            title=action.action_type,
            due_date=action.due_date,
            status=action.status.title(),
            detail=action.action_description or action.notes,
            owner=action.assigned_user or action.assigned_team,
            priority=action.priority,
            source_system=action.source_system,
            history=history,
        )

    def _build_drawer_appointment(
        self,
        pathway: CancerPathway,
        appointment: Appointment,
    ) -> PathwayDrawerAppointment:
        attended_date = None
        if (appointment.attendance_status or "").lower() in {"attended", "completed"}:
            attended_date = appointment.appointment_date
        return PathwayDrawerAppointment(
            record_id=str(appointment.appointment_id),
            name=appointment.clinic_name or appointment.location or appointment.appointment_type or "Outpatient appointment",
            status=appointment.attendance_status,
            ordered_date=pathway.date_referral_received,
            scheduled_date=appointment.appointment_date,
            attended_date=attended_date,
            specialty_name=appointment.specialty_code,
            consultant_name=appointment.consultant_name,
            source_system=appointment.source_system,
        )

    def _build_drawer_procedure(self, episode: Episode) -> PathwayDrawerProcedure:
        return PathwayDrawerProcedure(
            record_id=str(episode.episode_id),
            name=episode.primary_procedure_desc or episode.specialty_name or episode.episode_type or "Inpatient procedure",
            status=episode.discharge_method or episode.episode_type,
            ordered_date=episode.admission_date,
            scheduled_date=episode.procedure_date or episode.admission_date,
            attended_date=episode.procedure_date or episode.discharge_date,
            specialty_name=episode.specialty_name,
            consultant_name=episode.consultant_name,
            ward_name=episode.ward_name,
            source_system=episode.source_system,
        )

    def _is_histology_result(self, result: PathologyResult) -> bool:
        discipline = (result.discipline or "").lower()
        return "histo" in discipline or "cyto" in discipline

    def _build_drawer_histology_report(self, result: PathologyResult) -> PathwayDrawerReport:
        return PathwayDrawerReport(
            record_id=str(result.result_id),
            name=result.test_name or result.discipline or "Histology",
            status="reported" if (result.status or "").lower() == "final" else (result.status or "unknown"),
            priority="Urgent" if "urgent" in (result.narrative_report or "").lower() else "Normal",
            ordered_date=self._as_date(result.order_date) or self._as_date(result.specimen_date),
            report_date=self._as_date(result.report_date),
            summary=result.narrative_report,
            report_text=result.narrative_report,
            author_name=result.reporting_pathologist_name,
            clinical_question=result.test_name or result.discipline,
            reference_number=result.source_accession or result.order_id,
            hospital_name="Notional Hospital",
            source_system=result.source_system,
        )

    def _build_drawer_radiology_report(self, result: RadiologyResult) -> PathwayDrawerReport:
        return PathwayDrawerReport(
            record_id=str(result.result_id),
            name=result.exam_description or result.modality or "Radiology",
            status="reported" if (result.status or "").lower() in {"verified", "final"} else (result.status or "unknown"),
            priority=result.urgency or "Normal",
            ordered_date=self._as_date(result.exam_date),
            report_date=self._as_date(result.report_date),
            summary=result.conclusion or result.report_text,
            report_text=result.report_text or result.conclusion,
            author_name=result.reporting_radiologist_name,
            clinical_question=result.clinical_indication,
            reference_number=result.accession_number or result.order_id,
            hospital_name="Notional Hospital",
            source_system=result.source_system,
        )

    def _build_drawer_mdt_meeting(self, discussion: MDTDiscussion) -> PathwayDrawerMdtMeeting:
        notes = []
        if discussion.clinical_summary:
            notes.append(
                PathwayDrawerMdtNote(
                    note_type=self._classify_mdt_note_type(discussion.clinical_summary),
                    created_at=datetime.combine(discussion.mdt_date, datetime.min.time()),
                    text=discussion.clinical_summary,
                )
            )
        if discussion.decision:
            notes.append(
                PathwayDrawerMdtNote(
                    note_type=self._classify_mdt_note_type(discussion.decision, default="outcome"),
                    created_at=datetime.combine(discussion.mdt_date, datetime.min.time()),
                    text=discussion.decision,
                )
            )
        return PathwayDrawerMdtMeeting(
            meeting_id=discussion.mdt_id,
            meeting_date=discussion.mdt_date,
            status="MDT Attended" if discussion.mdt_date <= date.today() else "MDT Booked",
            note_count=len(notes),
            mdt_site=discussion.mdt_site,
            source_system=discussion.source_system,
            notes=notes,
        )

    def _build_drawer_test_results(self, pathology: list[PathologyResult]) -> list[PathwayDrawerTestResult]:
        results = []
        for result in pathology:
            for value in result.values:
                rendered_value = value.text_value
                if value.numeric_value is not None:
                    rendered_value = str(value.numeric_value)
                elif value.coded_display:
                    rendered_value = value.coded_display
                results.append(
                    PathwayDrawerTestResult(
                        record_id=str(value.value_id),
                        test_name=value.test_name or result.test_name or "Test result",
                        test_date=self._as_date(result.report_date),
                        value=rendered_value,
                        unit=value.unit,
                        value_type=value.value_type or value.test_name,
                        abnormal_flag=value.abnormal_flag,
                    )
                )
        if results:
            return results

        fallback = []
        for result in pathology:
            if self._is_histology_result(result):
                continue
            fallback.append(
                PathwayDrawerTestResult(
                    record_id=str(result.result_id),
                    test_name=result.test_name or result.discipline or "Test result",
                    test_date=self._as_date(result.report_date),
                    value=result.status,
                    unit=None,
                    value_type=result.discipline,
                    abnormal_flag=None,
                )
            )
        return fallback

    def _build_drawer_ipt(self, action: CancerAction, pathway_day: Optional[int]) -> PathwayDrawerIPT:
        note_blob = " ".join(filter(None, [action.action_type, action.action_description, action.notes]))
        sent_or_received = "received" if "received" in note_blob.lower() else "sent"
        return PathwayDrawerIPT(
            record_id=str(action.action_id),
            reason_for_ipt=self._derive_ipt_reason(action),
            sent_or_received=sent_or_received,
            ipt_date=action.due_date or self._as_date(action.created_at),
            ipt_on_day=pathway_day,
            sending_org_name=self._derive_ipt_organisation(action, sent_or_received, "sending"),
            receiving_org_name=self._derive_ipt_organisation(action, sent_or_received, "receiving"),
            source_system=action.source_system,
        )

    def _build_tracking_comments(
        self,
        tracking_actions: list[CancerAction],
        all_actions: list[CancerAction],
    ) -> list[PathwayDrawerTrackingComment]:
        comments = []
        source_actions = tracking_actions or all_actions[:5]
        for action in source_actions:
            comment_text = action.notes or action.action_description or action.action_type
            comments.append(
                PathwayDrawerTrackingComment(
                    record_id=str(action.action_id),
                    created_at=action.updated_at or action.created_at,
                    created_by=action.created_by,
                    title=action.action_type,
                    comment_text=comment_text,
                    source_system=action.source_system,
                )
            )
        comments.sort(key=lambda item: item.created_at, reverse=True)
        return comments

    def _classify_mdt_note_type(self, text_value: Optional[str], default: str = "general") -> str:
        blob = (text_value or "").lower()
        if any(term in blob for term in ["radiology", "scan", "imaging", "pet", "mri", "ct"]):
            return "radiology"
        if any(term in blob for term in ["histology", "pathology", "biopsy", "cytology"]):
            return "histology"
        if any(term in blob for term in ["decision", "plan", "outcome", "recommended", "agree"]):
            return "outcome"
        return default

    def _derive_ipt_reason(self, action: CancerAction) -> str:
        blob = " ".join(filter(None, [action.action_type, action.action_description, action.notes])).lower()
        if "treatment" in blob:
            return "Treatment"
        if "diagnos" in blob:
            return "Diagnosis"
        if "mdt" in blob:
            return "MDT Discussion"
        if "staging" in blob:
            return "Staging"
        return "Primary Treatment"

    def _derive_ipt_organisation(self, action: CancerAction, sent_or_received: str, side: str) -> str:
        blob = " ".join(filter(None, [action.action_type, action.action_description, action.notes]))
        upper_blob = blob.upper()
        if "NEWCASTLE UPON TYNE" in upper_blob:
            external_org = "NEWCASTLE UPON TYNE HOSPITALS NHS FOUNDATION TRUST"
        elif "NOTIONAL" in upper_blob:
            external_org = "Notional Hospital"
        elif "FOUNDATION TRUST" in upper_blob:
            external_org = "Regional Cancer Centre"
        else:
            external_org = "Regional Cancer Centre"

        local_org = "Notional Hospital"
        if side == "sending":
            return external_org if sent_or_received == "received" else local_org
        return local_org if sent_or_received == "received" else external_org

    def _build_timeline(self, pathway, referral, diagnosis, pathology, radiology, mdt, sact, rt):
        events = []
        if referral:
            events.append(PathwayTimelineEvent(
                event_date=referral.receipt_date, event_type="referral",
                label="Referral received", detail=f"{referral.referral_priority or ''} — {referral.referral_source or ''}", source_system="e-RS"
            ))
        for r in radiology:
            events.append(PathwayTimelineEvent(
                event_date=r.exam_date.date() if isinstance(r.exam_date, datetime) else r.exam_date,
                event_type="radiology", label=f"{r.modality} — {(r.exam_description or '')[:60]}",
                detail=r.conclusion, source_system="RIS"
            ))
        for r in pathology:
            d = r.report_date.date() if isinstance(r.report_date, datetime) and r.report_date else (r.specimen_date.date() if r.specimen_date else date.today())
            events.append(PathwayTimelineEvent(
                event_date=d, event_type="pathology",
                label=f"{r.discipline or 'Pathology'} — {r.test_name or ''}",
                detail=r.status, source_system="ICE"
            ))
        if diagnosis:
            events.append(PathwayTimelineEvent(
                event_date=diagnosis.diagnosis_date, event_type="diagnosis",
                label="Diagnosis confirmed", detail=f"{diagnosis.icd10_code} — {diagnosis.icd10_description or ''}", source_system="Somerset"
            ))
        for m in mdt:
            events.append(PathwayTimelineEvent(
                event_date=m.mdt_date, event_type="mdt",
                label=f"{m.mdt_type or ''} MDT", detail=m.decision, source_system="Infoflex"
            ))
        for c in sact:
            if c.start_date:
                events.append(PathwayTimelineEvent(
                    event_date=c.start_date, event_type="treatment",
                    label=f"Chemotherapy started — {c.regimen_name or ''}", detail=f"{c.completed_cycles} cycles", source_system="ChemoCare"
                ))
        for r in rt:
            if r.first_fraction_date:
                events.append(PathwayTimelineEvent(
                    event_date=r.first_fraction_date, event_type="treatment",
                    label=f"Radiotherapy started — {r.treatment_site or ''}", detail=f"{r.technique}", source_system="MOSAIQ"
                ))
        events.sort(key=lambda e: e.event_date)
        return events

    def _pathway_to_row(self, pw, patient):
        today = date.today()
        return PTLRow(
            pathway_id=pw.pathway_id, patient_id=pw.patient_id,
            nhs_number=patient.nhs_number,
            patient_name=f"{patient.surname}, {patient.forename}",
            date_of_birth=patient.date_of_birth, sex=patient.sex,
            cancer_type_code=pw.cancer_type_code, cancer_type_desc=pw.cancer_type_desc,
            date_referral_received=pw.date_referral_received,
            days_on_pathway=(today - pw.date_referral_received).days if pw.date_referral_received else None,
            date_diagnosis=pw.date_diagnosis, days_to_diagnosis=pw.days_to_diagnosis,
            fds_28day_met=pw.fds_28day_met, date_first_treatment=pw.date_first_treatment,
            days_to_treatment=pw.days_to_treatment, standard_62day_met=pw.standard_62day_met,
            pathway_status=pw.pathway_status, current_stage_label=pw.current_stage_label,
            next_action=pw.next_action, next_action_date=pw.next_action_date,
            assigned_team=pw.assigned_team, breach_risk=pw.breach_risk,
            treatment_modality=pw.treatment_modality,
        )

    async def get_dashboard(self) -> DashboardMetrics:
        """Compute dashboard-level aggregate metrics."""
        sub = select(CancerPathway).subquery()

        total = await self.db.scalar(select(func.count()).select_from(sub)) or 0
        active = await self.db.scalar(
            select(func.count()).select_from(sub).where(sub.c.pathway_status != "completed")
        ) or 0

        fds_d = await self.db.scalar(select(func.count()).select_from(sub).where(sub.c.date_diagnosis.isnot(None))) or 0
        fds_n = await self.db.scalar(select(func.count()).select_from(sub).where(and_(sub.c.date_diagnosis.isnot(None), sub.c.fds_28day_met == True))) or 0
        rtt_d = await self.db.scalar(select(func.count()).select_from(sub).where(sub.c.date_first_treatment.isnot(None))) or 0
        rtt_n = await self.db.scalar(select(func.count()).select_from(sub).where(and_(sub.c.date_first_treatment.isnot(None), sub.c.standard_62day_met == True))) or 0

        # By cancer type
        type_rows = await self.db.execute(
            select(sub.c.cancer_type_code, sub.c.cancer_type_desc, func.count().label("count"))
            .group_by(sub.c.cancer_type_code, sub.c.cancer_type_desc)
            .order_by(func.count().desc())
        )
        by_type = [{"code": r[0], "label": r[1], "count": r[2]} for r in type_rows]

        # By breach risk
        breach_rows = await self.db.execute(
            select(sub.c.breach_risk, func.count().label("count"))
            .group_by(sub.c.breach_risk)
        )
        by_breach = [{"risk": r[0], "count": r[1]} for r in breach_rows]

        # By status
        status_rows = await self.db.execute(
            select(sub.c.pathway_status, func.count().label("count"))
            .group_by(sub.c.pathway_status)
        )
        by_status = [{"status": r[0], "count": r[1]} for r in status_rows]

        return DashboardMetrics(
            total_pathways=total,
            active_pathways=active,
            fds_28d_numerator=fds_n,
            fds_28d_denominator=fds_d,
            fds_28d_performance=round(fds_n / fds_d * 100, 1) if fds_d > 0 else None,
            rtt_62d_numerator=rtt_n,
            rtt_62d_denominator=rtt_d,
            rtt_62d_performance=round(rtt_n / rtt_d * 100, 1) if rtt_d > 0 else None,
            by_cancer_type=by_type,
            by_breach_risk=by_breach,
            by_status=by_status,
        )

    async def get_service_overview(
        self,
        *,
        pathway_type: Optional[str] = None,
        tag: Optional[str] = None,
        cancer_site: Optional[str] = None,
        hospital_site: Optional[str] = None,
    ) -> ServiceOverviewResponse:
        rows = await self._get_filtered_ptl_rows_for_overview(
            pathway_type=pathway_type,
            tag=tag,
            cancer_site=cancer_site,
            hospital_site=hospital_site,
        )
        open_rows = [row for row in rows if row.pathway_status != "completed"]
        actions = await self._get_filtered_actions_for_overview(
            pathway_type=pathway_type,
            tag=tag,
            cancer_site=cancer_site,
            hospital_site=hospital_site,
        )

        ptl_size = self._build_service_ptl_size(open_rows)
        filters = self._build_service_filters(rows)
        total_open_actions = len(actions)

        chart_payload = ServiceOverviewResponse(
            filters=filters,
            ptl_size=ptl_size,
            by_cancer_site=self._build_service_by_cancer_site(open_rows),
            trending_ptl_size=self._build_trending_ptl_size(ptl_size),
            by_tag=self._build_service_by_tag(open_rows),
            by_pathway_type=self._build_service_by_pathway_type(open_rows),
            actions_by_type=self._build_service_actions_by_type(actions),
            actions_by_team=self._build_service_actions_by_team(actions),
            trending_close_day=self._build_trending_close_day(open_rows),
            trending_action_volume=self._build_trending_action_volume(total_open_actions),
            current_open_pathways_mean_age=self._mean_open_pathway_age(open_rows),
            mean_close_day_last_month=35,
            total_open_actions=total_open_actions or 3738,
            provenance={
                "ptl_size": "derived_live_from_cancer_pathway",
                "filters": "derived_live_from_cancer_pathway",
                "by_cancer_site": "synthetic_distribution_scaled_to_live_filtered_ptl_total",
                "trending_ptl_size": "synthetic_weekly_series_seeded_from_live_filtered_ptl_totals",
                "by_tag": "hybrid_live_tags_plus_seeded_defaults",
                "by_pathway_type": "hybrid_live_pathway_type_plus_seeded_defaults",
                "actions_by_type": "hybrid_live_action_counts_plus_seeded_defaults",
                "actions_by_team": "hybrid_live_team_counts_plus_seeded_defaults",
                "trending_close_day": "synthetic_monthly_series_until_snapshot_table_exists",
                "trending_action_volume": "synthetic_monthly_series_until_action_snapshot_table_exists",
            },
        )
        return chart_payload

    async def get_service_overview_trending(
        self,
        *,
        pathway_type: Optional[str] = None,
        tag: Optional[str] = None,
        cancer_site: Optional[str] = None,
        hospital_site: Optional[str] = None,
    ) -> ServiceOverviewTrendingResponse:
        overview = await self.get_service_overview(
            pathway_type=pathway_type,
            tag=tag,
            cancer_site=cancer_site,
            hospital_site=hospital_site,
        )
        return ServiceOverviewTrendingResponse(
            trending_ptl_size=overview.trending_ptl_size,
            trending_close_day=overview.trending_close_day,
            trending_action_volume=overview.trending_action_volume,
            current_open_pathways_mean_age=overview.current_open_pathways_mean_age,
            mean_close_day_last_month=overview.mean_close_day_last_month,
            provenance={key: overview.provenance[key] for key in [
                "trending_ptl_size",
                "trending_close_day",
                "trending_action_volume",
            ]},
        )

    async def get_service_overview_team(
        self,
        *,
        pathway_type: Optional[str] = None,
        tag: Optional[str] = None,
        cancer_site: Optional[str] = None,
        hospital_site: Optional[str] = None,
    ) -> ServiceOverviewTeamResponse:
        overview = await self.get_service_overview(
            pathway_type=pathway_type,
            tag=tag,
            cancer_site=cancer_site,
            hospital_site=hospital_site,
        )
        return ServiceOverviewTeamResponse(
            actions_by_type=overview.actions_by_type,
            actions_by_team=overview.actions_by_team,
            total_open_actions=overview.total_open_actions,
            provenance={key: overview.provenance[key] for key in [
                "actions_by_type",
                "actions_by_team",
            ]},
        )

    async def _get_filtered_ptl_rows_for_overview(
        self,
        *,
        pathway_type: Optional[str] = None,
        tag: Optional[str] = None,
        cancer_site: Optional[str] = None,
        hospital_site: Optional[str] = None,
    ) -> list[PTLRow]:
        result = await self.db.execute(
            select(CancerPathway)
            .join(Patient, CancerPathway.patient_id == Patient.patient_id)
            .options(selectinload(CancerPathway.patient))
        )
        pathways = result.scalars().all()
        related = await self._load_related_context(pathways)
        rows = [self._build_ptl_row(pathway, pathway.patient, related) for pathway in pathways if pathway.patient]
        if pathway_type:
            rows = [row for row in rows if self._derive_pathway_type_from_row(row).lower() == pathway_type.strip().lower()]
        if tag:
            rows = [row for row in rows if tag in (row.tags or [])]
        if cancer_site:
            rows = [row for row in rows if (row.cancer_site or "").lower() == cancer_site.strip().lower()]
        if hospital_site:
            rows = [row for row in rows if (row.hospital_site or "").lower() == hospital_site.strip().lower()]
        return rows

    async def _get_filtered_actions_for_overview(
        self,
        *,
        pathway_type: Optional[str] = None,
        tag: Optional[str] = None,
        cancer_site: Optional[str] = None,
        hospital_site: Optional[str] = None,
    ) -> list[CancerAction]:
        rows = await self._get_filtered_ptl_rows_for_overview(
            pathway_type=pathway_type,
            tag=tag,
            cancer_site=cancer_site,
            hospital_site=hospital_site,
        )
        if not rows:
            return []
        patient_ids = {row.patient_id for row in rows}
        pathway_ids = {row.pathway_id for row in rows}
        result = await self.db.execute(
            select(CancerAction)
            .where(
                or_(
                    CancerAction.pathway_id.in_(pathway_ids),
                    CancerAction.patient_id.in_(patient_ids),
                )
            )
            .order_by(CancerAction.created_at.asc())
        )
        return [action for action in result.scalars().all() if (action.status or "").lower() != "completed"]

    def _build_service_filters(self, rows: list[PTLRow]) -> dict[str, list[str]]:
        return {
            "pathway_types": sorted({self._derive_pathway_type_from_row(row) for row in rows}),
            "tags": sorted({tag for row in rows for tag in (row.tags or [])}),
            "cancer_sites": sorted({row.cancer_site for row in rows if row.cancer_site}),
            "hospital_sites": sorted({row.hospital_site for row in rows if row.hospital_site}),
        }

    def _build_service_ptl_size(self, rows: list[PTLRow]) -> dict[str, int]:
        return {
            "ptl_size": len(rows),
            "d028": len([row for row in rows if (row.days_on_pathway or 0) <= 28]),
            "d2962": len([row for row in rows if 29 <= (row.days_on_pathway or 0) <= 62]),
            "d63plus": len([row for row in rows if (row.days_on_pathway or 0) >= 63]),
            "watchlist": len([row for row in rows if row.watchlist_reason]),
        }

    def _bucket_for_days(self, days: Optional[int]) -> str:
        days = days or 0
        if days <= 28:
            return "d028"
        if days <= 62:
            return "d2962"
        return "d63plus"

    def _seeded_counts(self, total: int, labels: list[str], weights: list[int], *, floor_ratio: float = 0.0) -> dict[str, int]:
        if not labels:
            return {}
        adjusted_total = max(total, len(labels))
        total_weight = sum(weights) or len(labels)
        counts: dict[str, int] = {}
        remaining = adjusted_total
        for index, label in enumerate(labels):
            if index == len(labels) - 1:
                counts[label] = max(0, remaining)
                break
            raw = int(round(adjusted_total * (weights[index] / total_weight)))
            floor_value = int(adjusted_total * floor_ratio) if floor_ratio else 0
            value = max(floor_value, raw)
            counts[label] = value
            remaining -= value
        return counts

    def _build_stacked_records(self, counts_by_label: dict[str, int], *, default_split: tuple[float, float, float]) -> list[dict]:
        rows = []
        for label, total in counts_by_label.items():
            if total <= 0:
                rows.append({"label": label, "d028": 0, "d2962": 0, "d63plus": 0, "no_value": 0, "total": 0})
                continue
            d028 = int(round(total * default_split[0]))
            d2962 = int(round(total * default_split[1]))
            d63plus = max(total - d028 - d2962, 0)
            rows.append({
                "label": label,
                "d028": d028,
                "d2962": d2962,
                "d63plus": d63plus,
                "no_value": 0,
                "total": total,
            })
        return rows

    def _build_service_by_cancer_site(self, rows: list[PTLRow]) -> list[dict]:
        labels = [
            "Urology", "Gynaecology", "Upper GI", "Skin", "Colorectal",
            "Brain", "Head and Neck", "Sarcoma", "Haematology", "Breast",
            "Lung", "ADOC", "CUP", "Paediatric",
        ]
        total = max(len(rows), 40)
        weights = [520, 420, 244, 243, 242, 229, 209, 193, 189, 187, 131, 125, 107, 40]
        counts = self._seeded_counts(total, labels, weights)
        return self._build_stacked_records(counts, default_split=(0.77, 0.21, 0.02))

    def _build_service_by_tag(self, rows: list[PTLRow]) -> list[dict]:
        labels = [
            "Actions updated in the last 48h",
            "Unreported Histology On >12 Day Old Pathway",
            "Open actions > 5 days",
            "Recent radiology report available",
            "High Risk",
        ]
        live_counts = {label: 0 for label in labels}
        for row in rows:
            row_tags = set(row.tags or [])
            if row.recent_action_update:
                row_tags.add("Actions updated in the last 48h")
            if row.latest_radiology_attended_date:
                row_tags.add("Recent radiology report available")
            if (row.breach_risk or "").lower() in {"high", "breached"}:
                row_tags.add("High Risk")
            for label in labels:
                if label in row_tags:
                    live_counts[label] += 1
        if sum(live_counts.values()) == 0:
            total = max(len(rows), 2400)
            weights = [2440, 1540, 1290, 390, 45]
            live_counts = self._seeded_counts(total, labels, weights)
        return self._build_stacked_records(live_counts, default_split=(0.79, 0.19, 0.02))

    def _build_service_by_pathway_type(self, rows: list[PTLRow]) -> list[dict]:
        labels = ["62 Day", "Upgrade", "Screening", "Breast Symptomatic"]
        live_counts = {label: 0 for label in labels}
        for row in rows:
            label = self._derive_pathway_type_from_row(row)
            if label in live_counts:
                live_counts[label] += 1
        if sum(live_counts.values()) == 0:
            total = max(len(rows), 2400)
            weights = [2240, 420, 20, 10]
            live_counts = self._seeded_counts(total, labels, weights)
        return self._build_stacked_records(live_counts, default_split=(0.76, 0.21, 0.03))

    def _build_service_actions_by_type(self, actions: list[CancerAction]) -> list[dict]:
        labels = [
            "Book GA Diagnostic", "Book Surgery", "Bring Forward Endoscopy",
            "Bring Forward GA Diagnostic", "Bring Forward Surgery",
            "Cancel GA Diagnostic", "Cancel OP Diagnostic", "Chase Endoscopy Report",
            "Chase Histology Report", "Chase Imaging Report", "Clinical Review Required",
            "Enquiry of Sample Status", "Order Endoscopy", "Reschedule GA Diagnostic",
            "Reschedule Surgery", "Review Diagnostic Results", "Update Tracking Note",
            "Urgent Review Required",
        ]
        live_counts = {label: 0 for label in labels}
        for action in actions:
            label = action.action_type or "Review Diagnostic Results"
            if label in live_counts:
                live_counts[label] += 1
        if sum(live_counts.values()) < 100:
            weights = [6, 8, 9, 1, 1, 7, 7, 7, 8, 14, 8, 7, 2, 8, 1, 7, 9, 9]
            total = max(len(actions), 3738)
            seeded = self._seeded_counts(total, labels, weights)
            live_counts = {label: max(live_counts[label], seeded[label]) for label in labels}
        total_count = sum(live_counts.values()) or 1
        palette = [
            "#4575d4", "#d63b77", "#97b93c", "#8e44ad", "#4db6ac", "#d0a03a",
            "#c84d24", "#7869d6", "#56ab44", "#9c7440", "#4784bd", "#4978d6",
            "#cc4678", "#9cbb38", "#9045a2", "#4aa6a5", "#d5a72d", "#cb5129",
        ]
        return [
            {
                "label": label,
                "value": live_counts[label],
                "percentage": round((live_counts[label] / total_count) * 100, 1),
                "color": palette[index % len(palette)],
            }
            for index, label in enumerate(labels)
            if live_counts[label] > 0
        ]

    def _build_service_actions_by_team(self, actions: list[CancerAction]) -> list[dict]:
        labels = [
            "Admissions Managers",
            "Hospital Labs/Pathology",
            "Cancer Services - Senior...",
            "Clinical Leads",
            "Endoscopy Managers",
            "Admissions",
            "Histology Team",
            "Endoscopy Bookings Team",
            "Radiology Booking",
            "CNS",
            "Outpatient Booking Team...",
            "Radiology Managers",
            "Cancer Services - MDT Coordinators",
        ]
        baseline = {
            "Admissions Managers": [188, 54, 32, 78],
            "Hospital Labs/Pathology": [171, 70, 77, 32],
            "Cancer Services - Senior...": [47, 17, 74, 201],
            "Clinical Leads": [90, 40, 78, 130],
            "Endoscopy Managers": [136, 60, 92, 47],
            "Admissions": [59, 28, 43, 201],
            "Histology Team": [222, 1, 65, 34],
            "Endoscopy Bookings Team": [67, 29, 59, 156],
            "Radiology Booking": [101, 43, 101, 65],
            "CNS": [49, 18, 66, 177],
            "Outpatient Booking Team...": [285, 12, 8, 2],
            "Radiology Managers": [83, 38, 73, 108],
            "Cancer Services - MDT Coordinators": [75, 26, 71, 130],
        }
        live = {label: [0, 0, 0, 0] for label in labels}
        team_aliases = {label.lower(): label for label in labels}
        for action in actions:
            team = team_aliases.get((action.assigned_team or "").lower())
            if not team:
                continue
            days_open = max(0, (date.today() - self._as_date(action.created_at)).days)
            if days_open <= 3:
                live[team][0] += 1
            elif days_open <= 5:
                live[team][1] += 1
            elif days_open <= 10:
                live[team][2] += 1
            else:
                live[team][3] += 1
        use_live = sum(sum(values) for values in live.values()) >= 100
        source = live if use_live else baseline
        return [
            {
                "label": label,
                "open": source[label][0],
                "d35": source[label][1],
                "d510": source[label][2],
                "d10plus": source[label][3],
                "total": sum(source[label]),
            }
            for label in labels
        ]

    def _build_trending_ptl_size(self, ptl_size: dict[str, int]) -> list[dict]:
        total = max(ptl_size.get("ptl_size", 0), 2500)
        d028 = max(ptl_size.get("d028", 0), int(total * 0.76))
        d2962 = max(ptl_size.get("d2962", 0), int(total * 0.21))
        d63plus = max(ptl_size.get("d63plus", 0), int(total * 0.02))
        start = date(2024, 5, 11)
        points = []
        for index in range(40):
            stamp = start + timedelta(days=7 * index)
            wave = ((index % 5) - 2) * 18
            dip = -2550 if index in {5, 11} else 0
            point_total = max(total + wave + dip, 0)
            point_d028 = max(d028 + ((index % 6) - 3) * 12 + (dip if dip else 0), 0)
            point_d2962 = max(d2962 + ((index % 7) - 3) * 7 + (dip // 6 if dip else 0), 0)
            point_d63 = max(d63plus + ((index % 4) - 2) * 2 + (dip // 90 if dip else 0), 0)
            points.append({
                "date": stamp.isoformat(),
                "label": str(stamp.day),
                "total": point_total,
                "d028": point_d028,
                "d2962": point_d2962,
                "d63plus": point_d63,
            })
        return points

    def _mean_open_pathway_age(self, rows: list[PTLRow]) -> int:
        ages = [row.days_on_pathway for row in rows if row.days_on_pathway is not None]
        if not ages:
            return 21
        return max(1, round(sum(ages) / len(ages)))

    def _build_trending_close_day(self, rows: list[PTLRow]) -> list[dict]:
        start_year = 2022
        points = []
        for month_index in range(40):
            year = start_year + ((month_index) // 12)
            month = ((month_index) % 12) + 1
            label = f"{year}-{month:02d}-01"
            if month_index == 39:
                value = 44
            else:
                value = 22 + ((month_index % 5) * 0.3) + ((month_index % 3) * 0.2) - ((month_index % 4) * 0.15)
            points.append({"date": label, "value": round(value, 1), "target": 28})
        return points

    def _build_trending_action_volume(self, total_open_actions: int) -> list[dict]:
        monthly_targets = [
            0, 1200, 2500, 3800, 5100, 6500, 7800, 9200, 10500, 11800,
            13200, 14600, 15800, 18400, 21000, 23600, 26200, 28900, 31200,
            33600, 40100, 46800, 53300,
        ]
        start = date(2022, 1, 1)
        points = []
        for index, created in enumerate(monthly_targets):
            stamp = date(start.year + ((start.month - 1 + index) // 12), ((start.month - 1 + index) % 12) + 1, 1)
            closed = int(created * 0.89) if index < len(monthly_targets) - 1 else int(created * 0.885)
            points.append({
                "date": stamp.isoformat(),
                "created": created,
                "closed": closed,
            })
        return points

    async def get_navigation_actions_for_patient(self, nhs_number: str) -> list[ActionSchema]:
        result = await self.db.execute(
            select(Patient).where(Patient.nhs_number == nhs_number.replace(" ", ""))
        )
        patient = result.scalar_one_or_none()
        if not patient:
            return []

        action_result = await self.db.execute(
            select(CancerAction)
            .where(
                CancerAction.patient_id == patient.patient_id,
                CancerAction.source_system.in_(["Somerset", "Endoscopy"]),
            )
            .order_by(CancerAction.due_date.asc(), CancerAction.created_at.desc())
        )
        return [ActionSchema.model_validate(action) for action in action_result.scalars().all()]

    async def get_navigation_actions_for_pathway(self, pathway_id: UUID) -> list[ActionSchema]:
        action_result = await self.db.execute(
            select(CancerAction)
            .where(
                CancerAction.pathway_id == pathway_id,
                CancerAction.source_system.in_(["Somerset", "Endoscopy"]),
            )
            .order_by(CancerAction.due_date.asc(), CancerAction.created_at.desc())
        )
        return [ActionSchema.model_validate(action) for action in action_result.scalars().all()]

    async def get_actions_worklist(
        self,
        user: dict,
        view_scope: str = "all",
        watchlist_only: bool = False,
        cancer_site: Optional[str] = None,
        hospital_site: Optional[str] = None,
        action_description: Optional[str] = None,
        action_detail: Optional[str] = None,
        action_status: Optional[str] = None,
        team_name: Optional[str] = None,
        owner: Optional[str] = None,
        action_is_open: Optional[bool] = None,
        due_after: Optional[date] = None,
        due_before: Optional[date] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        search: Optional[str] = None,
    ) -> ActionWorklistResponse:
        actions = await self._query_actions(
            due_after=due_after,
            due_before=due_before,
            created_after=created_after,
            created_before=created_before,
            search=search,
            action_description=action_description,
            action_detail=action_detail,
        )
        rows = await self._build_action_worklist_rows(actions)

        if cancer_site:
            rows = [row for row in rows if (row.cancer_site or "").lower() == cancer_site.lower()]
        if hospital_site:
            rows = [row for row in rows if self._hospital_site_matches(hospital_site, row)]
        if action_status:
            rows = [row for row in rows if row.action_status.lower() == action_status.lower()]
        if team_name:
            rows = [row for row in rows if (row.team_name or "").lower() == team_name.lower()]
        if owner:
            owner_term = owner.lower()
            rows = [row for row in rows if owner_term in (row.owner or "").lower()]
        if action_is_open is not None:
            rows = [row for row in rows if (row.action_status != "Completed") == action_is_open]

        viewer_name = (user.get("full_name") or "").lower()
        viewer_team = (user.get("team") or team_name or "Cancer Navigation").lower()
        summary = self._build_actions_kpis(rows, viewer_name, viewer_team)

        scoped_rows = rows
        if view_scope == "my":
            scoped_rows = [
                row for row in rows
                if viewer_name and viewer_name in ((row.owner or "") + " " + (row.last_updated_by or "")).lower()
            ]
        elif view_scope == "team":
            scoped_rows = [row for row in rows if (row.team_name or "").lower() == viewer_team]

        if watchlist_only:
            scoped_rows = [row for row in scoped_rows if row.is_watchlist]

        scoped_rows.sort(key=lambda row: (row.due_date or date.max, -row.days_open, row.patient_name))
        return ActionWorklistResponse(items=scoped_rows, summary=summary)

    async def get_action_detail(self, action_id: UUID) -> Optional[ActionDetailResponse]:
        result = await self.db.execute(
            select(CancerAction).where(CancerAction.action_id == action_id)
        )
        action = result.scalar_one_or_none()
        if not action:
            return None

        rows = await self._build_action_worklist_rows([action])
        if not rows:
            return None
        return ActionDetailResponse(
            action=rows[0],
            history=self._build_action_history(action),
            data_provenance={
                "action": "cancer_action",
                "history": "Derived from cancer_action timestamps/status/assignment fields and appended event log stored in cancer_action.notes",
                "pathway": "cancer_pathway",
                "patient": "patient",
                "embedded_pathway_sections": "appointment, episode, pathology_result, radiology_result, mdt_discussion, pathology_result_value, and derived Somerset/endoscopy navigation actions",
            },
        )

    async def get_action_updates(
        self,
        user: dict,
        page: int = 1,
        per_page: int = 30,
        from_datetime: Optional[datetime] = None,
        to_datetime: Optional[datetime] = None,
        update_types: Optional[list[str]] = None,
        exclude_users: Optional[list[str]] = None,
    ) -> ActionUpdatesResponse:
        actions = await self._query_actions()
        rows = await self._build_action_worklist_rows(actions)
        row_by_action_id = {row.action_id: row for row in rows}
        exclude_names = {(value or "").lower() for value in (exclude_users or [])}
        allowed_types = {value.lower() for value in (update_types or [])}

        items: list[ActionUpdateItem] = []
        for action in actions:
            row = row_by_action_id.get(action.action_id)
            if not row:
                continue
            detail = ActionDetailResponse(action=row, history=self._build_action_history(action))
            for history_index, history_item in enumerate(detail.history):
                mapped_type = self._map_history_type_to_update(history_item.event_type)
                if not mapped_type:
                    continue
                if allowed_types and mapped_type.lower() not in allowed_types:
                    continue
                if from_datetime and history_item.timestamp < from_datetime:
                    continue
                if to_datetime and history_item.timestamp > to_datetime:
                    continue
                if exclude_names and (history_item.actor or "").lower() in exclude_names:
                    continue
                items.append(
                    ActionUpdateItem(
                        update_id=f"{action.action_id}:{history_index}",
                        action_id=action.action_id,
                        update_type=mapped_type,
                        update_tone=self._history_tone_to_update_tone(history_item),
                        title=f"{mapped_type} - {row.title} - {row.patient_name} | MRN: {row.mrn or 'No value'} | {row.cancer_site or 'Unknown'} | Day {row.pathway_day or 'No value'}",
                        timestamp=history_item.timestamp,
                        actor=history_item.actor,
                        comment_title=history_item.title if mapped_type == 'Comment Added' else None,
                        comment_text=history_item.detail,
                        action_detail=detail,
                    )
                )

        items.sort(key=lambda item: item.timestamp, reverse=True)
        total = len(items)
        start = max((page - 1) * per_page, 0)
        paged_items = items[start:start + per_page]
        return ActionUpdatesResponse(items=paged_items, total=total, page=page, per_page=per_page)

    async def _query_actions(
        self,
        due_after: Optional[date] = None,
        due_before: Optional[date] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        search: Optional[str] = None,
        action_description: Optional[str] = None,
        action_detail: Optional[str] = None,
    ) -> list[CancerAction]:
        query = select(CancerAction)
        if due_after:
            query = query.where(CancerAction.due_date >= due_after)
        if due_before:
            query = query.where(CancerAction.due_date <= due_before)
        if created_after:
            query = query.where(CancerAction.created_at >= created_after)
        if created_before:
            query = query.where(CancerAction.created_at <= created_before)
        if search:
            term = f"%{search}%"
            query = query.where(
                or_(
                    CancerAction.action_type.ilike(term),
                    CancerAction.action_description.ilike(term),
                    CancerAction.notes.ilike(term),
                )
            )
        if action_description:
            query = query.where(CancerAction.action_type.ilike(f"%{action_description}%"))
        if action_detail:
            query = query.where(
                or_(
                    CancerAction.action_description.ilike(f"%{action_detail}%"),
                    CancerAction.notes.ilike(f"%{action_detail}%"),
                )
            )
        query = query.order_by(CancerAction.due_date.asc().nullslast(), CancerAction.created_at.desc())
        result = await self.db.execute(query.limit(500))
        return list(result.scalars().all())

    async def _build_action_worklist_rows(self, actions: list[CancerAction]) -> list[ActionWorklistRow]:
        if not actions:
            return []

        patient_ids = list({action.patient_id for action in actions})
        pathway_ids = [action.pathway_id for action in actions if action.pathway_id]

        patient_result = await self.db.execute(
            select(Patient).where(Patient.patient_id.in_(patient_ids))
        )
        pathway_result = await self.db.execute(
            select(CancerPathway)
            .join(Patient, CancerPathway.patient_id == Patient.patient_id)
            .options(selectinload(CancerPathway.patient))
            .where(
                or_(
                    CancerPathway.patient_id.in_(patient_ids),
                    CancerPathway.pathway_id.in_(pathway_ids or [UUID("00000000-0000-0000-0000-000000000000")]),
                )
            )
        )

        patients = {patient.patient_id: patient for patient in patient_result.scalars().all()}
        pathways = list(pathway_result.scalars().all())
        related = await self._load_related_context(pathways)

        latest_pathway_by_patient: dict[UUID, CancerPathway] = {}
        pathway_by_id: dict[UUID, CancerPathway] = {}
        pathway_row_by_id: dict[UUID, PTLRow] = {}
        for pathway in sorted(pathways, key=lambda value: value.created_at or datetime.min, reverse=True):
            pathway_by_id[pathway.pathway_id] = pathway
            latest_pathway_by_patient.setdefault(pathway.patient_id, pathway)

        for pathway in pathways:
            if pathway.patient:
                pathway_row_by_id[pathway.pathway_id] = self._build_ptl_row(pathway, pathway.patient, related)

        rows = []
        for action in actions:
            patient = patients.get(action.patient_id)
            if not patient:
                continue
            pathway = pathway_by_id.get(action.pathway_id) or latest_pathway_by_patient.get(action.patient_id)
            pathway_row = pathway_row_by_id.get(pathway.pathway_id) if pathway else None
            rows.append(self._build_action_worklist_row(action, patient, pathway_row))
        return rows

    def _build_action_worklist_row(
        self,
        action: CancerAction,
        patient: Patient,
        pathway_row: Optional[PTLRow],
    ) -> ActionWorklistRow:
        days_open = max(0, (date.today() - self._as_date(action.created_at)).days)
        action_status, tone = self._action_status_display(action, days_open)
        latest_comment_text, latest_comment_actor, latest_comment_at = self._latest_action_comment_event(action)
        return ActionWorklistRow(
            action_id=action.action_id,
            pathway_id=action.pathway_id,
            patient_id=action.patient_id,
            due_date=action.due_date,
            title=action.action_type,
            priority=action.priority,
            action_detail_summary=action.action_description or action.notes,
            action_status=action_status,
            action_status_tone=tone,
            pathway_day=pathway_row.days_on_pathway if pathway_row else None,
            patient_name=f"{patient.surname}, {patient.forename}",
            cancer_site=pathway_row.cancer_site if pathway_row else None,
            hospital_site=pathway_row.hospital_site if pathway_row else None,
            mrn=patient.hospital_number,
            nhs_number=patient.nhs_number,
            owner=action.assigned_user or action.created_by,
            team_name=action.assigned_team,
            days_open=days_open,
            pathway_is_open=bool(pathway_row and pathway_row.pathway_status != "completed"),
            pathway_status=("Suspected" if pathway_row and pathway_row.pathway_status not in {"completed", "active_monitoring"} else "Benign") if pathway_row else None,
            latest_action_comment=latest_comment_text or action.action_description,
            latest_comment_at=latest_comment_at or action.updated_at or action.created_at,
            latest_comment_by=latest_comment_actor or action.completed_by or action.created_by or action.assigned_user,
            breach_date_28=pathway_row.breach_date_28 if pathway_row else None,
            breach_date_31=pathway_row.breach_date_31 if pathway_row else None,
            breach_date_62=pathway_row.breach_date_62 if pathway_row else None,
            first_op_appt_attended_date=pathway_row.first_outpatient_attended_date if pathway_row else None,
            next_op_appt_attended_date=pathway_row.next_outpatient_attended_date if pathway_row else None,
            latest_radiology_attended_date=pathway_row.latest_radiology_attended_date if pathway_row else None,
            latest_histology_attended_date=pathway_row.latest_histology_attended_date if pathway_row else None,
            latest_ip_procedure_tci_date=pathway_row.latest_inpatient_encounter_tci_date if pathway_row else None,
            watchlist_reason=pathway_row.watchlist_reason if pathway_row else None,
            is_watchlist=bool(pathway_row and pathway_row.watchlist_reason),
            last_updated=action.updated_at or action.created_at,
            last_updated_by=action.completed_by or action.created_by or action.assigned_user,
        )

    def _build_actions_kpis(
        self,
        rows: list[ActionWorklistRow],
        viewer_name: str,
        viewer_team: str,
    ) -> ActionsKpiSummary:
        return ActionsKpiSummary(
            my_actions=len([row for row in rows if viewer_name and viewer_name in ((row.owner or "") + " " + (row.last_updated_by or "")).lower()]),
            team_actions=len([row for row in rows if (row.team_name or "").lower() == viewer_team]),
            awaiting_assignment=len([row for row in rows if (row.team_name or "").lower() == viewer_team and not row.owner]),
            escalated_team_actions=len([row for row in rows if (row.team_name or "").lower() == viewer_team and row.action_status == "Escalated"]),
            all_actions=len(rows),
            watchlist_only=len([row for row in rows if row.is_watchlist]),
        )

    def _build_action_history(self, action: CancerAction) -> list[PathwayDrawerHistoryItem]:
        _, persisted_events = self._extract_action_note_events(action.notes)
        history = [
            PathwayDrawerHistoryItem(
                timestamp=action.created_at,
                event_type="CREATE ACTION",
                title=action.action_type,
                detail=action.action_description,
                actor=action.created_by,
                tone="success",
            )
        ]
        history.extend(persisted_events)

        if not any(item.event_type == "ASSIGN TO USER" for item in persisted_events) and (action.assigned_user or action.assigned_team):
            history.append(
                PathwayDrawerHistoryItem(
                    timestamp=(action.updated_at or action.created_at) + timedelta(minutes=2),
                    event_type="ASSIGN TO USER",
                    title="Assignment updated",
                    detail=f"Assigned to {action.assigned_user or action.assigned_team}",
                    actor=action.created_by,
                    tone="info",
                )
            )
        if action.completed_date and not any(item.event_type == "COMPLETE ACTION" for item in persisted_events):
            history.append(
                PathwayDrawerHistoryItem(
                    timestamp=action.completed_date,
                    event_type="COMPLETE ACTION",
                    title="Action completed",
                    detail=None,
                    actor=action.completed_by,
                    tone="success",
                )
            )
        history.sort(key=lambda item: self._normalise_event_timestamp(item.timestamp))
        return history

    def _extract_action_note_events(
        self,
        notes: Optional[str],
    ) -> tuple[Optional[str], list[PathwayDrawerHistoryItem]]:
        if not notes:
            return None, []

        plain_lines: list[str] = []
        events: list[PathwayDrawerHistoryItem] = []
        for raw_line in notes.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if not line.startswith(ACTION_EVENT_MARKER):
                plain_lines.append(raw_line)
                continue
            payload = line[len(ACTION_EVENT_MARKER):].strip()
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                continue
            timestamp_value = data.get("timestamp")
            try:
                timestamp = datetime.fromisoformat(timestamp_value) if timestamp_value else datetime.utcnow()
            except (TypeError, ValueError):
                timestamp = datetime.utcnow()
            events.append(
                PathwayDrawerHistoryItem(
                    timestamp=timestamp,
                    event_type=data.get("event_type") or "COMMENT",
                    title=data.get("title") or "General Comment",
                    detail=data.get("detail"),
                    actor=data.get("actor"),
                    tone=data.get("tone") or "comment",
                )
            )
        plain_note = "\n".join(line for line in plain_lines if line).strip() or None
        return plain_note, events

    def _append_action_event(
        self,
        notes: Optional[str],
        *,
        event_type: str,
        actor: Optional[str],
        title: Optional[str],
        detail: Optional[str],
        tone: str,
        timestamp: Optional[datetime] = None,
    ) -> str:
        encoded = json.dumps(
            {
                "timestamp": (timestamp or datetime.utcnow()).isoformat(),
                "event_type": event_type,
                "actor": actor,
                "title": title,
                "detail": detail,
                "tone": tone,
            },
            ensure_ascii=True,
        )
        existing = (notes or "").rstrip()
        prefix = f"{existing}\n" if existing else ""
        return f"{prefix}{ACTION_EVENT_MARKER}{encoded}"

    def _latest_action_comment_event(
        self,
        action: CancerAction,
    ) -> tuple[Optional[str], Optional[str], Optional[datetime]]:
        plain_note, events = self._extract_action_note_events(action.notes)
        comments = [item for item in events if item.event_type == "COMMENT"]
        if comments:
            latest = comments[-1]
            return latest.detail, latest.actor, latest.timestamp
        return plain_note, action.created_by, action.updated_at or action.created_at

    def _normalise_event_timestamp(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    async def mutate_action(
        self,
        action: CancerAction,
        *,
        actor: str,
        operation: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[date] = None,
        assigned_team: Optional[str] = None,
        assigned_user: Optional[str] = None,
        comment_title: Optional[str] = None,
        comment_text: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> CancerAction:
        now = datetime.utcnow()

        if priority is not None:
            action.priority = priority
        if due_date is not None:
            action.due_date = due_date
        if notes and not comment_text:
            action.notes = notes

        if comment_text:
            action.notes = self._append_action_event(
                action.notes,
                event_type="COMMENT",
                actor=actor,
                title=comment_title or "General Comment",
                detail=comment_text,
                tone="comment",
                timestamp=now,
            )

        team_changed = assigned_team is not None and assigned_team != action.assigned_team
        user_changed = assigned_user is not None and assigned_user != action.assigned_user
        if team_changed or user_changed:
            if assigned_team is not None:
                action.assigned_team = assigned_team
            if assigned_user is not None:
                action.assigned_user = assigned_user
            action.notes = self._append_action_event(
                action.notes,
                event_type="ASSIGN TO USER",
                actor=actor,
                title="Assignment updated",
                detail=f"Assigned to {assigned_user or assigned_team or 'Unassigned'}",
                tone="info",
                timestamp=now,
            )

        status_changed = status is not None and status != action.status
        if status_changed:
            action.status = status
            if status == "completed":
                action.completed_by = actor
                action.completed_date = now
                action.notes = self._append_action_event(
                    action.notes,
                    event_type="COMPLETE ACTION",
                    actor=actor,
                    title="Action completed",
                    detail=None,
                    tone="success",
                    timestamp=now,
                )
            elif status == "open" and operation == "reopen":
                action.completed_by = None
                action.completed_date = None
                action.notes = self._append_action_event(
                    action.notes,
                    event_type="REOPEN ACTION",
                    actor=actor,
                    title="Action reopened",
                    detail=None,
                    tone="info",
                    timestamp=now,
                )
            elif status == "escalated":
                action.notes = self._append_action_event(
                    action.notes,
                    event_type="ESCALATE ACTION",
                    actor=actor,
                    title="Action escalated",
                    detail=None,
                    tone="danger",
                    timestamp=now,
                )
            elif status == "revoked":
                action.notes = self._append_action_event(
                    action.notes,
                    event_type="REVOKE ACTION",
                    actor=actor,
                    title="Action revoked",
                    detail=None,
                    tone="danger",
                    timestamp=now,
                )

        action.updated_at = now
        await self.db.flush()
        await self.db.refresh(action)
        return action

    def _action_status_display(self, action: CancerAction, days_open: int) -> tuple[str, str]:
        raw_status = (action.status or "").lower()
        note_blob = ((action.notes or "") + " " + (action.action_description or "")).lower()
        escalated = raw_status == "escalated" or "high risk" in note_blob or (action.priority == "high" and days_open >= 7)
        if raw_status == "completed":
            return "Completed", "neutral"
        if escalated:
            return "Escalated", "danger"
        return "Open", "success"

    def _hospital_site_matches(self, hospital_site: str, row: ActionWorklistRow) -> bool:
        return (row.hospital_site or "").lower() == hospital_site.lower()

    def _map_history_type_to_update(self, event_type: str) -> Optional[str]:
        mapping = {
            "CREATE ACTION": "Created",
            "COMMENT": "Comment Added",
            "ASSIGN TO USER": "Assigned Owner",
        }
        return mapping.get(event_type)

    def _history_tone_to_update_tone(self, history_item: PathwayDrawerHistoryItem) -> str:
        if history_item.event_type == "CREATE ACTION":
            return "green"
        if history_item.event_type == "ASSIGN TO USER":
            return "blue"
        return "purple"

    async def get_integration_status(self) -> IntegrationStatusResponse:
        audit_total = await self.db.scalar(select(func.count()).select_from(text("integration_audit_log"))) or 0
        audit_success = await self.db.scalar(
            select(func.count()).select_from(text("integration_audit_log")).where(text("status = 'success'"))
        ) or 0
        audit_error = await self.db.scalar(
            select(func.count()).select_from(text("integration_audit_log")).where(text("status = 'error'"))
        ) or 0
        dlq_pending = await self.db.scalar(
            select(func.count()).select_from(text("dead_letter_queue")).where(text("status = 'pending'"))
        ) or 0
        dlq_total = await self.db.scalar(select(func.count()).select_from(text("dead_letter_queue"))) or 0

        source_rows = await self.db.execute(text("""
            SELECT
                COALESCE(source_system, 'UNKNOWN') AS source_system,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS error_count,
                MAX(created_at) AS last_event_at
            FROM integration_audit_log
            GROUP BY COALESCE(source_system, 'UNKNOWN')
            ORDER BY source_system
        """))
        sources = [
            IntegrationSourceStatus(
                source_system=row.source_system,
                success_count=row.success_count or 0,
                error_count=row.error_count or 0,
                last_event_at=row.last_event_at,
            )
            for row in source_rows
        ]

        error_rows = await self.db.execute(text("""
            SELECT source_system, message_type, status, error_message, created_at
            FROM integration_audit_log
            WHERE status = 'error'
            ORDER BY created_at DESC
            LIMIT 25
        """))
        recent_errors = [
            IntegrationIssue(
                source_system=row.source_system,
                message_type=row.message_type,
                status=row.status,
                error_message=row.error_message,
                created_at=row.created_at,
            )
            for row in error_rows
        ]

        return IntegrationStatusResponse(
            audit_total=audit_total,
            audit_success=audit_success,
            audit_error=audit_error,
            dlq_pending=dlq_pending,
            dlq_total=dlq_total,
            source_status=sources,
            recent_errors=recent_errors,
        )

    async def search_patients(self, query: str, limit: int = 20) -> list[SearchResult]:
        """Search patients by name, NHS number, or hospital number."""
        search_term = f"%{query}%"
        result = await self.db.execute(
            select(Patient)
            .outerjoin(CancerPathway, Patient.patient_id == CancerPathway.patient_id)
            .where(
                or_(
                    Patient.surname.ilike(search_term),
                    Patient.forename.ilike(search_term),
                    Patient.nhs_number.like(query.replace(" ", "")),
                    Patient.hospital_number.ilike(search_term),
                )
            )
            .limit(limit)
        )
        patients = result.scalars().all()
        return [
            SearchResult(
                patient_id=p.patient_id,
                nhs_number=p.nhs_number,
                forename=p.forename,
                surname=p.surname,
                date_of_birth=p.date_of_birth,
                sex=p.sex,
            )
            for p in patients
        ]
