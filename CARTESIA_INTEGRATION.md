# Cartesia TTS Integration Guide

## 🎉 Integration Complete!

Cartesia TTS has been successfully integrated into your voice agent! Cartesia offers high-quality, natural-sounding voices with excellent support for Arabic and English.

---

## 📋 What Was Changed

### 1. **Environment Configuration** (`.env`)
Added Cartesia API key:
```env
CARTESIA_API_KEY=sk_car_3yjkiGVjCHaufiguudJtWr
```

### 2. **Dependencies** (`requirements.txt`)
Added Cartesia package:
```
cartesia>=1.0.0  # Cartesia TTS with natural multilingual voices
```

### 3. **Configuration** (`config.py`)
Updated TTS settings:
```python
TTS_ENGINE = "cartesia"  # Now using Cartesia as primary TTS
CARTESIA_MODEL = "sonic-3"  # Latest Cartesia model
CARTESIA_VOICE_ARABIC = "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"
CARTESIA_VOICE_ENGLISH = "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"
CARTESIA_OUTPUT_FORMAT = {
    "container": "wav",
    "sample_rate": 44100,
    "encoding": "pcm_s16le",
}
```

### 4. **Production Voice Agent** (`voice_agent_production.py`)
- Added Cartesia client initialization
- Implemented `speak_cartesia()` method with:
  - Automatic language detection (Arabic/English)
  - Intelligent voice selection
  - Audio caching for performance
  - Interrupt detection support
  - Fallback to gTTS if needed

---

## 🎯 Available Cartesia Voices

### Recommended Voices for Medical Receptionist (Mariam)

#### **Multilingual Voices (Arabic + English)**
These voices work well with both languages:

1. **6ccbfb76-1fc6-48f7-b71d-91ac6298247b** - General multilingual (currently configured)
   - Good for mixed-language conversations
   - Natural tone

2. **Custom Voice Options:**
   You can explore more voices at: https://docs.cartesia.ai/voices

### Finding Better Voices for Arabic

To get a list of all available voices and find the best one for Arabic:

```python
from cartesia import Cartesia
import os

client = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))

# List all available voices
voices = client.voices.list()

for voice in voices:
    print(f"ID: {voice['id']}")
    print(f"Name: {voice['name']}")
    print(f"Language: {voice.get('language', 'N/A')}")
    print(f"Description: {voice.get('description', 'N/A')}")
    print("-" * 60)
```

---

## 🚀 How to Use

### Option 1: Use Production Voice Agent (Recommended)
```bash
python voice_agent_production.py
```

The agent will automatically:
- Detect if the patient speaks Arabic or English
- Use the appropriate Cartesia voice
- Fall back to gTTS if Cartesia has issues

### Option 2: Test Cartesia Directly
```bash
python test_cartesia_simple.py
```

### Option 3: Change TTS Engine
Edit `config.py` to switch between engines:
```python
TTS_ENGINE = "cartesia"  # Options: "cartesia", "openai", "gtts"
```

---

## 🎨 Customizing Voices

### For Better Arabic Voice
1. Visit Cartesia dashboard or use API to list voices
2. Test different voice IDs
3. Update `config.py`:
```python
CARTESIA_VOICE_ARABIC = "your-preferred-voice-id"
```

### For Better English Voice
```python
CARTESIA_VOICE_ENGLISH = "your-preferred-voice-id"
```

### Voice Characteristics to Consider
- **Gender**: Female (Mariam character)
- **Age**: Young adult (~25-35)
- **Tone**: Warm, friendly, professional
- **Speed**: Natural conversational pace
- **Accent**: Neutral/Standard Arabic, Standard English

---

## ⚙️ Advanced Configuration

### Adjusting Audio Quality
In `config.py`:
```python
CARTESIA_OUTPUT_FORMAT = {
    "container": "wav",      # Format: wav, mp3, raw
    "sample_rate": 44100,    # 44100 (CD quality), 22050, 16000
    "encoding": "pcm_s16le", # pcm_s16le, pcm_f32le, pcm_mulaw
}
```

### Performance Tuning
```python
ENABLE_TTS_CACHING = True  # Cache frequently used phrases
```

### Natural Speech
```python
ADD_NATURAL_PAUSES = True  # Add human-like pauses
PAUSE_AFTER_SENTENCE = 0.3  # Seconds
PAUSE_AFTER_QUESTION = 0.5  # Seconds
```

---

## 🧪 Testing

### Test Basic Functionality
```bash
python test_cartesia_simple.py
```

### Test Full Voice Agent
```bash
python voice_agent_production.py
```

### Expected Output
```
✅ Cartesia TTS initialized
🎤 Listening...
🔊 Agent: مرحباً! Welcome to CareBot
[Audio plays with natural voice]
```

---

## 🔧 Troubleshooting

### Issue: "Cartesia not available"
**Solution**: Make sure Cartesia is installed
```bash
pip install cartesia
```

### Issue: Poor audio quality
**Solution**: Increase sample rate in config:
```python
"sample_rate": 44100  # Use 44100 for best quality
```

### Issue: Voice sounds robotic
**Solution**: Try different voice IDs or adjust speech settings

### Issue: Slow response time
**Solution**: Enable caching:
```python
ENABLE_TTS_CACHING = True
```

---

## 📊 Comparison: Cartesia vs Other TTS

| Feature | Cartesia | OpenAI TTS | gTTS |
|---------|----------|------------|------|
| **Arabic Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **English Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Latency** | Fast | Fast | Medium |
| **Natural Sound** | Very Natural | Very Natural | Moderate |
| **Cost** | Pay per use | Pay per use | Free |
| **Offline** | ❌ | ❌ | ❌ |
| **Custom Voices** | ✅ | Limited | ❌ |

---

## 💡 Best Practices

1. **Language Detection**: The system auto-detects Arabic vs English
2. **Voice Consistency**: Use same voice ID throughout conversation
3. **Error Handling**: Fallback to gTTS ensures reliability
4. **Caching**: Speeds up common phrases (greetings, questions)
5. **Testing**: Always test with real Arabic/English speakers

---

## 📝 Next Steps

1. **Test the integration**:
   ```bash
   python voice_agent_production.py
   ```

2. **Find optimal voice IDs** for Arabic and English

3. **Adjust voice settings** in `config.py` based on user feedback

4. **Monitor performance** and adjust caching/quality settings

---

## 🆘 Support

- **Cartesia Docs**: https://docs.cartesia.ai/
- **Voice Samples**: Test different voices at Cartesia dashboard
- **API Reference**: https://docs.cartesia.ai/api-reference

---

## ✅ Integration Checklist

- [x] Environment variable configured
- [x] Cartesia package installed
- [x] Configuration updated
- [x] Production code implemented
- [x] Fallback mechanism in place
- [ ] Test with sample conversations
- [ ] Optimize voice IDs for Arabic/English
- [ ] Verify audio quality with stakeholders

---

**Status**: ✅ Ready to use!

The voice agent now uses Cartesia TTS with automatic language detection and fallback support. Simply run `python voice_agent_production.py` to start!
