import re

# Production Configuration for Voice Agent

# TTS Settings - Cartesia Only
TTS_ENGINE = "cartesia"  # Using Cartesia for natural multilingual voices

# Cartesia TTS Settings - Natural Multilingual Voices
CARTESIA_MODEL = "sonic-3"  # Cartesia's latest model
CARTESIA_VOICE_ARABIC = "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"  # Natural Arabic voice
CARTESIA_VOICE_ENGLISH = "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"  # Natural English voice
CARTESIA_VOICE_HINDI = "95d51f79-c397-46f9-b49a-23763d3eaa2d"  # Dedicated Hindi voice
CARTESIA_VOICE_DEFAULT = CARTESIA_VOICE_ENGLISH
CARTESIA_LANGUAGE_VOICES = {
    "ar": CARTESIA_VOICE_ARABIC,
    "en": CARTESIA_VOICE_ENGLISH,
    "hi": CARTESIA_VOICE_HINDI,
}
CARTESIA_OUTPUT_FORMAT = {
    "container": "wav",
    "sample_rate": 44100,
    "encoding": "pcm_s16le",
}

ARABIC_TEXT_PATTERN = re.compile(r"[\u0600-\u06FF]")
DEVANAGARI_TEXT_PATTERN = re.compile(r"[\u0900-\u097F]")
WORD_PATTERN = re.compile(r"[a-zA-Z']+")

# Lightweight keyword model for transliterated language detection.
# Script-based detection stays highest priority; this only handles Latin text.
TRANSLITERATED_KEYWORDS = {
    "hi": {
        "namaste", "namaskar", "dhanyavaad", "dhanyavad", "shukriya", "kripya", "kripyaa",
        "aap", "aapka", "aapki", "aapse", "mujhe", "mera", "meri", "hum", "main", "tum",
        "kaise", "kya", "kyu", "kyon", "kab", "kal", "aaj", "abhi", "kitna", "kitni",
        "haan", "haanji", "nahi", "nahin", "theek", "thik", "accha", "achha", "ji",
        "dard", "tez", "halka", "bukhar", "khansi", "sardi", "ulti", "chakkar", "sujan",
        "dawai", "dawa", "allergy", "dant", "daant", "masuda", "infection", "samasya",
        "madad", "chahiye", "hoga", "hai", "hain", "doctor", "clinic", "appointment"
    },
    "ar": {
        "salam", "salaam", "marhaba", "ahlan", "ahlanwa", "shukran", "afwan", "allah",
        "kaif", "kif", "halak", "halik", "ana", "anti", "inti", "anta", "enta", "mafi",
        "tayyib", "tabib", "doctor", "mustashfa", "clinic", "waja", "alam", "mushkila",
        "asnan", "sin", "dars", "daras", "dawa", "hassasiya", "sudaa", "harara", "sual",
        "bukra", "alyawm", "alyom", "inshallah", "yalla", "tamam", "mashi", "laa", "na3am"
    },
}


def _score_transliterated_language(text: str) -> dict[str, int]:
    """Return keyword hit counts per supported language for Latin-script text."""
    tokens = {token.lower() for token in WORD_PATTERN.findall(text)}
    if not tokens:
        return {"hi": 0, "ar": 0}

    return {
        lang: sum(1 for keyword in keywords if keyword in tokens)
        for lang, keywords in TRANSLITERATED_KEYWORDS.items()
    }


def detect_tts_language(text: str) -> str:
    """Infer the best Cartesia language code from text.

    Priority:
    1) Native script detection (Arabic/Devanagari)
    2) Transliteration keyword model for Hindi/Arabic in Latin script
    3) English fallback
    """
    if ARABIC_TEXT_PATTERN.search(text):
        return "ar"
    if DEVANAGARI_TEXT_PATTERN.search(text):
        return "hi"

    scores = _score_transliterated_language(text)
    # Stricter: require at least 3 keyword hits and a clear lead
    if scores["hi"] >= 3 and scores["hi"] > scores["ar"]:
        return "hi"
    if scores["ar"] >= 3 and scores["ar"] > scores["hi"]:
        return "ar"
    return "en"


def normalize_language_code(language_code: str | None) -> str:
    """Normalize locale codes like ar-EG or en_US to Cartesia language keys."""
    if not language_code:
        return "en"

    normalized = language_code.lower().replace("_", "-")
    base_language = normalized.split("-", 1)[0]
    return base_language if base_language in CARTESIA_LANGUAGE_VOICES else "en"


def get_cartesia_voice_id(language_code: str | None) -> str:
    """Resolve the configured Cartesia voice ID for a detected language."""
    normalized_language = normalize_language_code(language_code)
    return CARTESIA_LANGUAGE_VOICES.get(normalized_language, CARTESIA_VOICE_DEFAULT)

# STT Settings
STT_LANGUAGES = ["ar", "en", "hi"]
STT_ENERGY_THRESHOLD = 300
STT_DYNAMIC_ENERGY = False
STT_PAUSE_THRESHOLD = 0.6   # Seconds silence = end of speech; shorter = faster response
STT_PHRASE_TIME_LIMIT = 10  # Lowered for faster response

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
INTERRUPT_ENERGY_THRESHOLD = 1400  # Minimum RMS energy level to trigger interrupt
INTERRUPT_WARMUP_MS = 700  # Ignore early mic bleed right after playback starts (milliseconds)
INTERRUPT_CONSECUTIVE_FRAMES = 4  # Frames above threshold required before triggering interrupt
INTERRUPT_BASELINE_MULTIPLIER = 2.2  # Adaptive multiplier over ambient RMS during playback
INTERRUPT_PEAK_THRESHOLD = 2600  # Peak sample magnitude required to treat audio as speech-like

# Natural Speech Settings
ADD_NATURAL_PAUSES = True  # Add human-like pauses in speech
PAUSE_AFTER_SENTENCE = 0.5  # Seconds to pause after each sentence
PAUSE_AFTER_QUESTION = 0.7  # Seconds to pause after questions
TTS_TAIL_SILENCE_SEC = 0.35  # Short silence after playback so final words are not clipped

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
