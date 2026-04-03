"""Cancer 360 API v1 endpoints."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user, create_access_token, verify_password
from app.models import CancerAction, Patient
from app.schemas import (
    PTLResponse, Patient360Response, DashboardMetrics, SearchResult,
    ActionCreate, ActionUpdate, ActionSchema,
    TokenRequest, TokenResponse,
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
    pathway_status: Optional[str] = Query(None, description="Filter by pathway status"),
    breach_risk: Optional[str] = Query(None, description="Filter by breach risk level"),
    assigned_team: Optional[str] = Query(None, description="Filter by assigned MDT team"),
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
        cancer_type=cancer_type,
        pathway_status=pathway_status,
        breach_risk=breach_risk,
        assigned_team=assigned_team,
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


# ─── Actions ────────────────────────────────────────────────────────────────

@router.get("/actions", response_model=list[ActionSchema], tags=["actions"])
async def get_actions(
    status: Optional[str] = Query(None),
    assigned_team: Optional[str] = Query(None),
    patient_id: Optional[UUID] = Query(None),
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

    result = await db.execute(query.limit(200))
    return [ActionSchema.model_validate(a) for a in result.scalars().all()]


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

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(action, field, value)

    if body.status == "completed":
        action.completed_by = user.get("full_name", "System")
        action.completed_date = datetime.now(timezone.utc)

    action.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(action)
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
