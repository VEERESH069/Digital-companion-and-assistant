"""
Real-Time Voice Agent Test
===========================

Test the complete voice agent with live microphone input.
Simulates a real patient conversation in Arabic or English.

Usage:
    python tests/test_realtime.py
    
Press Ctrl+C to stop.
"""

import numpy as np
import sounddevice as sd
import queue
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run real-time voice agent test"""
    
    print("\n" + "="*70)
    print("  PRE-VISIT VOICE AGENT - Real-Time Test")
    print("="*70 + "\n")
    
    # Import modules
    from pre_visit_agent.config.config import AppConfig
    from pre_visit_agent.services.stt_service import RealTimeSTT
    from pre_visit_agent.services.llm_service import LLMService, Message, MessageRole
    from pre_visit_agent.core.conversation_manager import ConversationManager
    
    # Load configuration
    config = AppConfig()
    
    # Check API key
    if not config.llm.api_key:
        print("❌ ERROR: OPENAI_API_KEY not set in .env file")
        print("   Please add your API key and try again.\n")
        sys.exit(1)
    
    # Choose language
    print("Select language:")
    print("  1. Arabic (العربية)")
    print("  2. English")
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        language = "ar"
        lang_name = "Arabic"
        config.stt.language = "ar"
        config.stt.dialect_prompt = "This is a conversation in Egyptian Arabic about dental care."
    else:
        language = "en"
        lang_name = "English"
        config.stt.language = "en"
        config.stt.dialect_prompt = "This is a conversation in English about dental care."
    
    print(f"\n✓ Language: {lang_name}")
    print(f"✓ STT Model: {config.stt.model_size}")
    print(f"✓ LLM Model: {config.llm.model_name}")
    
    # Initialize services
    print("\nInitializing services...")
    
    print("  - Loading STT (Whisper)... This may take a moment...")
    stt = RealTimeSTT(
        model_size=config.stt.model_size,
        language=language,
        min_duration=2.0
    )
    print("  ✓ STT ready")
    
    print("  - Initializing LLM...")
    llm = LLMService(config.llm)
    print("  ✓ LLM ready")
    
    print("  - Initializing TTS...")
    from pre_visit_agent.services.tts_service import TTSService
    config.tts.language = language
    tts = TTSService(config.tts)
    print("  ✓ TTS ready")
    
    print("  - Starting conversation manager...")
    conversation = ConversationManager(config.conversation, llm)
    print("  ✓ Conversation manager ready")
    
    # Start conversation
    greeting = conversation.start_conversation()
    print("\n" + "="*70)
    print(f"🤖 AGENT: {greeting}")
    print("="*70 + "\n")
    
    # Play greeting with TTS
    print("🔊 Playing greeting...")
    tts.speak(greeting)
    
    # Print instructions
    print("📢 INSTRUCTIONS:")
    print("  • Speak into your microphone")
    print("  • Wait 2-3 seconds after speaking")
    print("  • Agent will respond to each input")
    print("  • Press Ctrl+C to end conversation")
    print("\n" + "-"*70 + "\n")
    
    # Audio queue
    audio_queue = queue.Queue()
    
    def audio_callback(indata, frames, time, status):
        """Called by sounddevice for each audio block"""
        if status:
            logger.warning(f"Audio status: {status}")
        audio_queue.put(indata.copy())
    
    def on_transcription(text):
        """Called when speech is transcribed"""
        if not text or text.strip() == "":
            return
        
        print(f"\n👤 YOU: {text}")
        print("-"*70)
        
        # Get agent response
        print("🤖 Agent is thinking...")
        try:
            response = conversation.process_turn(text)
            print(f"🤖 AGENT: {response}")
            
            # Play response with TTS
            print("🔊 Speaking...")
            tts.speak(response)
            print("-"*70 + "\n")
            
            # Check if conversation is complete
            summary = conversation.get_conversation_summary()
            if summary['completion_percentage'] >= 90:
                print("\n✅ Conversation appears complete!")
                print(f"   Collected: {len(summary['collected_data'])} items")
                print(f"   Completion: {summary['completion_percentage']:.0f}%")
                print("\nPress Ctrl+C to end or continue talking...\n")
                
        except Exception as e:
            logger.error(f"Error processing turn: {e}")
            print(f"❌ Error: {e}\n")
    
    # Start STT
    stt.start(on_transcription)
    
    # Start microphone
    try:
        print("🎤 Microphone is ACTIVE - Start speaking!\n")
        
        with sd.InputStream(
            samplerate=16000,
            channels=1,
            dtype='float32',
            callback=audio_callback,
            blocksize=8000  # 0.5s chunks
        ):
            while True:
                audio_chunk = audio_queue.get()
                audio_data = audio_chunk.flatten()
                
                # Volume indicator
                volume = np.max(np.abs(audio_data))
                if volume > 0.01:
                    print(f"\r🔊 Speaking... (volume: {volume:.3f})", end="", flush=True)
                else:
                    print(f"\r🔇 Listening...              ", end="", flush=True)
                
                # Send to STT
                stt.add_audio_chunk(audio_data)
                
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("Ending conversation...")
        print("="*70)
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\n❌ Error: {e}")
    finally:
        # Stop services
        stt.stop()
        
        # Show summary
        try:
            summary = conversation.get_conversation_summary()
            
            print("\n📊 CONVERSATION SUMMARY")
            print("="*70)
            print(f"Session ID: {conversation.session_id}")
            print(f"Duration: {summary['turn_count']} turns")
            print(f"Completion: {summary['completion_percentage']:.0f}%")
            print(f"\nData Collected ({len(summary['collected_data'])}):")
            
            for key, value in summary['collected_data'].items():
                print(f"  • {key}: {value}")
            
            print("\n" + "="*70)
            print("✅ Test completed successfully!")
            print("="*70 + "\n")
            
        except Exception as e:
            logger.error(f"Error getting summary: {e}")


if __name__ == "__main__":
    main()
