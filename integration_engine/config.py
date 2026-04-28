"""Shared configuration for the integration engine."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg2


ROOT = Path(__file__).resolve().parents[1]
SOURCE_OUTPUT_DIR = ROOT / "source_systems" / "output"
HL7_DIR = SOURCE_OUTPUT_DIR / "hl7"
CSV_DIR = SOURCE_OUTPUT_DIR / "csv"
XML_DIR = SOURCE_OUTPUT_DIR / "xml"
JSON_DIR = SOURCE_OUTPUT_DIR / "json"
MIGRATIONS_DIR = ROOT / "db" / "migrations"

DEFAULT_DATABASE_URL = "postgresql://cancer360:localdev@localhost:5432/cancer360"


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_connection():
    return psycopg2.connect(get_database_url())
