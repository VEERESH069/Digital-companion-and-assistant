# Pre-Visit Real-Time Voice Agent

A scalable, AI-powered conversational voice agent for dental clinics that automates pre-visit patient intake calls in Egyptian Arabic and English.

## 🎯 Key Features

- **Real-time Speech Recognition** - Whisper/Google Speech Recognition
- **Natural Voice Synthesis** - XTTS v2 / Google TTS
- **Intelligent Conversations** - GPT-4o mini with Egyptian Arabic awareness
- **Clinical Data Extraction** - Structured patient data with confidence scores
- **PDF Summary Generation** - Doctor briefing and patient copy
- **Automatic Routing** - Specialist assignment based on symptoms

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Microphone
- OpenAI API key
- Internet connection

### Installation

```powershell
# 1. Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
copy .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Run the voice agent
python voice_agent.py
```

## 📖 Documentation

See [docs/PROJECT_DOCUMENTATION.md](docs/PROJECT_DOCUMENTATION.md) for complete technical documentation.

## 🏗️ Architecture

```
Layer 1: Voice Infrastructure (STT + TTS)
    ↓
Layer 2: Conversational AI (LLM + State Machine)
    ↓
Layer 3: Data Extraction (Real-time + Post-call)
    ↓
Layer 4: Output (PDF Generation + Routing)
```

## 📁 Project Structure

```
.
├── src/
│   └── pre_visit_agent/
│       ├── config/            # Configuration management
│       ├── services/          # STT, TTS, LLM services
│       └── core/              # Conversation & data extraction
├── generate_pdf_summary.py    # PDF generation
├── voice_agent.py             # Main voice agent
├── requirements.txt           # Dependencies
└── docs/                      # Documentation
```

## 🔧 Usage Example

```python
from voice_agent import VoiceAgent

# Initialize
agent = VoiceAgent()

# Start session
session_id = agent.start_session(patient_id="P12345")

# End session and get summary
summary = agent.end_session(session_id)
print(f"Specialist: {summary.recommended_specialist}")
print(f"Urgency: {summary.urgency_level}")
```

### Generate PDF Summaries

```powershell
python generate_pdf_summary.py --output-dir output
```

## 📝 Data Collected

- Chief complaint (dental issue)
- Duration
- Severity (1-10)
- Location (tooth/area)
- Triggers
- Current medications
- Allergies
- Medical conditions

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

EnsanAI Team

---

**Version:** 1.0.0  
**Last Updated:** January 2026  
**Python:** 3.9+
