# Production Voice Agent - Quick Start

## 🚀 Setup (One Time)

```powershell
# Install dependencies
pip install -r requirements.txt

# Verify setup
python -c "import whisper, openai; print('✓ Ready')"
```

## ▶️ Run

```powershell
python voice_agent_production.py
```

## ⚙️ Configuration

Edit [config.py](config.py):

```python
# STT Accuracy (Whisper = more accurate)
STT_ENGINE = "whisper"        # or "google" (faster but less accurate)
WHISPER_MODEL = "base"        # tiny, base, small, medium, large
ENABLE_NOISE_REDUCTION = True # Reduce background noise

# Voice Quality
TTS_VOICE = "nova"            # nova, shimmer, alloy
TTS_SPEED = 1.0               # 0.9 slower, 1.1 faster

# Features
ENABLE_INTERRUPT_DETECTION = True  # Stop when user speaks
ADD_NATURAL_PAUSES = True          # Human-like pauses
```

## 🎯 Key Features

- **High Accuracy STT** - Whisper model (much better than Google)
- **Noise Reduction** - Filters background noise
- **Natural Voice** - OpenAI TTS (professional quality)
- **Interrupt Detection** - Stops when you speak
- **Low Latency** - Optimized performance

## 🐛 Troubleshooting

**STT not accurate?**
- Use `WHISPER_MODEL = "small"` or `"medium"` (more accurate but slower)
- Enable `ENABLE_NOISE_REDUCTION = True`
- Increase `STT_ENERGY_THRESHOLD = 500` (less sensitive to noise)

**Too slow?**
- Use `WHISPER_MODEL = "tiny"` or `"base"`
- Or switch to `STT_ENGINE = "google"`

**Whisper not installed?**
```powershell
pip install openai-whisper torch torchaudio
```

