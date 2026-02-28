# 🎙️ Voice AI Integration - Complete Pipeline

## Architecture Overview

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   User      │──►   │   OpenAI    │──►   │  Cartesia   │
│   Speech    │      │   GPT-4o    │      │     TTS     │
│   (Arabic/  │      │   (AI)      │      │  (Voice)    │
│   English)  │      │             │      │             │
└─────────────┘      └─────────────┘      └─────────────┘
     ▲                                            │
     │                                            │
     └────────────────────────────────────────────┘
              Voice conversation loop
```

---

## How It Works

### 1️⃣ **Speech-to-Text (STT)**
**File**: `voice_agent_production.py` - `STTEngine` class
- User speaks into microphone
- Speech Recognition converts to text
- Supports Arabic and English
- Uses Whisper (accurate) or Google STT (fast)

```python
class STTEngine:
    def listen(self) -> Tuple[Optional[str], Optional[str]]:
        # Captures audio and converts to text
```

---

### 2️⃣ **AI Processing (OpenAI)**
**File**: `voice_agent_production.py` - `LLMEngine` class
- Receives user text
- Sends to OpenAI GPT-4o mini
- Gets intelligent response
- Uses your existing OpenAI API key

```python
class LLMEngine:
    @staticmethod
    def get_response(conversation, user_message):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation.get_history(),
            temperature=0.7,
            max_tokens=100
        )
        return response.choices[0].message.content
```

---

### 3️⃣ **Text-to-Speech (Cartesia)**
**File**: `voice_agent_production.py` - `TTSEngine` class
- Receives AI response text
- Auto-detects language (Arabic/English)
- Generates natural voice with Cartesia
- Plays audio to user

```python
class TTSEngine:
    def speak_cartesia(self, text):
        # Detects language
        language = "ar" if has_arabic else "en"
        
        # Generates audio with Cartesia
        bytes_iter = cartesia_client.tts.bytes(
            model_id="sonic-3",
            transcript=text,
            language=language,
            ...
        )
```

---

## Conversation Flow

### Main Loop (`voice_agent_production.py`)

```python
while not conversation.is_complete():
    # 1. Listen to user
    user_text, lang = stt_engine.listen()
    
    # 2. Get AI response from OpenAI
    ai_response = LLMEngine.get_response(conversation, user_text)
    
    # 3. Speak response with Cartesia
    tts_engine.speak(ai_response)
```

---

## How to Run

### **Option 1: Quick Demo (3 turns)**
Test the integration quickly:
```powershell
python demo_voice_ai.py
```

**What it does:**
- 3 conversation turns
- Shows full pipeline: Speech → AI → Voice
- Perfect for testing

---

### **Option 2: Full Voice Agent (Production)**
Complete medical consultation:
```powershell
python voice_agent_production.py
```

**What it does:**
- Full conversation (up to 15 turns)
- Medical data extraction
- Generates JSON and PDF reports
- Production-ready

---

## Configuration

### API Keys (`.env` file)
```env
OPENAI_API_KEY=sk-proj-...    # ✅ Already set (for AI)
CARTESIA_API_KEY=sk_car_...   # ✅ Already set (for TTS)
```

### Settings (`config.py`)
```python
# AI (OpenAI)
LLM_MODEL = "gpt-4o-mini"           # AI model
LLM_TEMPERATURE = 0.7               # Response creativity
LLM_MAX_TOKENS_RESPONSE = 100       # Response length

# Speech Recognition (STT)
STT_ENGINE = "whisper"              # "whisper" or "google"
WHISPER_MODEL = "base"              # Model size
STT_LANGUAGES = ["ar", "en"]        # Supported languages

# Text-to-Speech (Cartesia)
TTS_ENGINE = "cartesia"             # Using Cartesia
CARTESIA_MODEL = "sonic-3"          # Latest model
CARTESIA_VOICE_ARABIC = "6ccb..."   # Arabic voice ID
CARTESIA_VOICE_ENGLISH = "6ccb..."  # English voice ID

