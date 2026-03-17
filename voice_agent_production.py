"""
Production Voice Agent - Primary Runtime
========================================
Primary, production-ready medical voice agent with:
- Low latency
- Interrupt detection
- Natural speech pauses
- Optimal error handling
- Clean architecture

Run (primary): python voice_agent_production.py
"""

import os
import sys
import json
import uuid
import time
import queue
import tempfile
import threading
import pyaudio
import speech_recognition as sr
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, Dict, List, Any, cast
import re
from openai import OpenAI
from dotenv import load_dotenv

# Import Cartesia for TTS
try:
    from cartesia import Cartesia
    CARTESIA_AVAILABLE = True
except ImportError:
    CARTESIA_AVAILABLE = False

# Import configuration
import config

# Load environment
load_dotenv()

# Validate API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ ERROR: OPENAI_API_KEY not set in .env file")
    sys.exit(1)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Cartesia client if available
cartesia_client = None
if CARTESIA_AVAILABLE and os.getenv("CARTESIA_API_KEY"):
    try:
        cartesia_client = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))
        print("✅ Cartesia TTS initialized")
    except Exception as e:
        print(f"⚠ Cartesia initialization failed: {e}")
        CARTESIA_AVAILABLE = False

# Setup directories
OUTPUT_DIR = Path(__file__).parent / config.OUTPUT_DIR
OUTPUT_DIR.mkdir(exist_ok=True)

# Global state
recognizer: Optional[sr.Recognizer] = None
microphone: Optional[sr.Microphone] = None


class ConversationManager:
    """Manages conversation history and state"""
    
    def __init__(self):
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": """أنت مريم، موظفة استقبال ودودة في عيادة كيربوت الطبية.

You are Mariam, a friendly receptionist at CareBot Clinic.
You're conducting a pre-visit consultation call to gather medical information.

Style Guidelines:
- Keep responses SHORT (1-2 sentences maximum)
- Ask ONE question at a time  
- Show empathy and understanding
- Natural conversational tone
- Add appropriate pauses with punctuation (. , ! ?)
- Respond in the SAME language the patient uses

Required Information:
1. Chief complaint
2. Duration  
3. Pain severity 1-10
4. Location
5. Triggers
6. Current medications
7. Allergies
8. Medical conditions

