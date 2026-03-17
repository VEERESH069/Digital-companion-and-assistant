"""
Quick Test - Generate Audio Samples with Cartesia
"""
import os
from dotenv import load_dotenv
from cartesia import Cartesia

import config

load_dotenv()

print("\n🎤 Cartesia TTS Audio Test")
print("=" * 60)

if not os.path.exists("output"):
    os.makedirs("output")

# Initialize client
client = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))
print("✅ Client initialized")


def generate_sample(output_path, transcript, language):
    voice_id = config.get_cartesia_voice_id(language)

    with open(output_path, "wb") as audio_file:
        for chunk in client.tts.bytes(
            model_id=config.CARTESIA_MODEL,
            transcript=transcript,
            voice={"mode": "id", "id": voice_id},
            language=language,
            output_format=config.CARTESIA_OUTPUT_FORMAT,  # type: ignore
        ):
            audio_file.write(chunk)

# Test 1: Arabic greeting
print("\n📝 Generating Arabic sample...")
generate_sample(
    "output/arabic_sample.wav",
    "مرحباً، أنا مريم من عيادة كيربوت الطبية. كيف يمكنني مساعدتك اليوم؟",
    "ar",
)
print("✅ Arabic saved: output/arabic_sample.wav")

# Test 2: English greeting
print("\n📝 Generating English sample...")
generate_sample(
    "output/english_sample.wav",
    "Hello! I'm Mariam from CareBot Medical Clinic. How can I help you today?",
    "en",
)
print("✅ English saved: output/english_sample.wav")

# Test 3: Medical question in Arabic
print("\n📝 Generating medical question (Arabic)...")
generate_sample(
    "output/arabic_medical.wav",
    "هل تعاني من أي حساسية؟ هذا مهم لتخطيط العلاج.",
    "ar",
)
print("✅ Medical question saved: output/arabic_medical.wav")

# Test 4: Medical question in English
print("\n📝 Generating medical question (English)...")
generate_sample(
    "output/english_medical.wav",
    "Do you have any allergies? This is important for treatment planning.",
    "en",
)
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
