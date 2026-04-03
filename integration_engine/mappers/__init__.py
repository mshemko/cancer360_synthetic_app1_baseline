"""CDM Mappers — transform parsed source system data into canonical data model entities.

Each mapper converts one source format into one or more CDM database records,
handling the translation from local codes/structures to the NHS canonical ontology.
"""

import logging
import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


# ─── Base mapper ────────────────────────────────────────────────────────────

class CDMMapper(ABC):
    """Abstract base for all CDM mappers."""

    def __init__(self, db_session=None):
        self.db = db_session

    @abstractmethod
    def get_source_system(self) -> str:
        pass

    @abstractmethod
    def map_to_entities(self, parsed: Any) -> List[Dict[str, Any]]:
        """Return list of dicts: [{"table": "tablename", "data": {...}}]"""
        pass

    @staticmethod
    def parse_hl7_datetime(ts: Optional[str]) -> Optional[datetime]:
        if not ts:
            return None
        for fmt in ("%Y%m%d%H%M%S", "%Y%m%d%H%M", "%Y%m%d"):
            try:
                return datetime.strptime(ts[:len(fmt.replace("%", ""))], fmt)
            except (ValueError, IndexError):
                continue
        return None

    @staticmethod
    def parse_date_str(ds: Optional[str]) -> Optional[date]:
        if not ds:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y%m%d"):
            try:
                return datetime.strptime(ds.strip(), fmt).date()
            except (ValueError, IndexError):
                continue
        return None


# ─── Pathology Result Mapper (ICE / WinPath HL7 ORU) ───────────────────────

