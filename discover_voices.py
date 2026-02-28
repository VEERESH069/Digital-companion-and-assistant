"""
Cartesia Voice Discovery Tool
Find the best voices for Arabic and English
"""
import os
from dotenv import load_dotenv
from cartesia import Cartesia

# Load environment
load_dotenv()

def discover_voices():
    """List all available Cartesia voices"""
    try:
        client = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))
        print("\n🎤 Discovering Cartesia Voices...")
        print("=" * 80)
        
        # Get all voices
        voices_response = client.voices.list()
        
        # Convert to list
        voices = list(voices_response)  # type: ignore
        
        print(f"\n✅ Found {len(voices)} voices\n")
        
        # Filter and display relevant voices
        arabic_voices = []
        english_voices = []
        multilingual_voices = []
        
        for voice in voices:
            # Access voice attributes directly (not using .get())
            voice_id = getattr(voice, 'id', 'N/A')  # type: ignore
            voice_name = getattr(voice, 'name', 'Unnamed')  # type: ignore
            language = str(getattr(voice, 'language', 'Unknown'))  # type: ignore
            description = str(getattr(voice, 'description', 'No description'))  # type: ignore
            
            # Categorize voices
            if 'ar' in language.lower() or 'arabic' in description.lower():
                arabic_voices.append(voice)
            elif 'en' in language.lower() or 'english' in description.lower():
                english_voices.append(voice)
            elif 'multilingual' in description.lower() or 'multi' in language.lower():
                multilingual_voices.append(voice)
        
        # Display results
        if multilingual_voices:
            print("\n🌍 MULTILINGUAL VOICES (Best for mixed Arabic/English)")
            print("-" * 80)
            for voice in multilingual_voices:
                print(f"ID:   {getattr(voice, 'id', 'N/A')}")
                print(f"Name: {getattr(voice, 'name', 'Unnamed')}")
                print(f"Lang: {getattr(voice, 'language', 'N/A')}")
                print(f"Desc: {getattr(voice, 'description', 'N/A')}")
                print()
        
        if arabic_voices:
            print("\n🇸🇦 ARABIC VOICES")
            print("-" * 80)
            for voice in arabic_voices:
                print(f"ID:   {getattr(voice, 'id', 'N/A')}")
                print(f"Name: {getattr(voice, 'name', 'Unnamed')}")
                print(f"Desc: {getattr(voice, 'description', 'N/A')}")
                print()
        
        if english_voices:
            print("\n🇬🇧 ENGLISH VOICES")
            print("-" * 80)
            for voice in english_voices:
                print(f"ID:   {getattr(voice, 'id', 'N/A')}")
                print(f"Name: {getattr(voice, 'name', 'Unnamed')}")
                print(f"Desc: {getattr(voice, 'description', 'N/A')}")
                print()
        
        # Show all voices if no specific languages found
        if not arabic_voices and not english_voices and not multilingual_voices:
            print("\n📋 ALL AVAILABLE VOICES")
            print("-" * 80)
            for voice in voices:
                print(f"ID:   {getattr(voice, 'id', 'N/A')}")
                print(f"Name: {getattr(voice, 'name', 'Unnamed')}")
                print(f"Lang: {getattr(voice, 'language', 'N/A')}")
                print(f"Desc: {getattr(voice, 'description', 'N/A')}")
                print()
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS FOR MEDICAL RECEPTIONIST (MARIAM)")
        print("-" * 80)
        print("Look for voices with these characteristics:")
        print("  • Female voice (professional receptionist)")
        print("  • Young adult age range (25-35)")
        print("  • Warm, friendly, professional tone")
        print("  • Clear articulation")
        print("  • Neutral/Standard Arabic accent")
        print("  • Natural English pronunciation")
        print()
        print("🔧 To test a voice, update config.py:")
        print("   CARTESIA_VOICE_ARABIC = 'voice-id-here'")
        print("   CARTESIA_VOICE_ENGLISH = 'voice-id-here'")
        print()
        
        return voices
        
    except Exception as e:
        print(f"\n❌ Error discovering voices: {e}")
        print("\nPossible issues:")
        print("  • Check your CARTESIA_API_KEY in .env")
        print("  • Verify internet connection")
        print("  • Ensure cartesia package is installed: pip install cartesia")
        return None

def test_voice(voice_id, text, language, output_file):
    """Test a specific voice"""
    try:
        client = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))
        
        print(f"\n🎙️ Testing voice: {voice_id}")
        print(f"Text: {text}")
        print(f"Language: {language}")
        
        with open(output_file, "wb") as f:
            bytes_iter = client.tts.bytes(
                model_id="sonic-3",
                transcript=text,
                voice={
                    "mode": "id",
                    "id": voice_id,
                },
                language=language,
                output_format={
                    "container": "wav",
                    "sample_rate": 44100,
                    "encoding": "pcm_s16le",
                },
            )
            
            for chunk in bytes_iter:
                f.write(chunk)
        
        print(f"✅ Audio saved: {output_file}")
        print("   Play the file to hear this voice")
        return True
        
    except Exception as e:
        print(f"❌ Error testing voice: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  CARTESIA VOICE DISCOVERY TOOL")
    print("  Find the perfect voices for your medical voice agent")
    print("=" * 80)
    
    # Discover all voices
    voices = discover_voices()
    
    # Test default voice
    if voices:
        print("\n\n🧪 Testing current configuration...")
        print("-" * 80)
        
        # Test Arabic
        test_voice(
            voice_id="6ccbfb76-1fc6-48f7-b71d-91ac6298247b",
            text="مرحباً، أنا مريم من عيادة كيربوت الطبية. كيف يمكنني مساعدتك؟",
            language="ar",
            output_file="output/voice_test_arabic.wav"
        )
        
        # Test English
        test_voice(
            voice_id="6ccbfb76-1fc6-48f7-b71d-91ac6298247b",
            text="Hello, I'm Mariam from CareBot Medical Clinic. How can I help you today?",
            language="en",
            output_file="output/voice_test_english.wav"
        )
    
    print("\n" + "=" * 80)
    print("✅ Voice discovery complete!")
    print("=" * 80)
