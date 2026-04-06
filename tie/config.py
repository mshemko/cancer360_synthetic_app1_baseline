"""Runtime configuration for the native TIE."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TieConfig:
    database_url: str = os.environ.get("DATABASE_URL", "postgresql+asyncpg://cancer360:localdev@localhost:5432/cancer360")
    mllp_host: str = os.environ.get("TIE_MLLP_HOST", "127.0.0.1")
    mllp_port: int = int(os.environ.get("TIE_MLLP_PORT", "2575"))
    incoming_root: Path = Path(os.environ.get("TIE_INCOMING_ROOT", "incoming"))
    poll_seconds: float = float(os.environ.get("TIE_POLL_SECONDS", "1.0"))
    file_subdirs: tuple[str, ...] = ("somerset", "aria", "endoscopy")


def get_config() -> TieConfig:
    return TieConfig()