Important:
- If diabetes + dental infection → high priority
- Note allergies for treatment planning"""}
        ]
        self.turn_count = 0
        self.assistant_turn_events: List[Dict[str, Any]] = []
    
    def add_user_message(self, message: str):
        """Add user message to history"""
        self.history.append({"role": "user", "content": message})
    
    def add_assistant_message(self, message: str):
        """Add assistant message to history"""
        self.history.append({"role": "assistant", "content": message})
        self.turn_count += 1
    
    def get_history(self):
        """Get conversation history"""
        return self.history
    
    def is_complete(self) -> bool:
        """Check if conversation should end"""
        return self.turn_count >= config.MAX_CONVERSATION_TURNS

    def add_assistant_turn_event(
        self,
        generated_text: str,
        played_text: str,
        interrupted: bool,
        completed: bool,
    ):
        """Track assistant turn delivery state for observability/debugging."""
        self.assistant_turn_events.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "generated_text": generated_text,
                "played_text": played_text,
                "interrupted": interrupted,
                "completed": completed,
            }
        )


class TTSEngine:
    """TTS Engine — streams raw PCM directly via PyAudio for minimum latency"""

    SAMPLE_RATE = 22050
    CHANNELS = 1
    CHUNK = 1024

    def __init__(self):
        self.cache: Dict[str, bytes] = {}  # caches raw PCM bytes
        self._pa = pyaudio.PyAudio()

    @staticmethod
    def _safe_stop_close_stream(stream: Any):
        """Best-effort stream cleanup to avoid device-busy leaks after exceptions."""
        if stream is None:
            return
        try:
            stream.stop_stream()
        except Exception:
            pass
        try:
            stream.close()
        except Exception:
            pass

    def _monitor_interrupt(self, interrupt_requested: threading.Event, playback_done: threading.Event):
        """Background monitor: raises interrupt_requested when user speech is detected."""
        mon: Optional[pyaudio.PyAudio] = None
        stream: Any = None
        warmup_ms = int(getattr(config, "INTERRUPT_WARMUP_MS", 250))
        consecutive_required = int(getattr(config, "INTERRUPT_CONSECUTIVE_FRAMES", 2))
        warmup_seconds = max(0, warmup_ms) / 1000.0
        start_time = time.monotonic()
        high_frames = 0

        try:
            mon = pyaudio.PyAudio()
            stream = mon.open(
                format=pyaudio.paInt16, channels=1, rate=16000,
                input=True, frames_per_buffer=512
            )
        except OSError as e:
            print(f"   ⚠ Interrupt monitor unavailable; continuing without barge-in: {e}")
            return
        except Exception as e:
            print(f"   ⚠ Interrupt monitor failed to start; continuing playback: {e}")
            return

        try:
            while not playback_done.is_set() and not interrupt_requested.is_set():
                try:
                    data = stream.read(512, exception_on_overflow=False)
                    samples = [int.from_bytes(data[i:i+2], 'little', signed=True)
                               for i in range(0, len(data) - 1, 2)]
                    if not samples:
                        continue

                    # Ignore early speaker bleed right after playback begins.
                    if (time.monotonic() - start_time) < warmup_seconds:
                        continue

                    rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
                    if rms > config.INTERRUPT_ENERGY_THRESHOLD:
                        high_frames += 1
                        if high_frames >= max(1, consecutive_required):
                            interrupt_requested.set()
                            break
                    else:
                        high_frames = 0
                except Exception:
                    break
        finally:
            self._safe_stop_close_stream(stream)
            if mon is not None:
                try:
                    mon.terminate()
                except Exception:
                    pass

    def speak_cartesia(self, text: str) -> bool:
        """Stream Cartesia raw PCM straight to speakers — zero file I/O, first sound in ~100ms"""
        global cartesia_client

        if not CARTESIA_AVAILABLE or not cartesia_client:
            print("   ✗ Cartesia not available")
            return False

        out: Any = None
        interrupt_thread: Optional[threading.Thread] = None
        interrupt_requested = threading.Event()
        playback_done = threading.Event()

        try:
            language = config.detect_tts_language(text)
            voice_id = config.get_cartesia_voice_id(language)
            cache_key = f"{text}_{language}_{voice_id}"

            out = self._pa.open(
                format=pyaudio.paInt16, channels=self.CHANNELS,
                rate=self.SAMPLE_RATE, output=True, frames_per_buffer=self.CHUNK
            )
            if config.ENABLE_INTERRUPT_DETECTION:
                interrupt_thread = threading.Thread(
                    target=self._monitor_interrupt,
                    args=(interrupt_requested, playback_done),
                    daemon=True,
                )
                interrupt_thread.start()

            # --- Cached: replay stored PCM ---
            if config.ENABLE_TTS_CACHING and cache_key in self.cache:
                pcm = self.cache[cache_key]
                for i in range(0, len(pcm), self.CHUNK * 2):
                    if interrupt_requested.is_set():
                        break
                    out.write(pcm[i:i + self.CHUNK * 2])
            else:
                # --- Live stream via SSE: pipe chunks straight to speakers ---
                from cartesia.types.sse_events import ChunkEvent  # type: ignore
                pcm_buffer = b""
                interrupted = False
                for event in cartesia_client.tts.sse(  # type: ignore
                    model_id=config.CARTESIA_MODEL,
                    transcript=text,
                    voice={"mode": "id", "id": voice_id},
                    language=language,
                    output_format={  # type: ignore
                        "container": "raw", "sample_rate": self.SAMPLE_RATE, "encoding": "pcm_s16le"
                    },
                ):
                    if interrupt_requested.is_set():
                        interrupted = True
                        break
                    if isinstance(event, ChunkEvent) and event.audio:
                        out.write(event.audio)
                        if config.ENABLE_TTS_CACHING:
                            pcm_buffer += event.audio

                if not interrupted and config.ENABLE_TTS_CACHING and pcm_buffer:
                    self.cache[cache_key] = pcm_buffer

            interrupted = interrupt_requested.is_set()

            if interrupted:
                print("   ✋ User interrupted — listening...")
                return False
            return True

        except Exception as e:
            print(f"   ✗ Cartesia TTS error: {e}")
            return False
        finally:
            playback_done.set()
            self._safe_stop_close_stream(out)
            if interrupt_thread is not None:
                interrupt_thread.join(timeout=0.3)

    def speak(self, text: str) -> bool:
        print(f"\n🔊 Agent: {text}")
        return self.speak_cartesia(text)

    def _fetch_pcm_to_queue(self, text: str, pcm_q: 'queue.Queue[Any]') -> None:
        """Fetch Cartesia SSE audio for `text` and push raw PCM chunks into pcm_q.
        Pushes None as sentinel when done or on error."""
        from cartesia.types.sse_events import ChunkEvent  # type: ignore
        try:
            language = config.detect_tts_language(text)
            voice_id = config.get_cartesia_voice_id(language)
            cache_key = f"{text}_{language}_{voice_id}"

            # Cached: push stored PCM straight to queue
            if config.ENABLE_TTS_CACHING and cache_key in self.cache:
                pcm = self.cache[cache_key]
                for i in range(0, len(pcm), self.CHUNK * 2):
                    pcm_q.put(pcm[i:i + self.CHUNK * 2])
                pcm_q.put({"type": "sentence_end", "text": text})
                return

            pcm_buffer = b""
            for event in cartesia_client.tts.sse(  # type: ignore
                model_id=config.CARTESIA_MODEL,
                transcript=text,
                voice={"mode": "id", "id": voice_id},
                language=language,
                output_format={  # type: ignore
                    "container": "raw", "sample_rate": self.SAMPLE_RATE, "encoding": "pcm_s16le"
                },
            ):
                if isinstance(event, ChunkEvent) and event.audio:
                    pcm_q.put(event.audio)
                    if config.ENABLE_TTS_CACHING:
                        pcm_buffer += event.audio

            if config.ENABLE_TTS_CACHING and pcm_buffer:
                self.cache[cache_key] = pcm_buffer

            pcm_q.put({"type": "sentence_end", "text": text})

        except Exception as e:
            print(f"   ✗ TTS fetch error: {e}")

    def play_continuous(self, pcm_q: 'queue.Queue[Any]') -> Tuple[bool, List[str]]:
        """Continuously play PCM chunks from pcm_q until None sentinel.
        Returns (is_interrupted, delivered_sentences)."""
        delivered_sentences: List[str] = []
        out: Any = None
        interrupt_thread: Optional[threading.Thread] = None
        interrupt_requested = threading.Event()
        playback_done = threading.Event()

        interrupted = False
        try:
            out = self._pa.open(
                format=pyaudio.paInt16, channels=self.CHANNELS,
                rate=self.SAMPLE_RATE, output=True, frames_per_buffer=self.CHUNK
            )
            if config.ENABLE_INTERRUPT_DETECTION:
                interrupt_thread = threading.Thread(
                    target=self._monitor_interrupt,
                    args=(interrupt_requested, playback_done),
                    daemon=True,
                )
                interrupt_thread.start()

            while True:
                try:
                    chunk = pcm_q.get(timeout=8)
                except queue.Empty:
                    break
                if chunk is None:
                    break
                if isinstance(chunk, dict) and chunk.get("type") == "sentence_end":
                    delivered_text = str(chunk.get("text", "")).strip()
                    if delivered_text:
                        delivered_sentences.append(delivered_text)
                    continue
                if interrupt_requested.is_set():
                    interrupted = True
                    # drain remaining queue quickly
                    while not pcm_q.empty():
                        try:
                            pcm_q.get_nowait()
                        except Exception:
                            break
                    break
                out.write(chunk)
        finally:
            playback_done.set()
            self._safe_stop_close_stream(out)
            if interrupt_thread is not None:
                interrupt_thread.join(timeout=0.3)

        if interrupted:
            print("   ✋ User interrupted — listening...")
        return interrupted, delivered_sentences


class STTEngine:
    """Speech-to-Text Engine"""
    
    def __init__(self, recognizer: sr.Recognizer, microphone: sr.Microphone):
        self.recognizer = recognizer
        self.microphone = microphone
        
        # Calibrate ambient noise ONCE at startup (not on every turn)
        print("   🎙 Calibrating microphone...")
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            recognizer.energy_threshold = config.STT_ENERGY_THRESHOLD
            recognizer.dynamic_energy_threshold = config.STT_DYNAMIC_ENERGY
            recognizer.pause_threshold = config.STT_PAUSE_THRESHOLD
        print(f"   ✓ Mic calibrated (energy threshold: {int(recognizer.energy_threshold)})")
    
    def _transcribe_google(self, audio_data) -> Tuple[Optional[str], Optional[str]]:
        """Transcribe using Google STT (fallback)"""
        try:
            # Try each language
            for lang_code in config.STT_LANGUAGES:
                try:
                    # Add language code format for Google
                    if '-' not in lang_code:
                        lang_map = {
                            "ar": "ar-EG",
                            "en": "en-US", 
                            "hi": "hi-IN"
                        }
                        google_lang = lang_map.get(lang_code, f"{lang_code}-US")
                    else:
                        google_lang = lang_code
                    
                    text = self.recognizer.recognize_google(audio_data, language=google_lang)  # type: ignore
                    lang_name = lang_code.split('-')[0].upper()
                    print(f"   ✓ Google: {lang_name}")
                    return text, lang_code.split('-')[0]
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    print(f"   ✗ Recognition service error: {e}")
                    return None, None
            
            return None, None
            
        except Exception as e:
            print(f"   ⚠ Google STT error: {e}")
            return None, None
    
    def _transcribe_openai_api(self, audio_data: sr.AudioData) -> Tuple[Optional[str], Optional[str]]:
        """Transcribe using OpenAI cloud Whisper API - fastest option"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data.get_wav_data())
                temp_path = f.name
            
            with open(temp_path, "rb") as audio_file:
                result = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            try:
                os.unlink(temp_path)
            except:
                pass
            
            text = str(result).strip() if result else ""
            # Detect language from content
            lang = "ar" if bool(re.search('[\u0600-\u06FF]', text)) else "en"
            
            if text:
                print(f"   ✓ Whisper: {lang.upper()}")
                return text, lang
            return None, None
        except Exception as e:
            print(f"   ⚠ OpenAI Whisper API error: {e}")
            return None, None

    def listen(self) -> Tuple[Optional[str], Optional[str]]:
        """Listen and convert speech to text - fast, no per-turn calibration"""
        try:
            print("\n🎤 Listening...")
            
            with self.microphone as source:
                # No calibration here — done once at startup
                audio = self.recognizer.listen(
                    source,
                    timeout=20,
                    phrase_time_limit=config.STT_PHRASE_TIME_LIMIT
                )
            
            print("   ⏳ Transcribing...")
            
            # Use OpenAI cloud Whisper API (fastest, auto-detects language)
            result = self._transcribe_openai_api(audio)
            if result[0]:
                return result
            # Fallback to Google if OpenAI API fails
            print("   → Falling back to Google STT")
            return self._transcribe_google(audio)
                    
        except sr.WaitTimeoutError:
            return "__silence__", None
        except KeyboardInterrupt:
            print("\n   ⚠ Interrupted by user")
            return None, None
        except Exception as e:
            print(f"   ✗ Listening error: {e}")
            return None, None


