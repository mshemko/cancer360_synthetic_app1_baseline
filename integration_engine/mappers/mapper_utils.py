"""Shared helpers for canonical mapping."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable


def empty_to_none(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped in {"", "None", "null", "NULL", "No value"}:
            return None
        return stripped
    return value


def parse_date(value: Any) -> date | None:
    value = empty_to_none(value)
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()

    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y%m%d%H%M", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(text[: len(datetime.now().strftime(fmt))], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def parse_datetime(value: Any) -> datetime | None:
    value = empty_to_none(value)
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)

    text = str(value).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y%m%d%H%M%S", "%Y%m%d%H%M", "%Y%m%d"):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_bool(value: Any) -> bool | None:
    value = empty_to_none(value)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "t", "1", "yes", "y"}:
        return True
    if text in {"false", "f", "0", "no", "n"}:
        return False
    return None


def current_timestamp() -> datetime:
    return datetime.now(timezone.utc)


def full_name(first_name: Any, surname: Any) -> str | None:
    first = empty_to_none(first_name)
    last = empty_to_none(surname)
    if not first and not last:
        return None
    if first and last:
        return f"{last}, {first}"
    return str(last or first)


def derive_stage(staging_t: str | None, staging_n: str | None, staging_m: str | None) -> str | None:
    if not staging_t and not staging_n and not staging_m:
        return None
    if (staging_m or "").upper() == "M1":
        return "Stage IV"
    t_val = (staging_t or "").upper()
    n_val = (staging_n or "").upper()
    if t_val in {"T1", "T2"} and n_val in {"", "N0"}:
        return "Stage I" if t_val == "T1" else "Stage II"
    if n_val in {"N1", "N2"} or t_val == "T3":
        return "Stage III"
    if t_val == "T4" or n_val == "N3":
        return "Stage IV"
    return "Stage II"


def person_id_from_lookup(
    nhs_number: str | None,
    mrn: str | None,
    lookup: dict[str, str] | None = None,
    resolver: Callable[[str | None, str | None], str | None] | None = None,
) -> str | None:
    if resolver is not None:
        return resolver(nhs_number, mrn)
    if lookup is None:
        return None
    for key in (nhs_number, mrn):
        key = empty_to_none(key)
        if key and key in lookup:
            return lookup[key]
    return None


def safe_date_plus(value: date | None, days: int) -> date | None:
    if value is None:
        return None
    return value + timedelta(days=days)
