"""
Test Cartesia TTS with Arabic and English
"""
import os
from dotenv import load_dotenv
from cartesia import Cartesia
import subprocess

# Load environment
load_dotenv()

# Initialize Cartesia
client = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))

def test_tts(text, language, filename):
    """Test TTS generation"""
    print(f"\n{'='*60}")
    print(f"Testing: {text}")
    print(f"Language: {language}")
    print(f"Output: {filename}")
    print(f"{'='*60}")
    
    try:
        # Generate audio
        from pathlib import Path
        parent = Path(filename).parent
        if not parent.exists():
            parent.mkdir(parents=True)
        with open(filename, "wb") as f:
            bytes_iter = client.tts.bytes(
                model_id="sonic-3",
                transcript=text,
                voice={
                    "mode": "id",
                    "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",
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
        
        print(f"✅ Audio generated: {filename}")
        
        # Try to play the audio (requires ffplay or similar)
        try:
            # On Windows, you can use pygame or another player
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            print(f"✅ Playback completed")
        except Exception as e:
            print(f"⚠ Playback failed (audio file saved): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("\n🎤 Testing Cartesia TTS")
    print(f"API Key: {'✅ Set' if os.getenv('CARTESIA_API_KEY') else '❌ Missing'}")
    
    # Test Arabic
    test_tts(
        text="مرحباً، أنا مريم من عيادة كيربوت. كيف يمكنني مساعدتك اليوم؟",
        language="ar",
        filename="output/test_arabic.wav"
    )
    
    # Test English
    test_tts(
        text="Welcome to Cartesia! I'm Mariam from CareBot Clinic. How can I help you today?",
        language="en",
        filename="output/test_english.wav"
    )
    
    # Test Mixed (common in real scenarios)
    test_tts(
        text="مرحباً! Welcome to CareBot Clinic. كيف حالك؟",
        language="ar",  # Primary language
        filename="output/test_mixed.wav"
    )
    
    print("\n✅ Testing complete!")
    print("Check the output/ folder for generated audio files.")
