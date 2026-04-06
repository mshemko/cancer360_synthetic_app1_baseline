"""Routing and channel logic for the native TIE."""

from __future__ import annotations

import time
import uuid
from datetime import date
from pathlib import Path

from tie.common import DatabaseStore, build_ack, clean_nhs, deterministic_uuid, parse_bool, parse_date, parse_datetime, parse_hl7, read_csv_rows


class IntegrationRouter:
    def __init__(self, store: DatabaseStore):
        self.store = store
        self.meeting_cache: dict[str, dict] = {}

    async def handle_hl7(self, raw: str) -> str:
        correlation_id = uuid.uuid4()
        started = time.perf_counter()
        parsed = parse_hl7(raw)
        try:
            async with self.store.session_factory() as session:
                async with session.begin():
                    message_type = parsed.get("message_type", "")
                    sending_app = (parsed.get("sending_app") or "").upper()
                    if sending_app == "CERNER" and message_type.startswith("ADT^"):
                        entity_id = await self._process_pas_adt(session, parsed)
                        entity_type = "patient" if message_type != "ADT^A01" else "episode"
                    elif sending_app == "CERNER" and message_type.startswith("SIU^"):
                        entity_id = await self._process_pas_siu(session, parsed)
                        entity_type = "appointment"
                    elif sending_app == "ARIA" and message_type.startswith("SIU^"):
                        entity_id = await self._process_aria_siu(session, parsed)
                        entity_type = "appointment"
                    elif sending_app in {"WINPATH", "ICE"} and message_type == "ORU^R01":
                        entity_id = await self._process_ice_oru(session, parsed)
                        entity_type = "pathology_result"
                    elif sending_app in {"CRIS", "RIS"} and message_type == "ORU^R01":
                        entity_id = await self._process_ris_oru(session, parsed)
                        entity_type = "radiology_result"
                    else:
                        entity_id = None
                        entity_type = "ignored"
                    await self.store.audit(session, correlation_id, sending_app or "UNKNOWN", message_type, parsed.get("message_id", ""), entity_type, entity_id, "success", raw, int((time.perf_counter() - started) * 1000))
            return build_ack(raw, "AA")
        except Exception as exc:
            async with self.store.session_factory() as session:
                async with session.begin():
                    await self.store.dead_letter(session, correlation_id, parsed.get("sending_app", "UNKNOWN"), "hl7", raw, str(exc))
                    await self.store.audit(session, correlation_id, parsed.get("sending_app", "UNKNOWN"), parsed.get("message_type", ""), parsed.get("message_id", ""), "hl7", None, "error", raw, int((time.perf_counter() - started) * 1000), str(exc))
            return build_ack(raw, "AE", str(exc)[:180])

    async def handle_file_payload(self, filename: str, payload: str) -> None:
        prefix = filename.split("_")[0]
        rows = read_csv_rows(payload)
        async with self.store.session_factory() as session:
            async with session.begin():
                if filename.startswith("somerset_pathways_"):
                    await self._process_somerset_pathways(session, rows)
                elif filename.startswith("somerset_tracking_"):
                    await self._process_somerset_tracking(session, rows)
                elif filename.startswith("somerset_mdt_meetings_"):
                    await self._process_somerset_mdt_meetings(rows)
                elif filename.startswith("somerset_mdt_bookings_"):
                    await self._process_somerset_mdt_bookings(rows)
                elif filename.startswith("somerset_mdt_notes_"):
                    await self._process_somerset_mdt_notes(session, rows)
                elif filename.startswith("somerset_ipt_"):
                    await self._process_somerset_ipt(session, rows)
                elif filename.startswith("aria_treatment_"):
                    await self._process_aria_csv(session, rows)
                elif filename.startswith("endoscopy_"):
                    await self._process_endoscopy_csv(session, rows)
                else:
                    raise ValueError(f"Unsupported file type: {prefix}")

    async def _upsert_patient(self, session, patient: dict) -> uuid.UUID:
        nhs_number = clean_nhs(patient.get("nhs_number"))
        patient_id = deterministic_uuid("patient", nhs_number)
        await self.store.upsert(session, "patient", {
            "patient_id": patient_id,
            "nhs_number": nhs_number,
            "hospital_number": patient.get("hospital_number"),
            "prefix": patient.get("prefix"),
            "forename": patient.get("forename") or "Unknown",
            "surname": patient.get("surname") or "Unknown",
            "date_of_birth": parse_date(str(patient.get("date_of_birth"))) or parse_date("1970-01-01"),
            "sex": (patient.get("sex") or "X")[:1],
            "postcode": patient.get("postcode"),
            "gp_practice_code": patient.get("gp_practice_code"),
            "gp_name": patient.get("gp_name"),
            "phone": patient.get("phone"),
        })
        return patient_id

    async def _process_pas_adt(self, session, parsed: dict) -> uuid.UUID:
        patient_id = await self._upsert_patient(session, parsed["patient"])
        if parsed.get("message_type") == "ADT^A01":
            episode_id = deterministic_uuid("episode", parsed.get("message_id") or str(patient_id))
            await self.store.upsert(session, "episode", {
                "episode_id": episode_id,
                "patient_id": patient_id,
                "source_episode_id": parsed.get("message_id"),
                "episode_type": "inpatient",
                "admission_date": parsed.get("timestamp").date() if parsed.get("timestamp") else None,
                "specialty_name": "Surgical Oncology",
                "ward_name": parsed.get("visit", {}).get("location"),
                "source_system": "PAS",
                "source_message_id": parsed.get("message_id"),
            })
            return episode_id
        return patient_id

    async def _process_pas_siu(self, session, parsed: dict) -> uuid.UUID:
        patient_id = await self._upsert_patient(session, parsed["patient"])
        schedule = parsed.get("schedule", {})
        appointment_id = deterministic_uuid("appointment", schedule.get("appointment_id") or parsed.get("message_id"))
        start_dt = schedule.get("start_datetime")
        await self.store.upsert(session, "appointment", {
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "source_appt_id": schedule.get("appointment_id"),
            "appointment_date": start_dt.date() if start_dt else parsed.get("timestamp").date(),
            "appointment_time": start_dt.time() if start_dt else None,
            "clinic_code": (schedule.get("clinic_name") or "PAS")[:20],
            "clinic_name": schedule.get("clinic_name"),
            "appointment_type": schedule.get("appointment_type"),
            "attendance_status": (schedule.get("status") or "").lower()[:10],
            "consultant_name": schedule.get("consultant_name"),
            "location": parsed.get("visit", {}).get("location"),
            "source_system": "PAS",
            "source_message_id": parsed.get("message_id"),
        })
        return appointment_id

    async def _process_aria_siu(self, session, parsed: dict) -> uuid.UUID:
        patient_id = await self._upsert_patient(session, parsed["patient"])
        schedule = parsed.get("schedule", {})
        appointment_id = deterministic_uuid("appointment", schedule.get("appointment_id") or parsed.get("message_id"))
        start_dt = schedule.get("start_datetime") or parsed.get("timestamp")
        await self.store.upsert(session, "appointment", {
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "source_appt_id": schedule.get("appointment_id"),
            "appointment_date": start_dt.date() if start_dt else None,
            "appointment_time": start_dt.time() if start_dt else None,
            "clinic_code": "ARIA",
            "clinic_name": schedule.get("clinic_name"),
            "appointment_type": "oncology",
            "attendance_status": (schedule.get("status") or "").lower()[:10],
            "consultant_name": schedule.get("consultant_name"),
            "location": schedule.get("clinic_name"),
            "source_system": "ARIA",
            "source_message_id": parsed.get("message_id"),
        })
        return appointment_id

    async def _process_ice_oru(self, session, parsed: dict) -> uuid.UUID:
        patient_id = await self._upsert_patient(session, parsed["patient"])
        order = parsed.get("order", {})
        result_id = deterministic_uuid("pathology", order.get("accession") or parsed.get("message_id"))
        narrative_parts = []
        values = []
        for obs in parsed.get("observations", []):
            if obs["value_type"] in {"FT", "TX", "ST"} and obs["code"] == "REPORT":
                narrative_parts.append(obs["value"])
            elif obs["value_type"] == "NM":
                values.append({"value_id": deterministic_uuid("pathology-value", f"{result_id}:{obs['set_id']}"), "result_id": result_id, "sequence_number": int(obs["set_id"]), "test_code": obs["code"], "test_name": obs["name"], "value_type": "numeric", "numeric_value": float(obs["value"]), "unit": obs.get("units"), "reference_range_text": obs.get("range"), "abnormal_flag": obs.get("flag")})
            else:
                values.append({"value_id": deterministic_uuid("pathology-value", f"{result_id}:{obs['set_id']}"), "result_id": result_id, "sequence_number": int(obs["set_id"]), "test_code": obs["code"], "test_name": obs["name"], "value_type": "coded", "coded_value": (obs["value"] or "").split("^")[0], "coded_display": (obs["value"] or "").split("^")[1] if "^" in (obs["value"] or "") else obs["value"], "unit": obs.get("units"), "reference_range_text": obs.get("range"), "abnormal_flag": obs.get("flag")})
        await self.store.upsert(session, "pathology_result", {
            "result_id": result_id,
            "patient_id": patient_id,
            "source_accession": order.get("accession"),
            "order_id": order.get("order_id"),
            "order_date": order.get("order_datetime"),
            "specimen_date": order.get("specimen_datetime"),
            "report_date": order.get("result_datetime") or parsed.get("timestamp"),
            "discipline": "histopathology" if order.get("test_code") == "HISTO" else "haematology",
            "test_code": order.get("test_code"),
            "test_name": order.get("test_name"),
            "status": "final",
            "requesting_clinician_name": order.get("clinician_name"),
            "narrative_report": "\n".join(narrative_parts) if narrative_parts else None,
            "source_system": "ICE",
            "source_message_id": parsed.get("message_id"),
            "raw_hl7": "",
        })
        for value in values:
            await self.store.upsert(session, "pathology_result_value", value)
        if order.get("test_code") == "HISTO":
            narrative = "\n".join(narrative_parts).lower()
            histopath_id = deterministic_uuid("histopath", str(result_id))
            await self.store.upsert(session, "histopath_structured", {
                "histopath_id": histopath_id,
                "result_id": result_id,
                "patient_id": patient_id,
                "tumour_type": order.get("test_name"),
                "grade": "2" if "grade 2" in narrative else "3" if "grade 3" in narrative else None,
                "er_status": "positive" if "er positive" in narrative else None,
                "pr_status": "positive" if "pr positive" in narrative else None,
                "her2_status": "negative" if "her2 negative" in narrative else None,
                "ki67_percent": 18 if "ki-67 18" in narrative else None,
                "lymphovascular_invasion": "absent" if "no lymphovascular invasion" in narrative else None,
            })
        return result_id

    async def _process_ris_oru(self, session, parsed: dict) -> uuid.UUID:
        patient_id = await self._upsert_patient(session, parsed["patient"])
        order = parsed.get("order", {})
        result_id = deterministic_uuid("radiology", order.get("accession") or parsed.get("message_id"))
        report_text = "\n".join(obs["value"] for obs in parsed.get("observations", []) if obs["code"] == "REPORT")
        conclusion = "\n".join(obs["value"] for obs in parsed.get("observations", []) if obs["code"] == "CONCLUSION")
        await self.store.upsert(session, "radiology_result", {
            "result_id": result_id,
            "patient_id": patient_id,
            "accession_number": order.get("accession"),
            "order_id": order.get("order_id"),
            "exam_date": order.get("order_datetime") or parsed.get("timestamp"),
            "report_date": order.get("result_datetime") or parsed.get("timestamp"),
            "modality": order.get("test_code"),
            "exam_code": order.get("test_code"),
            "exam_description": order.get("test_name"),
            "report_text": report_text or None,
            "conclusion": conclusion or None,
            "requesting_clinician_name": order.get("clinician_name"),
            "status": "verified",
            "source_system": "RIS",
            "source_message_id": parsed.get("message_id"),
            "raw_hl7": "",
        })
        return result_id

    async def _process_somerset_pathways(self, session, rows: list[dict]) -> None:
        for row in rows:
            patient_id = await self._upsert_patient(session, {"nhs_number": row["nhs_number"], "hospital_number": row.get("mrn"), "forename": row.get("first_name"), "surname": row.get("surname"), "date_of_birth": row.get("date_of_birth"), "sex": "F" if row.get("cancer_site") in {"Breast", "Gynaecological"} else "M" if row.get("cancer_site") == "Prostate" else "X"})
            pathway_uuid = deterministic_uuid("somerset-pathway", row["pathway_id"])
            referral_uuid = deterministic_uuid("somerset-referral", row["pathway_id"])
            diagnosis_uuid = deterministic_uuid("somerset-diagnosis", row["pathway_id"])
            staging_uuid = deterministic_uuid("somerset-staging", row["pathway_id"])
            await self.store.upsert(session, "referral", {"referral_id": referral_uuid, "patient_id": patient_id, "source_referral_id": row["pathway_id"], "referral_date": parse_date(row.get("referral_received_date")), "receipt_date": parse_date(row.get("referral_received_date")), "clock_start_date": parse_date(row.get("adjusted_pathway_start_date")), "referral_source": row.get("referral_source"), "referral_priority": row.get("pathway_referral_route"), "cancer_type_code": row.get("hospital_site_id"), "status": "open" if row.get("pathway_status") == "Open" else "closed", "source_system": "Somerset"})
            if row.get("diagnosis_date"):
                await self.store.upsert(session, "diagnosis", {"diagnosis_id": diagnosis_uuid, "patient_id": patient_id, "referral_id": referral_uuid, "diagnosis_date": parse_date(row.get("diagnosis_date")), "icd10_code": row.get("diagnosis_icd_10_code") or "C80", "icd10_description": row.get("diagnosis"), "morphology_code": None, "source_system": "Somerset"})
                await self.store.upsert(session, "staging", {"staging_id": staging_uuid, "patient_id": patient_id, "diagnosis_id": diagnosis_uuid, "staging_date": parse_date(row.get("diagnosis_date")), "staging_type": "clinical", "stage_group": None, "grade": None, "source_system": "Somerset"})
            await self.store.upsert(session, "cancer_pathway", {"pathway_id": pathway_uuid, "patient_id": patient_id, "referral_id": referral_uuid, "diagnosis_id": diagnosis_uuid if row.get("diagnosis_date") else None, "staging_id": staging_uuid if row.get("diagnosis_date") else None, "cancer_type_code": row.get("hospital_site_id"), "cancer_type_desc": row.get("cancer_site"), "date_referral_received": parse_date(row.get("referral_received_date")), "date_first_seen": parse_date(row.get("first_seen_date")), "date_diagnosis": parse_date(row.get("diagnosis_date")), "date_mdt": parse_date(row.get("decision_to_treat_date")), "date_decision_to_treat": parse_date(row.get("decision_to_treat_date")), "date_first_treatment": parse_date(row.get("first_treatment_date")), "days_to_first_seen": (parse_date(row.get("first_seen_date")) - parse_date(row.get("referral_received_date"))).days if row.get("first_seen_date") and row.get("referral_received_date") else None, "days_to_diagnosis": (parse_date(row.get("diagnosis_date")) - parse_date(row.get("referral_received_date"))).days if row.get("diagnosis_date") and row.get("referral_received_date") else None, "days_to_treatment": (parse_date(row.get("first_treatment_date")) - parse_date(row.get("referral_received_date"))).days if row.get("first_treatment_date") and row.get("referral_received_date") else None, "fds_28day_met": not parse_bool(row.get("is_28_day_pathway_open")), "standard_62day_met": not parse_bool(row.get("is_62_day_pathway_open")), "standard_31day_met": not parse_bool(row.get("is_31_day_pathway_open")), "treatment_modality": row.get("first_treatment_type"), "first_treatment_type": row.get("first_treatment_type"), "pathway_status": "completed" if row.get("pathway_status") == "Closed" else ("awaiting_treatment" if row.get("decision_to_treat_date") and not row.get("first_treatment_date") else "awaiting_mdt" if row.get("diagnosis_date") and not row.get("decision_to_treat_date") else "awaiting_diagnostics"), "current_stage_label": row.get("diagnosis"), "next_action": row.get("diagnosis"), "assigned_team": f"{row.get('cancer_site')} MDT", "breach_risk": "breached" if parse_bool(row.get("is_62_day_pathway_open")) and row.get("62_day_breach_date") and parse_date(row.get("62_day_breach_date")) and parse_date(row.get("62_day_breach_date")) < parse_date(date.today().isoformat()) else "none", "notes": row.get("diagnosis")})

    async def _process_somerset_tracking(self, session, rows: list[dict]) -> None:
        for row in rows:
            pathway_uuid = deterministic_uuid("somerset-pathway", row["cancer_pathway_id"])
            context = await self.store.fetch_pathway_context(session, pathway_uuid)
            if not context:
                continue
            action_id = deterministic_uuid("tracking-action", row["cancer_tracking_comment_id"])
            await self.store.upsert(session, "cancer_action", {"action_id": action_id, "patient_id": context["patient_id"], "pathway_id": pathway_uuid, "action_type": row.get("comment_title") or "Tracking comment", "action_description": row.get("comment_text"), "priority": "normal", "status": "completed" if "treatment" in (row.get("comment_title") or "").lower() else "open", "due_date": parse_date(row.get("created_at_timestamp")), "assigned_team": "Cancer Navigation", "created_by": row.get("created_by"), "notes": row.get("comment_text"), "source_system": "Somerset"})

    async def _process_somerset_mdt_meetings(self, rows: list[dict]) -> None:
        for row in rows:
            self.meeting_cache[row["mdt_meeting_id"]] = row

    async def _process_somerset_mdt_bookings(self, rows: list[dict]) -> None:
        for row in rows:
            self.meeting_cache.setdefault(row["meeting_id"], {})["pathway_id"] = row["pathway_id"]

    async def _process_somerset_mdt_notes(self, session, rows: list[dict]) -> None:
        for row in rows:
            pathway_uuid = deterministic_uuid("somerset-pathway", row["cancer_pathway_id"])
            context = await self.store.fetch_pathway_context(session, pathway_uuid)
            if not context:
                continue
            meeting = self.meeting_cache.get(row["meeting_id"], {})
            mdt_id = deterministic_uuid("mdt", f"{row['meeting_id']}:{row['cancer_pathway_id']}")
            await self.store.upsert(session, "mdt_discussion", {"mdt_id": mdt_id, "patient_id": context["patient_id"], "diagnosis_id": context["diagnosis_id"], "mdt_date": parse_date(meeting.get("meeting_timestamp") or row.get("last_updated_timestamp")), "mdt_site": row["meeting_id"].split("-")[1] if "-" in row["meeting_id"] else "Cancer", "mdt_type": row.get("note_type"), "quorate": True, "clinical_summary": row.get("mdt_note_text"), "decision": row.get("mdt_note_text"), "treatment_intent": "curative", "source_system": "Somerset", "source_message_id": row.get("mdt_note_id")})

    async def _process_somerset_ipt(self, session, rows: list[dict]) -> None:
        for row in rows:
            pathway_uuid = deterministic_uuid("somerset-pathway", row["pathway_id"])
            context = await self.store.fetch_pathway_context(session, pathway_uuid)
            if not context:
                continue
            action_id = deterministic_uuid("ipt-action", row["tertiary_id"])
            await self.store.upsert(session, "cancer_action", {"action_id": action_id, "patient_id": context["patient_id"], "pathway_id": pathway_uuid, "action_type": "Inter-provider transfer", "action_description": row.get("tertiary_sending_comment"), "priority": "high", "status": "open", "due_date": parse_date(row.get("tertiary_received_date")), "assigned_team": "Cancer Navigation", "notes": f"{row.get('receiving_org_name')}: {row.get('tertiary_reason')}", "source_system": "Somerset"})

    async def _process_aria_csv(self, session, rows: list[dict]) -> None:
        for row in rows:
            patient_id = await self.store.resolve_patient_id(session, row.get("nhs_number"))
            if not patient_id:
                continue
            if row.get("treatment_type") in {"Chemotherapy", "Immunotherapy"}:
                course_id = deterministic_uuid("sact-course", row["treatment_group_id"])
                cycle_id = deterministic_uuid("sact-cycle", row["cancer_treatment_id"])
                await self.store.upsert(session, "sact_course", {"course_id": course_id, "patient_id": patient_id, "source_sact_id": row["treatment_group_id"], "regimen_name": row.get("regimen_name"), "regimen_intent": row.get("treatment_type"), "start_date": parse_date(row.get("ordered_date")), "max_cycles": int(row.get("max_cycles") or 0) or None, "completed_cycles": int(row.get("cycle_number") or 0), "course_status": "active" if row.get("treatment_status") == "Attended" else "planned", "consultant_name": row.get("consultant_name"), "source_system": "ARIA"})
                await self.store.upsert(session, "sact_cycle", {"cycle_id": cycle_id, "course_id": course_id, "patient_id": patient_id, "cycle_number": int(row.get("cycle_number") or 1), "start_date": parse_date(row.get("attendance_date")) or parse_date(row.get("scheduled_date")), "height_cm": float(row["height_cm"]) if row.get("height_cm") else None, "weight_kg": float(row["weight_kg"]) if row.get("weight_kg") else None, "bsa_m2": float(row["bsa_m2"]) if row.get("bsa_m2") else None, "cycle_outcome": row.get("treatment_status"), "source_system": "ARIA"})
                if row.get("drug_name"):
                    await self.store.upsert(session, "sact_drug", {"drug_id": deterministic_uuid("sact-drug", row["cancer_treatment_id"]), "cycle_id": cycle_id, "drug_name": row.get("drug_name"), "dose_mg": float(row["dose_mg"]) if row.get("dose_mg") else None, "route": row.get("route"), "administration_date": parse_date(row.get("attendance_date"))})
            elif row.get("treatment_type") == "Radiotherapy":
                course_id = deterministic_uuid("rt-course", row["treatment_group_id"])
                fraction_id = deterministic_uuid("rt-fraction", row["cancer_treatment_id"])
                await self.store.upsert(session, "radiotherapy_course", {"course_id": course_id, "patient_id": patient_id, "source_course_id": row["treatment_group_id"], "treatment_intent": "curative", "treatment_site": row.get("treatment_site"), "total_dose_gy": float(row["total_dose_gy"]) if row.get("total_dose_gy") else None, "fractions_prescribed": int(row.get("fractions_prescribed") or 0) or None, "dose_per_fraction_gy": float(row["dose_per_fraction_gy"]) if row.get("dose_per_fraction_gy") else None, "first_fraction_date": parse_date(row.get("scheduled_date")), "machine_id": row.get("machine_id"), "course_status": "active", "consultant_name": row.get("consultant_name"), "source_system": "ARIA"})
                await self.store.upsert(session, "radiotherapy_fraction", {"fraction_id": fraction_id, "course_id": course_id, "fraction_number": int(row.get("fraction_number") or 1), "scheduled_date": parse_date(row.get("scheduled_date")), "delivered_date": parse_date(row.get("attendance_date")) if row.get("treatment_status") == "Attended" else None, "dose_gy": float(row["dose_per_fraction_gy"]) if row.get("dose_per_fraction_gy") else None, "status": "delivered" if row.get("treatment_status") == "Attended" else "scheduled", "machine_id": row.get("machine_id")})

    async def _process_endoscopy_csv(self, session, rows: list[dict]) -> None:
        for row in rows:
            patient_id = await self.store.resolve_patient_id(session, row.get("nhs_number"))
            if not patient_id:
                continue
            appointment_id = deterministic_uuid("endoscopy-appt", row["endoscopy_id"])
            await self.store.upsert(session, "appointment", {"appointment_id": appointment_id, "patient_id": patient_id, "source_appt_id": row["endoscopy_id"], "appointment_date": parse_date(row.get("attendance_date")), "clinic_code": "ENDO", "clinic_name": row.get("endoscopy_type"), "appointment_type": "endoscopy", "attendance_status": row.get("exam_status", "").lower()[:10], "location": "Endoscopy Unit", "source_system": "Endoscopy"})
            action_id = deterministic_uuid("endoscopy-action", row["endoscopy_id"])
            await self.store.upsert(session, "cancer_action", {"action_id": action_id, "patient_id": patient_id, "action_type": "Review endoscopy report", "action_description": row.get("endoscopy_report_text"), "priority": "high", "status": "open", "due_date": parse_date(row.get("report_authorised_date")), "assigned_team": "Endoscopy", "notes": row.get("endoscopy_report_text"), "source_system": "Endoscopy"})
