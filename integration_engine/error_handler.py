"""Helpers for recording integration errors."""

from __future__ import annotations

import logging
from typing import Any

from integration_engine import config


logger = logging.getLogger(__name__)


def log_error(
    source_system: str,
    correlation_id: str | None,
    error_type: str,
    error_message: str,
    payload_snippet: str | None = None,
    connection: Any | None = None,
) -> None:
    owns_connection = connection is None
    connection = connection or config.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO audit.error_log (
                    source_system,
                    correlation_id,
                    error_type,
                    error_message,
                    payload_snippet,
                    occurred_at
                )
                VALUES (%s, %s, %s, %s, %s, NOW())
                """,
                (
                    source_system,
                    correlation_id,
                    error_type,
                    error_message,
                    payload_snippet,
                ),
            )
        connection.commit()
    except Exception as exc:  # pragma: no cover - best-effort logging
        if connection:
            connection.rollback()
        logger.error("Failed to write audit.error_log entry: %s", exc)
    finally:
        if owns_connection and connection:
            connection.close()