class LLMEngine:
    """Large Language Model Engine"""

    @staticmethod
    def stream_and_speak(conversation: ConversationManager, user_message: str, tts_engine: TTSEngine) -> Optional[str]:
        """3-thread pipeline: LLM streams → sentence queue → Cartesia pre-fetches → playback.
        Zero gap between sentences because next audio is pre-fetched while current plays."""
        cancel_event = threading.Event()
        stop_speaking = cancel_event
        sentence_q: queue.Queue[Optional[str]]   = queue.Queue()
        pcm_q:      queue.Queue[Any] = queue.Queue(maxsize=100)
        full_response_box: List[str] = [""]

        # ── Thread 1: stream LLM tokens, split into sentences ──────────────
        def llm_worker():
            try:
                conversation.add_user_message(user_message)
                print("   🧠 Thinking...", end="", flush=True)
                stream = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=conversation.get_history(),  # type: ignore
                    temperature=config.LLM_TEMPERATURE,
                    max_tokens=config.LLM_MAX_TOKENS_RESPONSE,
                    stream=True
                )
                buf = ""
                for chunk in stream:
                    if stop_speaking.is_set():
                        break
                    token = chunk.choices[0].delta.content or ""
                    full_response_box[0] += token
                    buf += token
                    # Split on sentence-ending chars followed by space or end
                    parts = re.split(r'(?<=[.!?\u061f\u060c])\s+', buf)
                    for sentence in parts[:-1]:  # all but last (may be incomplete)
                        if stop_speaking.is_set():
                            break
                        s = sentence.strip()
                        if len(s) > 2:
                            sentence_q.put(s)
                    if stop_speaking.is_set():
                        break
                    buf = parts[-1]  # keep the incomplete tail
                if (not stop_speaking.is_set()) and buf.strip() and len(buf.strip()) > 2:
                    sentence_q.put(buf.strip())
            except Exception as e:
                print(f"\n   ✗ LLM error: {e}")
            finally:
                sentence_q.put(None)  # sentinel

        # ── Thread 2: for each sentence, fetch Cartesia PCM into pcm_q ─────
        def tts_worker():
            try:
                first = True
                while True:
                    sentence = sentence_q.get()
                    if sentence is None:
                        break
                    if cancel_event.is_set():
                        # drain sentence queue, don\'t fetch more
                        while not sentence_q.empty():
                            try: sentence_q.get_nowait()
                            except: break
                        break
                    if first:
                        print()  # newline after "Thinking..."
                        first = False
                    print(f"\n🔊 Agent: {sentence}")
                    tts_engine._fetch_pcm_to_queue(sentence, pcm_q)
            finally:
                pcm_q.put(None)  # sentinel

        llm_t = threading.Thread(target=llm_worker,  daemon=True)
        tts_t = threading.Thread(target=tts_worker,  daemon=True)
        llm_t.start()
        tts_t.start()

        # Main thread: play continuously from pcm_q (zero gaps between sentences)
        interrupted, delivered_sentences = tts_engine.play_continuous(pcm_q)

        if interrupted:
            cancel_event.set()

        tts_t.join(timeout=5)
        llm_t.join(timeout=5)

        full = full_response_box[0].strip()
        played = " ".join(delivered_sentences).strip()

        # Keep prompt history aligned with what patient actually heard.
        if played:
            conversation.add_assistant_message(played)

        conversation.add_assistant_turn_event(
            generated_text=full,
            played_text=played,
            interrupted=interrupted,
            completed=(not interrupted and bool(full) and full == played),
        )

        return played or None

    @staticmethod
    def get_response(conversation: ConversationManager, user_message: str) -> Optional[str]:
        """Get AI response (non-streaming, kept for internal use)"""
        try:
            conversation.add_user_message(user_message)
            
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=conversation.get_history(),  # type: ignore
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS_RESPONSE
            )
            
            ai_response = response.choices[0].message.content
            if ai_response:
                conversation.add_assistant_message(ai_response)
                return ai_response
            
            return "معلش، مفهمتش. ممكن تعيد تاني؟"
            
        except Exception as e:
            print(f"   ✗ LLM Error: {e}")
            return "Sorry, I encountered an error. Could you repeat that?"
    
    @staticmethod
    def extract_clinical_data(conversation: ConversationManager) -> dict:
        """Extract structured clinical data from conversation"""
        history = conversation.get_history()
        transcript = "\n".join([
            f"{'Agent' if msg['role'] == 'assistant' else 'Patient'}: {msg['content']}"
            for msg in history if msg['role'] != 'system'
        ])
        
        extraction_prompt = f"""Analyze this medical conversation and extract structured clinical data.

CONVERSATION:
{transcript}

Return JSON with this structure:
{{
    "clinical_data": {{
        "chief_complaint": "complaint or null",
        "duration": "duration or null",
        "severity": <1-10 or null>,
        "location": "location or null",
        "triggers": [],
        "current_medications": [],
        "allergies": [],
        "previous_dental_work": "description or null",
        "medical_conditions": []
    }},
    "confidence_scores": {{
        "chief_complaint": <0.0-1.0>,
        "duration": <0.0-1.0>,
        "severity": <0.0-1.0>,
        "location": <0.0-1.0>,
        "triggers": <0.0-1.0>,
        "current_medications": <0.0-1.0>,
        "allergies": <0.0-1.0>,
        "previous_dental_work": <0.0-1.0>,
        "medical_conditions": <0.0-1.0>
    }},
    "clinical_summary": "2-3 sentence summary",
    "red_flags": [],
    "urgency_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "recommended_specialist": "specialist type"
}}

Return ONLY valid JSON, no explanation."""

        try:
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0.1,
                max_tokens=config.LLM_MAX_TOKENS_EXTRACTION
            )
            
            result_text = response.choices[0].message.content or "{}"
            
            # Clean JSON
            result_text = result_text.strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            return json.loads(result_text)
            
        except Exception as e:
            print(f"   ⚠ Extraction error: {e}")
            return get_default_clinical_data()


