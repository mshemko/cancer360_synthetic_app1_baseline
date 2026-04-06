"""Generate synthetic cancer pathways from generated patient identities."""

from __future__ import annotations

import json
import random
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

try:
    from .patient_generator import generate_patients
except ImportError:
    from patient_generator import generate_patients


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "generation_params.yaml"
REFERENCE_DIR = ROOT / "source_systems" / "config" / "reference_data"
PATIENT_OUTPUT = ROOT / "source_systems" / "output" / "journeys" / "patients.json"
PATHWAY_OUTPUT = ROOT / "source_systems" / "output" / "journeys" / "pathways.json"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def choose_weighted(mapping: dict[str, float]) -> str:
    keys = list(mapping.keys())
    weights = list(mapping.values())
    return random.choices(keys, weights=weights, k=1)[0]


def random_date_between(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def maybe_probability(rate: float) -> bool:
    return random.random() < rate


def iso_or_none(value: date | None) -> str | None:
    return value.isoformat() if value else None


def get_icd10_for_site(site: str, codes: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    return random.choice(codes[site])


def choose_subsite(site: str, cancer_sites: list[dict[str, Any]]) -> str:
    match = next(item for item in cancer_sites if item["cancer_site"] == site)
    return random.choice(match["cancer_subsites"])


def build_scenarios(config: dict[str, Any]) -> dict[str, bool]:
    rates = config["generation"]["scenario_rates"]
    return {name: maybe_probability(float(rate)) for name, rate in rates.items()}


def maybe_second_pathway() -> bool:
    return random.random() < 0.10


def generate_pathways(patients: list[dict[str, Any]], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    config = config or load_yaml(CONFIG_PATH)
    cancer_sites = load_json(REFERENCE_DIR / "cancer_sites.json")
    hospital_sites = load_json(REFERENCE_DIR / "hospital_sites.json")
    icd10_codes = load_json(REFERENCE_DIR / "icd10_codes.json")

    start = parse_date(config["generation"]["date_range"]["start"])
    end = parse_date(config["generation"]["date_range"]["end"])
    pathway_settings = config["generation"]["pathway_settings"]
    site_distribution = config["generation"]["cancer_site_distribution"]

    referral_routes = [
        ("Two Week Wait", 0.60),
        ("Urgent", 0.15),
        ("Screening", 0.10),
        ("Upgrade", 0.10),
        ("Emergency", 0.05),
    ]

    pathways: list[dict[str, Any]] = []

    for patient in patients:
        pathway_count = 2 if maybe_second_pathway() else 1
        for _ in range(pathway_count):
            scenarios = build_scenarios(config)
            cancer_site = choose_weighted(site_distribution)
            cancer_sub_site = choose_subsite(cancer_site, cancer_sites)
            hospital = random.choice(hospital_sites)
            referral_route = random.choices(
                [item[0] for item in referral_routes],
                weights=[item[1] for item in referral_routes],
                k=1,
            )[0]

            original_start = random_date_between(start, end)
            waiting_adjustment = 0 if random.random() < 0.85 else random.randint(1, 14)
            adjusted_start = original_start + timedelta(days=waiting_adjustment)
            referral_received = original_start
            first_seen = referral_received + timedelta(days=random.randint(3, 21))
            patient_informed = first_seen + timedelta(days=random.randint(1, 5))

            diagnosis_date = None
            diagnosis_text = None
            diagnosis_icd10_code = None
            if scenarios["has_diagnosis"]:
                diagnosis_date = referral_received + timedelta(days=random.randint(7, 42))
                if diagnosis_date < first_seen:
                    diagnosis_date = first_seen + timedelta(days=random.randint(1, 10))
                icd10 = get_icd10_for_site(cancer_site, icd10_codes)
                diagnosis_text = icd10["description"]
                diagnosis_icd10_code = icd10["code"]

            decision_to_treat_date = None
            first_treatment_date = None
            first_treatment_type = None
            treatment_site = None
            treatment_site_ods_code = None
            organisation_site_treatment = None
            if scenarios["has_first_treatment"] and diagnosis_date is not None:
                decision_to_treat_date = diagnosis_date + timedelta(days=random.randint(1, 14))
                first_treatment_date = decision_to_treat_date + timedelta(days=random.randint(1, 21))
                first_treatment_type = random.choice(
                    ["Surgery", "Chemotherapy", "Radiotherapy", "Immunotherapy"]
                )
                treatment_org = random.choice(hospital_sites)
                treatment_site = treatment_org["hospital_site"]
                treatment_site_ods_code = treatment_org["ods_code"]
                organisation_site_treatment = treatment_org["hospital_site"]

            is_open = random.random() < float(pathway_settings["open_rate"])
            pathway_closed_date = None
            if not is_open:
                close_anchor = first_treatment_date or diagnosis_date or first_seen
                pathway_closed_date = close_anchor + timedelta(days=random.randint(30, 180))

            upgrade_date = referral_received if referral_route == "Upgrade" else None
            benign = diagnosis_date is not None and random.random() < float(pathway_settings["benign_rate"])
            breach_28 = adjusted_start + timedelta(days=28)
            breach_31 = adjusted_start + timedelta(days=31)
            breach_62 = adjusted_start + timedelta(days=62)

            current_or_close = pathway_closed_date or date.today()
            is_28_open = is_open and current_or_close >= breach_28
            is_31_open = is_open and current_or_close >= breach_31
            is_62_open = is_open and current_or_close >= breach_62
            referral_source = (
                patient["registered_gp"]["name"]
                if isinstance(patient["registered_gp"], dict)
                else random.choice([patient["registered_gp"], hospital["hospital_site"]])
            )

            pathway_id = str(uuid.uuid4())
            pathways.append(
                {
                    "pathway_id": pathway_id,
                    "person_id": patient["person_id"],
                    "mrn": patient["mrn"],
                    "nhs_number": patient["nhs_number"],
                    "first_name": patient["first_name"],
                    "surname": patient["surname"],
                    "full_name": f"{patient['surname']}, {patient['first_name']}",
                    "cancer_site": cancer_site,
                    "cancer_sub_site": cancer_sub_site,
                    "hospital_site": hospital["hospital_site"],
                    "hospital_site_id": hospital["hospital_site_id"],
                    "pathway_referral_route": referral_route,
                    "original_pathway_start_date": original_start.isoformat(),
                    "waiting_time_adjustment_days": waiting_adjustment,
                    "adjusted_pathway_start_date": adjusted_start.isoformat(),
                    "pathway_status": "open" if is_open else "closed",
                    "pathway_closed_date": iso_or_none(pathway_closed_date),
                    "28_day_breach_date": breach_28.isoformat(),
                    "31_day_breach_date": breach_31.isoformat(),
                    "62_day_breach_date": breach_62.isoformat(),
                    "referral_received_date": referral_received.isoformat(),
                    "first_seen_date": first_seen.isoformat(),
                    "first_seen_site": hospital["hospital_site"],
                    "first_seen_site_ods_code": hospital["ods_code"],
                    "patient_informed_date": patient_informed.isoformat(),
                    "diagnosis_date": iso_or_none(diagnosis_date),
                    "diagnosis": diagnosis_text,
                    "diagnosis_icd_10_code": diagnosis_icd10_code,
                    "decision_to_treat_date": iso_or_none(decision_to_treat_date),
                    "first_treatment_date": iso_or_none(first_treatment_date),
                    "first_treatment_type": first_treatment_type,
                    "treatment_site": treatment_site,
                    "treatment_site_ods_code": treatment_site_ods_code,
                    "organisation_site_treatment": organisation_site_treatment,
                    "upgrade_date": iso_or_none(upgrade_date),
                    "referral_source": referral_source,
                    "is_benign": benign,
                    "is_62_day_pathway_open": is_62_open,
                    "is_31_day_pathway_open": is_31_open,
                    "is_28_day_pathway_open": is_28_open,
                    "is_any_pathway_type_open": is_28_open or is_31_open or is_62_open,
                    "date_of_birth": patient["date_of_birth"],
                    "date_of_death": patient["date_of_death"],
                    "source_system_name": config["generation"]["source_systems"]["pathway"],
                    "last_refreshed_at_source_timestamp": datetime.now().astimezone().isoformat(),
                    "timeline_skeleton": {
                        "pathway_id": pathway_id,
                        "key_dates": {
                            "referral": referral_received.isoformat(),
                            "first_seen": first_seen.isoformat(),
                            "diagnosis": iso_or_none(diagnosis_date),
                            "dtt": iso_or_none(decision_to_treat_date),
                            "first_treatment": iso_or_none(first_treatment_date),
                            "closed": iso_or_none(pathway_closed_date),
                        },
                        "scenarios": scenarios,
                    },
                }
            )

    return pathways


def main() -> None:
    config = load_yaml(CONFIG_PATH)
    if PATIENT_OUTPUT.exists():
        patients = load_json(PATIENT_OUTPUT)
    else:
        patients = generate_patients(config)
        PATIENT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        PATIENT_OUTPUT.write_text(json.dumps(patients, indent=2), encoding="utf-8")

    pathways = generate_pathways(patients, config)
    PATHWAY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PATHWAY_OUTPUT.write_text(json.dumps(pathways, indent=2), encoding="utf-8")
    print(f"Generated {len(pathways)} pathways -> {PATHWAY_OUTPUT}")


if __name__ == "__main__":
    main()
