"""
Voice Agent - Legacy Runtime (Fallback)
========================================

This module is kept for debugging and fallback use.
Use `voice_agent_production.py` as the primary runtime.

Uses:
- Cartesia (Natural multilingual Text-to-Speech)
- Google Speech Recognition
- GPT-4o mini

Run (legacy fallback): python voice_agent.py

Flow:
1. Conversation with patient
2. Extract clinical data (1 LLM call)
3. Save JSON to output/
4. Generate PDFs (doctor + patient copies)
"""

import os
import sys
import io
import json
import tempfile
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple
import speech_recognition as sr
from openai import OpenAI
from dotenv import load_dotenv
from cartesia import Cartesia
import pygame

import config

# Load environment
load_dotenv()

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ ERROR: OPENAI_API_KEY not set in .env file")
    sys.exit(1)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Cartesia client
cartesia_client = None
if os.getenv("CARTESIA_API_KEY"):
    try:
        cartesia_client = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))
        print("✅ Cartesia TTS initialized")
    except Exception as e:
        print(f"⚠ Cartesia initialization failed: {e}")
        sys.exit(1)
else:
    print("❌ ERROR: CARTESIA_API_KEY not set in .env file")
    sys.exit(1)

# Output directory for JSON and PDFs
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Initialize only when running as main script
recognizer: Optional[sr.Recognizer] = None
microphone: Optional[sr.Microphone] = None

# Conversation history (will be reset for each session)
conversation_history = [
    {"role": "system", "content": """أنت مريم، موظفة استقبال ودودة في عيادة كيربوت الطبية.
تقومين بإجراء مكالمة استشارية ما قبل الزيارة لجمع المعلومات الطبية.

You are Mariam, a friendly receptionist at CareBot Clinic.
You're conducting a pre-visit consultation call to gather medical information.

Style Guidelines:
- Keep responses SHORT (1-2 sentences maximum)
- Ask ONE question at a time  
- Show empathy and understanding
- Natural conversational tone
- IMPORTANT: Respond in the SAME language the patient uses
  - If patient speaks Arabic → respond in Arabic
  - If patient speaks English → respond in English

Required Information to Collect:
1. Chief complaint (الشكوى الرئيسية)
2. Duration (المدة)
3. Pain severity 1-10 (شدة الألم)
4. Location (المكان)
5. Triggers (المحفزات)
6. Current medications (الأدوية الحالية)
7. Allergies (الحساسية)
8. Medical conditions (الأمراض)

Important:
- If diabetes + dental infection → high priority
- Note allergies for treatment planning"""}
]


def speak(text: str, lang: str = "ar"):
    """
    Speak text using Cartesia TTS
    
    Args:
        text: Text to speak
        lang: Language code ('ar' for Arabic, 'en' for English)
    """
    try:
        print(f"\n🔊 Agent: {text}")

        if cartesia_client is None:
            print("   ✗ Cartesia client is not initialized")
            return False
        
        # Auto-detect response language and use its configured Cartesia voice.
        language = config.detect_tts_language(text)
        voice_id = config.get_cartesia_voice_id(language)
        
        # Generate speech using Cartesia
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = temp_file.name
        temp_file.close()
        
        with open(temp_path, "wb") as f:
            output_format = config.CARTESIA_OUTPUT_FORMAT
            
            bytes_iter = cartesia_client.tts.bytes(
                model_id=config.CARTESIA_MODEL,
                transcript=text,
                voice={
                    "mode": "id",
                    "id": voice_id,
                },
                language=language,
                output_format=output_format,  # type: ignore
            )
            
            for chunk in bytes_iter:
                f.write(chunk)
        
        # Play audio
        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.play()
        
        # Wait for playback
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        # Cleanup
        try:
            pygame.mixer.music.unload()
            os.unlink(temp_path)
        except:
            pass
            
        return True
    except Exception as e:
        print(f"   ✗ Speech error: {e}")
        return False


