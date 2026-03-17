"""
Real-Time Voice Agent Test
===========================

Test the complete voice agent with live microphone input.
Simulates a real patient conversation in Arabic or English.

Usage:
    python tests/test_realtime.py

Press Ctrl+C to stop.
"""

import sys
import os
import logging

# Allow running from tests/ or project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import speech_recognition as sr
import config
from voice_agent_production import ConversationManager, TTSEngine, STTEngine, LLMEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run real-time voice agent test"""

    print("\n" + "=" * 70)
    print("  PRE-VISIT VOICE AGENT - Real-Time Test")
    print("=" * 70 + "\n")

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY not set in .env file")
        print("   Please add your API key and try again.\n")
        sys.exit(1)

    # Choose language
    print("Select language:")
    print("  1. Arabic (العربية)")
    print("  2. English")
    choice = input("\nEnter choice (1 or 2): ").strip()
    lang_name = "Arabic" if choice == "1" else "English"
    print(f"\n✓ Language: {lang_name}")
    print(f"✓ LLM Model: {config.LLM_MODEL}")

    # Initialize services
    print("\nInitializing services...")

    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    conversation = ConversationManager()
    tts_engine = TTSEngine()
    stt_engine = STTEngine(recognizer, microphone)
    print("  ✓ All services ready")

    # Greeting
    greeting = "صباح الخير! مرحباً! I'm Mariam from CareBot Clinic. كيف حالك النهاردة؟"
    print("\n" + "=" * 70)
    print(f"🤖 AGENT: {greeting}")
    print("=" * 70 + "\n")
    tts_engine.speak(greeting)
    conversation.add_assistant_message(greeting)

    print("📢 INSTRUCTIONS:")
    print("  • Speak into your microphone")
    print("  • Agent will respond to each input")
    print("  • Press Ctrl+C to end conversation")
    print("\n" + "-" * 70 + "\n")

    # Main loop
    silence_count = 0
    try:
        while not conversation.is_complete():
            user_text, lang = stt_engine.listen()

            if user_text == "__silence__":
                silence_count += 1
                if silence_count == 1:
                    tts_engine.speak("هل أنت هناك؟ Are you still there? Take your time.")
                else:
                    tts_engine.speak("لم أسمعك. I didn't hear anything — please speak when you're ready.")
                    silence_count = 0
                continue

            if not user_text:
                continue

            silence_count = 0
            print(f"\n👤 YOU: {user_text}")
            print("-" * 70)

            LLMEngine.stream_and_speak(conversation, user_text, tts_engine)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("Ending conversation...")
        print("=" * 70)
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\n❌ Error: {e}")
    finally:
        print("\n📊 CONVERSATION SUMMARY")
        print("=" * 70)
        print(f"Total turns: {conversation.turn_count}")
        print("\n" + "=" * 70)
        print("✅ Test completed.")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
