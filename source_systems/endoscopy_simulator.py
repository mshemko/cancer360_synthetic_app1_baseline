"""Endoscopy simulator producing a nightly CSV export."""

from __future__ import annotations

from datetime import datetime

from source_systems.common import render_csv

ENDOSCOPY_FIELDS = ["endoscopy_id", "nhs_number", "is_reported", "ordered_date", "scheduled_date", "attendance_date", "report_authorised_date", "report_prepared_date", "exam_status", "modality", "endoscopy_type", "endoscopy_priority", "endoscopy_report_text", "source_system_name", "last_refreshed_at_source_timestamp"]


def generate_events(journeys: list[dict]) -> list[dict]:
    rows = [journey["endoscopy"] for journey in journeys if journey["endoscopy"]]
    if not rows:
        return []
    extract_time = datetime.now().replace(hour=20, minute=0, second=0, microsecond=0)
    return [{"timestamp": extract_time.isoformat(), "source": "endoscopy", "format": "file", "subdir": "endoscopy", "filename": f"endoscopy_{extract_time.strftime('%Y%m%d%H%M%S')}.csv", "payload": render_csv(rows, ENDOSCOPY_FIELDS)}]