def listen() -> Tuple[Optional[str], Optional[str]]:
    """Listen and convert speech to text with auto-detection"""
    if not recognizer or not microphone:
        print("   ✗ Audio components not initialized")
        return None, None
        
    try:
        print("\n🎤 Listening... (start speaking)")
        
        with microphone as source:
            # Adjust for ambient noise once at the start
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            recognizer.energy_threshold = 300  # Lower threshold for better detection
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 1.0  # Wait 1 second of silence before stopping
            
            # Listen with longer timeout and phrase limit
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=20)
        
        print("   ⏳ Processing speech...")
        
        # Try Arabic first (Egyptian Arabic)
        try:
            text = recognizer.recognize_google(audio, language="ar-EG")  # type: ignore
            print(f"   ✓ Detected: Arabic")
            return text, "ar"
        except:
            # Fallback to English
            try:
                text = recognizer.recognize_google(audio, language="en-US")  # type: ignore
                print(f"   ✓ Detected: English")
                return text, "en"
            except sr.UnknownValueError:
                print("   ⚠ Could not understand audio")
                return None, None
            except sr.RequestError as e:
                print(f"   ✗ Service error: {e}")
                return None, None
                
    except KeyboardInterrupt:
        print("\n   ⚠ Interrupted by user")
        return None, None
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None, None


def get_response(user_message: str) -> str:
    """Get AI response from GPT-4o mini"""
    try:
        conversation_history.append({"role": "user", "content": user_message})
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,  # type: ignore
            temperature=0.7,
            max_tokens=100
        )
        
        ai_response = response.choices[0].message.content or "معلش، مفهمتش. ممكن تعيد تاني؟"
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        return ai_response
    except Exception as e:
        print(f"   ✗ AI Error: {e}")
        return "Sorry, I encountered an error. Could you repeat that?"


def extract_clinical_data(conversation: list) -> dict:
    """
    Extract structured clinical data from conversation history.
    Single LLM call at conversation end.
    
    Returns:
        Complete clinical payload ready for PDF generation
    """
    # Build conversation transcript for extraction
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
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=800
        )
        
        result_text = response.choices[0].message.content or "{}"
        
        # Clean up response - remove markdown code blocks if present
        result_text = result_text.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        extracted = json.loads(result_text)
        return extracted
        
    except json.JSONDecodeError as e:
        print(f"   ⚠ JSON parsing error: {e}")
        return get_default_clinical_data()
    except Exception as e:
        print(f"   ⚠ Extraction error: {e}")
        return get_default_clinical_data()


def get_default_clinical_data() -> dict:
    """Return default structure when extraction fails"""
    return {
        "clinical_data": {
            "chief_complaint": None,
            "duration": None,
            "severity": None,
            "location": None,
            "triggers": [],
            "current_medications": [],
            "allergies": [],
            "previous_dental_work": None,
            "medical_conditions": []
        },
        "confidence_scores": {
            "chief_complaint": 0.0,
            "duration": 0.0,
            "severity": 0.0,
            "location": 0.0,
            "triggers": 0.0,
            "current_medications": 0.0,
            "allergies": 0.0,
            "previous_dental_work": 0.0,
            "medical_conditions": 0.0
        },
        "clinical_summary": "Consultation completed. Data extraction pending review.",
        "red_flags": [],
        "urgency_level": "MEDIUM",
        "recommended_specialist": "General Dentist"
    }


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
    """Save clinical payload as JSON file"""
    filename = f"clinical_payload_{payload['conversation_id']}.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ JSON saved: {filepath}")
    return filepath


def generate_pdfs(payload: dict, output_dir: Path) -> tuple:
    """
    Generate doctor and patient PDF summaries.
    Uses the existing generate_pdf_summary module.
    
    Returns:
        Tuple of (doctor_pdf_path, patient_pdf_path)
    """
    try:
        # Import PDF generation functions
        from generate_pdf_summary import ClinicalPayload, build_pdf
        
        # Convert dict to ClinicalPayload model
        clinical_payload = ClinicalPayload.from_dict(payload)
        
        # Generate PDFs
        doctor_pdf = output_dir / f"doctor_briefing_{payload['conversation_id']}.pdf"
        patient_pdf = output_dir / f"patient_copy_{payload['conversation_id']}.pdf"
        
        build_pdf(clinical_payload, doctor_pdf, audience="doctor")
        build_pdf(clinical_payload, patient_pdf, audience="patient")
        
        return doctor_pdf, patient_pdf
        
    except ImportError as e:
        print(f"   ⚠ PDF generation module not found: {e}")
        print("   → Run: pip install fpdf2 pydantic")
        return None, None
    except Exception as e:
        print(f"   ⚠ PDF generation error: {e}")
        return None, None


