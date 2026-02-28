# 🧪 Testing Guide - Voice Agent with Cartesia TTS

## Quick Start Testing

### 1️⃣ Test Cartesia TTS Only (Audio Generation)

This tests if Cartesia can generate speech without the full voice agent:

```powershell
python test_audio.py
```

**What it does:**
- Generates 4 audio samples (Arabic greeting, English greeting, Arabic medical, English medical)
- Saves them to `output/` folder
- Plays them automatically

**Expected Output:**
```
🎤 Cartesia TTS Audio Test
============================================================
✅ Client initialized

📝 Generating Arabic sample...
✅ Arabic saved: output/arabic_sample.wav

📝 Generating English sample...
✅ English saved: output/english_sample.wav
```

**Files Created:**
- `output/arabic_sample.wav`
- `output/english_sample.wav`
- `output/arabic_medical.wav`
- `output/english_medical.wav`

---

### 2️⃣ Play Audio Samples Interactively

If you want to listen to the generated samples:

```powershell
python play_samples.py
```

**What it does:**
- Shows a menu of all audio samples
- Lets you play individual samples or all at once
- Interactive player

**Menu:**
```
📋 Available Samples:
  1. Arabic Greeting
  2. English Greeting
  3. Arabic Medical Question
  4. English Medical Question
  5. Play All Samples
  Q. Quit
```

---

### 3️⃣ Test Full Voice Agent (Production)

This is the complete voice agent with speech recognition and Cartesia TTS:

```powershell
python voice_agent_production.py
```

**What it does:**
- Listens to your voice via microphone
- Converts speech to text (STT)
- Processes with GPT-4o mini
- Responds using Cartesia TTS
- Full conversation flow

**Expected Output:**
```
══════════════════════════════════════════════════════════════
  PRODUCTION VOICE AGENT
══════════════════════════════════════════════════════════════
✅ Cartesia TTS initialized

🔊 Agent: مرحباً! أنا مريم من عيادة كيربوت. كيف يمكنني مساعدتك؟

🎤 Listening... (start speaking)
```

**What to say:**
- Start with: "مرحباً" (Arabic) or "Hello" (English)
- The agent will ask medical questions
- Answer naturally
- Say "goodbye" or "مع السلامة" to end

---

### 4️⃣ Test Basic Voice Agent (Simple Version)

Simpler version without advanced features:

```powershell
python voice_agent.py
```

**Differences from production:**
- No advanced features
- Basic conversation flow
- Good for quick testing

---

## 🔍 Troubleshooting Tests

### Test 1: Verify Environment

Check if all packages are installed:

```powershell
python -c "import cartesia, openai, speech_recognition, pygame; print('✅ All packages installed')"
```

**Expected:** `✅ All packages installed`

### Test 2: Check API Keys

Verify your API keys are set:

```powershell
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Cartesia:', '✅' if os.getenv('CARTESIA_API_KEY') else '❌'); print('OpenAI:', '✅' if os.getenv('OPENAI_API_KEY') else '❌')"
```

**Expected:**
```
Cartesia: ✅
OpenAI: ✅
```

### Test 3: Check Microphone

Test if your microphone works:

```powershell
python -c "import speech_recognition as sr; r = sr.Recognizer(); m = sr.Microphone(); print('✅ Microphone detected'); print(f'Device: {m.device_index}')"
```

**Expected:** `✅ Microphone detected`

---

## 📋 Test Sequence (Recommended)

Follow this order for complete testing:

### Step 1: Environment Check ✅
```powershell
python -c "import cartesia, openai, speech_recognition, pygame; print('✅ Ready to test')"
```

### Step 2: Test Cartesia Audio Generation ✅
```powershell
python test_audio.py
```
- Listen to the generated files
- Verify voice quality

### Step 3: Test Interactive Player ✅
```powershell
python play_samples.py
```
- Play each sample
- Confirm audio playback works

### Step 4: Test Full Voice Agent ✅
```powershell
python voice_agent_production.py
```
- Speak into microphone
- Have a short conversation
- Verify end-to-end flow

---

## 🎯 What Each Test Validates

| Test | Validates |
|------|-----------|
| `test_audio.py` | Cartesia API connection, audio generation, file saving |
| `play_samples.py` | Audio playback, pygame functionality |
| `voice_agent_production.py` | Full system: STT + LLM + Cartesia TTS |
| `voice_agent.py` | Basic conversation flow |

---

## 🐛 Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'cartesia'"
**Solution:**
```powershell
pip install cartesia
```

### Issue: "CARTESIA_API_KEY not set"
**Solution:**
1. Check `.env` file exists
2. Verify it contains: `CARTESIA_API_KEY=your_key_here`
3. Restart terminal

### Issue: "No audio output"
**Solution:**
1. Check speakers/headphones are connected
2. Verify Windows audio settings
3. Try: `python play_samples.py`

### Issue: "Microphone not detected"
**Solution:**
1. Check microphone permissions in Windows
2. Test microphone in Windows settings
3. Verify it's set as default recording device

### Issue: Audio sounds robotic/poor quality
**Solution:**
1. Try different voice IDs in `config.py`
2. Run `python discover_voices.py` to find better voices
3. Increase sample rate in config if needed

---

## 📊 Expected Results Summary

### ✅ Successful Test Indicators:

**Audio Quality:**
- ✅ Clear, natural-sounding voice
- ✅ Proper Arabic pronunciation
- ✅ Natural English speech
- ✅ Appropriate speed and intonation

**Conversation Flow:**
- ✅ Agent greets in appropriate language
- ✅ Asks medical questions one at a time
- ✅ Understands patient responses
- ✅ Maintains conversation context
- ✅ Generates final medical summary

**Technical:**
- ✅ No error messages
- ✅ Audio plays without stuttering
- ✅ Low latency (< 2 seconds response time)
- ✅ Proper cleanup (temp files deleted)

---

## 🚀 Advanced Testing

### Discover Better Voices

Find optimal voice IDs for your use case:

```powershell
python discover_voices.py
```

This will:
- List all available Cartesia voices
- Test default voice with Arabic and English
- Save test samples

### Load Testing

Test multiple conversations:

```powershell
# Run 5 test conversations
for ($i=1; $i -le 5; $i++) {
    Write-Host "Test $i of 5"
    python voice_agent_production.py
}
```

---

## 📝 Test Checklist

Before deploying to production, verify:

- [ ] Audio samples sound natural
- [ ] Arabic pronunciation is clear
- [ ] English pronunciation is clear
- [ ] Microphone captures speech accurately
- [ ] Response time is acceptable (< 3 seconds)
- [ ] Conversation flows naturally
- [ ] Medical data is extracted correctly
- [ ] JSON files are saved properly
- [ ] No memory leaks (test multiple sessions)
- [ ] Error handling works (test with no internet)

---

## 🎬 Next Steps After Testing

1. **If tests pass:** Start using in development environment
2. **If voice quality is poor:** Run `discover_voices.py` to find better voices
3. **If latency is high:** Enable caching in `config.py`
4. **If accuracy is low:** Adjust STT settings in `config.py`

---

**Quick Test Command:**
```powershell
# Test everything in sequence
python test_audio.py; python play_samples.py
```

**Need Help?** Check:
- `CARTESIA_INTEGRATION.md` - Integration details
- `PROBLEMS_SOLVED.md` - Common issues
- `config.py` - Configuration options