class PathologyMapper(CDMMapper):
    """Map ICE/WinPath HL7 ORU^R01 messages to pathology_result + values + histopath."""

    # Patterns for structured histopath field extraction
    GRADE_PATTERN = re.compile(r"grade\s*(\d)", re.IGNORECASE)
    SIZE_PATTERN = re.compile(r"(?:measuring|size[:\s]+|tumour[:\s]+)(\d+(?:\.\d+)?)\s*mm", re.IGNORECASE)
    MARGIN_PATTERN = re.compile(r"margin[s]?\s*(?:are\s+)?(\w+)", re.IGNORECASE)
    MARGIN_MM_PATTERN = re.compile(r"(?:closest\s+margin|margin\s+clearance)[:\s]*(\d+(?:\.\d+)?)\s*mm", re.IGNORECASE)
    LVI_PATTERN = re.compile(r"lymphovascular\s+invasion\s+(\w+)", re.IGNORECASE)
    NODES_EXAMINED_PATTERN = re.compile(r"(\d+)\s+(?:lymph\s+)?nodes?\s+(?:examined|sampled|identified)", re.IGNORECASE)
    NODES_POSITIVE_PATTERN = re.compile(r"(\d+)\s+(?:of\s+\d+\s+)?(?:lymph\s+)?nodes?\s+(?:positive|involved|containing)", re.IGNORECASE)
    ER_PATTERN = re.compile(r"(?:oestrogen|estrogen)\s+receptor[:\s]*(\w+)", re.IGNORECASE)
    PR_PATTERN = re.compile(r"progesterone\s+receptor[:\s]*(\w+)", re.IGNORECASE)
    HER2_PATTERN = re.compile(r"HER2[:\s]*(\w+)", re.IGNORECASE)
    KI67_PATTERN = re.compile(r"Ki-?67[:\s]*(\d+(?:\.\d+)?)\s*%", re.IGNORECASE)
    GLEASON_PATTERN = re.compile(r"Gleason\s+(\d)\s*\+\s*(\d)", re.IGNORECASE)

    def get_source_system(self) -> str:
        return "ICE"

    def map_to_entities(self, parsed) -> List[Dict[str, Any]]:
        entities = []

        # Determine discipline from test code or sending app
        discipline = self._determine_discipline(parsed)

        result_id = uuid.uuid4()
        nhs_number = parsed.patient.nhs_number

        # Main pathology_result record
        result = {
            "table": "pathology_result",
            "data": {
                "result_id": result_id,
                "source_accession": parsed.order.filler_id if parsed.order else None,
                "order_id": parsed.order.order_id if parsed.order else None,
                "order_date": self.parse_hl7_datetime(parsed.order.order_datetime) if parsed.order else None,
                "specimen_date": self.parse_hl7_datetime(parsed.order.specimen_datetime) if parsed.order else None,
                "report_date": self.parse_hl7_datetime(parsed.order.result_datetime or parsed.timestamp),
                "discipline": discipline,
                "test_code": parsed.order.test_code if parsed.order else None,
                "test_name": parsed.order.test_name if parsed.order else None,
                "status": self._map_result_status(parsed.order.result_status if parsed.order else "F"),
                "requesting_clinician_code": parsed.order.ordering_provider_code if parsed.order else None,
                "requesting_clinician_name": parsed.order.ordering_provider_name if parsed.order else None,
                "narrative_report": None,
                "source_system": "ICE",
                "source_message_id": parsed.message_id,
                "raw_hl7": parsed.raw[:5000],  # Truncate for storage
                "_nhs_number": nhs_number,  # For patient resolution
            },
        }

        # Process observations (OBX segments)
        narrative_parts = []
        values = []
        for i, obs in enumerate(parsed.observations):
            if obs.value_type == "FT" or obs.value_type == "TX":
                # Free text — histopathology narrative
                narrative_parts.append(obs.value or "")
            elif obs.value_type == "NM":
                values.append({
                    "table": "pathology_result_value",
                    "data": {
                        "value_id": uuid.uuid4(),
                        "result_id": result_id,
                        "sequence_number": i + 1,
                        "test_code": obs.identifier,
                        "test_name": obs.identifier_name,
                        "value_type": "numeric",
                        "numeric_value": Decimal(obs.value) if obs.value else None,
                        "unit": obs.units,
                        "reference_range_text": obs.reference_range,
                        "abnormal_flag": obs.abnormal_flag,
                    },
                })
            elif obs.value_type == "CE" or obs.value_type == "ST":
                code_parts = (obs.value or "").split("^") if obs.value else [""]
                values.append({
                    "table": "pathology_result_value",
                    "data": {
                        "value_id": uuid.uuid4(),
                        "result_id": result_id,
                        "sequence_number": i + 1,
                        "test_code": obs.identifier,
                        "test_name": obs.identifier_name,
                        "value_type": "coded",
                        "coded_value": code_parts[0],
                        "coded_display": code_parts[1] if len(code_parts) > 1 else code_parts[0],
                        "coding_system": code_parts[2] if len(code_parts) > 2 else "LOCAL",
                    },
                })

        if narrative_parts:
            result["data"]["narrative_report"] = "\n".join(narrative_parts)

        entities.append(result)
        entities.extend(values)

        # Extract structured histopath if it's a histopathology result
        if discipline == "histopathology" and result["data"]["narrative_report"]:
            histopath = self._extract_histopath(result["data"]["narrative_report"], result_id, nhs_number)
            if histopath:
                entities.append(histopath)

        return entities

    def _determine_discipline(self, parsed) -> str:
        code = (parsed.order.test_code or "").upper() if parsed.order else ""
        name = (parsed.order.test_name or "").upper() if parsed.order else ""
        combined = code + " " + name

        if any(k in combined for k in ["HISTO", "BIOPSY", "RESECTION", "CYTOLOGY", "PATH"]):
            return "histopathology"
        if any(k in combined for k in ["FBC", "HAEM", "COAG", "BLOOD COUNT"]):
            return "haematology"
        if any(k in combined for k in ["BIOCHEM", "UE", "LFT", "BONE", "GLUC", "HBA1C", "PSA", "CEA", "CA125", "CA153", "AFP", "TUMOUR MARKER"]):
            return "biochemistry"
        if any(k in combined for k in ["MICRO", "CULTURE", "SENSITIVITY", "SWAB"]):
            return "microbiology"
        if any(k in combined for k in ["IMMUNO", "IHC", "MOLECULAR", "EGFR", "ALK", "KRAS", "BRAF", "MMR", "MSI"]):
            return "molecular"
        return "pathology"

    @staticmethod
    def _map_result_status(status: Optional[str]) -> str:
        return {"F": "final", "P": "preliminary", "C": "corrected", "X": "cancelled"}.get(
            (status or "F").upper(), "final"
        )

    def _extract_histopath(self, narrative: str, result_id: uuid.UUID, nhs_number: str) -> Optional[Dict]:
        """Extract structured fields from histopathology narrative text using regex."""
        data = {
            "histopath_id": uuid.uuid4(),
            "result_id": result_id,
            "_nhs_number": nhs_number,
        }

        m = self.GRADE_PATTERN.search(narrative)
        if m:
            data["grade"] = m.group(1)

        m = self.SIZE_PATTERN.search(narrative)
        if m:
            data["tumour_size_mm"] = Decimal(m.group(1))

        m = self.MARGIN_PATTERN.search(narrative)
        if m:
            data["margin_status"] = m.group(1).lower()

        m = self.MARGIN_MM_PATTERN.search(narrative)
        if m:
            data["margin_closest_mm"] = Decimal(m.group(1))

        m = self.LVI_PATTERN.search(narrative)
        if m:
            val = m.group(1).lower()
            data["lymphovascular_invasion"] = "present" if val in ("present", "identified", "seen") else "absent"

        m = self.NODES_EXAMINED_PATTERN.search(narrative)
        if m:
            data["nodes_examined"] = int(m.group(1))

        m = self.NODES_POSITIVE_PATTERN.search(narrative)
        if m:
            data["nodes_positive"] = int(m.group(1))

        m = self.ER_PATTERN.search(narrative)
        if m:
            data["er_status"] = "positive" if m.group(1).lower() in ("positive", "pos") else "negative"

        m = self.PR_PATTERN.search(narrative)
        if m:
            data["pr_status"] = "positive" if m.group(1).lower() in ("positive", "pos") else "negative"

        m = self.HER2_PATTERN.search(narrative)
        if m:
            data["her2_status"] = "positive" if m.group(1).lower() in ("positive", "pos", "3+") else "negative"

        m = self.KI67_PATTERN.search(narrative)
        if m:
            data["ki67_percent"] = Decimal(m.group(1))

        m = self.GLEASON_PATTERN.search(narrative)
        if m:
            data["gleason_primary"] = int(m.group(1))
            data["gleason_secondary"] = int(m.group(2))
            data["gleason_total"] = data["gleason_primary"] + data["gleason_secondary"]

        # Only return if we extracted something meaningful
        if len(data) > 3:
            return {"table": "histopath_structured", "data": data}
        return None


