"""
Quick Test - Generate Audio Samples with Cartesia
"""
import os
from dotenv import load_dotenv
from cartesia import Cartesia

load_dotenv()

print("\n🎤 Cartesia TTS Audio Test")
print("=" * 60)

# Initialize client
client = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))
print("✅ Client initialized")

# Test 1: Arabic greeting
print("\n📝 Generating Arabic sample...")
with open("output/arabic_sample.wav", "wb") as f:
    for chunk in client.tts.bytes(
        model_id="sonic-3",
        transcript="مرحباً، أنا مريم من عيادة كيربوت الطبية. كيف يمكنني مساعدتك اليوم؟",
        voice={"mode": "id", "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"},
        language="ar",
        output_format={"container": "wav", "sample_rate": 44100, "encoding": "pcm_s16le"},
    ):
        f.write(chunk)
print("✅ Arabic saved: output/arabic_sample.wav")

# Test 2: English greeting
print("\n📝 Generating English sample...")
with open("output/english_sample.wav", "wb") as f:
    for chunk in client.tts.bytes(
        model_id="sonic-3",
        transcript="Hello! I'm Mariam from CareBot Medical Clinic. How can I help you today?",
        voice={"mode": "id", "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"},
        language="en",
        output_format={"container": "wav", "sample_rate": 44100, "encoding": "pcm_s16le"},
    ):
        f.write(chunk)
print("✅ English saved: output/english_sample.wav")

# Test 3: Medical question in Arabic
print("\n📝 Generating medical question (Arabic)...")
with open("output/arabic_medical.wav", "wb") as f:
    for chunk in client.tts.bytes(
        model_id="sonic-3",
        transcript="هل تعاني من أي حساسية؟ هذا مهم لتخطيط العلاج.",
        voice={"mode": "id", "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"},
        language="ar",
        output_format={"container": "wav", "sample_rate": 44100, "encoding": "pcm_s16le"},
    ):
        f.write(chunk)
print("✅ Medical question saved: output/arabic_medical.wav")

# Test 4: Medical question in English
print("\n📝 Generating medical question (English)...")
with open("output/english_medical.wav", "wb") as f:
    for chunk in client.tts.bytes(
        model_id="sonic-3",
        transcript="Do you have any allergies? This is important for treatment planning.",
        voice={"mode": "id", "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"},
        language="en",
        output_format={"container": "wav", "sample_rate": 44100, "encoding": "pcm_s16le"},
    ):
        f.write(chunk)
print("✅ Medical question saved: output/english_medical.wav")

print("\n" + "=" * 60)
print("✅ All samples generated successfully!")
print("\nGenerated files:")
print("  • output/arabic_sample.wav      - Arabic greeting")
print("  • output/english_sample.wav     - English greeting")
print("  • output/arabic_medical.wav     - Arabic medical question")
print("  • output/english_medical.wav    - English medical question")
print("\n🔊 Open these files to hear how Cartesia sounds!")
print("=" * 60)
