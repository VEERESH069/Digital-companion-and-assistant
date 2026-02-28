"""
Quick Test: User Speech → OpenAI AI → Cartesia TTS
====================================================
This demonstrates the complete voice interaction pipeline
"""
import os
from dotenv import load_dotenv
from openai import OpenAI
from cartesia import Cartesia
import speech_recognition as sr
import pygame
import tempfile
import re

# Load environment
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
cartesia_client = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))
pygame.mixer.init()

# Initialize speech recognition
recognizer = sr.Recognizer()
microphone = sr.Microphone()

print("\n" + "="*70)
print("  🎤 VOICE AI DEMO: Speech → OpenAI → Cartesia TTS")
print("="*70)

def listen_to_user():
    """Capture user speech and convert to text"""
    print("\n🎤 Listening... (speak now)")
    
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
    
    print("⏳ Processing speech...")
    
    try:
        # Use Google Speech Recognition
        text = recognizer.recognize_google(audio, language="ar-SA")
        return text
    except:
        try:
            # Fallback to English
            text = recognizer.recognize_google(audio)
            return text
        except Exception as e:
            print(f"❌ Could not understand: {e}")
            return None

def get_ai_response(user_text, conversation_history):
    """Get response from OpenAI"""
    print(f"\n👤 You: {user_text}")
    print("🤖 AI is thinking...")
    
    # Add user message
    conversation_history.append({"role": "user", "content": user_text})
    
    # Get AI response
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history,
        temperature=0.7,
        max_tokens=100
    )
    
    ai_text = response.choices[0].message.content
    
    # Add AI response to history
    conversation_history.append({"role": "assistant", "content": ai_text})
    
    return ai_text

def speak_with_cartesia(text):
    """Convert text to speech using Cartesia"""
    print(f"\n🔊 Mariam: {text}")
    
    # Detect language
    has_arabic = bool(re.search('[\u0600-\u06FF]', text))
    language = "ar" if has_arabic else "en"
    
    # Generate audio
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_path = temp_file.name
    temp_file.close()
    
    with open(temp_path, "wb") as f:
        output_format = {
            "container": "wav",
            "sample_rate": 44100,
            "encoding": "pcm_s16le",
        }
        
        for chunk in cartesia_client.tts.bytes(
            model_id="sonic-3",
            transcript=text,
            voice={"mode": "id", "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"},
            language=language,
            output_format=output_format,  # type: ignore
        ):
            f.write(chunk)
    
    # Play audio
    pygame.mixer.music.load(temp_path)
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
    # Cleanup
    pygame.mixer.music.unload()
    os.unlink(temp_path)

# Main demo
def run_demo():
    """Run interactive voice demo"""
    
    # System prompt for Mariam
    conversation_history = [{
        "role": "system",
        "content": """أنت مريم، موظفة استقبال ودودة في عيادة طبية.
You are Mariam, a friendly receptionist at a medical clinic.
- Keep responses SHORT (1-2 sentences)
- Be warm and helpful
- Respond in the SAME language the user speaks
- If Arabic → respond in Arabic
- If English → respond in English"""
    }]
    
    print("\n💡 Instructions:")
    print("   • Speak in Arabic or English")
    print("   • Say 'goodbye' or 'مع السلامة' to exit")
    print("   • Each turn: You speak → AI responds → Repeat")
    
    # Initial greeting
    greeting = "مرحباً! I'm Mariam. How can I help you today?"
    speak_with_cartesia(greeting)
    conversation_history.append({"role": "assistant", "content": greeting})
    
    # Conversation loop (3 turns demo)
    for turn in range(3):
        print(f"\n{'─'*70}")
        print(f"Turn {turn + 1}/3")
        print('─'*70)
        
        # 1. Listen to user
        user_text = listen_to_user()
        
        if not user_text:
            print("⚠️ No speech detected, trying again...")
            continue
        
        # Check for exit
        if any(word in user_text.lower() for word in ['goodbye', 'bye', 'مع السلامة', 'وداعا']):
            farewell = "شكراً! Thank you! Goodbye!"
            speak_with_cartesia(farewell)
            break
        
        # 2. Get AI response
        ai_response = get_ai_response(user_text, conversation_history)
        
        # 3. Speak AI response
        speak_with_cartesia(ai_response)
    
    print("\n" + "="*70)
    print("✅ Demo Complete!")
    print("="*70)
    print(f"\n📊 Total messages: {len(conversation_history)}")
    print("\nTo run full voice agent: python voice_agent_production.py")

if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
