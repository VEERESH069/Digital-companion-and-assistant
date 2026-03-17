# Pre-Visit Real-Time Voice Agent

Production-ready multilingual medical pre-visit intake assistant with low-latency speech flow.

The current implementation uses:
- `OpenAI` for conversational intelligence and clinical extraction
- `Cartesia` for multilingual text-to-speech (`sonic-3`)
- `SpeechRecognition + microphone input` for speech capture
- PDF/JSON clinical summaries in `output/`

## Key Capabilities

- Real-time intake conversation in Arabic, English, and Hindi
- Cartesia voice routing by detected language (`CARTESIA_LANGUAGE_VOICES`)
- Interrupt handling while TTS is playing (`ENABLE_INTERRUPT_DETECTION`)
- Structured post-call payload and PDF generation
- Basic TTS caching and configurable conversation limits

## Project Structure

- `voice_agent_production.py`: Primary production runtime (recommended)
- `voice_agent.py`: Legacy fallback runtime (debugging/reference)
- `config.py`: Runtime configuration (Cartesia, STT behavior, LLM, output, retries)
- `discover_voices.py`: Lists and tests available Cartesia voices
- `test_audio.py`: Generates multilingual Cartesia test audio files
- `test_cartesia_simple.py`: Minimal Cartesia connectivity and synthesis test
- `test_pdf_pipeline.py`: Clinical extraction and PDF pipeline test
- `output/`: Generated JSON/PDF/audio artifacts

## Environment Setup

### 1. Prerequisites

- Python `3.9+` (3.10/3.11 recommended)
- Working microphone and speaker output
- `ffmpeg` available on `PATH` (required by Whisper)
- PortAudio support for `PyAudio`
- API keys:
	- `OPENAI_API_KEY` (required)
	- `CARTESIA_API_KEY` (required for TTS)

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

Create `.env` in the project root:

```env
OPENAI_API_KEY=your_openai_key
CARTESIA_API_KEY=your_cartesia_key
```

Optional runtime variables:

```env
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Runtime Configuration

Edit `config.py` to tune behavior. The active config keys are Cartesia/STT-based, not OpenAI-TTS keys.

Common settings:

```python
# TTS
TTS_ENGINE = "cartesia"
CARTESIA_MODEL = "sonic-3"
CARTESIA_VOICE_ARABIC = "<voice-id>"
CARTESIA_VOICE_ENGLISH = "<voice-id>"
CARTESIA_VOICE_HINDI = CARTESIA_VOICE_ENGLISH
CARTESIA_OUTPUT_FORMAT = {
		"container": "wav",
		"sample_rate": 44100,
		"encoding": "pcm_s16le",
}

# STT behavior
STT_LANGUAGES = ["ar", "en", "hi"]
STT_ENERGY_THRESHOLD = 300
STT_PAUSE_THRESHOLD = 0.6
STT_PHRASE_TIME_LIMIT = 25

# Conversation / UX
MAX_CONVERSATION_TURNS = 15
ENABLE_INTERRUPT_DETECTION = True
ADD_NATURAL_PAUSES = True

# Output
OUTPUT_DIR = "output"
SAVE_JSON = True
GENERATE_PDFS = True
```

## Run Locally (Development)

Primary entrypoint:

- Use `voice_agent_production.py` for all normal development and production testing.
- Use `voice_agent.py` only as a fallback/debug path.

Start the production voice agent:

```powershell
python voice_agent_production.py
```

Expected startup includes:
- Cartesia initialization confirmation
- Microphone calibration/listening prompt
- Interactive multilingual intake flow

End session by saying one of the exit keywords (for example: `goodbye`, `مع السلامة`, `बाय`).

## Run with Docker

The repository includes a Dockerfile for reproducible dependency setup and API-level validation.

Build:

```powershell
docker build -t previsit-voice-agent .
```

Run non-interactive tests (recommended in container):

```powershell
docker run --rm \
	--env OPENAI_API_KEY=$env:OPENAI_API_KEY \
	--env CARTESIA_API_KEY=$env:CARTESIA_API_KEY \
	-v "${PWD}:/app" \
	previsit-voice-agent python test_cartesia_simple.py
```

Notes:
- Real-time microphone capture from containers depends on host OS/audio routing and is not guaranteed.
- For full live voice interaction, local host execution is recommended.

## Run Tests

### Smoke tests

```powershell
python test_cartesia_simple.py
python test_audio.py
python test_pdf_pipeline.py
```

### Voice discovery and manual voice audition

```powershell
python discover_voices.py
```

### Full end-to-end interactive test

```powershell
python voice_agent_production.py
```

## Output Artifacts

Generated under `output/`:

- `clinical_payload_CONV-YYYY-MM-DD-XXXXXX.json`
- `doctor_briefing_CONV-YYYY-MM-DD-XXXXXX.pdf`
- `patient_copy_CONV-YYYY-MM-DD-XXXXXX.pdf`
- Test `.wav` files from TTS scripts

## Troubleshooting

`CARTESIA_API_KEY missing`
- Confirm `.env` exists in project root.
- Verify key is valid and not expired.

`OPENAI_API_KEY missing`
- Required for LLM responses and extraction pipeline.

`No module named pyaudio`
- Install system PortAudio dependencies, then reinstall `PyAudio`.

`Whisper errors / ffmpeg not found`
- Install `ffmpeg` and ensure it is available in terminal `PATH`.

`No microphone input`
- Confirm OS microphone permissions and default input device settings.

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
