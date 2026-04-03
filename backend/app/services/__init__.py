"""Patient Tracking List service — core query logic for Cancer 360."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import select, func, case, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    CancerPathway, Patient, Referral, Diagnosis, Staging,
    PathologyResult, RadiologyResult, SACTCourse, RadiotherapyCourse,
    MDTDiscussion, CancerAction, Episode, Appointment,
)
from app.schemas import (
    PTLRow, PTLSummary, PTLResponse, Patient360Response,
    PatientDetail, ReferralSchema, DiagnosisSchema, StagingSchema,
    PathologyResultSchema, RadiologyResultSchema, SACTCourseSchema,
    RTCourseSchema, MDTDiscussionSchema, ActionSchema,
    PathwayTimelineEvent, DashboardMetrics, SearchResult,
)


class PTLService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_ptl(
        self,
        cancer_type: Optional[str] = None,
        pathway_status: Optional[str] = None,
        breach_risk: Optional[str] = None,
        assigned_team: Optional[str] = None,
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

        # Sort
        breach_order = case(
            (CancerPathway.breach_risk == "breached", 0),
            (CancerPathway.breach_risk == "high", 1),
            (CancerPathway.breach_risk == "medium", 2),
            (CancerPathway.breach_risk == "low", 3),
            else_=4,
        )

        if sort_by == "breach_risk":
            query = query.order_by(breach_order, CancerPathway.date_referral_received.asc())
        elif sort_by == "days":
            query = query.order_by(CancerPathway.date_referral_received.asc())
        elif sort_by == "name":
            query = query.order_by(Patient.surname.asc(), Patient.forename.asc())
        else:
            query = query.order_by(breach_order)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # Paginate
        results = await self.db.execute(
            query.offset((page - 1) * per_page).limit(per_page)
        )
        pathways = results.scalars().all()

        # Build PTL rows
        today = date.today()
        items = []
        for pw in pathways:
            p = pw.patient
            days_on = (today - pw.date_referral_received).days if pw.date_referral_received else None
            items.append(PTLRow(
                pathway_id=pw.pathway_id,
                patient_id=pw.patient_id,
                nhs_number=p.nhs_number,
                patient_name=f"{p.surname}, {p.forename}",
                date_of_birth=p.date_of_birth,
                sex=p.sex,
                cancer_type_code=pw.cancer_type_code,
                cancer_type_desc=pw.cancer_type_desc,
                stage_group=None,
                date_referral_received=pw.date_referral_received,
                days_on_pathway=days_on,
                date_diagnosis=pw.date_diagnosis,
                days_to_diagnosis=pw.days_to_diagnosis,
                fds_28day_met=pw.fds_28day_met,
                date_first_treatment=pw.date_first_treatment,
                days_to_treatment=pw.days_to_treatment,
                standard_62day_met=pw.standard_62day_met,
                pathway_status=pw.pathway_status,
                current_stage_label=pw.current_stage_label,
                next_action=pw.next_action,
                next_action_date=pw.next_action_date,
                assigned_team=pw.assigned_team,
                breach_risk=pw.breach_risk,
                treatment_modality=pw.treatment_modality,
            ))

        # Summary
        summary = await self._get_summary(cancer_type, assigned_team)

        return PTLResponse(
            items=items,
            total=total or 0,
            page=page,
            per_page=per_page,
            summary=summary,
        )

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
            .options(selectinload(SACTCourse.cycles).selectinload("drugs"))
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
        )

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
