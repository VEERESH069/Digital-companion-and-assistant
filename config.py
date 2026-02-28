# Production Configuration for Voice Agent

# TTS Settings - Cartesia Only
TTS_ENGINE = "cartesia"  # Using Cartesia for natural multilingual voices

# Cartesia TTS Settings - Natural Multilingual Voices
CARTESIA_MODEL = "sonic-3"  # Cartesia's latest model
CARTESIA_VOICE_ARABIC = "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"  # Natural Arabic voice
CARTESIA_VOICE_ENGLISH = "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"  # Natural English voice
CARTESIA_OUTPUT_FORMAT = {
    "container": "wav",
    "sample_rate": 44100,
    "encoding": "pcm_s16le",
}

# STT Settings
STT_LANGUAGES = ["ar", "en", "hi"]
STT_ENERGY_THRESHOLD = 300
STT_DYNAMIC_ENERGY = False
STT_PAUSE_THRESHOLD = 0.6   # Seconds silence = end of speech; shorter = faster response
STT_PHRASE_TIME_LIMIT = 25

# Voice Cloning
ENABLE_VOICE_CLONING = False  # Set to True to use custom voice samples
VOICE_SAMPLE_PATH = "voice_samples/mariam_voice.wav"

# LLM Settings
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS_RESPONSE = 100
LLM_MAX_TOKENS_EXTRACTION = 800

# Conversation Settings
MAX_CONVERSATION_TURNS = 15

# Interrupt Detection
ENABLE_INTERRUPT_DETECTION = True
INTERRUPT_CHECK_INTERVAL = 0.05   # How often to check for interrupt (seconds)
INTERRUPT_ENERGY_THRESHOLD = 800  # RMS energy level to trigger interrupt (tune if needed)

# Natural Speech Settings
ADD_NATURAL_PAUSES = True  # Add human-like pauses in speech
PAUSE_AFTER_SENTENCE = 0.3  # Seconds to pause after each sentence
PAUSE_AFTER_QUESTION = 0.5  # Seconds to pause after questions

# Performance Settings
ENABLE_TTS_CACHING = True  # Cache common phrases
PRELOAD_TTS_MODEL = False  # Load TTS model at startup (slower start, faster responses)
USE_GPU = False  # Enable GPU acceleration for F5-TTS (if available)

# Output Settings
OUTPUT_DIR = "output"
SAVE_JSON = True
GENERATE_PDFS = True
VERBOSE_LOGGING = True

# Error Handling
MAX_RETRIES_STT = 2
MAX_RETRIES_TTS = 2

# Exit Keywords
EXIT_KEYWORDS = [
    # English
    "goodbye", "bye", "exit", "stop", "end", "quit",
    # Arabic
    "مع السلامة", "وداعا", "خلاص", "باي",
    # Hindi
    "धन्यवाद", "बाय", "अलविदा"
]
