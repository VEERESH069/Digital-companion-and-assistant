"""
Voice Agent with OpenAI TTS - Natural Multilingual Voice
=========================================================
Uses OpenAI TTS for natural Arabic + English voice mixing

Features:
- Natural female voice (nova)
- Fluent Arabic and English
- Handles code-switching seamlessly
- High quality audio

Run: python voice_agent_windows_tts.py
"""

import os
import sys
import tempfile
import speech_recognition as sr
from openai import OpenAI
from dotenv import load_dotenv
import pygame

# Load environment
load_dotenv()

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ ERROR: OPENAI_API_KEY not set in .env file")
    sys.exit(1)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("=" * 70)
print("PRE-VISIT VOICE AGENT - Natural Multilingual")
print("Powered by: OpenAI TTS (nova) + GPT-4o mini")
print("=" * 70)

# Initialize
recognizer = sr.Recognizer()
microphone = sr.Microphone()
pygame.mixer.init()

# Conversation history
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
- Note allergies for treatment planning
- Respond in the same language the patient uses"""}
]


def speak(text: str):
    """
    Speak text using OpenAI TTS - Natural female voice
    
    Supports:
    - Arabic and English
    - Code-switching (mixing languages)
    - Natural intonation
    - Emotion
    """
    try:
        print(f"\n🔊 Agent: {text}")
        
        # Generate speech using OpenAI TTS
        response = client.audio.speech.create(
            model="tts-1",  # Use "tts-1-hd" for higher quality
            voice="nova",   # Female voice options: alloy, nova, shimmer
            input=text,
            speed=1.0       # Adjust speed: 0.25 to 4.0
        )
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_path = temp_file.name
        temp_file.close()
        
        # Write audio data
        response.stream_to_file(temp_path)
        
        # Play audio
        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
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
        print(f"   → Falling back to text output")
        return False


def listen():
    """Listen and convert speech to text"""
    try:
        print("\n🎤 Listening... (speak now)")
        
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
        
        print("   ⏳ Processing...")
        
        # Try Arabic first
        try:
            text = recognizer.recognize_google(audio, language="ar-EG")
            return text, "ar"
        except:
            # Try English
            try:
                text = recognizer.recognize_google(audio, language="en-US")
                return text, "en"
            except:
                return None, None
                
    except sr.WaitTimeoutError:
        print("   ⚠ No speech detected")
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
            messages=conversation_history,
            temperature=0.7,
            max_tokens=100
        )
        
        ai_response = response.choices[0].message.content or "معلش، مفهمتش. ممكن تعيد تاني؟"
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        return ai_response
    except Exception as e:
        print(f"   ✗ AI Error: {e}")
        return "Sorry, I encountered an error. Could you repeat that?"


# Start conversation
print("\n✓ Ready! Starting conversation...\n")
print("💡 Tip: Speak clearly in Arabic or English")
print("💡 Voice can mix both languages naturally")
print("💡 Say 'goodbye' or 'مع السلامة' to exit\n")

# Greeting with language mixing (natural code-switching)
speak("صباح الخير! Good morning! I'm Mariam from CareBot Clinic. كيف حالك النهاردة؟")

# Main conversation loop
turn = 0
max_turns = 15

while turn < max_turns:
    user_text, lang = listen()
    
    if user_text:
        print(f"\n👤 You: {user_text}")
        
        # Check for exit
        user_lower = user_text.lower()
        if any(word in user_lower for word in ["goodbye", "bye", "مع السلامة", "وداعا", "exit", "stop", "end"]):
            speak("شكراً جداً! Thank you for calling. ربنا يشفيك. Get well soon!")
            break
        
        # Get AI response
        ai_response = get_response(user_text)
        
        # Speak response
        speak(ai_response)
        
        turn += 1
    else:
        print("   (No speech detected, try again)")

print("\n" + "=" * 70)
print(f"CONVERSATION COMPLETE - {turn} turns")
print("=" * 70)

# Summary
print("\n📊 Consultation Summary:")
print(f"   Total turns: {turn}")
print(f"   Messages: {len(conversation_history) - 1}")
print("\n✓ Patient information collected")
print("✓ Ready for doctor review")
