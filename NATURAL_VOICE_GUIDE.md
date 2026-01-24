# Natural Voice Solutions for Pre-Visit Agent

## Problem
Coqui TTS requires Python 3.11 and complex setup. Need natural-sounding alternatives, preferably with voice cloning for Egyptian Arabic.

## ✅ Solutions Ranked by Recommendation

### 🏆 Option 1: Edge TTS (RECOMMENDED) ⭐⭐⭐⭐⭐

**Best free option with very natural Egyptian Arabic**

```bash
# Installation
pip install edge-tts pygame

# Run the agent
python voice_agent_edge_tts.py
```

**Pros:**
- ✅ **FREE** (uses Microsoft Edge TTS)
- ✅ **Very natural** Egyptian Arabic voice
- ✅ **ar-EG-SalmaNeural** - Female Egyptian voice
- ✅ **ar-EG-ShakirNeural** - Male Egyptian voice
- ✅ Fast response time
- ✅ Easy to implement
- ✅ No API key needed

**Cons:**
- ⚠️ Unofficial API (could change)
- ⚠️ Requires internet connection

**Quality:** ⭐⭐⭐⭐⭐ (9/10)
**Cost:** FREE
**Setup:** Easy

---

### 💎 Option 2: ElevenLabs (Voice Cloning) ⭐⭐⭐⭐⭐⭐

**Best quality with voice cloning capability**

```bash
# Installation
pip install elevenlabs

# Set API key in .env
ELEVENLABS_API_KEY=your_key_here
```

**Pros:**
- ✅ **Best quality** (most natural)
- ✅ **Voice cloning** - Upload Egyptian Arabic sample
- ✅ Emotion control
- ✅ Multilingual (Arabic + English)
- ✅ Streaming support
- ✅ Professional grade

**Cons:**
- 💰 Costs money (~$5/1000 API calls)
- 🔑 Requires API key

**Quality:** ⭐⭐⭐⭐⭐⭐ (10/10)
**Cost:** $5-30/month
**Setup:** Medium
**Voice Cloning:** YES

**How to Clone Voice:**
1. Record 10-minute Egyptian Arabic sample
2. Upload to ElevenLabs dashboard
3. Train custom voice (5-10 minutes)
4. Use voice ID in API calls

```python
from elevenlabs import generate, play

audio = generate(
    text="صباح الخير! أنا مريم",
    voice="your_cloned_voice_id",
    model="eleven_multilingual_v2"
)
play(audio)
```

---

### 🏢 Option 3: Azure Cognitive Services ⭐⭐⭐⭐⭐

**Enterprise-grade with SSML support**

```bash
# Installation
pip install azure-cognitiveservices-speech

# Set API key in .env
AZURE_SPEECH_KEY=your_key_here
AZURE_SPEECH_REGION=eastus
```

**Pros:**
- ✅ Professional quality
- ✅ Neural voices (very natural)
- ✅ **SSML support** - Control emotion, speed, pitch
- ✅ Excellent Arabic support
- ✅ Reliable, enterprise-grade
- ✅ Custom neural voices available

**Cons:**
- 💰 Costs money (~$4/1000 API calls)
- 🔑 Requires Azure account

**Quality:** ⭐⭐⭐⭐⭐ (9/10)
**Cost:** $4-16/1000 calls
**Setup:** Medium
**SSML:** YES (emotion control)

**Example with Emotion:**
```python
ssml = '''
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ar-EG">
    <voice name="ar-EG-SalmaNeural">
        <prosody rate="medium" pitch="medium">
            <emphasis level="moderate">صباح الخير!</emphasis>
            أنا مريم من عيادة كيربوت.
        </prosody>
    </voice>
</speak>
'''
```

---

### 📦 Option 4: Enhanced gTTS ⭐⭐⭐

**Basic but functional fallback**

```bash
# Already installed
pip install gtts pygame
```

**Pros:**
- ✅ FREE
- ✅ Easy to use
- ✅ No API key needed
- ✅ Arabic support
- ✅ Works everywhere

**Cons:**
- ⚠️ Less natural
- ⚠️ No emotion control
- ⚠️ Limited voice options
- ⚠️ Basic quality

