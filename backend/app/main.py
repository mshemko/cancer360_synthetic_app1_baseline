"""Cancer 360 — NHS FDP PoC Application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.v1 import router as v1_router

settings = get_settings()

app = FastAPI(
    title="Cancer 360 API",
    description="NHS Federated Data Platform — Cancer 360 Patient Tracking and Clinical Decision Support",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(v1_router)


@app.get("/", tags=["root"])
async def root():
    return {
        "service": "Cancer 360 API",
        "version": settings.app_version,
        "trust": settings.trust_name,
        "docs": "/docs",
    }
