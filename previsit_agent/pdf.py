"""PDF generation and clinical data management module"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

import config


def build_clinical_payload(extracted_data: dict, patient_id: Optional[str] = None) -> dict:
    """
    Build complete clinical payload for PDF generation.
    
    Args:
        extracted_data: Data extracted from conversation
        patient_id: Optional patient ID (auto-generated if not provided)
    
    Returns:
        Complete payload matching clinical_payload.json schema
    """
    # Generate IDs
    if not patient_id:
        patient_id = f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    conversation_id = f"CONV-{datetime.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Determine routing decision based on urgency
    urgency = extracted_data.get("urgency_level", "MEDIUM")
    routing_decision = {
        "needs_triage": urgency in ["HIGH", "CRITICAL"],
        "pre_scheduled": urgency not in ["CRITICAL"],
        "appointment_confirmed": False,
        "doctor_assigned": None
    }
    
    # Build complete payload
    payload = {
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
    
    return payload


def save_clinical_payload(payload: dict, output_dir: Path) -> Path:
    """
    Save clinical payload as JSON file
    
    Args:
        payload: Clinical data payload
        output_dir: Output directory for JSON file
    
    Returns:
        Path to saved JSON file
    """
    filename = f"clinical_payload_{payload['conversation_id']}.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ JSON saved: {filepath}")
    return filepath


def generate_pdfs(payload: dict, output_dir: Path) -> Tuple[Optional[Path], Optional[Path]]:
    """
    DEPRECATED: PDF generation disabled for production web deployment.
    
    All clinical data is stored in JSON format and accessed via the API.
    Users can generate PDFs client-side if needed using the exported JSON.
    
    Args:
        payload: Clinical data payload (unused in web version)
        output_dir: Output directory (unused in web version)
    
    Returns:
        Tuple of (None, None) - PDFs not generated in web deployment
    """
    print("   ℹ PDF generation disabled in web deployment")
    print("   → Clinical data available via API as JSON export")
    return None, None


def process_conversation_end(conversation_history: list, output_dir: Path, llm_engine=None):
    """
    Process conversation end: extract data and save JSON (Web Version).
    
    Updated for production web deployment:
    - Only generates JSON export (no PDFs)
    - Clinical data stored in database via API
    - PDFs can be generated client-side from JSON if needed
    
    Args:
        conversation_history: Full conversation history
        output_dir: Output directory for JSON files
        llm_engine: LLM engine for clinical data extraction (optional)
    
    Returns:
        Clinical payload dict
    """
    from .conversation import ConversationManager
    from .llm import LLMEngine
    
    print("\n" + "=" * 70)
    print("📋 PROCESSING CONSULTATION DATA (WEB VERSION)...")
    print("=" * 70)
    
    # Step 1: Extract clinical data (1 LLM call)
    print("\n1️⃣ Extracting clinical data from conversation...")
    
    if llm_engine is None:
        llm_engine = LLMEngine()
    
    # Create a temporary conversation manager for extraction
    conversation = ConversationManager()
    conversation.history = conversation_history
    
    extracted_data = llm_engine.extract_clinical_data(conversation)
    print("   ✓ Data extracted")
    
    # Step 2: Build complete payload
    print("\n2️⃣ Building clinical payload...")
    payload = build_clinical_payload(extracted_data)
    print(f"   ✓ Patient ID: {payload['patient_id']}")
    print(f"   ✓ Conversation ID: {payload['conversation_id']}")
    print(f"   ✓ Urgency Level: {payload['urgency_level']}")
    
    if payload['red_flags']:
        print(f"   ⚠ Red Flags: {len(payload['red_flags'])} detected")
    
    # Step 3: Save JSON
    print("\n3️⃣ Saving clinical payload...")
    json_path = save_clinical_payload(payload, output_dir)
    
    # Note: PDF generation is disabled in web deployment
    print("\n4️⃣ PDF generation disabled (web deployment)")
    print("   → Access clinical data via API: /api/sessions/{session_id}/export")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ CONSULTATION PROCESSING COMPLETE (JSON ONLY)")
    print("=" * 70)
    print(f"\n📁 Output files saved to: {output_dir}")
    print(f"   • JSON: {json_path.name}")
    
    print(f"\n📊 Clinical Summary:")
    print(f"   {payload['clinical_summary'][:200]}...")
    
    print("\n📤 Next Steps:")
    print("   1. Session is stored in database")
    print("   2. Access via: /api/sessions/{session_id}/export")
    print("   3. Client can generate PDF from JSON if needed")
    
    return payload
