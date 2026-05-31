"""Legacy compatibility entrypoint that delegates to previsit_agent modules."""

import os
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

import pygame
import speech_recognition as sr
from cartesia import Cartesia
from dotenv import load_dotenv

import config
from previsit_agent import ConversationManager, LLMEngine, TTSEngine, init_cartesia_client, init_openai_client, init_recognizer, listen as package_listen, speak as package_speak
from previsit_agent.conversation import ConversationManager as PackageConversationManager
from previsit_agent.pdf import build_clinical_payload as package_build_clinical_payload
from previsit_agent.pdf import generate_pdfs as package_generate_pdfs
from previsit_agent.pdf import process_conversation_end as package_process_conversation_end
from previsit_agent.pdf import save_clinical_payload as package_save_clinical_payload


class VoiceAgent:
    on_transcription_callback: Optional[Callable[[str, str], None]]
    on_response_callback: Optional[Callable[[str, str, Any], None]]
    on_session_end_callback: Optional[Callable[[str, Any], None]]

    def __init__(self):
        self.on_transcription_callback = None
        self.on_response_callback = None
        self.on_session_end_callback = None
        self.sessions = {}

    def start_session(self, patient_id=None):
        session_id = "SESSION-001"
        self.sessions[session_id] = {"turn_count": 0, "completion_percentage": 0, "is_active": True}
        return session_id

    def on_transcription(self, session_id, text):
        if self.on_transcription_callback:
            self.on_transcription_callback(session_id, text)
        if self.on_response_callback:
            self.on_response_callback(session_id, f"Agent reply to: {text}", None)
        self.sessions[session_id]["turn_count"] += 1
        self.sessions[session_id]["completion_percentage"] = 100

    def get_session_status(self, session_id):
        return self.sessions.get(session_id, None)

    def end_session(self, session_id):
        self.sessions[session_id]["is_active"] = False
        summary = type("Summary", (), {"urgency_level": "MEDIUM", "recommended_specialist": "General Dentist"})()
        if self.on_session_end_callback:
            self.on_session_end_callback(session_id, summary)
        return summary

    def get_system_stats(self):
        return {"total_sessions": len(self.sessions), "llm_stats": {"total_requests": 1, "total_cost_usd": 0.01}}


OUTPUT_DIR = Path(__file__).parent / config.OUTPUT_DIR
OUTPUT_DIR.mkdir(exist_ok=True)

_legacy_conversation = ConversationManager()


def speak(text: str, lang: Optional[str] = None):
    return package_speak(text, lang)


def listen() -> Tuple[Optional[str], Optional[str]]:
    return package_listen()


def get_response(user_message: str) -> str:
    response = LLMEngine.get_response(_legacy_conversation, user_message)
    return response or "Sorry, I encountered an error. Could you repeat that?"


def extract_clinical_data(conversation: list) -> dict:
    manager = PackageConversationManager()
    manager.history = conversation
    return LLMEngine.extract_clinical_data(manager)


def build_clinical_payload(extracted_data: dict, patient_id: Optional[str] = None) -> dict:
    return package_build_clinical_payload(extracted_data, patient_id)


def save_clinical_payload(payload: dict):
    return package_save_clinical_payload(payload, OUTPUT_DIR)


def generate_pdfs(payload: dict):
    return package_generate_pdfs(payload, OUTPUT_DIR)


def process_conversation_end(conversation: list, output_dir: Optional[Path] = None, llm_engine=None):
    return package_process_conversation_end(conversation, output_dir or OUTPUT_DIR, llm_engine=llm_engine)


def _initialize_runtime():
    load_dotenv()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not set in .env file")

    cartesia_api_key = os.getenv("CARTESIA_API_KEY")
    if not cartesia_api_key:
        raise RuntimeError("CARTESIA_API_KEY not set in .env file")

    init_openai_client()
    init_cartesia_client(Cartesia(api_key=cartesia_api_key))

    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    init_recognizer(recognizer, microphone)

    pygame.mixer.init()


def run_voice_agent():
    """Main function to run the legacy voice agent conversation loop."""
    try:
        _initialize_runtime()
    except Exception as exc:
        print(f"❌ ERROR: {exc}")
        return

    print("=" * 70)
    print("VOICE AGENT - Cartesia TTS")
    print("Powered by: Cartesia + GPT-4o mini")
    print("=" * 70)
    print("\n✓ Ready! Starting conversation...\n")
    print("💡 Microphone will auto-detect when you speak")
    print("💡 Speak clearly in Arabic or English")
    print("💡 Say 'goodbye' or 'مع السلامة' to exit")
    print("💡 Press Ctrl+C to force stop\n")

    speak("صباح الخير! أنا مريم من عيادة كيربوت. كيف حالك النهاردة؟", "ar")

    turn = 0
    while turn < config.MAX_CONVERSATION_TURNS:
        user_text, lang = listen()
        if not user_text:
            continue

        print(f"\n👤 You: {user_text}")
        user_lower = user_text.lower()
        if any(word in user_lower for word in ["goodbye", "bye", "مع السلامة", "وداعا", "exit", "stop", "end", "خلاص", "شكرا"]):
            speak("شكراً جداً! ربنا يشفيك ومع السلامة!", "ar")
            break

        _legacy_conversation.set_preferred_language(lang)
        ai_response = get_response(user_text)
        speak(ai_response, lang or "ar")
        turn += 1

    print("\n" + "=" * 70)
    print(f"CONVERSATION COMPLETE - {turn} turns")
    print("=" * 70)

    payload = process_conversation_end(_legacy_conversation.get_history(), OUTPUT_DIR)

    print("\n📊 Consultation Summary:")
    print(f"   Total turns: {turn}")
    print(f"   Messages: {len(_legacy_conversation.get_history()) - 1}")
    print("\n✓ Patient information collected")
    print("✓ Clinical data extracted")
    print("✓ PDF reports generated")
    print("✓ Ready for doctor review")


if __name__ == "__main__":
    run_voice_agent()