def get_default_clinical_data() -> dict:
    """Default clinical data structure"""
    return {
        "clinical_data": {
            "chief_complaint": None,
            "duration": None,
            "severity": None,
            "location": None,
            "triggers": [],
            "current_medications": [],
            "allergies": [],
            "previous_dental_work": None,
            "medical_conditions": []
        },
        "confidence_scores": {k: 0.0 for k in [
            "chief_complaint", "duration", "severity", "location",
            "triggers", "current_medications", "allergies",
            "previous_dental_work", "medical_conditions"
        ]},
        "clinical_summary": "Consultation completed. Data extraction pending review.",
        "red_flags": [],
        "urgency_level": "MEDIUM",
        "recommended_specialist": "General Dentist"
    }


def build_clinical_payload(extracted_data: dict, patient_id: Optional[str] = None) -> dict:
    """Build complete clinical payload"""
    if not patient_id:
        patient_id = f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    conversation_id = f"CONV-{datetime.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()
    
    urgency = extracted_data.get("urgency_level", "MEDIUM")
    
    return {
        "patient_id": patient_id,
        "conversation_id": conversation_id,
        "timestamp": timestamp,
        "clinical_data": extracted_data.get("clinical_data", {}),
        "confidence_scores": extracted_data.get("confidence_scores", {}),
        "clinical_summary": extracted_data.get("clinical_summary", ""),
        "red_flags": extracted_data.get("red_flags", []),
        "urgency_level": urgency,
        "recommended_specialist": extracted_data.get("recommended_specialist", "General Dentist"),
        "routing_decision": {
            "needs_triage": urgency in ["HIGH", "CRITICAL"],
            "pre_scheduled": urgency not in ["CRITICAL"],
            "appointment_confirmed": False,
            "doctor_assigned": None
        }
    }


