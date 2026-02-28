# Production Voice Agent for Medical Pre-Visit Consultations

AI-powered voice agent for automated patient intake in Arabic, English, and Hindi.

## Features

- **High Accuracy STT** - Whisper model with noise reduction
- **Natural Voice** - OpenAI TTS (professional quality)
- **Interrupt Detection** - Agent stops when patient speaks
- **Clinical Data Extraction** - Structured JSON + PDF reports
- **Multilingual** - Arabic, English, Hindi with auto-detection

## Quick Start

```powershell
# Install
pip install -r requirements.txt

# Setup .env file
OPENAI_API_KEY=your_key_here

# Run
python voice_agent_production.py
```

## Configuration

Edit `config.py`:

```python
# STT Accuracy
STT_ENGINE = "whisper"        # High accuracy
WHISPER_MODEL = "base"        # tiny, base, small, medium
ENABLE_NOISE_REDUCTION = True

# Voice
TTS_VOICE = "nova"            # Natural female voice
TTS_SPEED = 1.0

# Features
ENABLE_INTERRUPT_DETECTION = True
ADD_NATURAL_PAUSES = True
```

## Usage

1. Run: `python voice_agent_production.py`
2. Speak clearly when prompted
3. Say "goodbye" to end consultation
4. Check `output/` for JSON and PDF files

## Files

- `voice_agent_production.py` - Main production agent
- `config.py` - Configuration settings
- `voice_agent.py` - Original version (backup)

## Requirements

- Python 3.9+
- Microphone
- OpenAI API key
- ~500MB RAM

## Troubleshooting

**STT not accurate?**
- Increase accuracy: `WHISPER_MODEL = "small"`
- Enable noise reduction: `ENABLE_NOISE_REDUCTION = True`

**Too slow?**
- Use faster model: `WHISPER_MODEL = "tiny"`
- Or: `STT_ENGINE = "google"`

## Output Structure

```
output/
├── clinical_payload_CONV-YYYY-MM-DD-XXXXXX.json
├── doctor_briefing_CONV-YYYY-MM-DD-XXXXXX.pdf
└── patient_copy_CONV-YYYY-MM-DD-XXXXXX.pdf
```

## Data Collected

- Chief complaint
- Duration
- Severity (1-10)
- Location
- Triggers
- Current medications
- Allergies
- Medical conditions

## License
## 🎯 Conversation Flow

```
GREETING → Build rapport
    ↓
DISCOVERY → Collect data naturally
    ↓
COMPLETION → Verify information
    ↓
CLOSING → Thank and confirm
```

## 🚦 Patient Routing

Automatic specialist assignment:
- **Endodontist** - Root canal, pulp issues
- **Periodontist** - Gum disease
- **Oral Surgeon** - Extractions, trauma
- **Emergency** - Severity ≥8, fever+swelling

## 🔐 Environment Variables

Create `.env` file:

```env
OPENAI_API_KEY=sk-your-key-here
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## 🧪 Testing

```powershell
# Test PDF generation
python generate_pdf_summary.py --output-dir output

# Test microphone
python tests/test_mic_live.py
```



## 👥 Authors

(Veeresh S K)EnsanAI Team

---

Proprietary - CareBot Clinic
