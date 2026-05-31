# Pre-Visit Real-Time Voice Agent
python voice_agent_production.py
\

![Python](https://img.shields.io/badge/Python-3.9+-3776ab?style=flat-square) ![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square) ![Status](https://img.shields.io/badge/Status-Production--Ready-green?style=flat-square)

> Production-grade multilingual medical pre-visit intake assistant with real-time speech interaction, clinical data extraction, and low-latency conversation flows.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Output Artifacts](#output-artifacts)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Support](#support)

---

## 🎯 Overview

This voice agent conducts real-time intake conversations with patients in multiple languages (Arabic, English, Hindi) and generates structured clinical summaries. It uses OpenAI's language intelligence with Cartesia's natural multilingual TTS, supports patient interruptions, and produces both JSON payloads and PDF briefings suitable for clinical workflows.

**Tech Stack:**
- **LLM:** OpenAI GPT-4o-mini for conversational intelligence and clinical data extraction
- **TTS:** Cartesia sonic-3 with native multilingual voices and language detection
- **STT:** OpenAI Whisper API (primary) with Google Speech Recognition fallback
- **Audio:** PyAudio for low-latency PCM streaming (22050 Hz, 16-bit mono)

## ✨ Features

### Core Capabilities
- **Multilingual Support:** Arabic, English, Hindi with automatic language detection
- **Real-Time Interruption:** Patient can interrupt agent speech with built-in vocal interrupt detection
- **Natural Speech Flow:** Configurable pauses after sentences and questions for human-like conversation
- **Clinical Data Extraction:** Structured clinical payload generation from conversation
- **Dual Output Format:** JSON payload + PDF briefing (doctor + patient copies)
- **Low Latency:** 3-thread LLM→TTS→playback pipeline with zero playback gaps

### Production Features
- **Configurable Behavior:** All tuning via `config.py` without code changes
- **Graceful Fallbacks:** If interrupt detection unavailable, conversation continues safely
- **Automatic Retries:** Built-in retry logic for STT, TTS, and LLM failures
- **Extensible LLM:** Easy switch to Anthropic Claude for compatible use cases
- **Docker Support:** Reproducible containerized environment for deployment

### Developer Experience
- **Comprehensive Tests:** Smoke tests for all components, end-to-end integration tests
- **Voice Discovery Tool:** List and audition all available Cartesia voices
- **Debug Mode:** Legacy `voice_agent.py` fallback for troubleshooting
- **Clear Logging:** Verbose output for monitoring conversation flow

---

## 🔧 System Requirements

### Hardware
- **Microphone:** Working audio input device with OS permission
- **Speaker:** Audio output for TTS playback
- **Network:** Stable internet connection (required for OpenAI and Cartesia APIs)

### Software
| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.9 - 3.11 | 3.10/3.11 recommended for best compatibility |
| ffmpeg | Latest | Required by Whisper for audio encoding |
| PortAudio | Linux: libportaudio2/portaudio19-dev | Compiled into Docker image |
| PyAudio | 0.2.11+ | Auto-installed via requirements.txt |

### API Keys (Required)
| Service | Purpose | Get It |
|---------|---------|--------|
| `OPENAI_API_KEY` | GPT-4o-mini LLM + Whisper STT | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `CARTESIA_API_KEY` | sonic-3 TTS | [Cartesia Console](https://console.cartesia.ai/) |

### Optional
- `ANTHROPIC_API_KEY`: For fallback LLM (not configured by default)

---

## 📥 Installation & Environment Setup

### Prerequisites Verification

Before installation, verify your system has all dependencies:

**Windows PowerShell:**
```powershell
# Check Python version
python --version

# Verify pip is available
pip --version

# Check for ffmpeg
ffmpeg -version | Select-Object -First 1

# Check microphone/audio devices
Get-PnpDevice -Class AudioEndpoint | Select-Object Name, Status
```

**macOS/Linux:**
```bash
# Check Python version
python3 --version

# Verify pip is available
pip3 --version

# Check for ffmpeg
ffmpeg -version | head -1

# List audio devices
# macOS:
system_profiler SPAudioDataType

# Linux:
pactl list short devices
```

**Missing Components?** 
- **Python 3.9+:** Download from [python.org](https://www.python.org/downloads/)
- **ffmpeg:** [ffmpeg.org](https://ffmpeg.org/download.html)
- **PortAudio (Linux):** `sudo apt-get install libportaudio2 portaudio19-dev`
- **PortAudio (macOS):** `brew install portaudio`

---

### Option 1: Local Development Setup (Recommended)

#### Step 1: Clone Repository
```bash
cd Pre-Visit-real-time-voice-agent
```

#### Step 2: Create Python Virtual Environment

**Windows PowerShell:**
```powershell
# Create virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Upgrade pip and setuptools
python -m pip install --upgrade pip setuptools wheel
```

**macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Upgrade pip and setuptools
python -m pip install --upgrade pip setuptools wheel
```

**Verify Virtual Environment:**
```powershell
# Python path should point to .venv
python -c "import sys; print(sys.prefix)"
```

#### Step 3: Install Python Dependencies

```powershell
pip install -r requirements.txt
```

**Expected Installation Output:**
```
Successfully installed cartesia-1.0.0
Successfully installed openai-1.12.0
Successfully installed SpeechRecognition-3.10.0
Successfully installed PyAudio-0.2.11
... (additional packages)
Successfully installed <N> packages
```

> **Note:** PyAudio installation may require compilation. If it fails, install PortAudio dev headers first (see Prerequisites).

#### Step 4: Non-Production Dependencies (Optional)

For development and testing:
```powershell
# Install dev/testing dependencies
pip install pytest pytest-cov black flake8 mypy
```

#### Step 5: Configure Environment Variables

**Copy template to working .env file:**
```powershell
# Windows
copy .env.example .env

# Linux/macOS
cp .env.example .env
```

**Edit `.env` with your credentials:**
```env
# REQUIRED: OpenAI API Key
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# REQUIRED: Cartesia API Key
CARTESIA_API_KEY=your-actual-cartesia-api-key-here

# OPTIONAL: Application Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
VERBOSE_LOGGING=True
```

**Verify .env is in .gitignore:**
```bash
cat .gitignore | grep ".env"
# Output should include: .env
```

#### Step 6: Verify Installation

Run the comprehensive installation test:
```powershell
python tests/test_installation.py
```

**Expected Output:**
```
✓ Python version: 3.10.x
✓ Virtual environment: Active
✓ Dependencies installed: 22/22
✓ OpenAI API: Connected
✓ Cartesia API: Connected
✓ Microphone access: Available
✓ Speaker output: Available

Installation Status: READY ✓
```

---

### Option 2: Docker Setup (Containerized)

#### Prerequisites
- Docker Desktop installed ([download](https://www.docker.com/products/docker-desktop))
- Docker daemon running
- 2GB+ available disk space

#### Build Docker Image

**Build from Dockerfile:**
```bash
docker build -t previsit-voice-agent:latest .
```

**Verify build success:**
```bash
docker image ls | grep previsit-voice-agent
# Output: previsit-voice-agent  latest  <image-id>  <size>
```

#### Run Container: Smoke Test (No Microphone Needed)

Best for API validation in CI/CD or cloud environments:

```bash
docker run --rm \
  --env OPENAI_API_KEY=$OPENAI_API_KEY \
  --env CARTESIA_API_KEY=$CARTESIA_API_KEY \
  -v "${PWD}/output:/app/output" \
  previsit-voice-agent:latest \
  python test_cartesia_simple.py
```

**Expected Output:**
```
Cartesia API: CONNECTED ✓
Model: sonic-3
Voice ID: 6ccbfb76-1fc6-48f7-b71d-91ac6298247b
Synthesis: SUCCESS
Output: output/generated_audio.wav
```

#### Run Container: Interactive Mode (Linux Only)

For live microphone interaction on Linux:

```bash
docker run -it --rm \
  --env OPENAI_API_KEY=$OPENAI_API_KEY \
  --env CARTESIA_API_KEY=$CARTESIA_API_KEY \
  --device /dev/snd \
  -v "${PWD}/output:/app/output" \
  previsit-voice-agent:latest \
  python voice_agent_production.py
```

#### Run Container: Test Suite

```bash
docker run --rm \
  --env OPENAI_API_KEY=$OPENAI_API_KEY \
  --env CARTESIA_API_KEY=$CARTESIA_API_KEY \
  -v "${PWD}/output:/app/output" \
  previsit-voice-agent:latest \
  python -m pytest tests/ -v
```

#### Troubleshooting Docker

| Issue | Cause | Solution |
|-------|-------|----------|
| `docker: command not found` | Docker not installed | Install [Docker Desktop](https://www.docker.com/products/docker-desktop) |
| `Cannot connect to Docker daemon` | Docker not running | Start Docker Desktop or `sudo systemctl start docker` |
| `pull access denied` | Image not found | Run `docker build` first; verify tag with `docker image ls` |
| `no audio in container` | Audio device not mounted | Add `--device /dev/snd` on Linux; use local mode on macOS/Windows |

---

### Quick Environment Health Check

**One-liner to verify everything is ready:**

```powershell
python -c "
import sys
import openai
import cartesia
import pyaudio
import speech_recognition as sr

print('✓ Python:', sys.version.split()[0])
print('✓ OpenAI:', openai.__version__)
print('✓ Cartesia: Available')
print('✓ PyAudio: Available')
print('✓ SpeechRecognition: Available')
print('\n🎉 Environment ready for voice agent!')
"
```

Expected output:
```
✓ Python: 3.10.x
✓ OpenAI: 1.12.0
✓ Cartesia: Available
✓ PyAudio: Available
✓ SpeechRecognition: Available

🎉 Environment ready for voice agent!
```

---

## ⚙️ Configuration

All runtime behavior is controlled via `config.py`. Below are commonly tuned settings:

### Text-to-Speech (Cartesia)
```python
# Model and voice selection
TTS_ENGINE = "cartesia"
CARTESIA_MODEL = "sonic-3"
CARTESIA_VOICE_ARABIC = "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"
CARTESIA_VOICE_ENGLISH = "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"
CARTESIA_VOICE_HINDI = "95d51f79-c397-46f9-b49a-23763d3eaa2d"  # Dedicated Hindi voice

# Audio format (22050 Hz is optimal for fast synthesis)
CARTESIA_OUTPUT_FORMAT = {
  "container": "wav",
  "sample_rate": 44100,
  "encoding": "pcm_s16le",
}
```
#### Environment Variables (Required in .env)

| Variable             | Purpose                                 | Example/Notes                                 |
|----------------------|-----------------------------------------|-----------------------------------------------|
| OPENAI_API_KEY       | OpenAI LLM + Whisper STT                | sk-... (get from OpenAI platform)             |
| CARTESIA_API_KEY     | Cartesia TTS                            | sk_car_... (get from Cartesia Console)        |
| ANTHROPIC_API_KEY    | (Optional) Claude fallback LLM          | sk-ant-...                                    |
| ENVIRONMENT          | App mode (development/production)       | development                                   |
| LOG_LEVEL            | Logging verbosity                       | INFO, DEBUG                                   |
| DATA_DIR             | Data storage directory                  | ./data                                        |
| LOGS_DIR             | Log file directory                      | ./logs                                        |

See `.env.example` for a full template and required fields.

### Speech-to-Text (Whisper)
```python
# Supported languages
STT_LANGUAGES = ["ar", "en", "hi"]

# Silence detection
STT_ENERGY_THRESHOLD = 300        # Lower = more sensitive; higher = less sensitive
STT_PAUSE_THRESHOLD = 0.6         # Seconds of silence = end of speech
STT_PHRASE_TIME_LIMIT = 25        # Max seconds per phrase

# Automatic retries
MAX_RETRIES_STT = 2
```

### Interrupt Detection
```python
ENABLE_INTERRUPT_DETECTION = True
INTERRUPT_ENERGY_THRESHOLD = 800   # RMS level to trigger interrupt
INTERRUPT_WARMUP_MS = 250          # Ignore speaker bleed first 250ms
INTERRUPT_CONSECUTIVE_FRAMES = 2   # Require 2 frames above threshold
```

### Conversation & Output
```python
MAX_CONVERSATION_TURNS = 15   # Session length limit
ADD_NATURAL_PAUSES = True     # Human-like speech pauses
PAUSE_AFTER_SENTENCE = 0.3    # Seconds after sentence
PAUSE_AFTER_QUESTION = 0.5    # Seconds after question

OUTPUT_DIR = "output"
SAVE_JSON = True
GENERATE_PDFS = True
```

### LLM Behavior
```python
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.7              # 0.7 = balanced, 0.0 = deterministic
LLM_MAX_TOKENS_RESPONSE = 100      # Per conversational response
LLM_MAX_TOKENS_EXTRACTION = 800    # For clinical data extraction
```

**Find all config keys** in [config.py](config.py).

---

## 🚀 Usage & Running the Agent

### Local Development Workflow

#### Development Mode (Debug Enabled)

Run with verbose logging for development:

```powershell
# Ensure virtual environment is active
.\.venv\Scripts\Activate.ps1

# Run with debug output
python voice_agent_production.py --debug
```

**Edit config.py for development:**
```python
ENVIRONMENT = "development"
LOG_LEVEL = "DEBUG"
VERBOSE_LOGGING = True
MAX_CONVERSATION_TURNS = 5  # Limit turns for quick testing
PAUSE_AFTER_SENTENCE = 0.1  # Minimal pauses for faster iteration
```

#### Production Mode (Optimized)

Run with normal logging:

```powershell
python voice_agent_production.py
```

**Recommended production settings in config.py:**
```python
ENVIRONMENT = "production"
LOG_LEVEL = "INFO"
VERBOSE_LOGGING = False
MAX_CONVERSATION_TURNS = 15
ENABLE_INTERRUPT_DETECTION = True
```

#### Headless Mode (CI/CD)

Run without interactive prompts:

```powershell
python voice_agent_production.py --headless --input "patient input file.txt"
```

#### Expected Startup Output

```
[2026-03-17 10:30:00] Initializing Pre-Visit Voice Agent...
[2026-03-17 10:30:00] ✓ OpenAI API: Connected
[2026-03-17 10:30:01] ✓ Cartesia API: Connected
[2026-03-17 10:30:02] ✓ Microphone: Active (default device)
[2026-03-17 10:30:02] ✓ Speaker: Ready
[2026-03-17 10:30:02] Ready for conversation. Say 'goodbye' to exit.
```

#### Example Interactive Session

```
Agent: Hello! I'm here to help prepare you for your appointment.
       Can you tell me about any concerns or symptoms?

You:   I have a sharp pain in my left molar.

Agent: I understand. How long have you had this pain?

You:   About one week.

Agent: Has the pain been constant or does it come and go?

You:   Mostly when I chew food.

Agent: Thank you for that information. I'm preparing your summary...
       [Processing...]

[Session Complete]
- Conversation ID: CONV-2026-03-17-A1B2C3
- Duration: 45 seconds
- Turns: 6
- Language: English
- Output: Generated to /output/

Generated Files:
✓ clinical_payload_CONV-2026-03-17-A1B2C3.json
✓ doctor_briefing_CONV-2026-03-17-A1B2C3.pdf
✓ patient_copy_CONV-2026-03-17-A1B2C3.pdf
```

#### Exit Options

Trigger session end by saying any of these exit keywords:
- **English:** `goodbye`, `bye`, `exit`, `stop`, `end`, `quit`
- **Arabic:** `مع السلامة`, `وداعا`, `خلاص`, `باي`
- **Hindi:** `धन्यवाद`, `बाय`, `अलविदा`

---

## 🧪 Testing

### Test Strategy Overview

```
Unit Tests              Smoke Tests            Integration Tests       E2E Tests
(Individual)           (Component Health)     (Feature Flow)         (Full Session)
                                              ↓                       ↓
tests/test_installation.py → tests/test_cartesia_*.py → tests/test_pdf_pipeline.py → voice_agent_production.py
                               tests/test_audio.py      tests/test_mic_live.py
```

### Step 1: Pre-Flight Checks (Run First)

#### Installation Health Check

```powershell
python tests/test_installation.py
```

**What it validates:**
- ✓ Python version and environment
- ✓ Required packages installed and importable
- ✓ API keys configured in `.env`
- ✓ File permissions and directory structure
- ✓ System audio device availability

**Expected Output (Success):**
```
PRE-FLIGHT CHECKS
=================
[✓] Python version: 3.10.8
[✓] Virtual environment: Active at .venv
[✓] Dependencies: 22/22 installed
[✓] OPENAI_API_KEY: Configured
[✓] CARTESIA_API_KEY: Configured
[✓] Microphone: Accessible (Built-in Microphone)
[✓] Speaker: Accessible (Built-in Audio)
[✓] Output directory: ./output/ (writable)
[✓] .env file: Present and valid

STATUS: ✅ READY FOR TESTING
```

**Troubleshooting:**
```
[✗] OPENAI_API_KEY: Missing
    → Review .env file; ensure key is set without quotes

[✗] Microphone: Not found
    → Check OS audio settings; run test as admin if needed

[✗] Dependencies: 22/22 installed → MISSING: PyAudio
    → Run: pip install PyAudio (may require PortAudio dev headers)
```

---

### Step 2: Component Smoke Tests

Test each system component independently:

#### 2a. Cartesia TTS Connectivity

```powershell
python test_cartesia_simple.py
```

**Purpose:** Verify TTS API connectivity and voice synthesis

**Expected Output:**
```
Testing Cartesia Integration
=============================
Model: sonic-3
Voice: 6ccbfb76-1fc6-48f7-b71d-91ac6298247b
Text: "Hello, I am ready to conduct your pre-visit intake."

[Calling Cartesia API...]
✓ Synthesis successful (3.2 seconds)
✓ Audio quality: 44100 Hz, 16-bit mono
✓ Duration: 5.2 seconds
✓ Output: ./output/generated_audio.wav

STATUS: ✅ CARTESIA OK
```

**If it fails:**
- Check API key validity in Cartesia Console
- Verify network connectivity
- Check for API rate limiting

#### 2b. Multilingual Audio Generation

```powershell
python tests/test_audio.py
```

**Purpose:** Test TTS across all supported languages

**Expected Output:**
```
Testing Multilingual Audio Generation
=====================================
[1/3] Arabic: ✓ (4.1 sec)
      File: output/audio_ar_greeting.wav
      
[2/3] English: ✓ (3.8 sec)
      File: output/audio_en_greeting.wav
      
[3/3] Hindi: ✓ (5.2 sec)
      File: output/audio_hi_greeting.wav

STATUS: ✅ ALL LANGUAGES OK
```

**Verify audio files:**
```powershell
ls output/*.wav -Name
# audio_ar_greeting.wav
# audio_en_greeting.wav
# audio_hi_greeting.wav
```

#### 2c. Clinical Extraction & PDF Generation

```powershell
python tests/test_pdf_pipeline.py
```

**Purpose:** Test clinical data extraction and PDF generation

**Expected Output:**
```
Testing Clinical PDF Pipeline
=============================
[1/2] Extracting clinical data from sample conversation...
      ✓ Chief Complaint: "Sharp pain in left molar"
      ✓ Duration: "1 week"
      ✓ Severity: "7/10"
      ✓ Specialist: "Dentist"

[2/2] Generating PDF briefings...
      ✓ doctor_briefing_SAMPLE.pdf (410 KB)
      ✓ patient_copy_SAMPLE.pdf (380 KB)

STATUS: ✅ PDF GENERATION OK
```

**Verify PDF files exist:**
```powershell
ls output/*.pdf -Name
# doctor_briefing_SAMPLE.pdf
# patient_copy_SAMPLE.pdf
```

---

### Step 3: Integration Tests

#### 3a. Real-Time Microphone Live Test

```powershell
python tests/test_mic_live.py
```

**What to do:**
1. Speak into your microphone when prompted
2. Say: "Test audio from microphone"
3. Wait for transcription verification

**Expected Output:**
```
Live Microphone Integration Test
================================
Microphone: Built-in Audio
Sample Rate: 44100 Hz
Format: 16-bit PCM
Duration: 5 seconds

[Recording...] "Please speak now..."
You: "Test audio from microphone"

[Whisper API Processing...]
Transcribed: "Test audio from microphone"
Confidence: 0.98

STATUS: ✅ MICROPHONE & STT OK
```

#### 3b. Quick End-to-End Test

```powershell
python tests/quick_test.py
```

**What it does:**
- Calls Whisper API (STT)
- Calls OpenAI API (LLM)
- Calls Cartesia API (TTS)
- All in 30 seconds

**Expected Output:**
```
Quick E2E Test (30 seconds)
==========================
[1/3] Whisper STT: ✓ (1.2 sec)
      Sample: "How can I help?"
      
[2/3] OpenAI LLM: ✓ (1.5 sec)
      Response length: 47 tokens
      
[3/3] Cartesia TTS: ✓ (2.1 sec)
      Audio: 4.8 seconds
      
STATUS: ✅ ALL APIS RESPONDING
Estimated Latency: 4.8 seconds per turn
```

---

### Step 4: Full Interactive Test (Master Test)

Run the complete agent with manual interaction:

```powershell
python voice_agent_production.py
```

**Test Scenarios:**

| Scenario | Test Steps | Expected Result |
|----------|-----------|-----------------|
| **Happy Path** | Speak naturally through 3-5 turns then say "goodbye" | Complete session w/ all artifacts generated |
| **Language Switch** | Start in English, respond in Arabic on 3rd turn | Agent detects Arabic, routes to Arabic voice |
| **Interrupt Test** | Let agent speak then interrupt with your voice | Agent stops mid-sentence, accepts new input |
| **Long Pause** | Say something, stay silent for 3+ seconds | Agent recognizes end-of-speech, generates response |
| **Quick Exit** | Say "goodbye" on first turn | Session ends, minimal artifacts |
| **Error Recovery** | Whisper timeout then try again | Agent retries, or falls back to Google STT |

---

### Step 5: Continuous Integration / Automated Testing

#### Run All Tests in Sequence

```powershell
# Clean up previous test outputs
rm output/*.wav, output/*.pdf -Force

# Run test suite
python -m pytest tests/ -v --tb=short
```

**Expected Output:**
```
tests/test_installation.py::test_python_version PASSED        [12%]
tests/test_installation.py::test_dependencies PASSED          [25%]
tests/test_installation.py::test_api_keys PASSED              [37%]
tests/test_cartesia_simple.py::test_synthesis PASSED          [50%]
tests/test_audio.py::test_multilingual_audio PASSED           [62%]
tests/test_pdf_pipeline.py::test_pdf_generation PASSED        [75%]
tests/test_mic_live.py::test_microphone_input PASSED          [87%]
tests/quick_test.py::test_system_latency PASSED               [100%]

====== 8 passed in 23.4s ======
```

#### Docker-Based Testing

Run all tests in isolated container:

```bash
docker run --rm \
  --env OPENAI_API_KEY=$OPENAI_API_KEY \
  --env CARTESIA_API_KEY=$CARTESIA_API_KEY \
  -v "${PWD}/output:/app/output" \
  previsit-voice-agent:latest \
  python -m pytest tests/ -v --junit-xml=output/test-results.xml
```

This generates an XML report for CI/CD integration.

---

### Test Maintenance Checklist

After each deployment, verify:

- [ ] `tests/test_installation.py` passes
- [ ] `tests/test_cartesia_simple.py` generates valid audio
- [ ] `tests/test_audio.py` supports all 3 languages
- [ ] `tests/test_pdf_pipeline.py` produces readable PDFs
- [ ] `tests/test_mic_live.py` captures and transcribes correctly
- [ ] Full session via `voice_agent_production.py` completes without errors
- [ ] All output artifacts appear in `output/` directory
- [ ] No API errors or rate-limit warnings in logs

---

### Performance Baselines (Reference)

Expected performance on typical hardware:

| Metric | Target | Tolerance |
|--------|--------|-----------|
| STT Latency | 2-3s | <5s |
| LLM Response | 1-2s | <4s |
| TTS Synthesis | 2-4s | <6s |
| Full Turn (STT→LLM→TTS) | 5-9s | <15s |
| Session Startup | 2-3s | <5s |
| Interrupt Response | <500ms | <1s |

---

### Debugging Test Failures

If tests fail, check in order:

1. **API Keys:** `echo $OPENAI_API_KEY` / `echo $CARTESIA_API_KEY`
2. **Network:** `ping api.openai.com` / `ping api.cartesia.ai`
3. **Dependencies:** `pip list | grep -E "(openai|cartesia|pyaudio)"`
4. **Audio:** `python tests/test_mic_live.py`
5. **Logs:** Check `/output/*.log` for error traces
6. **Config:** Verify settings in `config.py` match your environment

---

## 🏗️ Architecture

#### High-Level Architecture

The system is modular, with each major function (STT, LLM, TTS, PDF generation) separated for maintainability and scalability. The primary entry point is `voice_agent_production.py`, which orchestrates the conversation pipeline. All configuration is centralized in `config.py` and environment variables.

For production deployments or scaling, consider moving core logic into a package directory (e.g., `previsit_agent/`) and keeping only entry points and config files at the root.

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Voice Agent Pipeline                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Microphone] → [STT: Whisper] → [LLM: GPT-4o-mini]       │
│                                        ↓                    │
│                              [TTS: Cartesia sonic-3]        │
│                                        ↓                    │
│                       [PyAudio PCM Stream] → [Speaker]     │
│                                                              │
│  ▲─────────────────────────────────────────────────────────┤
│  │ Interrupt Detection (Optional) – Monitors for patient   │
│  │ voice during TTS playback; cancels speech if detected   │
│  └─────────────────────────────────────────────────────────┘
│                                                              │
│  [Conversation Manager]                                    │
│  - Tracks turn history                                     │
│  - Audits generated vs. played text                        │
│  - Detects early exit/interruption                         │
│  - Generates clinical payload                             │
│  - Outputs PDF + JSON artifacts                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Key Classes

| Module | Class | Purpose |
|--------|-------|---------|
| `voice_agent_production.py` | `ConversationManager` | Track history, manage turns, generate payloads |
| `voice_agent_production.py` | `STTEngine` | Whisper API + fallback speech recognition |
| `voice_agent_production.py` | `LLMEngine` | OpenAI streaming chat + interrupt cancellation |
| `voice_agent_production.py` | `TTSEngine` | Cartesia synthesis with PCM caching + safe cleanup |
| `config.py` | Various functions | Language detection, voice routing, config helpers |
| `generate_pdf_summary.py` | `PDFSummaryGenerator` | Extract and format clinical payload as PDF |

### Thread Model
- **Main Thread:** Coordinator and REPL
- **LLM Thread:** Streams response tokens
- **TTS Thread:** Synthesizes and caches audio chunks
- **Playback Thread:** Continuous PCM streaming to speaker

### Interrupt Safety
- Uses `threading.Event()` for signal-safe cross-thread communication
- Prevents global state races; cancels workers if patient interrupts
- Tracks `generated_text` vs. `played_text` to avoid history bloat

---

## 📊 Output Artifacts

Generated under `output/` after each session:

### JSON Payload
**File:** `clinical_payload_CONV-YYYY-MM-DD-XXXXXX.json`
```json
{
  "conversation_id": "CONV-2026-03-17-A1B2C3",
  "timestamp": "2026-03-17T10:30:00Z",
  "language": "en",
  "turns": [
    {
      "role": "patient",
      "text": "I have a sharp pain in my left molar.",
      "timestamp": "2026-03-17T10:30:05Z"
    },
    {
      "role": "agent",
      "text": "I understand. Has this been happening for days or weeks?",
      "timestamp": "2026-03-17T10:30:08Z"
    }
  ],
  "extracted_data": {
    "chief_complaint": "Sharp pain in left molar",
    "duration": "1 week",
    "severity": "moderate",
    "specialist_recommendation": "Dentist"
  }
}
```

### PDF Briefing (Doctor Copy)
**File:** `doctor_briefing_CONV-YYYY-MM-DD-XXXXXX.pdf`
- Structured chief complaint extract
- Symptom timeline and severity
- Specialist routing recommendation
- Full conversation transcript

### PDF Briefing (Patient Copy)
**File:** `patient_copy_CONV-YYYY-MM-DD-XXXXXX.pdf`
- Patient-friendly summary of visit
- Recommendations and next steps
- Appointment confirmation details

---

## 🐛 Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `OPENAI_API_KEY missing` | `.env` not found or key not set | Run `cp .env.example .env` and edit with your key. Verify file exists in project root. |
| `CARTESIA_API_KEY missing` | Invalid or expired key | Verify in [Cartesia Console](https://console.cartesia.ai/). Create new key if expired. |
| `No module named 'pyaudio'` | PortAudio not installed on system | **Windows:** Download installer; **Linux:** `apt-get install portaudio19-dev`; **macOS:** `brew install portaudio` |
| `ffmpeg not found` | Whisper can't encode audio | Install ffmpeg and add to PATH. Verify with `ffmpeg -version` |
| `No microphone input` | Microphone permission denied or not default device | Check OS audio settings; ensure app has mic permission. Select default input device in OS. |
| `Interrupt triggers immediately` | Speaker bleed at playback start | Increase `INTERRUPT_WARMUP_MS` in config.py (e.g., 350ms). |
| `Interrupt never triggers` | Microphone capturing voice weakly | Increase `STT_ENERGY_THRESHOLD` in config.py; test with `python tests/test_mic_live.py`. |
| `Audio stutters / playback gaps` | System I/O overhead or sample rate mismatch | Reduce `MAX_CONVERSATION_TURNS` or close other apps. Verify sample rate in `CARTESIA_OUTPUT_FORMAT`. |
| `Whisper times out` | Network latency or API overload | Retry with shorter audio; reduce `STT_PHRASE_TIME_LIMIT`. Check OpenAI status page. |

### Debug Mode

Enable verbose logging for detailed execution trace:
```env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
VERBOSE_LOGGING=True
```

Use legacy agent for simpler debugging:
```powershell
python voice_agent.py
```

### Check Installation Health
```powershell
python tests/test_installation.py
```

---

## 🛠️ Development

### Project Structure
```
.
├── README.md                        # This file
├── requirements.txt                 # Python dependencies
├── config.py                        # Runtime configuration (edit for tuning)
├── .env.example                     # Environment template (copy to .env)
├── Dockerfile                       # Container build recipe
│
├── voice_agent_production.py        # ⭐ Primary runtime (use this)
├── voice_agent.py                   # Legacy fallback (debugging)
├── generate_pdf_summary.py          # Clinical payload → PDF
│
├── discover_voices.py               # List/preview Cartesia voices
├── tests/test_cartesia_simple.py    # 1-line TTS test
├── tests/test_audio.py              # Multilingual audio generation
├── tests/test_pdf_pipeline.py       # Clinical extraction test
│
├── tests/                           # Integration tests
│   ├── test_installation.py
│   ├── test_mic_live.py
│   ├── test_realtime.py
│   └── quick_test.py
│
├── docs/                            # Extended documentation
│   ├── QUICK_START_PRODUCTION.md    # Professional ops guide
│   ├── CARTESIA_INTEGRATION.md      # TTS deep dive
│   ├── TESTING_GUIDE.md             # Detailed test procedures
│   ├── VOICE_AI_INTEGRATION.md      # Architecture notes
│   └── PROBLEMS_SOLVED.md           # Known issues + fixes
│
├── output/                          # Generated artifacts (JSON/PDF)
├── voice_samples/                   # Optional voice cloning samples
└── venv/                            # Virtual environment (gitignored)
```

### Adding Features

1. **New LLM Provider:** Update `config.py` and `voice_agent_production.py`'s `LLMEngine`
2. **New Language:** Add voice ID to `CARTESIA_LANGUAGE_VOICES` in `config.py`
3. **Custom STT:** Replace `STTEngine.transcribe()` in `voice_agent_production.py`
4. **Custom PDF Layout:** Modify `generate_pdf_summary.py` logic

### Code Style
- Python 3.9+ syntax
- Type hints recommended for clarity
- Docstrings for public methods
- Exception handling with specific catches (not bare `except`)

### Testing Checklist Before Production
- [ ] `python tests/test_cartesia_simple.py` passes
- [ ] `python tests/test_audio.py` produces audio files
- [ ] `python tests/test_pdf_pipeline.py` generates PDFs without errors
- [ ] `python tests/test_installation.py` all checks pass
- [ ] Manual session: `python voice_agent_production.py` with full conversation

---

## 🤝 Support

### Documentation
- **Quick Start:** See [docs/QUICK_START_PRODUCTION.md](docs/QUICK_START_PRODUCTION.md) for ops-focused guide
- **Testing:** See [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md) for smoke test commands
- **Architecture:** See [docs/VOICE_AI_INTEGRATION.md](docs/VOICE_AI_INTEGRATION.md) for design details
- **Problem Solving:** See [docs/PROBLEMS_SOLVED.md](docs/PROBLEMS_SOLVED.md) for known issues

### Reporting Issues
When reporting bugs, include:
1. Python version: `python --version`
2. Error message and full traceback
3. Steps to reproduce
4. System details (OS, audio device)
5. Output of `python test_installation.py`

### Feature Requests
Submit feature requests with:
- Use case description
- Current workaround (if any)
- Priority level

---

## 📄 License

**Proprietary - EnsanAI / CareBot Clinic**

All source code, documentation, and assets are proprietary and confidential. Unauthorized reproduction, distribution, or use is strictly prohibited.

---

## 👥 Authors

**EnsanAI Team** — Building intelligent healthcare technology

---

## 📞 Contact

For questions, issues, or deployment support:
- **Internal:** Contact EnsanAI Team
- **External:** Submit via documented issue channels

---

**Last Updated:** March 17, 2026  
**Version:** 1.0.0  
**Status:** Production Ready