# ─── Radiology Mapper (RIS HL7 ORU) ────────────────────────────────────────

class RadiologyMapper(CDMMapper):
    """Map RIS HL7 ORU^R01 messages to radiology_result."""

    def get_source_system(self) -> str:
        return "RIS"

    def map_to_entities(self, parsed) -> List[Dict[str, Any]]:
        report_parts = []
        conclusion_parts = []

        for obs in parsed.observations:
            name = (obs.identifier_name or obs.identifier or "").upper()
            if "CONCLUSION" in name or "IMPRESSION" in name:
                conclusion_parts.append(obs.value or "")
            elif obs.value:
                report_parts.append(obs.value)

        return [{
            "table": "radiology_result",
            "data": {
                "result_id": uuid.uuid4(),
                "accession_number": parsed.order.filler_id if parsed.order else None,
                "order_id": parsed.order.order_id if parsed.order else None,
                "exam_date": self.parse_hl7_datetime(parsed.order.order_datetime or parsed.timestamp),
                "report_date": self.parse_hl7_datetime(parsed.order.result_datetime or parsed.timestamp),
                "modality": self._determine_modality(parsed),
                "body_part": None,
                "exam_code": parsed.order.test_code if parsed.order else None,
                "exam_description": parsed.order.test_name if parsed.order else None,
                "clinical_indication": parsed.order.clinical_info if parsed.order else None,
                "report_text": "\n".join(report_parts) if report_parts else None,
                "conclusion": "\n".join(conclusion_parts) if conclusion_parts else None,
                "requesting_clinician_code": parsed.order.ordering_provider_code if parsed.order else None,
                "requesting_clinician_name": parsed.order.ordering_provider_name if parsed.order else None,
                "status": "verified",
                "source_system": "RIS",
                "source_message_id": parsed.message_id,
                "raw_hl7": parsed.raw[:5000],
                "_nhs_number": parsed.patient.nhs_number,
            },
        }]

    def _determine_modality(self, parsed) -> str:
        code = ((parsed.order.test_code or "") + " " + (parsed.order.test_name or "")).upper() if parsed.order else ""
        if "CT" in code or "COMPUTED" in code:
            return "CT"
        if "MRI" in code or "MR " in code or "MAGNETIC" in code:
            return "MRI"
        if "PET" in code:
            return "PET-CT"
        if "US" in code or "ULTRASOUND" in code:
            return "US"
        if "XR" in code or "X-RAY" in code or "XRAY" in code:
            return "XR"
        if "MAMMO" in code:
            return "MG"
        if "NM" in code or "BONE SCAN" in code or "NUCLEAR" in code:
            return "NM"
        return "OTHER"


