"""
Test script for PDF generation pipeline.
Tests the extraction → JSON → PDF flow without voice interaction.

Usage: python tests/test_pdf_pipeline.py
"""

import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Make project root importable when running this script from tests/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load environment
load_dotenv()

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ ERROR: OPENAI_API_KEY not set in .env file")
    sys.exit(1)

# Set up output directory
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Import OpenAI client
from openai import OpenAI
import json
import uuid
from datetime import datetime, timezone

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Sample conversation history for testing
test_conversation = [
    {"role": "system", "content": "You are a medical receptionist..."},
    {"role": "assistant", "content": "Good morning! I'm Mariam from CareBot Clinic. How can I help you today?"},
    {"role": "user", "content": "Hi, I have a really bad toothache that's been bothering me for about 3 days now."},
    {"role": "assistant", "content": "I'm sorry to hear that. On a scale of 1-10, how would you rate the pain?"},
    {"role": "user", "content": "It's about an 8, especially when I drink something hot or cold."},
    {"role": "assistant", "content": "That sounds quite painful. Which tooth is affected?"},
    {"role": "user", "content": "It's my upper right back tooth, the molar I think."},
    {"role": "assistant", "content": "I see. Are you currently taking any medications for the pain?"},
    {"role": "user", "content": "Yes, I've been taking ibuprofen but it only helps a little bit."},
    {"role": "assistant", "content": "Do you have any allergies to medications we should know about?"},
    {"role": "user", "content": "Yes, I'm allergic to penicillin. It gives me a rash."},
    {"role": "assistant", "content": "Thank you for letting us know. Do you have any other medical conditions?"},
    {"role": "user", "content": "I have diabetes type 2, and I take metformin for it. Also high blood pressure."},
    {"role": "assistant", "content": "Thank you for sharing that. We'll make sure the doctor is aware."},
]


