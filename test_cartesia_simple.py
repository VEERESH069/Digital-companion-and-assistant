"""
Simple Cartesia TTS Test
"""
import os
from dotenv import load_dotenv
from cartesia import Cartesia

# Load environment
load_dotenv()

print("\n🎤 Testing Cartesia TTS API")
print(f"API Key: {'✅ Set' if os.getenv('CARTESIA_API_KEY') else '❌ Missing'}")

# Initialize Cartesia
try:
    client = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))
    print("✅ Cartesia client initialized")
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    exit(1)

# Test Arabic
print("\n📝 Generating Arabic audio...")
text_ar = "مرحباً، أنا مريم من عيادة كيربوت"

try:
    with open("output/test_arabic.wav", "wb") as f:
        bytes_iter = client.tts.bytes(
            model_id="sonic-3",
            transcript=text_ar,
            voice={
                "mode": "id",
                "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",
            },
            language="ar",
            output_format={
                "container": "wav",
                "sample_rate": 44100,
                "encoding": "pcm_s16le",
            },
        )
        
        for chunk in bytes_iter:
            f.write(chunk)
    
    print("✅ Arabic audio saved: output/test_arabic.wav")
except Exception as e:
    print(f"❌ Arabic test failed: {e}")

# Test English
print("\n📝 Generating English audio...")
text_en = "Welcome to Cartesia! I'm Mariam from CareBot Clinic."

try:
    with open("output/test_english.wav", "wb") as f:
        bytes_iter = client.tts.bytes(
            model_id="sonic-3",
            transcript=text_en,
            voice={
                "mode": "id",
                "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",
            },
            language="en",
            output_format={
                "container": "wav",
                "sample_rate": 44100,
                "encoding": "pcm_s16le",
            },
        )
        
        for chunk in bytes_iter:
            f.write(chunk)
    
    print("✅ English audio saved: output/test_english.wav")
except Exception as e:
    print(f"❌ English test failed: {e}")

print("\n✅ Test complete! Check output/ folder for audio files.")