# ─── Somerset CWT Mapper ───────────────────────────────────────────────────

class SomersetMapper(CDMMapper):
    """Map Somerset Cancer Register CWT XML records to referral + diagnosis + staging + cancer_pathway."""

    CANCER_TYPE_MAP = {
        "101": ("breast", "Breast"), "102": ("colorectal", "Colorectal"),
        "103": ("lung", "Lung"), "104": ("prostate", "Prostate"),
        "105": ("gynae", "Gynaecological"), "106": ("upper_gi", "Upper GI"),
        "107": ("urology", "Urological"), "108": ("haem", "Haematological"),
        "109": ("head_neck", "Head & Neck"), "110": ("skin", "Skin/Melanoma"),
        "111": ("brain_cns", "Brain/CNS"), "112": ("sarcoma", "Sarcoma"),
        "113": ("thyroid", "Thyroid"), "114": ("unknown_primary", "Unknown Primary"),
    }

    def get_source_system(self) -> str:
        return "SOMERSET"

    def map_to_entities(self, record) -> List[Dict[str, Any]]:
        f = record.fields
        entities = []
        nhs_number = f.get("nhs_number", "")

        ref_id = uuid.uuid4()
        diag_id = uuid.uuid4()
        staging_id = uuid.uuid4()
        pathway_id = uuid.uuid4()

        # Cancer type lookup
        ct_code = f.get("cancer_type", "")
        ct_info = self.CANCER_TYPE_MAP.get(ct_code, (ct_code, ct_code))

        # Referral
        ref_date = self.parse_date_str(f.get("date_receipt_referral"))
        if ref_date:
            entities.append({
                "table": "referral",
                "data": {
                    "referral_id": ref_id,
                    "referral_date": ref_date,
                    "receipt_date": ref_date,
                    "clock_start_date": ref_date,
                    "referral_source": f.get("referral_source"),
                    "referral_priority": f.get("referral_priority"),
                    "cancer_type_code": ct_info[0],
                    "status": "open",
                    "source_system": "SOMERSET",
                    "_nhs_number": nhs_number,
                },
            })

        # Diagnosis
        diag_date = self.parse_date_str(f.get("date_of_diagnosis"))
        diag_code = f.get("diagnosis_code", "")
        if diag_date and diag_code:
            entities.append({
                "table": "diagnosis",
                "data": {
                    "diagnosis_id": diag_id,
                    "referral_id": ref_id,
                    "diagnosis_date": diag_date,
                    "icd10_code": diag_code,
                    "morphology_code": f.get("morphology"),
                    "laterality": f.get("laterality"),
                    "basis_of_diagnosis": f.get("basis_of_diagnosis"),
                    "source_system": "SOMERSET",
                    "_nhs_number": nhs_number,
                },
            })

        # Staging
        tnm_t = f.get("tnm_t", "")
        if tnm_t:
            entities.append({
                "table": "staging",
                "data": {
                    "staging_id": staging_id,
                    "diagnosis_id": diag_id if diag_date else None,
                    "staging_date": diag_date or ref_date or date.today(),
                    "staging_type": "clinical",
                    "tnm_t": tnm_t,
                    "tnm_n": f.get("tnm_n"),
                    "tnm_m": f.get("tnm_m"),
                    "stage_group": f.get("stage_group"),
                    "grade": f.get("grade"),
                    "performance_status": int(f["performance_status"]) if f.get("performance_status", "").isdigit() else None,
                    "source_system": "SOMERSET",
                    "_nhs_number": nhs_number,
                },
            })

        # Cancer pathway (derived)
        first_seen = self.parse_date_str(f.get("date_first_seen"))
        tx_date = self.parse_date_str(f.get("date_first_treatment"))
        dtt_date = self.parse_date_str(f.get("date_decision_to_treat"))

        days_to_diag = (diag_date - ref_date).days if diag_date and ref_date else None
        days_to_tx = (tx_date - ref_date).days if tx_date and ref_date else None

        entities.append({
            "table": "cancer_pathway",
            "data": {
                "pathway_id": pathway_id,
                "referral_id": ref_id if ref_date else None,
                "diagnosis_id": diag_id if diag_date else None,
                "staging_id": staging_id if tnm_t else None,
                "cancer_type_code": ct_info[0],
                "cancer_type_desc": ct_info[1],
                "date_referral_received": ref_date,
                "date_first_seen": first_seen,
                "date_diagnosis": diag_date,
                "date_mdt": self.parse_date_str(f.get("mdt_date")),
                "date_decision_to_treat": dtt_date,
                "date_first_treatment": tx_date,
                "days_to_first_seen": (first_seen - ref_date).days if first_seen and ref_date else None,
                "days_to_diagnosis": days_to_diag,
                "days_to_treatment": days_to_tx,
                "fds_28day_met": days_to_diag is not None and days_to_diag <= 28,
                "standard_62day_met": days_to_tx is not None and days_to_tx <= 62,
                "standard_31day_met": (tx_date - dtt_date).days <= 31 if tx_date and dtt_date else None,
                "treatment_modality": f.get("treatment_modality"),
                "pathway_status": self._determine_status(f),
                "breach_risk": self._calculate_breach_risk(ref_date, diag_date, tx_date),
                "source_system": "SOMERSET",
                "_nhs_number": nhs_number,
            },
        })

        return entities

    def _determine_status(self, f: dict) -> str:
        if f.get("date_first_treatment"):
            return "on_treatment"
        if f.get("date_decision_to_treat"):
            return "awaiting_treatment"
        if f.get("mdt_date"):
            return "awaiting_treatment"
        if f.get("date_of_diagnosis"):
            return "awaiting_mdt"
        return "awaiting_diagnostics"

    def _calculate_breach_risk(self, ref_date, diag_date, tx_date) -> str:
        if not ref_date:
            return "none"
        today = date.today()
        days = (today - ref_date).days

        if tx_date:
            return "breached" if (tx_date - ref_date).days > 62 else "none"
        if days > 62:
            return "breached"
        if days > 50:
            return "high"
        if days > 35:
            return "medium"
        if days > 21:
            return "low"
        return "none"


