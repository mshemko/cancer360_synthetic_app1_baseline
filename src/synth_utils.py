"""Shared utility functions for Cancer 360 synthetic data and integration."""

from datetime import date, datetime, timedelta
from typing import Optional, List
import random


# ─── NHS Number ─────────────────────────────────────────────────────────────

def generate_nhs_number(index: int) -> str:
    """Generate a valid NHS number using Modulus 11 check digit.

    Uses the synthetic range 999-xxx-xxxx to avoid collisions with real numbers.
    """
    # Base: 999 + 6 digit sequential number
    base = f"999{index:06d}"
    if len(base) != 9:
        base = base[:9]

    # Calculate Modulus 11 check digit
    weights = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(base[i]) * weights[i] for i in range(9))
    remainder = total % 11
    check_digit = 11 - remainder

    if check_digit == 11:
        check_digit = 0
    elif check_digit == 10:
        # Invalid — adjust base and recalculate
        return generate_nhs_number(index + 100000)

    return base + str(check_digit)


def validate_nhs_number(nhs_number: str) -> bool:
    """Validate an NHS number using Modulus 11."""
    nhs = nhs_number.replace(" ", "").replace("-", "").strip()
    if len(nhs) != 10 or not nhs.isdigit():
        return False

    weights = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(nhs[i]) * weights[i] for i in range(9))
    remainder = total % 11
    check_digit = 11 - remainder

    if check_digit == 11:
        check_digit = 0
    elif check_digit == 10:
        return False

    return int(nhs[9]) == check_digit


def format_nhs_number(nhs: str) -> str:
    """Format NHS number as XXX XXX XXXX."""
    clean = nhs.replace(" ", "").replace("-", "")
    if len(clean) == 10:
        return f"{clean[:3]} {clean[3:6]} {clean[6:]}"
    return clean


# ─── Date/Time Helpers ──────────────────────────────────────────────────────

UK_BANK_HOLIDAYS_2024_2025 = {
    date(2024, 1, 1), date(2024, 3, 29), date(2024, 4, 1),
    date(2024, 5, 6), date(2024, 5, 27), date(2024, 8, 26),
    date(2024, 12, 25), date(2024, 12, 26),
    date(2025, 1, 1), date(2025, 4, 18), date(2025, 4, 21),
    date(2025, 5, 5), date(2025, 5, 26), date(2025, 8, 25),
    date(2025, 12, 25), date(2025, 12, 26),
}


def is_working_day(d: date) -> bool:
    """Check if a date is a working day (not weekend or bank holiday)."""
    return d.weekday() < 5 and d not in UK_BANK_HOLIDAYS_2024_2025


def next_working_day(d: date) -> date:
    """Return the next working day on or after the given date."""
    while not is_working_day(d):
        d += timedelta(days=1)
    return d


def add_working_days(start: date, days: int) -> date:
    """Add N working days to a date."""
    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if is_working_day(current):
            added += 1
    return current


def random_working_day(start: date, min_days: int, max_days: int) -> date:
    """Generate a random working day between min_days and max_days from start."""
    target = start + timedelta(days=random.randint(min_days, max_days))
    return next_working_day(target)


def random_time(hour_start: int = 8, hour_end: int = 17) -> str:
    """Generate a random clinic time between hour_start and hour_end."""
    hour = random.randint(hour_start, hour_end - 1)
    minute = random.choice([0, 15, 30, 45])
    return f"{hour:02d}:{minute:02d}"


# ─── Clinical Logic Helpers ─────────────────────────────────────────────────

CANCER_TYPE_MAP = {
    "breast": {"code": "101", "icd10": ["C50.1", "C50.2", "C50.3", "C50.4", "C50.8", "C50.9"], "specialty": "103"},
    "colorectal": {"code": "102", "icd10": ["C18.0", "C18.2", "C18.7", "C19", "C20"], "specialty": "104"},
    "lung": {"code": "103", "icd10": ["C34.1", "C34.2", "C34.3", "C34.9"], "specialty": "340"},
    "prostate": {"code": "104", "icd10": ["C61"], "specialty": "101"},
    "gynae": {"code": "105", "icd10": ["C53.0", "C54.1", "C56"], "specialty": "502"},
    "upper_gi": {"code": "106", "icd10": ["C15.3", "C15.5", "C16.0", "C16.9"], "specialty": "100"},
    "urology": {"code": "107", "icd10": ["C64", "C67.0", "C67.9"], "specialty": "101"},
    "haem": {"code": "108", "icd10": ["C81.1", "C83.3", "C85.1", "C91.0", "C92.0"], "specialty": "370"},
    "head_neck": {"code": "109", "icd10": ["C01", "C02.1", "C10.0", "C32.0"], "specialty": "120"},
    "melanoma": {"code": "110", "icd10": ["C43.5", "C43.6", "C43.7"], "specialty": "100"},
}

