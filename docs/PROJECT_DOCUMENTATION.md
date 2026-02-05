# Pre-Visit Voice Agent - Complete Documentation

## Overview

The Pre-Visit Voice Agent is an AI-powered conversational system for dental clinics that automates patient intake calls. It collects medical information before appointments using natural voice conversations in Egyptian Arabic and English.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRE-VISIT VOICE AGENT                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 1: VOICE INFRASTRUCTURE                              │
│  ┌──────────────┐              ┌──────────────┐            │
│  │ STT Service  │◄────audio────│ TTS Service  │            │
│  │ (Whisper)    │              │ (XTTS v2)    │            │
│  └──────┬───────┘              └───────▲──────┘            │
│         │                              │                     │
│  Layer 2: CONVERSATIONAL AI                                 │
│  ┌──────▼────────────────────────┬────┴──────┐            │
│  │  Conversation Manager         │  LLM      │            │
│  │  - State Machine              │  Service  │            │
│  │  - Turn Logic                 │  (GPT-4o) │            │
│  └──────┬────────────────────────┴───────────┘            │
│         │                                                   │
│  Layer 3: DATA EXTRACTION                                   │
│  ┌──────▼─────────────────────────────────┐               │
│  │  Data Extractor                        │               │
│  │  - Real-time extraction (every 2 turns)│               │
│  │  - Post-conversation analysis          │               │
│  │  - Confidence scoring                  │               │
│  │  - Red flag detection                  │               │
│  └──────┬─────────────────────────────────┘               │
│         │                                                   │
│  Layer 4: INTEGRATION & OUTPUT                              │
│  ┌──────▼────────┐  ┌──────────┐  ┌──────────┐           │
│  │  Routing      │  │   PDF    │  │   EHR    │           │
│  │  Engine       │  │ Generator│  │ (Future) │           │
│  └───────────────┘  └──────────┘  └──────────┘           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
Pre-Visit-real-time-voice-agent/
├── src/
│   └── pre_visit_agent/
│       ├── config/
│       │   └── config.py           # Configuration management
│       ├── services/
│       │   ├── stt_service.py      # Speech-to-Text (Whisper)
│       │   ├── tts_service.py      # Text-to-Speech (XTTS v2)
│       │   └── llm_service.py      # LLM integration (GPT-4o mini)
│       ├── core/
│       │   ├── conversation_manager.py  # State machine & dialogue
│       │   └── data_extractor.py   # Data extraction layer
│       └── main.py                 # Voice Agent orchestrator
├── generate_pdf_summary.py         # PDF generation for summaries
├── voice_agent.py                  # Standalone voice agent
├── requirements.txt                # Python dependencies
├── docs/
│   └── PROJECT_DOCUMENTATION.md    # This file
└── output/                         # Generated PDFs and JSON
```

---

## Installation

### Prerequisites

- Python 3.9+
- Microphone (for voice input)
- OpenAI API key
- Internet connection

### Setup Steps

```powershell
# 1. Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env and add OPENAI_API_KEY