# ─── SACT Mapper ────────────────────────────────────────────────────────────

class SACTMapper(CDMMapper):
    """Map SACT CSV records to sact_course + sact_cycle + sact_drug."""

    def get_source_system(self) -> str:
        return "CHEMOCARE"

    def map_to_entities(self, record) -> List[Dict[str, Any]]:
        f = record.fields
        entities = []

        cycle_id = uuid.uuid4()
        entities.append({
            "table": "sact_cycle",
            "data": {
                "cycle_id": cycle_id,
                "cycle_number": f.get("cycle_number") or 1,
                "start_date": self.parse_date_str(f.get("start_date_cycle")),
                "height_cm": Decimal(str(f["height"])) if f.get("height") else None,
                "weight_kg": Decimal(str(f["weight"])) if f.get("weight") else None,
                "bsa_m2": Decimal(str(f["bsa"])) if f.get("bsa") else None,
                "performance_status": f.get("performance_status"),
                "cycle_outcome": f.get("cycle_outcome"),
                "source_system": "CHEMOCARE",
                "_nhs_number": f.get("nhs_number"),
                "_regimen": f.get("regimen"),
                "_regimen_intent": f.get("regimen_intent"),
                "_start_date_regimen": f.get("start_date_regimen"),
                "_max_cycles": f.get("max_cycles"),
            },
        })

        if f.get("drug_name"):
            entities.append({
                "table": "sact_drug",
                "data": {
                    "drug_id": uuid.uuid4(),
                    "cycle_id": cycle_id,
                    "drug_name": f["drug_name"],
                    "dose_mg": Decimal(str(f["drug_dose"])) if f.get("drug_dose") else None,
                    "route": f.get("route"),
                    "administration_date": self.parse_date_str(f.get("administration_date")),
                },
            })

        return entities


