"""HL7 v2.4 message parser for ICE pathology and RIS radiology messages."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

logger = logging.getLogger(__name__)


@dataclass
class HL7Patient:
    nhs_number: Optional[str] = None
    hospital_number: Optional[str] = None
    surname: Optional[str] = None
    forename: Optional[str] = None
    prefix: Optional[str] = None
    dob: Optional[str] = None
    sex: Optional[str] = None
    address: Optional[str] = None
    postcode: Optional[str] = None
    phone: Optional[str] = None


@dataclass
class HL7Order:
    order_id: Optional[str] = None
    filler_id: Optional[str] = None
    test_code: Optional[str] = None
    test_name: Optional[str] = None
    order_datetime: Optional[str] = None
    specimen_datetime: Optional[str] = None
    result_datetime: Optional[str] = None
    result_status: Optional[str] = None
    ordering_provider_code: Optional[str] = None
    ordering_provider_name: Optional[str] = None
    clinical_info: Optional[str] = None


@dataclass
class HL7Observation:
    set_id: Optional[str] = None
    value_type: Optional[str] = None  # NM, CE, FT, ST, TX
    identifier: Optional[str] = None
    identifier_name: Optional[str] = None
    value: Optional[str] = None
    units: Optional[str] = None
    reference_range: Optional[str] = None
    abnormal_flag: Optional[str] = None
    status: Optional[str] = None  # F=Final, P=Preliminary, C=Corrected


@dataclass
class HL7Visit:
    patient_class: Optional[str] = None  # I=Inpatient, O=Outpatient, E=Emergency
    location: Optional[str] = None
    attending_doctor_code: Optional[str] = None
    attending_doctor_name: Optional[str] = None


@dataclass
class ParsedHL7Message:
    message_type: str  # ORM_O01, ORU_R01, ADT_A01, etc.
    message_id: str
    timestamp: str
    sending_app: str
    sending_facility: str
    receiving_app: str
    receiving_facility: str
    patient: HL7Patient = field(default_factory=HL7Patient)
    visit: Optional[HL7Visit] = None
    order: Optional[HL7Order] = None
    observations: List[HL7Observation] = field(default_factory=list)
    raw: str = ""


class HL7Parser:
    """Parse HL7 v2.4 pipe-delimited messages into structured objects."""

    def parse(self, raw: str) -> ParsedHL7Message:
        """Parse a raw HL7 message string."""
        segments = self._split_segments(raw)

        if not segments or not segments[0].startswith("MSH"):
            raise ValueError("Invalid HL7 message: missing MSH segment")

        msh = self._parse_segment(segments[0])

        msg = ParsedHL7Message(
            message_type=self._get_field(msh, 8, ""),
            message_id=self._get_field(msh, 9, ""),
            timestamp=self._get_field(msh, 6, ""),
            sending_app=self._get_field(msh, 2, ""),
            sending_facility=self._get_field(msh, 3, ""),
            receiving_app=self._get_field(msh, 4, ""),
            receiving_facility=self._get_field(msh, 5, ""),
            raw=raw,
        )

        for seg_str in segments[1:]:
            seg = self._parse_segment(seg_str)
            seg_type = seg[0] if seg else ""

            if seg_type == "PID":
                msg.patient = self._parse_pid(seg)
            elif seg_type == "PV1":
                msg.visit = self._parse_pv1(seg)
            elif seg_type == "OBR":
                msg.order = self._parse_obr(seg)
            elif seg_type == "ORC":
                if not msg.order:
                    msg.order = HL7Order()
                msg.order.order_id = self._get_field(seg, 2, msg.order.order_id)
            elif seg_type == "OBX":
                msg.observations.append(self._parse_obx(seg))

        return msg

    def _split_segments(self, raw: str) -> List[str]:
        """Split HL7 message into segments (handle both \\r and \\n)."""
        raw = raw.strip()
        if "\r" in raw:
            return [s.strip() for s in raw.split("\r") if s.strip()]
        return [s.strip() for s in raw.split("\n") if s.strip()]

    def _parse_segment(self, segment: str) -> List[str]:
        """Split a segment into fields."""
        return segment.split("|")

    def _get_field(self, fields: List[str], index: int, default: str = None) -> Optional[str]:
        """Safely get a field by index."""
        # MSH is special: field 0 = "MSH", field 1 = "|" (separator), so indices shift by 1
        if fields and fields[0] == "MSH":
            index = index  # MSH fields already include separator
        try:
            val = fields[index] if index < len(fields) else default
            return val if val else default
        except (IndexError, TypeError):
            return default

    def _parse_pid(self, fields: List[str]) -> HL7Patient:
        """Parse PID (Patient Identification) segment."""
        patient = HL7Patient()

        # PID-3: Patient identifier list (can contain multiple IDs separated by ~)
        id_list = self._get_field(fields, 3, "")
        if id_list:
            for pid_id in id_list.split("~"):
                components = pid_id.split("^")
                if len(components) >= 5:
                    id_value = components[0]
                    id_type = components[4] if len(components) > 4 else ""
                    if id_type == "NH":  # NHS number
                        patient.nhs_number = id_value.replace(" ", "")
                    elif id_type == "MR":  # Hospital number
                        patient.hospital_number = id_value
                elif len(components) >= 1 and len(components[0]) == 10:
                    # Likely NHS number if 10 digits
                    patient.nhs_number = components[0]

        # PID-5: Patient name
        name = self._get_field(fields, 5, "")
        if name:
            parts = name.split("^")
            patient.surname = parts[0] if parts else None
            patient.forename = parts[1] if len(parts) > 1 else None
            patient.prefix = parts[4] if len(parts) > 4 else None

        # PID-7: Date of birth
        patient.dob = self._get_field(fields, 7)

        # PID-8: Sex
        patient.sex = self._get_field(fields, 8)

        # PID-11: Address
        addr = self._get_field(fields, 11, "")
        if addr:
            addr_parts = addr.split("^")
            patient.address = addr_parts[0] if addr_parts else None
            patient.postcode = addr_parts[4] if len(addr_parts) > 4 else None

        # PID-13: Phone
        patient.phone = self._get_field(fields, 13)

        return patient

    def _parse_pv1(self, fields: List[str]) -> HL7Visit:
        """Parse PV1 (Patient Visit) segment."""
        visit = HL7Visit()
        visit.patient_class = self._get_field(fields, 2)
        visit.location = self._get_field(fields, 3)

        doctor = self._get_field(fields, 7, "")
        if doctor:
            parts = doctor.split("^")
            visit.attending_doctor_code = parts[0] if parts else None
            visit.attending_doctor_name = f"{parts[1]} {parts[2]}".strip() if len(parts) > 2 else parts[0]

        return visit

    def _parse_obr(self, fields: List[str]) -> HL7Order:
        """Parse OBR (Observation Request) segment."""
        order = HL7Order()

        order.order_id = self._get_field(fields, 2)
        order.filler_id = self._get_field(fields, 3)

        # OBR-4: Universal Service ID (test code)
        test = self._get_field(fields, 4, "")
        if test:
            parts = test.split("^")
            order.test_code = parts[0] if parts else None
            order.test_name = parts[1] if len(parts) > 1 else None

        order.order_datetime = self._get_field(fields, 7)
        order.specimen_datetime = self._get_field(fields, 14)
        order.result_datetime = self._get_field(fields, 22)
        order.result_status = self._get_field(fields, 25)

        # OBR-16: Ordering provider
        provider = self._get_field(fields, 16, "")
        if provider:
            parts = provider.split("^")
            order.ordering_provider_code = parts[0] if parts else None
            order.ordering_provider_name = f"{parts[1]} {parts[2]}".strip() if len(parts) > 2 else None

        # OBR-13: Clinical info
        order.clinical_info = self._get_field(fields, 13)

        return order

    def _parse_obx(self, fields: List[str]) -> HL7Observation:
        """Parse OBX (Observation/Result) segment."""
        obs = HL7Observation()

        obs.set_id = self._get_field(fields, 1)
        obs.value_type = self._get_field(fields, 2)

        # OBX-3: Observation identifier
        identifier = self._get_field(fields, 3, "")
        if identifier:
            parts = identifier.split("^")
            obs.identifier = parts[0] if parts else None
            obs.identifier_name = parts[1] if len(parts) > 1 else None

        obs.value = self._get_field(fields, 5)
        obs.units = self._get_field(fields, 6)
        obs.reference_range = self._get_field(fields, 7)
        obs.abnormal_flag = self._get_field(fields, 8)
        obs.status = self._get_field(fields, 11)

        return obs

    @staticmethod
    def determine_source_system(msg: ParsedHL7Message) -> str:
        """Determine the source system from message headers."""
        app = (msg.sending_app or "").upper()
        if "WINPATH" in app or "ICE" in app or "PATHLAB" in app or "LIMS" in app:
            return "ICE"
        if "RIS" in app or "PACS" in app or "CRIS" in app or "SECTRA" in app:
            return "RIS"
        if "PAS" in app or "CERNER" in app or "EPIC" in app:
            return "PAS"
        return "UNKNOWN"

    @staticmethod
    def determine_message_category(msg: ParsedHL7Message) -> str:
        """Determine the message category (pathology result, radiology result, order, ADT)."""
        msg_type = (msg.message_type or "").upper()
        source = HL7Parser.determine_source_system(msg)

        if "ORU" in msg_type:
            return "pathology_result" if source == "ICE" else "radiology_result"
        if "ORM" in msg_type:
            return "pathology_order" if source == "ICE" else "radiology_order"
        if "ADT" in msg_type:
            return "adt"
        return "unknown"
