"""Synthetic data generators for Cancer 360 foundation build."""

from .appointment_generator import generate_appointments, link_attendance_ids
from .comment_generator import generate_comments
from .diagnosis_generator import generate_diagnoses
from .encounter_generator import generate_encounters
from .endoscopy_generator import generate_endoscopy
from .histology_generator import generate_histology
from .ipt_generator import generate_ipt
from .mdt_generator import generate_mdt_entities
from .patient_generator import generate_patients
from .pathway_generator import generate_pathways
from .radiology_generator import generate_radiology
from .test_result_generator import generate_test_results
from .treatment_generator import generate_treatments

__all__ = [
    "generate_patients",
    "generate_pathways",
    "generate_diagnoses",
    "generate_mdt_entities",
    "generate_appointments",
    "link_attendance_ids",
    "generate_encounters",
    "generate_endoscopy",
    "generate_ipt",
    "generate_comments",
    "generate_radiology",
    "generate_histology",
    "generate_test_results",
    "generate_treatments",
]
