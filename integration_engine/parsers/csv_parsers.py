"""CSV parsers for NHS national dataset formats — SACT, RTDS, CDS."""

import csv
import io
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class ParsedCSVRecord:
    record_type: str
    source_file: str
    row_number: int
    fields: Dict[str, Any]
    raw_row: str = ""


@dataclass
class ParsedCSVFile:
    file_type: str
    filename: str
    records: List[ParsedCSVRecord] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    total_rows: int = 0
    parsed_rows: int = 0


class SACTParser:
    """Parse SACT (Systemic Anti-Cancer Therapy) national dataset CSV files."""

    EXPECTED_COLUMNS = [
        "NHS_NUMBER", "ORGANISATION_CODE", "CONSULTANT_CODE",
        "PRIMARY_DIAGNOSIS", "MORPHOLOGY", "REGIMEN",
        "REGIMEN_INTENT", "CYCLE_NUMBER", "MAX_CYCLES",
        "START_DATE_REGIMEN", "START_DATE_CYCLE",
        "DRUG_NAME", "DRUG_DOSE", "DRUG_DOSE_UNIT", "ROUTE",
        "BSA", "HEIGHT", "WEIGHT",
        "PERFORMANCE_STATUS", "CYCLE_OUTCOME",
        "ADMINISTRATION_DATE",
    ]

    def parse(self, content: str, filename: str = "") -> ParsedCSVFile:
        result = ParsedCSVFile(file_type="SACT", filename=filename)

        reader = csv.DictReader(io.StringIO(content))
        for i, row in enumerate(reader, start=1):
            result.total_rows += 1
            try:
                record = ParsedCSVRecord(
                    record_type="sact_cycle",
                    source_file=filename,
                    row_number=i,
                    fields={
                        "nhs_number": self._clean_nhs(row.get("NHS_NUMBER", "")),
                        "organisation_code": row.get("ORGANISATION_CODE", "").strip(),
                        "consultant_code": row.get("CONSULTANT_CODE", "").strip(),
                        "primary_diagnosis": row.get("PRIMARY_DIAGNOSIS", "").strip(),
                        "morphology": row.get("MORPHOLOGY", "").strip(),
                        "regimen": row.get("REGIMEN", "").strip(),
                        "regimen_intent": row.get("REGIMEN_INTENT", "").strip(),
                        "cycle_number": self._int_or_none(row.get("CYCLE_NUMBER")),
                        "max_cycles": self._int_or_none(row.get("MAX_CYCLES")),
                        "start_date_regimen": self._parse_date(row.get("START_DATE_REGIMEN")),
                        "start_date_cycle": self._parse_date(row.get("START_DATE_CYCLE")),
                        "drug_name": row.get("DRUG_NAME", "").strip(),
                        "drug_dose": self._float_or_none(row.get("DRUG_DOSE")),
                        "drug_dose_unit": row.get("DRUG_DOSE_UNIT", "").strip(),
                        "route": row.get("ROUTE", "").strip(),
                        "bsa": self._float_or_none(row.get("BSA")),
                        "height": self._float_or_none(row.get("HEIGHT")),
                        "weight": self._float_or_none(row.get("WEIGHT")),
                        "performance_status": self._int_or_none(row.get("PERFORMANCE_STATUS")),
                        "cycle_outcome": row.get("CYCLE_OUTCOME", "").strip(),
                        "administration_date": self._parse_date(row.get("ADMINISTRATION_DATE")),
                    },
                )
                result.records.append(record)
                result.parsed_rows += 1
            except Exception as e:
                result.errors.append(f"Row {i}: {e}")

        logger.info(f"SACT: parsed {result.parsed_rows}/{result.total_rows} rows from {filename}")
        return result

    @staticmethod
    def _clean_nhs(val: str) -> str:
        return val.replace(" ", "").replace("-", "").strip()[:10]

    @staticmethod
    def _parse_date(val: Optional[str]) -> Optional[str]:
        if not val or not val.strip():
            return None
        v = val.strip()
        # Handle common NHS date formats
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y%m%d", "%d-%m-%Y"):
            try:
                from datetime import datetime
                return datetime.strptime(v, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return v

    @staticmethod
    def _int_or_none(val: Optional[str]) -> Optional[int]:
        if not val or not val.strip():
            return None
        try:
            return int(float(val.strip()))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _float_or_none(val: Optional[str]) -> Optional[float]:
        if not val or not val.strip():
            return None
        try:
            return float(val.strip())
        except (ValueError, TypeError):
            return None


class RTDSParser:
    """Parse RTDS (Radiotherapy Dataset) national CSV files."""

    def parse(self, content: str, filename: str = "") -> ParsedCSVFile:
        result = ParsedCSVFile(file_type="RTDS", filename=filename)

        reader = csv.DictReader(io.StringIO(content))
        for i, row in enumerate(reader, start=1):
            result.total_rows += 1
            try:
                record = ParsedCSVRecord(
                    record_type="rt_course",
                    source_file=filename,
                    row_number=i,
                    fields={
                        "nhs_number": row.get("NHS_NUMBER", "").replace(" ", "").strip(),
                        "organisation_code": row.get("ORGANISATION_CODE", "").strip(),
                        "treatment_intent": row.get("TREATMENT_INTENT", "").strip(),
                        "treatment_site": row.get("TREATMENT_SITE", "").strip(),
                        "treatment_modality": row.get("TREATMENT_MODALITY", "").strip(),
                        "technique": row.get("TECHNIQUE", "").strip(),
                        "total_dose": SACTParser._float_or_none(row.get("TOTAL_DOSE_GY")),
                        "fractions_prescribed": SACTParser._int_or_none(row.get("FRACTIONS_PRESCRIBED")),
                        "dose_per_fraction": SACTParser._float_or_none(row.get("DOSE_PER_FRACTION_GY")),
                        "first_treatment_date": SACTParser._parse_date(row.get("FIRST_TREATMENT_DATE")),
                        "last_treatment_date": SACTParser._parse_date(row.get("LAST_TREATMENT_DATE")),
                        "machine_id": row.get("MACHINE_ID", "").strip(),
                        "concurrent_chemo": row.get("CONCURRENT_CHEMO", "").strip().upper() == "Y",
                    },
                )
                result.records.append(record)
                result.parsed_rows += 1
            except Exception as e:
                result.errors.append(f"Row {i}: {e}")

        logger.info(f"RTDS: parsed {result.parsed_rows}/{result.total_rows} rows from {filename}")
        return result


class CDSParser:
    """Parse CDS (Commissioning Data Set) v6.3 flat file extract from PAS."""

    def parse(self, content: str, filename: str = "") -> ParsedCSVFile:
        result = ParsedCSVFile(file_type="CDS", filename=filename)

        reader = csv.DictReader(io.StringIO(content))
        for i, row in enumerate(reader, start=1):
            result.total_rows += 1
            try:
                record_type = row.get("CDS_TYPE", "").strip()
                if record_type in ("120", "130"):  # Admitted / outpatient CDS
                    record = ParsedCSVRecord(
                        record_type="episode" if record_type == "120" else "outpatient",
                        source_file=filename,
                        row_number=i,
                        fields={
                            "nhs_number": row.get("NHS_NUMBER", "").replace(" ", "").strip(),
                            "hospital_number": row.get("LOCAL_PATIENT_ID", "").strip(),
                            "spell_id": row.get("HOSPITAL_PROVIDER_SPELL_NUMBER", "").strip(),
                            "episode_number": SACTParser._int_or_none(row.get("EPISODE_NUMBER")),
                            "admission_date": SACTParser._parse_date(row.get("START_DATE_HOSPITAL_PROVIDER_SPELL")),
                            "admission_method": row.get("ADMISSION_METHOD", "").strip(),
                            "discharge_date": SACTParser._parse_date(row.get("DISCHARGE_DATE")),
                            "discharge_method": row.get("DISCHARGE_METHOD", "").strip(),
                            "specialty_code": row.get("MAIN_SPECIALTY_CODE", "").strip(),
                            "consultant_code": row.get("CONSULTANT_CODE", "").strip(),
                            "primary_diagnosis": row.get("PRIMARY_DIAGNOSIS", "").strip(),
                            "primary_procedure": row.get("PRIMARY_PROCEDURE_CODE", "").strip(),
                            "procedure_date": SACTParser._parse_date(row.get("PRIMARY_PROCEDURE_DATE")),
                            "hrg_code": row.get("HRG_CODE", "").strip(),
                            "appointment_date": SACTParser._parse_date(row.get("APPOINTMENT_DATE")),
                            "attendance_status": row.get("ATTENDED_OR_DID_NOT_ATTEND", "").strip(),
                            "outcome": row.get("OUTCOME_OF_ATTENDANCE", "").strip(),
                        },
                    )
                    result.records.append(record)
                    result.parsed_rows += 1
            except Exception as e:
                result.errors.append(f"Row {i}: {e}")

        logger.info(f"CDS: parsed {result.parsed_rows}/{result.total_rows} rows from {filename}")
        return result


class SomersetXMLParser:
    """Parse Somerset Cancer Register COSD XML exports."""

    def parse(self, content: str, filename: str = "") -> ParsedCSVFile:
        result = ParsedCSVFile(file_type="SOMERSET", filename=filename)

        try:
            from lxml import etree
            root = etree.fromstring(content.encode("utf-8"))

            # Handle various COSD XML structures
            ns = {"cosd": "http://www.datadictionary.nhs.uk/COSD"}
            patients = root.findall(".//cosd:Patient", ns) or root.findall(".//Patient") or root.findall(".//*[NHS_NUMBER]")

            if not patients:
                # Try flat structure
                patients = [root] if root.find(".//NHS_NUMBER") is not None else root.findall(".//*")

            for i, patient_elem in enumerate(patients, start=1):
                result.total_rows += 1
                try:
                    fields = {}
                    for elem in patient_elem.iter():
                        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                        if elem.text and elem.text.strip():
                            fields[tag.upper()] = elem.text.strip()

                    if "NHS_NUMBER" not in fields:
                        continue

                    record = ParsedCSVRecord(
                        record_type="cwt_pathway",
                        source_file=filename,
                        row_number=i,
                        fields={
                            "nhs_number": fields.get("NHS_NUMBER", "").replace(" ", ""),
                            "cancer_type": fields.get("CANCER_TYPE", ""),
                            "referral_source": fields.get("REFERRAL_SOURCE", ""),
                            "referral_priority": fields.get("REFERRAL_PRIORITY", ""),
                            "date_receipt_referral": fields.get("DATE_RECEIPT_REFERRAL", ""),
                            "date_first_seen": fields.get("DATE_FIRST_SEEN", ""),
                            "date_of_diagnosis": fields.get("DATE_OF_DIAGNOSIS", ""),
                            "date_decision_to_treat": fields.get("DATE_DECISION_TO_TREAT", ""),
                            "date_first_treatment": fields.get("DATE_FIRST_TREATMENT", ""),
                            "treatment_modality": fields.get("TREATMENT_MODALITY", ""),
                            "diagnosis_code": fields.get("DIAGNOSIS_CODE", fields.get("PRIMARY_DIAGNOSIS", "")),
                            "morphology": fields.get("MORPHOLOGY_CODE", ""),
                            "laterality": fields.get("LATERALITY", ""),
                            "basis_of_diagnosis": fields.get("BASIS_OF_DIAGNOSIS", ""),
                            "tnm_t": fields.get("TNM_T", ""),
                            "tnm_n": fields.get("TNM_N", ""),
                            "tnm_m": fields.get("TNM_M", ""),
                            "stage_group": fields.get("STAGE_GROUP", ""),
                            "grade": fields.get("GRADE", ""),
                            "performance_status": fields.get("PERFORMANCE_STATUS", ""),
                            "mdt_date": fields.get("MDT_DATE", ""),
                        },
                    )
                    result.records.append(record)
                    result.parsed_rows += 1
                except Exception as e:
                    result.errors.append(f"Patient {i}: {e}")

        except Exception as e:
            result.errors.append(f"XML parse error: {e}")
            logger.error(f"Somerset XML parse error: {e}")

        logger.info(f"Somerset: parsed {result.parsed_rows}/{result.total_rows} records from {filename}")
        return result
