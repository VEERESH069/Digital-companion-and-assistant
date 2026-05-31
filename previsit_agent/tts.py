"""Text-to-speech module using Cartesia TTS with PyAudio streaming"""

import os
import sys
import tempfile
import threading
import time
import queue
import pyaudio
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timezone

try:
    from cartesia import Cartesia
    CARTESIA_AVAILABLE = True
except ImportError:
    CARTESIA_AVAILABLE = False

import config

# Global Cartesia client (initialized from main)
cartesia_client = None


def init_cartesia_client(client):
    """Initialize global Cartesia client"""
    global cartesia_client
    cartesia_client = client


def speak(text: str, lang: Optional[str] = None):
    """
    Speak text using Cartesia TTS (simple version for voice_agent.py)
    
    Args:
        text: Text to speak
        lang: Language code ('ar' for Arabic, 'en' for English) - if provided, uses this explicitly;
              otherwise auto-detects from text content
    """
    try:
        print(f"\n🔊 Agent: {text}")

        if cartesia_client is None:
            print("   ✗ Cartesia client is not initialized")
            return False
        
        # Use provided language or auto-detect from text
        language = lang if lang else config.detect_tts_language(text)
        voice_id = config.get_cartesia_voice_id(language)
        
        # Generate speech using Cartesia
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = temp_file.name
        temp_file.close()
        
        with open(temp_path, "wb") as f:
            output_format = config.CARTESIA_OUTPUT_FORMAT
            
            bytes_iter = cartesia_client.tts.bytes(
                model_id=config.CARTESIA_MODEL,
                transcript=text,
                voice={
                    "mode": "id",
                    "id": voice_id,
                },
                language=language,
                output_format=output_format,  # type: ignore
            )
            
            for chunk in bytes_iter:
                f.write(chunk)
        
        # Play audio using pygame
        import pygame
        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.play()
        
        # Wait for playback
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        # Cleanup
        try:
            pygame.mixer.music.unload()
            os.unlink(temp_path)
        except:
            pass
            
        return True
    except Exception as e:
        print(f"   ✗ Speech error: {e}")
        return False