**Quality:** ⭐⭐⭐ (6/10)
**Cost:** FREE
**Setup:** Very easy

---

## 🎯 Recommendation Based on Use Case

### For Development/Testing
→ **Edge TTS** (ar-EG-SalmaNeural)
- Free, natural, easy setup
- Perfect for prototyping

### For Production with Budget
→ **ElevenLabs** with voice cloning
- Best quality
- Can clone actual Egyptian receptionist voice
- Professional impression

### For Enterprise/Healthcare
→ **Azure Cognitive Services**
- HIPAA compliant
- Enterprise SLA
- SSML for emotion control
- Reliable

### For Quick MVP/No Budget
→ **Edge TTS** or enhanced gTTS
- Both free
- Edge TTS much better quality

---

## 🚀 Quick Start Guide

### Using Edge TTS (Recommended)

1. **Install:**
   ```bash
   pip install edge-tts pygame
   ```

2. **Run:**
   ```bash
   python voice_agent_edge_tts.py
   ```

3. **Test voices:**
   ```bash
   # List all Arabic voices
   edge-tts --list-voices | grep "ar-"
   
   # Test Egyptian Female voice
   edge-tts --voice ar-EG-SalmaNeural --text "مرحبا" --write-media test.mp3
   ```

### Using ElevenLabs with Voice Cloning

1. **Get API key:** https://elevenlabs.io (free tier available)

2. **Clone a voice:**
   - Record 10-minute Egyptian Arabic sample
   - Upload at elevenlabs.io/voice-lab
   - Get voice ID

3. **Use in code:**
   ```python
   from elevenlabs import generate, play, set_api_key
   
   set_api_key("your_key")
   
   audio = generate(
       text="صباح الخير! أنا مريم من عيادة كيربوت",
       voice="cloned_voice_id",
       model="eleven_multilingual_v2"
   )
   
   play(audio)
   ```

---

## 📊 Comparison Table

| Feature | Edge TTS | ElevenLabs | Azure | gTTS |
|---------|----------|------------|-------|------|
| **Quality** | 9/10 | 10/10 | 9/10 | 6/10 |
| **Cost** | FREE | $5-30/mo | $4-16/1k | FREE |
| **Egyptian Arabic** | ✅ Native | ✅ Cloneable | ✅ Native | ✅ Basic |
| **Voice Cloning** | ❌ | ✅ YES | ✅ Custom | ❌ |
| **Emotion Control** | ⚠️ Limited | ✅ YES | ✅ SSML | ❌ |
| **Offline** | ❌ | ❌ | ❌ | ❌ |
| **API Reliability** | ⚠️ Unofficial | ✅ Official | ✅ Official | ✅ Official |
| **Setup Difficulty** | Easy | Medium | Medium | Easy |

---

## 🎤 Voice Cloning Best Practices

If you choose ElevenLabs or Azure Custom:

1. **Recording requirements:**
   - 10-30 minutes of clear audio
   - Native Egyptian Arabic speaker
   - Professional microphone
   - Quiet environment
   - Natural conversation tone

2. **Content:**
   - Mix of questions and statements
   - Common medical phrases
   - Emotional variation (empathy, concern, reassurance)
   - Different sentence lengths

3. **Quality checks:**
   - No background noise
   - Consistent volume
   - Natural pace
   - Clear pronunciation

---

## 🔧 Implementation in Your Project

The voice agent is already set up! Just run:

```bash
# Best option (Edge TTS)
python voice_agent_edge_tts.py

# Or test all options
python natural_voice_options.py
```

All TTS options integrate with your existing:
- ✅ Speech recognition (Google STT)
- ✅ GPT-4o mini conversation
- ✅ Pre-visit consultation flow
- ✅ Data extraction

---

## 💡 Next Steps

1. **Test Edge TTS** (recommended, free)
   ```bash
   python voice_agent_edge_tts.py
   ```

2. **If satisfied:** Use in production

3. **If need voice cloning:**
   - Get ElevenLabs account
   - Record Egyptian Arabic sample
   - Train voice
   - Update code with voice ID

4. **For enterprise:**
   - Set up Azure account
   - Use SSML for emotion
   - Implement custom neural voice
