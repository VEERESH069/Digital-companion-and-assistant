"""
Generate doctor and patient PDF summaries from structured clinical JSON.

The script is deterministic, schema-validated, and highlights red flags and
low-confidence fields for clinicians while keeping the patient copy concise.

Usage:
    python generate_pdf_summary.py                # uses embedded sample data
    python generate_pdf_summary.py payload.json   # uses provided JSON
"""

import json
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fpdf import FPDF
from pydantic import BaseModel, Field, ValidationError


LOW_CONFIDENCE_THRESHOLD = 0.85


class ClinicalData(BaseModel):
    chief_complaint: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[int] = Field(default=None, ge=1, le=10)
    location: Optional[str] = None
    triggers: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    previous_dental_work: Optional[str] = None
    medical_conditions: List[str] = Field(default_factory=list)


class ConfidenceScores(BaseModel):
    chief_complaint: float = 0.0
    duration: float = 0.0
    severity: float = 0.0
    location: float = 0.0
    triggers: float = 0.0
    current_medications: float = 0.0
    allergies: float = 0.0
    previous_dental_work: float = 0.0
    medical_conditions: float = 0.0


class RoutingDecision(BaseModel):
    needs_triage: bool = False
    pre_scheduled: bool = False
    appointment_confirmed: bool = False
    doctor_assigned: Optional[str] = None


class ClinicalPayload(BaseModel):
    patient_id: str
    conversation_id: str
    timestamp: str
    clinical_data: ClinicalData
    confidence_scores: ConfidenceScores
    clinical_summary: str
    red_flags: List[str] = Field(default_factory=list)
    urgency_level: str
    recommended_specialist: Optional[str] = None
    routing_decision: RoutingDecision = Field(default_factory=RoutingDecision)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "ClinicalPayload":
        return cls.model_validate(raw)

    def to_machine_json(self) -> Dict[str, Any]:
        return json.loads(self.model_dump_json())


SAMPLE_DATA: Dict[str, Any] = {
    "patient_id": "P12345",
    "conversation_id": "CONV-2026-01-13-001",
    "timestamp": "2026-01-13T14:30:00Z",
    "clinical_data": {
        "chief_complaint": "Severe toothache in upper right molar",
        "duration": "3 days, started Tuesday morning",
        "severity": 8,
        "location": "Upper right first molar (#3)",
        "triggers": [
            "Hot beverages",
            "Chewing on right side",
            "Worse at night"
        ],
        "current_medications": [
            "Ibuprofen 400mg - minimal relief"
        ],
        "allergies": [
            "Penicillin - causes rash"
        ],
        "previous_dental_work": "Root canal on #14 six months ago",
        "medical_conditions": [
            "Type 2 Diabetes - controlled with Metformin",
            "Hypertension - takes Lisinopril"
        ]
    },
    "confidence_scores": {
        "chief_complaint": 0.95,
        "duration": 0.90,
        "severity": 0.95,
        "location": 0.85,
        "triggers": 0.90,
        "current_medications": 0.95,
        "allergies": 1.0,
        "previous_dental_work": 0.85,
        "medical_conditions": 0.95
    },
    "clinical_summary": (
        "Patient reports severe (8/10) pain in upper right first molar (#3) "
        "for 3 days, worsened by hot beverages and chewing, worse at night. "
        "History notable for Type 2 Diabetes, hypertension, and penicillin allergy. "
        "Pain pattern suggests pulpitis or early abscess; NSAIDs provide minimal relief."
    ),
    "red_flags": [
        "Night pain escalation suggests possible abscess",
        "Diabetes increases infection risk",
        "Penicillin allergy limits first-line antibiotics"
    ],
    "urgency_level": "HIGH",
    "recommended_specialist": "Endodontist",
    "routing_decision": {
        "needs_triage": False,
        "pre_scheduled": True,
        "appointment_confirmed": True,
        "doctor_assigned": "Dr. Ahmed Hassan"
    }
}


class SummaryPDF(FPDF):
    def __init__(self, title: str):
        super().__init__()
        self.title_text = title
        self.set_auto_page_break(auto=True, margin=10)
        self.set_margins(10, 10, 10)

    def header(self):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 6, self.title_text, new_y="NEXT", align="C")
        self.ln(1)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def _safe_value(value: Any) -> str:
    return "N/A" if value in (None, "", [], {}) else str(value)


def draw_key_value(pdf: FPDF, key: str, value: Any, line_height: int = 5):
    usable_width = pdf.w - pdf.l_margin - pdf.r_margin - 5
    label_width = 45
    value_width = usable_width - label_width

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(pdf.l_margin)
    pdf.cell(label_width, line_height, f"{key}:")

    pdf.set_font("Helvetica", "", 9)
    current_y = pdf.get_y()
    pdf.set_xy(pdf.l_margin + label_width, current_y)
    pdf.multi_cell(value_width, line_height, _safe_value(value))
    pdf.ln(0.5)


def draw_list(pdf: FPDF, title: str, items: List[str], line_height: int = 5):
    content = items if items else ["None reported"]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(pdf.l_margin)
    pdf.cell(0, line_height, f"{title}:", new_y="NEXT", new_x="LMARGIN")
    pdf.set_font("Helvetica", "", 9)
    usable_width = pdf.w - pdf.l_margin - pdf.r_margin - 5
    for item in content:
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(usable_width, line_height, f"- {item}")
    pdf.ln(1)