def extract_clinical_data(conversation: list) -> dict:
    """Extract structured clinical data from conversation history."""
    transcript = "\n".join([
        f"{'Agent' if msg['role'] == 'assistant' else 'Patient'}: {msg['content']}"
        for msg in conversation if msg['role'] != 'system'
    ])
    
    extraction_prompt = f"""Analyze this pre-visit medical conversation and extract structured clinical data.

CONVERSATION:
{transcript}

Extract and return a JSON object with this EXACT structure:
{{
    "clinical_data": {{
        "chief_complaint": "main complaint or null",
        "duration": "how long symptoms or null",
        "severity": <1-10 or null>,
        "location": "body location or null",
        "triggers": ["trigger1", "trigger2"],
        "current_medications": ["med1", "med2"],
        "allergies": ["allergy1"],
        "previous_dental_work": "description or null",
        "medical_conditions": ["condition1", "condition2"]
    }},
    "confidence_scores": {{
        "chief_complaint": <0.0-1.0>,
        "duration": <0.0-1.0>,
        "severity": <0.0-1.0>,
        "location": <0.0-1.0>,
        "triggers": <0.0-1.0>,
        "current_medications": <0.0-1.0>,
        "allergies": <0.0-1.0>,
        "previous_dental_work": <0.0-1.0>,
        "medical_conditions": <0.0-1.0>
    }},
    "clinical_summary": "2-3 sentence clinical summary",
    "red_flags": ["red flag 1", "red flag 2"],
    "urgency_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "recommended_specialist": "specialist type or General Dentist"
}}

IMPORTANT:
- Set confidence to 0.0 if information was not discussed
- Detect red flags: diabetes+infection, severe pain, swelling, fever, etc.
- Urgency: CRITICAL=immediate, HIGH=same day, MEDIUM=within week, LOW=routine
- Return ONLY valid JSON, no explanation"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0.1,
            max_tokens=800
        )
        
        result_text = response.choices[0].message.content or "{}"
        result_text = result_text.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        return json.loads(result_text)
    except Exception as e:
        print(f"   ⚠ Extraction error: {e}")
        return {}


def build_clinical_payload(extracted_data: dict, patient_id: Optional[str] = None) -> dict:
    """Build complete clinical payload for PDF generation."""
    if not patient_id:
        patient_id = f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    conversation_id = f"CONV-{datetime.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()
    
    urgency = extracted_data.get("urgency_level", "MEDIUM")
    routing_decision = {
        "needs_triage": urgency in ["HIGH", "CRITICAL"],
        "pre_scheduled": urgency not in ["CRITICAL"],
        "appointment_confirmed": False,
        "doctor_assigned": None
    }
    
    return {
        "patient_id": patient_id,
        "conversation_id": conversation_id,
        "timestamp": timestamp,
        "clinical_data": extracted_data.get("clinical_data", {}),
        "confidence_scores": extracted_data.get("confidence_scores", {}),
        "clinical_summary": extracted_data.get("clinical_summary", ""),
        "red_flags": extracted_data.get("red_flags", []),
        "urgency_level": urgency,
        "recommended_specialist": extracted_data.get("recommended_specialist", "General Dentist"),
        "routing_decision": routing_decision
    }


def save_clinical_payload(payload: dict, output_dir: Path) -> Path:
    """Save clinical payload as JSON file."""
    filename = f"clinical_payload_{payload['conversation_id']}.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ JSON saved: {filepath}")
    return filepath


def generate_pdfs(payload: dict, output_dir: Path) -> tuple:
    """Generate doctor and patient PDF summaries."""
    try:
        from previsit_agent.generate_pdf_summary import ClinicalPayload, build_pdf
        
        clinical_payload = ClinicalPayload.from_dict(payload)
        
        doctor_pdf = output_dir / f"doctor_briefing_{payload['conversation_id']}.pdf"
        patient_pdf = output_dir / f"patient_copy_{payload['conversation_id']}.pdf"
        
        build_pdf(clinical_payload, doctor_pdf, audience="doctor")
        build_pdf(clinical_payload, patient_pdf, audience="patient")
        
        return doctor_pdf, patient_pdf
    except ImportError as e:
        print(f"   ⚠ PDF generation module not found: {e}")
        return None, None
    except Exception as e:
        print(f"   ⚠ PDF generation error: {e}")
        return None, None


def main():
    print("=" * 70)
    print("🧪 TESTING PDF GENERATION PIPELINE")
    print("=" * 70)
    
    # Step 1: Extract clinical data
    print("\n1️⃣ Testing clinical data extraction...")
    extracted_data = extract_clinical_data(test_conversation)
    
    print("\n   Extracted data preview:")
    print(f"   - Chief complaint: {extracted_data.get('clinical_data', {}).get('chief_complaint', 'N/A')}")
    print(f"   - Severity: {extracted_data.get('clinical_data', {}).get('severity', 'N/A')}")
    print(f"   - Urgency: {extracted_data.get('urgency_level', 'N/A')}")
    print(f"   - Red flags: {len(extracted_data.get('red_flags', []))}")
    
    # Step 2: Build payload
    print("\n2️⃣ Building clinical payload...")
    payload = build_clinical_payload(extracted_data, patient_id="TEST-001")
    print(f"   - Patient ID: {payload['patient_id']}")
    print(f"   - Conversation ID: {payload['conversation_id']}")
    
    # Step 3: Save JSON
    print("\n3️⃣ Saving JSON...")
    json_path = save_clinical_payload(payload, OUTPUT_DIR)
    
    # Step 4: Generate PDFs
    print("\n4️⃣ Generating PDFs...")
    doctor_pdf, patient_pdf = generate_pdfs(payload, OUTPUT_DIR)
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    print(f"\n📁 Files created in: {OUTPUT_DIR}")
    
    # List files
    for f in OUTPUT_DIR.iterdir():
        if f.name.startswith(("clinical_payload_", "doctor_briefing_", "patient_copy_")):
            print(f"   • {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    
    print("\n📋 Clinical Summary:")
    print(f"   {payload['clinical_summary']}")
    
    if payload['red_flags']:
        print("\n⚠️ Red Flags Detected:")
        for flag in payload['red_flags']:
            print(f"   • {flag}")

if __name__ == "__main__":
    main()