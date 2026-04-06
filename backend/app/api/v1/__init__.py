"""Cancer 360 API v1 endpoints."""

from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user, create_access_token, verify_password
from app.models import CancerAction, Patient
from app.simulation import simulation_hub
from app.schemas import (
    PTLResponse, Patient360Response, DashboardMetrics, SearchResult,
    ActionCreate, ActionUpdate, ActionSchema,
    TokenRequest, TokenResponse,
    ActionDetailResponse,
    ActionUpdatesResponse,
    ActionWorklistResponse,
    IntegrationStatusResponse,
    PathwayDrawerResponse,
    ServiceOverviewResponse,
    ServiceOverviewTeamResponse,
    ServiceOverviewTrendingResponse,
    SimulationCatalogResponse,
    SimulationRunDetail,
    SimulationRunRequest,
    SimulationRunSummary,
)
from app.services import PTLService

router = APIRouter(prefix="/api/v1")


# ─── Auth ───────────────────────────────────────────────────────────────────

@router.post("/auth/token", response_model=TokenResponse, tags=["auth"])
async def login(body: TokenRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and receive a JWT token."""
    from app.models import Base  # avoid circular — user table is in init.sql
    result = await db.execute(
        select(Patient).limit(0)  # placeholder, real auth uses app_user table
    )
    # For PoC: accept any username with password "cancer360"
    if body.password != "cancer360":
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": body.username,
        "username": body.username,
        "full_name": body.username.replace(".", " ").title(),
        "role": "clinician",
        "team": None,
    })
    return TokenResponse(
        access_token=token,
        user={"username": body.username, "role": "clinician"},
    )


# ─── PTL ────────────────────────────────────────────────────────────────────

@router.get("/ptl", response_model=PTLResponse, tags=["ptl"])
async def get_ptl(
    cancer_type: Optional[str] = Query(None, description="Filter by cancer type code"),
    cancer_site: Optional[str] = Query(None, description="Filter by cancer site code"),
    pathway_status: Optional[str] = Query(None, description="Filter by pathway status"),
    breach_risk: Optional[str] = Query(None, description="Filter by breach risk level"),
    assigned_team: Optional[str] = Query(None, description="Filter by assigned MDT team"),
    hospital_site: Optional[str] = Query(None, description="Filter by derived hospital site"),
    pathway_type: Optional[str] = Query(None, description="Filter by pathway type"),
    search: Optional[str] = Query(None, description="Search by patient name or NHS number"),
    sort_by: str = Query("breach_risk", description="Sort field: breach_risk, days, name"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get the cancer Patient Tracking List with filtering and pagination."""
    svc = PTLService(db)
    return await svc.get_ptl(
        cancer_type=cancer_site or cancer_type,
        pathway_status=pathway_status,
        breach_risk=breach_risk,
        assigned_team=assigned_team,
        hospital_site=hospital_site,
        pathway_type=pathway_type,
        search=search,
        sort_by=sort_by,
        page=page,
        per_page=per_page,
    )


@router.get("/ptl/summary", tags=["ptl"])
async def get_ptl_summary(
    cancer_type: Optional[str] = None,
    assigned_team: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get PTL summary statistics."""
    svc = PTLService(db)
    return await svc._get_summary(cancer_type, assigned_team)


# ─── Patient 360 ───────────────────────────────────────────────────────────

@router.get("/patients/{nhs_number}", response_model=Patient360Response, tags=["patients"])
async def get_patient_360(
    nhs_number: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get the full 360° view for a patient by NHS number."""
    svc = PTLService(db)
    result = await svc.get_patient_360(nhs_number)
    if not result:
        raise HTTPException(status_code=404, detail="Patient not found")
    return result


@router.get("/patients/{nhs_number}/pathology", tags=["patients"])
async def get_patient_pathology(
    nhs_number: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get pathology results for a patient."""
    from app.models import PathologyResult
    from sqlalchemy.orm import selectinload

    patient = await db.execute(
        select(Patient).where(Patient.nhs_number == nhs_number.replace(" ", ""))
    )
    p = patient.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    results = await db.execute(
        select(PathologyResult)
        .options(selectinload(PathologyResult.values), selectinload(PathologyResult.histopath))
        .where(PathologyResult.patient_id == p.patient_id)
        .order_by(PathologyResult.report_date.desc())
    )
    return [r.__dict__ for r in results.scalars().all()]


@router.get("/patients/{nhs_number}/radiology", tags=["patients"])
async def get_patient_radiology(
    nhs_number: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get radiology results for a patient."""
    from app.models import RadiologyResult

    patient = await db.execute(
        select(Patient).where(Patient.nhs_number == nhs_number.replace(" ", ""))
    )
    p = patient.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    results = await db.execute(
        select(RadiologyResult).where(RadiologyResult.patient_id == p.patient_id)
        .order_by(RadiologyResult.exam_date.desc())
    )
    return [r.__dict__ for r in results.scalars().all()]


@router.get("/patients/{nhs_number}/treatment", tags=["patients"])
async def get_patient_treatment(
    nhs_number: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get SACT and radiotherapy records for a patient."""
    from app.models import SACTCourse, RadiotherapyCourse
    from sqlalchemy.orm import selectinload

    patient = await db.execute(
        select(Patient).where(Patient.nhs_number == nhs_number.replace(" ", ""))
    )
    p = patient.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    sact = await db.execute(
        select(SACTCourse).options(selectinload(SACTCourse.cycles))
        .where(SACTCourse.patient_id == p.patient_id)
    )
    rt = await db.execute(
        select(RadiotherapyCourse).options(selectinload(RadiotherapyCourse.fractions))
        .where(RadiotherapyCourse.patient_id == p.patient_id)
    )
    return {"sact": [c.__dict__ for c in sact.scalars().all()], "rt": [c.__dict__ for c in rt.scalars().all()]}


@router.get("/patients/{nhs_number}/mdt", tags=["patients"])
async def get_patient_mdt(
    nhs_number: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get MDT discussion records for a patient."""
    from app.models import MDTDiscussion

    patient = await db.execute(
        select(Patient).where(Patient.nhs_number == nhs_number.replace(" ", ""))
    )
    p = patient.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    results = await db.execute(
        select(MDTDiscussion).where(MDTDiscussion.patient_id == p.patient_id)
        .order_by(MDTDiscussion.mdt_date.desc())
    )
    return [r.__dict__ for r in results.scalars().all()]


@router.get("/patients/{nhs_number}/navigation", response_model=list[ActionSchema], tags=["patients"])
async def get_patient_navigation(
    nhs_number: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get Somerset/endoscopy-derived navigation items for a patient."""
    svc = PTLService(db)
    return await svc.get_navigation_actions_for_patient(nhs_number)


@router.get("/pathways/{pathway_id}", response_model=PathwayDrawerResponse, tags=["pathways"])
async def get_pathway_drawer(
    pathway_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get the reusable pathway drawer payload for a single pathway."""
    svc = PTLService(db)
    result = await svc.get_pathway_drawer(pathway_id)
    if not result:
        raise HTTPException(status_code=404, detail="Pathway not found")
    return result


@router.get("/pathways/{pathway_id}/navigation", response_model=list[ActionSchema], tags=["pathways"])
async def get_pathway_navigation(
    pathway_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get Somerset/endoscopy-derived navigation items for a pathway."""
    svc = PTLService(db)
    return await svc.get_navigation_actions_for_pathway(pathway_id)


# ─── Actions ────────────────────────────────────────────────────────────────

@router.get("/actions", response_model=list[ActionSchema], tags=["actions"])
async def get_actions(
    status: Optional[str] = Query(None),
    assigned_team: Optional[str] = Query(None),
    patient_id: Optional[UUID] = Query(None),
    pathway_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get cancer actions (worklist/inbox)."""
    query = select(CancerAction).order_by(CancerAction.due_date.asc())
    if status:
        query = query.where(CancerAction.status == status)
    if assigned_team:
        query = query.where(CancerAction.assigned_team == assigned_team)
    if patient_id:
        query = query.where(CancerAction.patient_id == patient_id)
    if pathway_id:
        query = query.where(CancerAction.pathway_id == pathway_id)

    result = await db.execute(query.limit(200))
    return [ActionSchema.model_validate(a) for a in result.scalars().all()]


@router.get("/actions/worklist", response_model=ActionWorklistResponse, tags=["actions"])
async def get_actions_worklist(
    view_scope: str = Query("all", pattern="^(all|my|team)$"),
    watchlist_only: bool = Query(False),
    cancer_site: Optional[str] = Query(None),
    hospital_site: Optional[str] = Query(None),
    action_description: Optional[str] = Query(None),
    action_detail: Optional[str] = Query(None),
    action_status: Optional[str] = Query(None),
    team_name: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    action_is_open: Optional[bool] = Query(None),
    due_after: Optional[date] = Query(None),
    due_before: Optional[date] = Query(None),
    created_after: Optional[datetime] = Query(None),
    created_before: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get the Screen 3 Cancer Actions worklist with KPI summary."""
    svc = PTLService(db)
    return await svc.get_actions_worklist(
        user=user,
        view_scope=view_scope,
        watchlist_only=watchlist_only,
        cancer_site=cancer_site,
        hospital_site=hospital_site,
        action_description=action_description,
        action_detail=action_detail,
        action_status=action_status,
        team_name=team_name,
        owner=owner,
        action_is_open=action_is_open,
        due_after=due_after,
        due_before=due_before,
        created_after=created_after,
        created_before=created_before,
        search=search,
    )


@router.get("/actions/updates", response_model=ActionUpdatesResponse, tags=["actions"])
@router.get("/actions/recent-updates", response_model=ActionUpdatesResponse, tags=["actions"])
async def get_action_updates(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    from_datetime: Optional[datetime] = Query(None),
    to_datetime: Optional[datetime] = Query(None),
    update_type: Optional[list[str]] = Query(None),
    exclude_user: Optional[list[str]] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get the Recent Action Updates feed for Screen 3."""
    svc = PTLService(db)
    return await svc.get_action_updates(
        user=user,
        page=page,
        per_page=per_page,
        from_datetime=from_datetime,
        to_datetime=to_datetime,
        update_types=update_type,
        exclude_users=exclude_user,
    )


@router.get("/actions/{action_id}/detail", response_model=ActionDetailResponse, tags=["actions"])
async def get_action_detail(
    action_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get the Screen 3 single-action drawer payload."""
    svc = PTLService(db)
    result = await svc.get_action_detail(action_id)
    if not result:
        raise HTTPException(status_code=404, detail="Action not found")
    return result


@router.get("/actions/{action_id}/history", response_model=list, tags=["actions"])
async def get_action_history(
    action_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get the action history timeline as a standalone feed."""
    svc = PTLService(db)
    result = await svc.get_action_detail(action_id)
    if not result:
        raise HTTPException(status_code=404, detail="Action not found")
    return result.history


@router.post("/actions", response_model=ActionSchema, status_code=201, tags=["actions"])
async def create_action(
    body: ActionCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create a new cancer action."""
    action = CancerAction(
        patient_id=body.patient_id,
        pathway_id=body.pathway_id,
        action_type=body.action_type,
        action_description=body.action_description,
        priority=body.priority,
        due_date=body.due_date,
        assigned_team=body.assigned_team,
        assigned_user=body.assigned_user,
        created_by=user.get("full_name", "System"),
        notes=body.notes,
    )
    db.add(action)
    await db.flush()
    await db.refresh(action)
    return ActionSchema.model_validate(action)


@router.patch("/actions/{action_id}", response_model=ActionSchema, tags=["actions"])
async def update_action(
    action_id: UUID,
    body: ActionUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Update an existing cancer action."""
    result = await db.execute(
        select(CancerAction).where(CancerAction.action_id == action_id)
    )
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    svc = PTLService(db)
    action = await svc.mutate_action(
        action,
        actor=user.get("full_name", "System"),
        operation=body.operation,
        status=body.status,
        priority=body.priority,
        due_date=body.due_date,
        assigned_team=body.assigned_team,
        assigned_user=body.assigned_user,
        comment_title=body.comment_title,
        comment_text=body.comment_text,
        notes=body.notes,
    )
    return ActionSchema.model_validate(action)


# ─── Dashboard ──────────────────────────────────────────────────────────────

@router.get("/dashboard/performance", response_model=DashboardMetrics, tags=["dashboard"])
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get dashboard aggregate metrics."""
    svc = PTLService(db)
    return await svc.get_dashboard()


@router.get("/dashboard", response_model=ServiceOverviewResponse, tags=["dashboard"])
async def get_service_overview_dashboard(
    pathway_type: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    cancer_site: Optional[str] = Query(None),
    hospital_site: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get the full Service Overview payload for the dashboard module."""
    svc = PTLService(db)
    return await svc.get_service_overview(
        pathway_type=pathway_type,
        tag=tag,
        cancer_site=cancer_site,
        hospital_site=hospital_site,
    )


@router.get("/dashboard/trending", response_model=ServiceOverviewTrendingResponse, tags=["dashboard"])
async def get_service_overview_trending(
    pathway_type: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    cancer_site: Optional[str] = Query(None),
    hospital_site: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get the trending series used by Service Overview."""
    svc = PTLService(db)
    return await svc.get_service_overview_trending(
        pathway_type=pathway_type,
        tag=tag,
        cancer_site=cancer_site,
        hospital_site=hospital_site,
    )


@router.get("/dashboard/team", response_model=ServiceOverviewTeamResponse, tags=["dashboard"])
async def get_service_overview_team(
    pathway_type: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    cancer_site: Optional[str] = Query(None),
    hospital_site: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get the open action distribution charts used by Service Overview."""
    svc = PTLService(db)
    return await svc.get_service_overview_team(
        pathway_type=pathway_type,
        tag=tag,
        cancer_site=cancer_site,
        hospital_site=hospital_site,
    )


@router.get("/integration/status", response_model=IntegrationStatusResponse, tags=["system"])
async def get_integration_status(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get TIE/audit pipeline status, source outcomes, and recent errors."""
    svc = PTLService(db)
    return await svc.get_integration_status()


@router.get("/simulation/catalog", response_model=SimulationCatalogResponse, tags=["simulation"])
async def get_simulation_catalog():
    """Get available synthetic source-system options for the operator studio."""
    return simulation_hub.get_catalog()


@router.get("/simulation/runs", response_model=list[SimulationRunSummary], tags=["simulation"])
async def list_simulation_runs():
    """List recent synthetic integration runs."""
    return await simulation_hub.list_runs()


@router.post("/simulation/runs", response_model=SimulationRunDetail, status_code=202, tags=["simulation"])
async def create_simulation_run(body: SimulationRunRequest):
    """Start a synthetic integration replay and return the queued run."""
    return await simulation_hub.start_run(body)


@router.get("/simulation/runs/{run_id}", response_model=SimulationRunDetail, tags=["simulation"])
async def get_simulation_run(run_id: str):
    """Get the full status and event stream for one simulation run."""
    run = await simulation_hub.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    return run


# ─── Search ─────────────────────────────────────────────────────────────────

@router.get("/search", response_model=list[SearchResult], tags=["search"])
async def search_patients(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Search patients by name, NHS number, or hospital number."""
    svc = PTLService(db)
    return await svc.search_patients(q, limit)


# ─── Health ─────────────────────────────────────────────────────────────────

@router.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "service": "cancer360-api", "version": "0.1.0"}