def draw_confidence_table(pdf: FPDF, scores: ConfidenceScores):
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(pdf.l_margin)
    pdf.cell(0, 5, "Confidence by field", new_y="NEXT", new_x="LMARGIN")
    pdf.set_font("Helvetica", "", 8)
    usable_width = pdf.w - pdf.l_margin - pdf.r_margin - 5
    label_w = usable_width * 0.7
    value_w = usable_width * 0.3

    for field_name, value in scores.model_dump().items():
        is_low = value < LOW_CONFIDENCE_THRESHOLD
        pdf.set_x(pdf.l_margin)
        pdf.cell(label_w, 5, field_name.replace("_", " ").title())
        if is_low:
            pdf.set_fill_color(255, 235, 232)  # pale red background
        pdf.cell(value_w, 5, f"{value:.2f}", fill=is_low)
        if is_low:
            pdf.set_fill_color(255, 255, 255)  # reset
        pdf.ln(5)
    pdf.ln(1)


def draw_red_flags(pdf: FPDF, red_flags: List[str], urgency_level: str):
    pdf.set_fill_color(255, 230, 230)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(pdf.l_margin)
    usable_width = pdf.w - pdf.l_margin - pdf.r_margin - 5
    pdf.cell(usable_width, 6, f"Urgency: {urgency_level.upper()}", new_y="NEXT", new_x="LMARGIN", fill=True)
    pdf.ln(1)
    draw_list(pdf, "Red Flags", red_flags, line_height=5)


def build_pdf(payload: ClinicalPayload, output_path: Path, audience: str):
    title = "Doctor Briefing" if audience == "doctor" else "Patient Copy"
    pdf = SummaryPDF(f"Pre-Visit Clinical Summary - {title}")
    pdf.add_page()

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Patient ID: {payload.patient_id}", new_y="NEXT", new_x="LMARGIN")
    pdf.cell(0, 5, f"Conversation ID: {payload.conversation_id}", new_y="NEXT", new_x="LMARGIN")
    pdf.cell(0, 5, f"Generated: {datetime.now(timezone.utc).isoformat()}", new_y="NEXT", new_x="LMARGIN")
    pdf.ln(1)

    clinical = payload.clinical_data
    draw_key_value(pdf, "Chief Complaint", clinical.chief_complaint)
    draw_key_value(pdf, "Duration", clinical.duration)
    draw_key_value(pdf, "Severity", clinical.severity)
    draw_key_value(pdf, "Location", clinical.location)

    draw_list(pdf, "Triggers", clinical.triggers)
    draw_list(pdf, "Current Medications", clinical.current_medications)
    draw_list(pdf, "Allergies", clinical.allergies)

    if clinical.previous_dental_work:
        draw_key_value(pdf, "Previous Dental Work", clinical.previous_dental_work)

    draw_list(pdf, "Medical Conditions", clinical.medical_conditions)

    draw_key_value(pdf, "Clinical Summary", payload.clinical_summary, line_height=6)
    draw_red_flags(pdf, payload.red_flags, payload.urgency_level)

    draw_key_value(pdf, "Urgency Level", payload.urgency_level)
    draw_key_value(pdf, "Recommended Specialist", payload.recommended_specialist)

    routing = payload.routing_decision
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(pdf.l_margin)
    pdf.cell(0, 5, "Routing Decision:", new_y="NEXT", new_x="LMARGIN")
    pdf.set_font("Helvetica", "", 9)
    usable_width = pdf.w - pdf.l_margin - pdf.r_margin - 5
    lines = [
        f"Needs triage: {'Yes' if routing.needs_triage else 'No'}",
        f"Pre-scheduled: {'Yes' if routing.pre_scheduled else 'No'}",
        f"Appointment confirmed: {'Yes' if routing.appointment_confirmed else 'No'}",
        f"Doctor assigned: {routing.doctor_assigned or 'TBD'}",
    ]
    for line in lines:
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(usable_width, 5, f"- {line}")
    pdf.ln(1)

    if audience == "doctor":
        draw_confidence_table(pdf, payload.confidence_scores)
    else:
        pdf.ln(2)
        pdf.set_font("Helvetica", "I", 8)
        pdf.multi_cell(0, 5, "This summary is for your reference. Please share any updates with your doctor.")

    pdf.output(str(output_path))
    print(f"✓ PDF saved: {output_path}")


def load_payload(path: Optional[Path]) -> ClinicalPayload:
    if path is None:
        return ClinicalPayload.from_dict(SAMPLE_DATA)

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    return ClinicalPayload.from_dict(raw)


def parse_args():
    parser = ArgumentParser(description="Generate clinician and patient PDFs from structured clinical JSON.")
    parser.add_argument("json_path", nargs="?", type=Path, help="Path to structured JSON payload")
    parser.add_argument("--output-dir", type=Path, default=Path("."), help="Directory to write PDFs")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        payload = load_payload(args.json_path)
    except FileNotFoundError:
        print("❌ JSON file not found. Falling back to sample payload.")
        payload = ClinicalPayload.from_dict(SAMPLE_DATA)
    except ValidationError as exc:
        print("❌ Payload failed validation:")
        print(exc)
        return

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    build_pdf(payload, output_dir / "doctor_briefing.pdf", audience="doctor")
    build_pdf(payload, output_dir / "patient_copy.pdf", audience="patient")

    machine_json_path = output_dir / "clinical_payload.json"
    with machine_json_path.open("w", encoding="utf-8") as f:
        json.dump(payload.to_machine_json(), f, indent=2)
    print(f"✓ Machine-readable JSON saved: {machine_json_path}")


if __name__ == "__main__":
    main()
