"""Generate synthetic patient master data for Cancer 360."""

from __future__ import annotations

import json
import random
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "generation_params.yaml"
REFERENCE_DIR = ROOT / "source_systems" / "config" / "reference_data"
OUTPUT_PATH = ROOT / "source_systems" / "output" / "journeys" / "patients.json"

TITLE_WEIGHTS = [
    ("Mr", 0.32),
    ("Mrs", 0.18),
    ("Ms", 0.24),
    ("Miss", 0.08),
    ("Dr", 0.18),
]
NORFOLK_TOWNS = [
    "Norwich",
    "Great Yarmouth",
    "King's Lynn",
    "Dereham",
    "Thetford",
    "Wymondham",
    "Attleborough",
    "Cromer",
    "Aylsham",
    "North Walsham",
    "Sheringham",
    "Fakenham",
    "Diss",
    "Beccles",
    "Bungay",
]
ROAD_NAMES = [
    "Oak",
    "Church",
    "Mill",
    "Station",
    "Victoria",
    "Queen",
    "Market",
    "Castle",
    "Highfield",
    "Willow",
    "Cedar",
    "Beech",
    "River",
    "Norfolk",
    "Meadow",
    "School",
    "Rectory",
    "Yarmouth",
    "Crown",
]
ROAD_TYPES = ["Road", "Street", "Close", "Lane", "Avenue", "Drive", "Gardens", "Way"]


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def weighted_choice(options: list[tuple[str, float]]) -> str:
    labels, weights = zip(*options)
    return random.choices(labels, weights=weights, k=1)[0]


def generate_nhs_number() -> str:
    while True:
        base_digits = [random.randint(0, 9) for _ in range(9)]
        total = sum((10 - idx) * digit for idx, digit in enumerate(base_digits))
        remainder = total % 11
        check_digit = 11 - remainder
        if check_digit == 11:
            check_digit = 0
        if check_digit == 10:
            continue
        return "".join(str(digit) for digit in base_digits) + str(check_digit)


def random_date_of_birth() -> date:
    age_band = random.choices(
        population=["30_44", "45_54", "55_64", "65_74", "75_90"],
        weights=[0.06, 0.14, 0.34, 0.30, 0.16],
        k=1,
    )[0]
    bounds = {
        "30_44": (30, 44),
        "45_54": (45, 54),
        "55_64": (55, 64),
        "65_74": (65, 74),
        "75_90": (75, 90),
    }
    min_age, max_age = bounds[age_band]
    age = random.randint(min_age, max_age)
    today = date.today()
    start = today - timedelta(days=(age * 365) + 364)
    end = today - timedelta(days=age * 365)
    return start + timedelta(days=random.randint(0, (end - start).days))


def random_postcode() -> str:
    district = random.randint(1, 35)
    sector = random.randint(1, 9)
    suffix = "".join(random.choices("ABCDEFGHJKSTUWXYZ", k=2))
    return f"NR{district} {sector}{suffix}"


def random_phone() -> str:
    return f"07{random.randint(100, 999)} {random.randint(100000, 999999)}"


def random_address() -> tuple[str, str, str]:
    number = random.randint(1, 199)
    road = random.choice(ROAD_NAMES)
    road_type = random.choice(ROAD_TYPES)
    town = random.choice(NORFOLK_TOWNS)
    return f"{number} {road} {road_type}", town, random_postcode()


def maybe_date_of_death(dob: date) -> str | None:
    if random.random() > 0.05:
        return None
    min_death = dob + timedelta(days=35 * 365)
    max_death = date.today() - timedelta(days=14)
    if min_death >= max_death:
        return None
    death_date = min_death + timedelta(days=random.randint(0, (max_death - min_death).days))
    return death_date.isoformat()


def generate_patients(config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    config = config or load_yaml(CONFIG_PATH)
    patient_count = int(config["generation"]["patients"])
    names = load_json(REFERENCE_DIR / "first_names.json")
    surnames = load_json(REFERENCE_DIR / "surnames.json")
    gp_practices = load_json(REFERENCE_DIR / "gp_practices.json")

    patients: list[dict[str, Any]] = []
    next_mrn = 1000001

    for _ in range(patient_count):
        sex = random.choice(["Male", "Female"])
        if sex == "Male":
            first_name = random.choice(names["male"])
            preferred_titles = [("Mr", 0.80), ("Dr", 0.20)]
        else:
            first_name = random.choice(names["female"])
            preferred_titles = [("Mrs", 0.26), ("Ms", 0.34), ("Miss", 0.18), ("Dr", 0.22)]

        title = weighted_choice(preferred_titles if random.random() < 0.8 else TITLE_WEIGHTS)
        surname = random.choice(surnames)
        dob = random_date_of_birth()
        address_line_1, town, postcode = random_address()
        gp = random.choice(gp_practices)
        next_of_kin_present = random.random() < 0.8
        next_of_kin_name = (
            f"{random.choice(names['male'] + names['female'])} {random.choice(surnames)}"
            if next_of_kin_present
            else None
        )
        next_of_kin_number = random_phone() if next_of_kin_present else None
        gender_identity = sex if random.random() < 0.98 else ("Female" if sex == "Male" else "Male")

        patients.append(
            {
                "person_id": str(uuid.uuid4()),
                "mrn": f"{next_mrn:07d}",
                "nhs_number": generate_nhs_number(),
                "first_name": first_name,
                "surname": surname,
                "title": title,
                "date_of_birth": dob.isoformat(),
                "date_of_death": maybe_date_of_death(dob),
                "sex": sex,
                "gender_identity": gender_identity,
                "address_line_1": address_line_1,
                "address_line_2": town,
                "postcode": postcode,
                "phone_number": random_phone(),
                "registered_gp": gp,
                "next_of_kin_name": next_of_kin_name,
                "next_of_kin_number": next_of_kin_number,
                "source_system_name": config["generation"]["source_systems"]["patient"],
                "last_refreshed_at_source_timestamp": datetime.now().astimezone().isoformat(),
            }
        )
        next_mrn += 1

    return patients


def main() -> None:
    patients = generate_patients()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(patients, indent=2), encoding="utf-8")
    print(f"Generated {len(patients)} patients -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