def save_clinical_payload(payload: dict) -> Path:
    """Save clinical payload as JSON"""
    filename = f"clinical_payload_{payload['conversation_id']}.json"
    filepath = OUTPUT_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    
    if config.VERBOSE_LOGGING:
        print(f"   ✓ JSON saved: {filepath.name}")
    
    return filepath


def generate_pdfs(payload: dict) -> Tuple[Optional[Path], Optional[Path]]:
    """Generate PDF reports"""
    if not config.GENERATE_PDFS:
        return None, None
    
    try:
        from generate_pdf_summary import ClinicalPayload, build_pdf
        
        clinical_payload = ClinicalPayload.from_dict(payload)
        
        doctor_pdf = OUTPUT_DIR / f"doctor_briefing_{payload['conversation_id']}.pdf"
        patient_pdf = OUTPUT_DIR / f"patient_copy_{payload['conversation_id']}.pdf"
        
        build_pdf(clinical_payload, doctor_pdf, audience="doctor")
        build_pdf(clinical_payload, patient_pdf, audience="patient")
        
        if config.VERBOSE_LOGGING:
            print(f"   ✓ Doctor PDF: {doctor_pdf.name}")
            print(f"   ✓ Patient PDF: {patient_pdf.name}")
        
        return doctor_pdf, patient_pdf
        
    except Exception as e:
        print(f"   ⚠ PDF generation error: {e}")
        return None, None