TNM_STAGES = {
    "IA": [("T1", "N0", "M0")],
    "IB": [("T2", "N0", "M0")],
    "IIA": [("T2", "N1", "M0"), ("T3", "N0", "M0")],
    "IIB": [("T3", "N1", "M0"), ("T4", "N0", "M0")],
    "IIIA": [("T3", "N2", "M0"), ("T4", "N1", "M0")],
    "IIIB": [("T4", "N2", "M0")],
    "IIIC": [("T4", "N3", "M0")],
    "IV": [("T4", "N3", "M1"), ("T2", "N1", "M1"), ("T3", "N2", "M1")],
}


def stage_to_tnm(stage_group: str) -> tuple:
    """Convert a stage group to a realistic TNM combination."""
    combos = TNM_STAGES.get(stage_group, [("TX", "NX", "MX")])
    return random.choice(combos)


def calculate_bsa(height_cm: float, weight_kg: float) -> float:
    """Calculate body surface area using the Du Bois formula."""
    return 0.007184 * (height_cm ** 0.725) * (weight_kg ** 0.425)


def calculate_breach_risk(referral_date: date, diagnosis_date: Optional[date] = None,
                          treatment_date: Optional[date] = None) -> str:
    """Calculate CWT breach risk based on days elapsed."""
    today = date.today()
    days = (today - referral_date).days

    if treatment_date:
        tx_days = (treatment_date - referral_date).days
        return "breached" if tx_days > 62 else "none"

    if days > 62:
        return "breached"
    if days > 50:
        return "high"
    if days > 35:
        return "medium"
    if days > 21:
        return "low"
    return "none"


# ─── HL7 Message Builder ───────────────────────────────────────────────────

def build_hl7_msh(sending_app: str, sending_fac: str, receiving_app: str,
                   receiving_fac: str, msg_type: str, msg_id: str,
                   timestamp: Optional[datetime] = None) -> str:
    """Build an MSH segment."""
    ts = (timestamp or datetime.now()).strftime("%Y%m%d%H%M%S")
    return f"MSH|^~\\&|{sending_app}|{sending_fac}|{receiving_app}|{receiving_fac}|{ts}||{msg_type}|{msg_id}|P|2.4"


def build_hl7_pid(nhs_number: str, hospital_number: str, surname: str,
                   forename: str, dob: date, sex: str, address: str = "",
                   postcode: str = "", phone: str = "", prefix: str = "") -> str:
    """Build a PID segment."""
    dob_str = dob.strftime("%Y%m%d")
    return (
        f"PID|1||{nhs_number}^^^NHS^NH~{hospital_number}^^^LOCAL^MR||"
        f"{surname}^{forename}^^^{prefix}||{dob_str}|{sex}|||"
        f"{address}^^London^^{postcode}||{phone}"
    )


def build_hl7_obr(order_id: str, filler_id: str, test_code: str, test_name: str,
                    order_dt: datetime, result_dt: Optional[datetime] = None,
                    provider_code: str = "", provider_name: str = "",
                    status: str = "F") -> str:
    """Build an OBR segment."""
    dt_str = order_dt.strftime("%Y%m%d%H%M%S")
    res_str = result_dt.strftime("%Y%m%d%H%M%S") if result_dt else ""
    return (
        f"OBR|1|{order_id}|{filler_id}|{test_code}^{test_name}^LOCAL|||{dt_str}"
        f"|||||||{dt_str}|{provider_code}^{provider_name}||||||"
        f"{res_str}|||{status}"
    )


def build_hl7_obx(set_id: int, value_type: str, code: str, name: str,
                    value: str, units: str = "", ref_range: str = "",
                    flag: str = "", status: str = "F") -> str:
    """Build an OBX segment."""
    return (
        f"OBX|{set_id}|{value_type}|{code}^{name}^LOCAL||{value}|{units}|{ref_range}|{flag}|||{status}"
    )
