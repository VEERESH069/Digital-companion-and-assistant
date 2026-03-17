# Production Voice Agent - Quick Start

This guide reflects the current production implementation.

Runtime stack:
- STT: OpenAI Whisper API (`whisper-1`) with Google Speech fallback
- TTS: Cartesia (`sonic-3`) with language-based voice routing
- LLM: OpenAI chat completion (`gpt-4o-mini` by default)

## 1. Prerequisites

- Python `3.9+` (3.10 or 3.11 recommended)
- Working microphone and speaker/headset
- Internet connectivity for OpenAI and Cartesia APIs
- Valid API keys:
	- `OPENAI_API_KEY`
	- `CARTESIA_API_KEY`

## 2. Environment Setup (One Time)

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create `.env` in project root:

```env
OPENAI_API_KEY=your_openai_api_key
CARTESIA_API_KEY=your_cartesia_api_key
```

Optional:

```env
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## 3. Verify Installation

```powershell
python -c "import openai, cartesia, speech_recognition, pyaudio; print('Ready')"
```

Expected output: `Ready`

## 4. Run (Production Runtime)

```powershell
python voice_agent_production.py
```

The application prints active settings and starts the multilingual intake loop.

## 5. Configuration (Current Keys)

Edit `config.py` to tune runtime behavior.

```python
# TTS (Cartesia)
TTS_ENGINE = "cartesia"
CARTESIA_MODEL = "sonic-3"
CARTESIA_VOICE_ARABIC = "<voice-id>"
CARTESIA_VOICE_ENGLISH = "<voice-id>"
CARTESIA_VOICE_HINDI = CARTESIA_VOICE_ENGLISH

# STT behavior
STT_LANGUAGES = ["ar", "en", "hi"]
STT_ENERGY_THRESHOLD = 300
STT_DYNAMIC_ENERGY = False
STT_PAUSE_THRESHOLD = 0.6
STT_PHRASE_TIME_LIMIT = 25

# Interrupt handling
ENABLE_INTERRUPT_DETECTION = True
INTERRUPT_ENERGY_THRESHOLD = 800
INTERRUPT_WARMUP_MS = 250
INTERRUPT_CONSECUTIVE_FRAMES = 2

# LLM
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS_RESPONSE = 100

# Output
OUTPUT_DIR = "output"
SAVE_JSON = True
GENERATE_PDFS = True
```

## 6. Operational Validation

Run smoke checks before production rollout:

```powershell
python test_cartesia_simple.py
python test_audio.py
python test_pdf_pipeline.py
```

Optional voice selection workflow:

```powershell
python discover_voices.py
```

## 7. Output Artifacts

Generated in `output/`:
- `clinical_payload_CONV-YYYY-MM-DD-XXXXXX.json`
- `doctor_briefing_CONV-YYYY-MM-DD-XXXXXX.pdf`
- `patient_copy_CONV-YYYY-MM-DD-XXXXXX.pdf`

## 8. Troubleshooting

`OPENAI_API_KEY not set`
- Add `OPENAI_API_KEY` to `.env`.

`CARTESIA_API_KEY not set`
- Add `CARTESIA_API_KEY` to `.env`.

`Microphone/device errors`
- Confirm default input/output devices in OS settings.
- Close applications locking audio devices.

`Frequent false interruptions`
- Increase `INTERRUPT_ENERGY_THRESHOLD`.
- Increase `INTERRUPT_WARMUP_MS` (for speaker bleed).
- Increase `INTERRUPT_CONSECUTIVE_FRAMES`.

`High latency`
- Reduce `LLM_MAX_TOKENS_RESPONSE`.
- Keep responses short in the system prompt.
- Verify network conditions to OpenAI/Cartesia endpoints.