def process_conversation_end(conversation: ConversationManager) -> dict:
    """Process conversation: extract data, save JSON, generate PDFs"""
    print("\n" + "=" * 70)
    print("📋 PROCESSING CONSULTATION DATA")
    print("=" * 70)
    
    # Extract clinical data
    print("\n1️⃣ Extracting clinical data...")
    extracted_data = LLMEngine.extract_clinical_data(conversation)
    print("   ✓ Extraction complete")
    
    # Build payload
    print("\n2️⃣ Building clinical payload...")
    payload = build_clinical_payload(extracted_data)
    print(f"   ✓ Patient ID: {payload['patient_id']}")
    print(f"   ✓ Urgency: {payload['urgency_level']}")
    
    if payload['red_flags']:
        print(f"   ⚠ Red Flags: {', '.join(payload['red_flags'])}")
    
    # Save JSON
    if config.SAVE_JSON:
        print("\n3️⃣ Saving clinical payload...")
        json_path = save_clinical_payload(payload)
    
    # Generate PDFs
    print("\n4️⃣ Generating PDF reports...")
    doctor_pdf, patient_pdf = generate_pdfs(payload)
    
    print("\n" + "=" * 70)
    print("✅ PROCESSING COMPLETE")
    print("=" * 70)
    
    return payload