# ─── Radiotherapy Mapper ────────────────────────────────────────────────────

class RadiotherapyMapper(CDMMapper):
    """Map RTDS CSV records to radiotherapy_course + radiotherapy_fraction."""

    def get_source_system(self) -> str:
        return "MOSAIQ"

    def map_to_entities(self, record) -> List[Dict[str, Any]]:
        f = record.fields
        course_id = uuid.uuid4()

        entities = [{
            "table": "radiotherapy_course",
            "data": {
                "course_id": course_id,
                "treatment_intent": f.get("treatment_intent"),
                "treatment_site": f.get("treatment_site"),
                "technique": f.get("technique"),
                "total_dose_gy": Decimal(str(f["total_dose"])) if f.get("total_dose") else None,
                "fractions_prescribed": f.get("fractions_prescribed"),
                "dose_per_fraction_gy": Decimal(str(f["dose_per_fraction"])) if f.get("dose_per_fraction") else None,
                "first_fraction_date": self.parse_date_str(f.get("first_treatment_date")),
                "last_fraction_date": self.parse_date_str(f.get("last_treatment_date")),
                "machine_id": f.get("machine_id"),
                "concurrent_sact": f.get("concurrent_chemo", False),
                "source_system": "MOSAIQ",
                "_nhs_number": f.get("nhs_number"),
            },
        }]

        return entities


# ─── MDT Mapper (JSON) ─────────────────────────────────────────────────────

class MDTMapper(CDMMapper):
    """Map Infoflex MDT JSON records to mdt_discussion."""

    def get_source_system(self) -> str:
        return "INFOFLEX"

    def map_to_entities(self, record: dict) -> List[Dict[str, Any]]:
        return [{
            "table": "mdt_discussion",
            "data": {
                "mdt_id": uuid.uuid4(),
                "mdt_date": self.parse_date_str(record.get("date")),
                "mdt_site": record.get("site"),
                "mdt_type": record.get("type"),
                "chair_name": record.get("chair"),
                "quorate": record.get("quorate", True),
                "clinical_summary": record.get("summary"),
                "staging_presented": record.get("staging"),
                "decision": record.get("decision"),
                "treatment_intent": record.get("intent"),
                "source_system": "INFOFLEX",
                "_nhs_number": record.get("nhs_number"),
            },
        }]


# ─── Admission / PAS Mapper (CDS) ──────────────────────────────────────────

class AdmissionMapper(CDMMapper):
    """Map CDS v6.3 flat file records to episode + appointment."""

    def get_source_system(self) -> str:
        return "PAS"

    def map_to_entities(self, record) -> List[Dict[str, Any]]:
        f = record.fields

        if record.record_type == "episode":
            adm = self.parse_date_str(f.get("admission_date"))
            dis = self.parse_date_str(f.get("discharge_date"))
            return [{
                "table": "episode",
                "data": {
                    "episode_id": uuid.uuid4(),
                    "source_spell_id": f.get("spell_id"),
                    "episode_type": "inpatient",
                    "admission_date": adm,
                    "admission_method": f.get("admission_method"),
                    "discharge_date": dis,
                    "discharge_method": f.get("discharge_method"),
                    "specialty_code": f.get("specialty_code"),
                    "consultant_code": f.get("consultant_code"),
                    "primary_diagnosis": f.get("primary_diagnosis"),
                    "primary_procedure": f.get("primary_procedure"),
                    "procedure_date": self.parse_date_str(f.get("procedure_date")),
                    "hrg_code": f.get("hrg_code"),
                    "los_days": (dis - adm).days if adm and dis else None,
                    "source_system": "PAS",
                    "_nhs_number": f.get("nhs_number"),
                },
            }]

        elif record.record_type == "outpatient":
            return [{
                "table": "appointment",
                "data": {
                    "appointment_id": uuid.uuid4(),
                    "appointment_date": self.parse_date_str(f.get("appointment_date")),
                    "specialty_code": f.get("specialty_code"),
                    "consultant_code": f.get("consultant_code"),
                    "attendance_status": f.get("attendance_status"),
                    "outcome_code": f.get("outcome"),
                    "appointment_type": "first" if f.get("attendance_status") == "5" else "follow_up",
                    "source_system": "PAS",
                    "_nhs_number": f.get("nhs_number"),
                },
            }]

        return []
