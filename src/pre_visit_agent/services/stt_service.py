import torch
import numpy as np
import whisper
import queue
import threading
import time
from typing import Optional, Callable
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealTimeSTT:
    def __init__(self, model_size="medium", language="ar", dialect_prompt=None, min_duration=1.0):
        """
        Initialize the Real-Time Speech-to-Text Engine.
        
        Args:
            model_size (str): Whisper model size ('tiny', 'base', 'small', 'medium', 'large-v2').
            language (str): Language code ('ar', 'en', or None for auto-detect).
            dialect_prompt (str): Initial prompt to guide the model. If None, defaults based on language.
            min_duration (float): Minimum audio duration (in seconds) to accumulate before transcribing.
        """
        self.language = language
        
        # Smart prompt selection
        if dialect_prompt is None:
            if language == "ar":
                self.initial_prompt = "This is a conversation in Egyptian Arabic."
            elif language == "en":
                self.initial_prompt = "The following is a conversation in English."
            else:
                self.initial_prompt = None
        else:
            self.initial_prompt = dialect_prompt

        self.min_duration = min_duration
        self.sample_rate = 16000
        self.audio_queue = queue.Queue()
        self.is_running = False
        
        # Hardware configuration
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.fp16 = self.device == "cuda"  # FP16 is only for CUDA
        
        logger.info(f"Loading Whisper model '{model_size}' on {self.device} (FP16: {self.fp16})")
        logger.info(f"Note: First-time download may take several minutes depending on model size...")
        logger.info(f"Model sizes: tiny=39MB, base=74MB, small=244MB, medium=769MB, large=1550MB")
        
        try:
            self.model = whisper.load_model(model_size, device=self.device)
            logger.info("✓ Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
        
        # Validation: Check for FFmpeg if we intend to load files (though we use chunks primarily)
        # This is a good health check for the environment.
        if self._check_ffmpeg():
            logger.info("FFmpeg is available.")
        else:
            logger.warning("FFmpeg NOT found. File loading will fail, but raw audio chunks (numpy) will work.")

    def _check_ffmpeg(self):
        """Check if ffmpeg is installed and accessible."""
        import subprocess
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    def process_queue(self, callback: Callable[[str], None]):
        """
        Worker function to process audio chunks from the queue.
        Uses a buffer to accumulate minimal context before running inference.
        
        Args:
            callback (function): Function to call with the transcribed text.
        """
        logger.info("Starting processing loop...")
        audio_buffer = []
        current_buffer_duration = 0.0

        while self.is_running:
            try:
                # Wait for next chunk (timeout allows checking is_running)
                # If we have data in buffer but queue is empty, we wait a bit then process what we have
                timeout = 0.5 if current_buffer_duration > 0 else 1.0
                audio_data = self.audio_queue.get(timeout=timeout)
                
                # Check for "poison pill" to stop
                if audio_data is None:
                    break
                
                # Add to buffer
                audio_buffer.append(audio_data)
                chunk_duration = len(audio_data) / self.sample_rate
                current_buffer_duration += chunk_duration
                
                # If we haven't reached min_duration, continue collecting
                if current_buffer_duration < self.min_duration:
                    self.audio_queue.task_done()
                    continue

                # Prepare the batch
                full_audio = np.concatenate(audio_buffer)
                audio_buffer = []  # Reset buffer
                current_buffer_duration = 0.0
                self.audio_queue.task_done()

                # Transcribe
                text = self._transcribe_chunk(full_audio)
                if text.strip():
                    callback(text)
                
            except queue.Empty:
                # If buffer has residual data (e.g. end of sentence), transcribe it now
                if audio_buffer:
                    full_audio = np.concatenate(audio_buffer)
                    audio_buffer = []
                    current_buffer_duration = 0.0
                    
                    text = self._transcribe_chunk(full_audio)
                    if text.strip():
                        callback(text)
                continue
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")

    def _transcribe_chunk(self, audio_np: np.ndarray) -> str:
        """
        Transcribe a single numpy array of audio.
        """
        # Ensure audio is float32 and normalized (Whisper expects this)
        if audio_np.dtype != np.float32:
            audio_np = audio_np.astype(np.float32)

        # Pad or trim to fit Whisper's expectations if necessary
        # Whisper expects 30s. inputting shorter audio is fine, it pads internally.
        
        # Explicit specific decoding options for streaming
        # condition_on_previous_text=False: We are processing chunks independently for now (stateless)
        # to avoid hallucinations based on empty/missing context.
        result = self.model.transcribe(
            audio_np, 
            language=self.language,
            fp16=self.fp16,
            initial_prompt=self.initial_prompt,
            condition_on_previous_text=False,
            no_speech_threshold=0.6,  # Enabled: Ignore non-speech audio
            logprob_threshold=-0.8,   # Enabled: Filter low-confidence transcriptions
            compression_ratio_threshold=2.4,  # Filter repetitive/corrupted output
        )
        # Extract text from result (handle both dict and direct string)
        text = result['text'] if isinstance(result, dict) else result
        text_str = str(text).strip() if text else ""
        
        # Additional filtering: Remove common false transcriptions
        filter_patterns = [
            "The following is a conversation in",
            "Thank you for watching",
            "Subscribe",
            "Like and subscribe",
            "Transcribed by",
            "www.",
            "http",
        ]
        
        for pattern in filter_patterns:
            if pattern.lower() in text_str.lower():
                logger.debug(f"Filtered out false transcription: {text_str[:50]}")
                return ""
        
        return text_str

    def start(self, callback: Callable[[str], None]):
        """Start the background processing thread."""
        self.is_running = True
        self.thread = threading.Thread(target=self.process_queue, args=(callback,))
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop the processing thread."""
        self.is_running = False
        self.audio_queue.put(None) # Signal thread to stop
        if self.thread:
            self.thread.join()
        logger.info("STT Service stopped.")

    def add_audio_chunk(self, audio_chunk: np.ndarray):
        """
        Add an audio chunk to the processing queue.
        
        Args:
            audio_chunk (np.ndarray): Audio data in 16kHz mono float32.
        """
        self.audio_queue.put(audio_chunk)

# --- Example Usage Logic ---
if __name__ == "__main__":
    # This block simulates how you would run this.
    
    print("Initializing STT Service...")
    stt = RealTimeSTT(model_size="base") # Using base for quick test, use 'medium' on T4

    def on_transcription(text):
        print(f"Transcript: {text}")

    stt.start(on_transcription)

    try:
        # Simulate incoming audio frames (silence/noise in this dummy example)
        # In production, this comes from your websocket or microphone
        print("Simulating audio stream (Ctrl+C to stop)...")
        for _ in range(5):
            # Create 2 seconds of dummy audio (16kHz)
            dummy_audio = np.random.uniform(-0.2, 0.2, 16000 * 2).astype(np.float32)
            stt.add_audio_chunk(dummy_audio)
            time.sleep(2) # Simulate real-time gap
            
    except KeyboardInterrupt:
        pass
    finally:
        stt.stop()