# Conversation
MAX_CONVERSATION_TURNS = 15         # Max turns before ending
ENABLE_INTERRUPT_DETECTION = True   # User can interrupt
ADD_NATURAL_PAUSES = True          # Human-like pauses
```

---

## Integration Points

### 1. **Conversation Manager**
Manages conversation state and history:
```python
class ConversationManager:
    def __init__(self):
        self.history = [
            {"role": "system", "content": "You are Mariam..."}
        ]
    
    def add_user_message(self, message):
        self.history.append({"role": "user", "content": message})
    
    def add_assistant_message(self, message):
        self.history.append({"role": "assistant", "content": message})
```

### 2. **System Prompt**
Defines Mariam's behavior:
```python
{
    "role": "system",
    "content": """أنت مريم، موظفة استقبال ودودة.
    You are Mariam, a friendly receptionist.
    
    Guidelines:
    - Keep responses SHORT (1-2 sentences)
    - Respond in SAME language as user
    - Show empathy and understanding
    """
}
```

### 3. **Language Auto-Detection**
Automatically detects and responds in correct language:
```python
# Detect Arabic
has_arabic = bool(re.search('[\u0600-\u06FF]', text))
language = "ar" if has_arabic else "en"

# Use appropriate voice and language settings
```

---

## Testing the Integration

### ✅ Test 1: Quick Demo (Recommended)
```powershell
python demo_voice_ai.py
```
- 3 conversation turns
- Shows complete pipeline
- Good for testing

### ✅ Test 2: Audio Only (No AI)
```powershell
python test_audio.py
```
- Tests Cartesia TTS only
- No microphone needed
- Verifies voice quality

### ✅ Test 3: Full Agent
```powershell
python voice_agent_production.py
```
- Complete medical consultation
- All features enabled
- Production mode

---

## Troubleshooting

### Issue: No audio input detected
**Solution:**
- Check microphone permissions in Windows
- Verify microphone is set as default
- Test: `python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"`

### Issue: AI responses are slow
**Solution:**
- Reduce `LLM_MAX_TOKENS_RESPONSE` in config
- Use faster model (already using gpt-4o-mini)
- Check internet connection

### Issue: Voice sounds unnatural
**Solution:**
- Try different voice IDs: `python discover_voices.py`
- Adjust sample rate in config
- Test different voices for Arabic vs English

### Issue: Language detection wrong
**Solution:**
- System auto-detects based on Arabic Unicode characters
- Arabic: [\u0600-\u06FF]
- Speak clearly in one language at a time

---

## API Usage & Costs

### OpenAI (GPT-4o mini)
- **Cost**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **Per conversation**: ~$0.01 - $0.03
- **Usage**: Conversation responses + data extraction

### Cartesia TTS
- **Cost**: Pay per character
- **Per conversation**: Varies by length
- **Usage**: Voice generation (Arabic & English)

### Speech Recognition
- **Google STT**: Free (limited)
- **Whisper**: Free (local processing, uses more CPU)

---

## Key Files

| File | Purpose |
|------|---------|
| `voice_agent_production.py` | ⭐ Main voice agent with full integration |
| `demo_voice_ai.py` | Quick demo (3 turns) |
| `config.py` | Configuration settings |
| `.env` | API keys |
| `test_audio.py` | Test Cartesia TTS only |

---

## Next Steps

1. **Test the demo:**
   ```powershell
   python demo_voice_ai.py
   ```

2. **Run full agent:**
   ```powershell
   python voice_agent_production.py
   ```

3. **Customize voice:**
   - Run `python discover_voices.py` to find better voices
   - Update voice IDs in `config.py`

4. **Adjust AI behavior:**
   - Edit system prompt in `voice_agent_production.py`
   - Tune temperature and max_tokens in `config.py`

---

**🎉 Your voice AI is ready!**

The integration is complete:
- ✅ Speech Recognition (Whisper/Google)
- ✅ AI Processing (OpenAI GPT-4o mini)
- ✅ Voice Synthesis (Cartesia TTS)
- ✅ Natural bilingual conversations (Arabic + English)

Just run `python demo_voice_ai.py` to see it in action!