# 4. Run the voice agent
python voice_agent.py
```

---

## Components

### Layer 1: Voice Infrastructure

#### STT Service (Speech-to-Text)
- **Engine**: Google Speech Recognition
- **Languages**: Arabic (Egyptian `ar-EG`), English (`en-US`)
- **Detection**: Tries Arabic first, falls back to English
- **Features**: Real-time transcription, dialect support

#### TTS Service (Text-to-Speech)
- **Engine**: Google TTS (gTTS) - FREE
- **Languages**: Arabic, English (auto-detected from text content)
- **Detection**: Checks for Arabic characters (`\u0600-\u06FF`) in text
- **Features**: Natural voices, automatic language switching

### Layer 2: Conversational AI

#### Conversation Manager (conversation_manager.py)
State machine with four phases:
1. **GREETING** - Build rapport, introduce purpose
2. **DISCOVERY** - Collect data naturally (not sequential)
3. **COMPLETION** - Verify all info collected
4. **CLOSING** - Thank patient, confirm appointment

#### LLM Service (llm_service.py)
- **Primary**: GPT-4o mini
- **Fallback**: Claude Haiku 4.5
- **Features**: Streaming, function calling, retry logic

### Layer 3: Data Extraction

#### Data Extractor (data_extractor.py)
- **Real-time**: Every 2-3 turns during conversation
- **Post-conversation**: Comprehensive analysis after call ends
- **Outputs**: Confidence scores, red flags, clinical summary

**Required Fields Collected:**
- Chief complaint (dental issue)
- Duration (how long)
- Severity (pain level 1-10)
- Location (which tooth/area)
- Triggers (what makes it worse)
- Current medications
- Allergies
- Medical conditions

### Layer 4: Output & Integration

#### PDF Generator (generate_pdf_summary.py)
Generates two PDF variants:
1. **Doctor Briefing** - Full clinical data, confidence scores, red flags
2. **Patient Copy** - Simplified summary without internal metrics

#### Routing Engine
Automatic specialist assignment:
- **Endodontist** - Root canal, pulp issues
- **Periodontist** - Gum disease
- **Oral Surgeon** - Extractions, trauma
- **Emergency** - Severity ≥8, fever+swelling

---

## Language Support (Bilingual)

The voice agent supports **Arabic (Egyptian)** and **English** with intelligent language handling:

### How It Works

| Component | Language Behavior |
|-----------|------------------|
| **Greeting** | Arabic (صباح الخير!) |
| **Speech Recognition** | Tries Arabic first → English fallback |
| **Agent Responses** | Matches patient's language |
| **Text-to-Speech** | Auto-detects from response text |
| **Clinical Documents** | **Always English** (medical standard) |

### Language Flow

```
Patient speaks Arabic → STT detects Arabic → LLM responds in Arabic → TTS speaks Arabic
Patient speaks English → STT detects English → LLM responds in English → TTS speaks English
```

### Exit Keywords

| English | Arabic |
|---------|--------|
| goodbye, bye | مع السلامة |
| exit, stop, end | وداعا، خلاص، شكرا |

### Why Documents Stay in English

- Medical terminology is standardized in English
- EHR systems typically use English
- Doctors can read regardless of patient's language
- The LLM extracts and translates Arabic responses to English clinical data

---

## Usage

### Running the Voice Agent

```powershell
# Run bilingual voice agent (Arabic + English)
python voice_agent.py
```

**Console Output:**
```
✓ Ready! Starting conversation...

💡 Microphone will auto-detect when you speak
💡 Speak clearly in Arabic or English
💡 Say 'goodbye' or 'مع السلامة' to exit
💡 Press Ctrl+C to force stop

🔊 Agent: صباح الخير! أنا مريم من عيادة كيربوت. كيف حالك النهاردة؟
```

### Generating PDF Summaries

```powershell
# Using sample data
python generate_pdf_summary.py --output-dir output

# Using custom JSON
python generate_pdf_summary.py patient_data.json --output-dir output
```

---

## Conversation Flow

```
Patient calls → Agent greets warmly
         ↓
Agent asks about dental concern
         ↓
Natural conversation (not robotic Q&A)
         ↓
Data extracted in real-time
         ↓
Agent confirms information
         ↓
Session ends → Clinical summary generated
         ↓
PDF output + Specialist routing
```

---

## Configuration

### Environment Variables (.env)

```env
OPENAI_API_KEY=sk-your-key-here
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Key Settings (config.py)

- **STT**: Model size, language, dialect prompt
- **TTS**: Voice sample, emotion support
- **LLM**: Model, temperature, max tokens
- **Conversation**: Max turns, required fields

---

## Data Pipeline (Post-Call)

1. **Voice Input** → STT converts to text (in-memory)
2. **Conversation** → LLM manages dialogue
3. **Extraction** → Structured JSON with confidence scores
4. **Output** → PDFs generated from validated schema
5. **Cleanup** → Temporary data purged

### Storage Guidelines
- Raw audio: Keep off-disk when possible
- STT text: In-memory, purge after PDF generation
- Structured payload: Validated JSON to disk/cloud
- Logs: Structured, no PHI content

---

## Testing

```powershell
# Test configuration
python -c "from src.pre_visit_agent.config.config import config; config.validate()"

# Test PDF generation
python generate_pdf_summary.py --output-dir output

# Test live microphone
python tests/test_mic_live.py
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| GPU not detected | Check CUDA installation |
| API errors | Verify OPENAI_API_KEY in .env |
| Slow transcription | Use smaller Whisper model |
| Audio not playing | Check PyAudio installation |

---

## Future Integrations

- **CareBot Memory Agent** - Patient history persistence
- **EHR Systems** - Direct patient record integration
- **Appointment Systems** - Automated scheduling

---

**Version:** 1.1.0  
**Last Updated:** February 2026  
**Python:** 3.9+  
**Languages:** Arabic (Egyptian), English