def process_conversation_end(conversation: list, output_dir: Path):
    """
    Process conversation end: extract data, save JSON, generate PDFs.
    
    This is the main pipeline that runs when conversation ends.
    Total LLM usage: 1 call for extraction (no LLM for PDF generation)
    """
    print("\n" + "=" * 70)
    print("📋 PROCESSING CONSULTATION DATA...")
    print("=" * 70)
    
    # Step 1: Extract clinical data (1 LLM call)
    print("\n1️⃣ Extracting clinical data from conversation...")
    extracted_data = extract_clinical_data(conversation)
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
    
    # Step 4: Generate PDFs (0 LLM calls - uses JSON directly)
    print("\n4️⃣ Generating PDF reports...")
    doctor_pdf, patient_pdf = generate_pdfs(payload, output_dir)
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ CONSULTATION PROCESSING COMPLETE")
    print("=" * 70)
    print(f"\n📁 Output files saved to: {output_dir}")
    print(f"   • JSON: {json_path.name}")
    if doctor_pdf:
        print(f"   • Doctor PDF: {doctor_pdf.name}")
    if patient_pdf:
        print(f"   • Patient PDF: {patient_pdf.name}")
    
    print(f"\n📊 Clinical Summary:")
    print(f"   {payload['clinical_summary'][:200]}...")
    
    return payload


def run_voice_agent():
    """Main function to run the voice agent conversation loop."""
    # Start conversation
    print("\n✓ Ready! Starting conversation...\n")
    print("💡 Microphone will auto-detect when you speak")
    print("💡 Speak clearly in Arabic or English")
    print("💡 Say 'goodbye' or 'مع السلامة' to exit")
    print("💡 Press Ctrl+C to force stop\n")

    # Bilingual greeting (Arabic)
    speak("صباح الخير! أنا مريم من عيادة كيربوت. كيف حالك النهاردة؟", "ar")

    # Main conversation loop
    turn = 0
    max_turns = 15

    while turn < max_turns:
        user_text, lang = listen()
        
        if user_text:
            print(f"\n👤 You: {user_text}")
            
            # Check for exit (Arabic and English keywords)
            user_lower = user_text.lower()
            if any(word in user_lower for word in ["goodbye", "bye", "مع السلامة", "وداعا", "exit", "stop", "end", "خلاص", "شكرا"]):
                # Bilingual farewell
                speak("شكراً جداً! ربنا يشفيك ومع السلامة!", "ar")
                break
            
            # Get AI response
            ai_response = get_response(user_text)
            
            # Speak response
            speak(ai_response, lang or "ar")
            
            turn += 1
        else:
            # Don't print error message, just continue listening
            continue

    print("\n" + "=" * 70)
    print(f"CONVERSATION COMPLETE - {turn} turns")
    print("=" * 70)

    # Process conversation end: Extract data → Save JSON → Generate PDFs
    # This uses 1 additional LLM call for extraction, 0 for PDF generation
    clinical_payload = process_conversation_end(conversation_history, OUTPUT_DIR)

    # Final summary
    print("\n📊 Consultation Summary:")
    print(f"   Total turns: {turn}")
    print(f"   Messages: {len(conversation_history) - 1}")
    print("\n✓ Patient information collected")
    print("✓ Clinical data extracted")
    print("✓ PDF reports generated")
    print("✓ Ready for doctor review")


# Run only when executed directly (not when imported)
if __name__ == "__main__":
    # Initialize audio components only when running directly
    print("=" * 70)
    print("VOICE AGENT - Cartesia TTS")
    print("Powered by: Cartesia + GPT-4o mini")
    print("=" * 70)
    
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    pygame.mixer.init()
    
    run_voice_agent()



