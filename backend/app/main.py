"""Cancer 360 application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import router as v1_router
from app.config import get_settings

settings = get_settings()
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="Cancer 360 API",
    description="NHS Federated Data Platform - Cancer 360 Patient Tracking and Clinical Decision Support",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/service-info", tags=["root"])
async def service_info():
    return {
        "service": "Cancer 360 API",
        "version": settings.app_version,
        "trust": settings.trust_name,
        "app": "/",
        "ptl": "/ptl",
        "actions": "/actions",
        "service_overview": "/service-overview",
        "team_overview": "/team-overview",
        "integration": "/integration",
        "playback": "/playback",
        "seeding": "/seeding",
        "docs": "/docs",
        "studio": "/studio",
        "studio_playback": "/studio/playback",
    }


@app.get("/", include_in_schema=False)
@app.get("/app", include_in_schema=False)
@app.get("/ptl", include_in_schema=False)
@app.get("/actions", include_in_schema=False)
@app.get("/service-overview", include_in_schema=False)
@app.get("/team-overview", include_in_schema=False)
async def main_app():
    return FileResponse(STATIC_DIR / "cancer360_workspace.html")


@app.get("/integration", include_in_schema=False)
async def integration_dashboard():
    return FileResponse(STATIC_DIR / "integration_dashboard.html")


@app.get("/seeding", include_in_schema=False)
@app.get("/studio", include_in_schema=False)
async def seeding_console():
    return FileResponse(STATIC_DIR / "seeding_console.html")


@app.get("/playback", include_in_schema=False)
@app.get("/studio/playback", include_in_schema=False)
async def integration_playback():
    return FileResponse(STATIC_DIR / "integration_playback.html")
