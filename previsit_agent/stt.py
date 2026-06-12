"""Speech-to-text module using Google Speech Recognition"""

import speech_recognition as sr
from typing import Optional, Tuple


def listen() -> Tuple[Optional[str], Optional[str]]:
    """
    Listen and convert speech to text with auto-detection.
    
    Returns:
        Tuple of (text, language_code) or (None, None) if error
    """
    global recognizer, microphone
    
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
        
        # Try multiple languages in priority order
        languages = [
            ("hi-IN", "Hindi", "hi"),
            ("mr-IN", "Marathi", "mr"),
            ("te-IN", "Telugu", "te"),
            ("bn-IN", "Bengali", "bn"),
            ("ta-IN", "Tamil", "ta"),
            ("ml-IN", "Malayalam", "ml"),
            ("en-IN", "English", "en"),
        ]
        
        for lang_code, lang_name, lang_abbr in languages:
            try:
                text = recognizer.recognize_google(audio, language=lang_code)  # type: ignore
                print(f"   ✓ Detected: {lang_name}")
                return text, lang_abbr
            except:
                continue
        
        # Final fallback to English (US)
        try:
            text = recognizer.recognize_google(audio, language="en-US")  # type: ignore
            print(f"   ✓ Detected: English (US)")
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


# Global recognizer and microphone (initialized from main)
recognizer: Optional[sr.Recognizer] = None
microphone: Optional[sr.Microphone] = None


def init_recognizer(rec: sr.Recognizer, mic: sr.Microphone):
    """Initialize global recognizer and microphone"""
    global recognizer, microphone
    recognizer = rec
    microphone = mic
