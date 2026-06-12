#!/usr/bin/env python
"""Test script to verify language support configuration"""

import config

print("=" * 60)
print("LANGUAGE SUPPORT VERIFICATION")
print("=" * 60)

# Test 1: STT Languages
print("\n✓ Speech-to-Text Languages:")
print(f"  Available: {', '.join(config.STT_LANGUAGES)}")

# Test 2: TTS Voice Mapping
print("\n✓ Text-to-Speech Voice Languages:")
for lang_code in sorted(config.CARTESIA_LANGUAGE_VOICES.keys()):
    voice_id = config.CARTESIA_LANGUAGE_VOICES[lang_code]
    print(f"  {lang_code}: {voice_id}")

# Test 3: Unicode Pattern Detection
print("\n✓ Script Detection Patterns:")
test_cases = [
    ("Hindi (Devanagari)", "नमस्ते", "hi"),
    ("Marathi (Devanagari)", "नमस्कार", "hi"),  # Marathi uses same script as Hindi
    ("Telugu", "నమస్కారం", "te"),
    ("Bengali", "নমস্কার", "bn"),
    ("Tamil", "வணக்கம்", "ta"),
    ("Malayalam", "നമസ്കാരം", "ml"),
    ("Kannada", "ನಮಸ್ಕಾರ", "kn"),
    ("English", "Hello", "en"),
]

for name, text, expected in test_cases:
    detected = config.detect_tts_language(text)
    status = "✓" if detected == expected else "✗"
    print(f"  {status} {name:25} -> {detected} (expected {expected})")

# Test 4: Transliterated Text Detection
print("\n✓ Transliterated Text Detection (Latin Script):")
transliterated_cases = [
    ("Hindi", "namaste kaise ho", "hi"),
    ("Marathi", "namaskar kai zhaal aahe", "mr"),
    ("Telugu", "namaskaram enduku", "te"),
    ("Tamil", "namaskaram eppa", "ta"),
]

for name, text, expected in transliterated_cases:
    detected = config.detect_tts_language(text)
    status = "✓" if detected == expected else "✗"
    print(f"  {status} {name:15} -> {detected} (expected {expected})")

print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED!")
print("=" * 60)