def check_exit_intent(text: str) -> bool:
    """Check if user wants to exit"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in config.EXIT_KEYWORDS)


def run_voice_agent():
    """Main conversation loop"""
    global recognizer, microphone
    
    # Initialize components
    print("\n🚀 Initializing voice agent...")
    
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    conversation = ConversationManager()
    tts_engine = TTSEngine()
    stt_engine = STTEngine(recognizer, microphone)
    
    print("✓ Components initialized")
    
    # Start conversation
    print("\n" + "=" * 70)
    print("VOICE AGENT READY")
    print("=" * 70)
    print(f"\n💡 Settings:")
    print(f"   • TTS Engine: {config.TTS_ENGINE.upper()}")
    print(f"   • Voice (AR): {config.CARTESIA_VOICE_ARABIC}")
    print(f"   • Voice (EN): {config.CARTESIA_VOICE_ENGLISH}")
    print(f"   • Voice (HI): {config.CARTESIA_VOICE_HINDI}")
    print(f"   • Interrupt Detection: {'ON' if config.ENABLE_INTERRUPT_DETECTION else 'OFF'}")
    print(f"   • Natural Pauses: {'ON' if config.ADD_NATURAL_PAUSES else 'OFF'}")
    print(f"\n💡 Say goodbye to exit\n")
    
    # Greeting
    greeting = "صباح الخير! مرحباً! I'm Mariam from CareBot Clinic. كيف حالك النهاردة؟"
    tts_engine.speak(greeting)
    conversation.add_assistant_message(greeting)
    
    # Main loop
    silence_count = 0
    while not conversation.is_complete():
        # Listen to user
        user_text, lang = stt_engine.listen()
        
        # Handle silence timeout
        if user_text == "__silence__":
            silence_count += 1
            if silence_count == 1:
                tts_engine.speak("هل أنت هناك؟ Are you still there? Take your time.")
            else:
                tts_engine.speak("لم أسمعك. I didn't hear anything — please speak when you're ready.")
                silence_count = 0
            continue
        
        if not user_text:
            continue
        
        silence_count = 0
        print(f"\n👤 Patient: {user_text}")
        
        # Check exit intent
        if check_exit_intent(user_text):
            farewell = "شكراً جداً! Thank you for calling. ربنا يشفيك! Get well soon!"
            tts_engine.speak(farewell)
            break
        
        # Stream LLM response — first sentence spoken the moment it's ready
        LLMEngine.stream_and_speak(conversation, user_text, tts_engine)
    
    # Process conversation end
    print("\n" + "=" * 70)
    print(f"CONVERSATION COMPLETE - {conversation.turn_count} turns")
    print("=" * 70)
    
    payload = process_conversation_end(conversation)
    
    # Summary
    print(f"\n📊 Session Summary:")
    print(f"   • Total turns: {conversation.turn_count}")
    print(f"   • Clinical summary: {payload['clinical_summary'][:100]}...")
    print(f"   • Output directory: {OUTPUT_DIR}")
    print("\n✓ Ready for doctor review\n")


if __name__ == "__main__":
    try:
        print("=" * 70)
        print("PRODUCTION VOICE AGENT")
        print("Optimized • Low Latency • Natural Voice")
        print("=" * 70)
        
        run_voice_agent()
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nSession ended.")