class TTSEngine:
    """TTS Engine — streams raw PCM directly via PyAudio for minimum latency"""

    SAMPLE_RATE = int(config.CARTESIA_OUTPUT_FORMAT.get("sample_rate", 44100))
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

    def _write_silence(self, stream: Any, duration_seconds: float):
        """Write a short block of silence to avoid abrupt audio cutoffs."""
        if stream is None or duration_seconds <= 0:
            return
        frame_count = max(1, int(self.SAMPLE_RATE * duration_seconds))
        silence = b"\x00\x00" * frame_count
        self._write_audio_chunk(stream, silence)

    @staticmethod
    def _write_audio_chunk(stream: Any, chunk: bytes) -> bool:
        """Write PCM to the output stream without letting device errors crash the app."""
        if stream is None:
            return False
        try:
            stream.write(chunk)
            return True
        except OSError as exc:
            print(f"   ⚠ Audio playback interrupted: {exc}")
            return False
        except Exception as exc:
            print(f"   ⚠ Audio playback failed: {exc}")
            return False

    @staticmethod
    def _flush_output_stream(stream: Any):
        """Give the audio backend time to drain buffered PCM before closing."""
        if stream is None:
            return
        try:
            latency = float(stream.get_output_latency())
        except Exception:
            latency = 0.0
        if latency > 0:
            time.sleep(min(max(latency, 0.05), 0.5))

    @staticmethod
    def _iter_cartesia_sse(**kwargs: Any):
        """Use the current Cartesia streaming API while remaining compatible with older SDKs."""
        tts_api = cartesia_client.tts  # type: ignore[union-attr]
        if hasattr(tts_api, "generate_sse"):
            return tts_api.generate_sse(**kwargs)
        return tts_api.sse(**kwargs)

    def _monitor_interrupt(self, interrupt_requested: threading.Event, playback_done: threading.Event):
        """Background monitor: raises interrupt_requested when user speech is detected."""
        mon: Optional[pyaudio.PyAudio] = None
        stream: Any = None
        warmup_ms = int(getattr(config, "INTERRUPT_WARMUP_MS", 250))
        consecutive_required = int(getattr(config, "INTERRUPT_CONSECUTIVE_FRAMES", 2))
        baseline_multiplier = float(getattr(config, "INTERRUPT_BASELINE_MULTIPLIER", 2.2))
        peak_threshold = int(getattr(config, "INTERRUPT_PEAK_THRESHOLD", 2600))
        warmup_seconds = max(0, warmup_ms) / 1000.0
        start_time = time.monotonic()
        high_frames = 0
        warmup_rms_values: List[float] = []

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

                    peak = max(abs(sample) for sample in samples)
                    rms = (sum(s * s for s in samples) / len(samples)) ** 0.5

                    # Ignore early speaker bleed right after playback begins.
                    if (time.monotonic() - start_time) < warmup_seconds:
                        warmup_rms_values.append(rms)
                        continue

                    ambient_rms = max(warmup_rms_values) if warmup_rms_values else 0.0
                    adaptive_threshold = max(
                        float(config.INTERRUPT_ENERGY_THRESHOLD),
                        ambient_rms * baseline_multiplier,
                    )

                    if rms > adaptive_threshold and peak > peak_threshold:
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

    def speak_cartesia(
        self,
        text: str,
        language_code: Optional[str] = None,
        allow_interrupt: bool = True,
    ) -> bool:
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
            language = config.normalize_language_code(language_code) if language_code else config.detect_tts_language(text)
            voice_id = config.get_cartesia_voice_id(language)
            cache_key = f"{text}_{language}_{voice_id}"

            out = self._pa.open(
                format=pyaudio.paInt16, channels=self.CHANNELS,
                rate=self.SAMPLE_RATE, output=True, frames_per_buffer=self.CHUNK
            )
            if config.ENABLE_INTERRUPT_DETECTION and allow_interrupt:
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
                    if not self._write_audio_chunk(out, pcm[i:i + self.CHUNK * 2]):
                        interrupted = True
                        break
            else:
                # --- Live stream via SSE: pipe chunks straight to speakers ---
                from cartesia.types.sse_events import ChunkEvent  # type: ignore
                pcm_buffer = b""
                interrupted = False
                for event in self._iter_cartesia_sse(
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
                        if not self._write_audio_chunk(out, event.audio):
                            interrupted = True
                            break
                        if config.ENABLE_TTS_CACHING:
                            pcm_buffer += event.audio

                if not interrupted and config.ENABLE_TTS_CACHING and pcm_buffer:
                    self.cache[cache_key] = pcm_buffer

            interrupted = interrupt_requested.is_set()

            if not interrupted:
                self._write_silence(out, float(getattr(config, "TTS_TAIL_SILENCE_SEC", 0.2)))

            if interrupted:
                print("   ✋ User interrupted — listening...")
                return False
            return True

        except Exception as e:
            print(f"   ✗ Cartesia TTS error: {e}")
            return False
        finally:
            playback_done.set()
            self._flush_output_stream(out)
            self._safe_stop_close_stream(out)
            if interrupt_thread is not None:
                interrupt_thread.join(timeout=0.3)

    def speak(
        self,
        text: str,
        language_code: Optional[str] = None,
        allow_interrupt: bool = True,
    ) -> bool:
        print(f"\n🔊 Agent: {text}")
        return self.speak_cartesia(text, language_code=language_code, allow_interrupt=allow_interrupt)

    def _fetch_pcm_to_queue(self, text: str, pcm_q: 'queue.Queue[Any]') -> None:
        """Fetch Cartesia SSE audio for `text` and push raw PCM chunks into pcm_q."""
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
            for event in self._iter_cartesia_sse(
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
        """Continuously play PCM chunks from pcm_q until None sentinel."""
        delivered_sentences: List[str] = []
        out: Any = None
        interrupt_thread: Optional[threading.Thread] = None
        interrupt_requested = threading.Event()
        playback_done = threading.Event()

        interrupted = False
        playback_failed = False
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
                        if config.ADD_NATURAL_PAUSES:
                            pause_duration = float(getattr(config, "PAUSE_AFTER_SENTENCE", 0.3))
                            if delivered_text.endswith("?") or delivered_text.endswith("؟"):
                                pause_duration = float(getattr(config, "PAUSE_AFTER_QUESTION", 0.5))
                            self._write_silence(out, pause_duration)
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
                if not isinstance(chunk, (bytes, bytearray)):
                    continue
                if not self._write_audio_chunk(out, bytes(chunk)):
                    playback_failed = True
                    break

            if not interrupted and not playback_failed:
                self._write_silence(out, float(getattr(config, "TTS_TAIL_SILENCE_SEC", 0.2)))
        finally:
            playback_done.set()
            self._flush_output_stream(out)
            self._safe_stop_close_stream(out)
            if interrupt_thread is not None:
                interrupt_thread.join(timeout=0.3)

        if interrupted:
            print("   ✋ User interrupted — listening...")
        elif playback_failed:
            print("   ⚠ Audio output stream closed unexpectedly.")
        return interrupted, delivered_sentences
