"""Audio processing utilities for web-based STT/TTS"""

import os
import tempfile
import logging
from typing import Optional, Tuple
from io import BytesIO

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    from cartesia import Cartesia
    CARTESIA_AVAILABLE = True
except ImportError:
    CARTESIA_AVAILABLE = False

import config

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles audio transcription and synthesis for web interface"""
    
    def __init__(self, cartesia_client: Optional[Cartesia] = None):
        """
        Initialize audio processor
        
        Args:
            cartesia_client: Cartesia client for TTS
        """
        self.cartesia_client = cartesia_client
        self.recognizer = sr.Recognizer() if SPEECH_RECOGNITION_AVAILABLE else None
    
    def transcribe_audio(self, audio_file_path: str, language: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Transcribe audio file to text using Google Speech Recognition
        
        Args:
            audio_file_path: Path to audio file (WAV, FLAC, etc.)
            language: Language code ('en', 'hi', 'kn') - if None, tries to auto-detect
        
        Returns:
            Tuple of (text, detected_language) or (None, None) if error
        """
        if not SPEECH_RECOGNITION_AVAILABLE:
            logger.error("speech_recognition library not available")
            return None, None
        
        if not self.recognizer:
            logger.error("Recognizer not initialized")
            return None, None
        
        try:
            # Load audio file
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
            
            # Try specified language first if provided
            if language == "hi":
                try:
                    text = self.recognizer.recognize_google(audio, language="hi-IN")
                    return text, "hi"
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    logger.error(f"Google STT service error: {e}")
                    return None, None
            
            elif language == "kn":
                try:
                    text = self.recognizer.recognize_google(audio, language="kn-IN")
                    return text, "kn"
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    logger.error(f"Google STT service error: {e}")
                    return None, None
            
            # Try English
            try:
                text = self.recognizer.recognize_google(audio, language="en-US")
                return text, "en"
            except sr.UnknownValueError:
                pass
            
            # Try Hindi
            try:
                text = self.recognizer.recognize_google(audio, language="hi-IN")
                return text, "hi"
            except sr.UnknownValueError:
                pass
            
            # Try Kannada
            try:
                text = self.recognizer.recognize_google(audio, language="kn-IN")
                return text, "kn"
            except sr.UnknownValueError:
                logger.warning("Could not understand audio in any language")
                return None, None
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None, None
    
    def synthesize_speech(self, text: str, language: Optional[str] = None) -> Optional[bytes]:
        """
        Synthesize text to speech using Cartesia TTS
        
        Args:
            text: Text to synthesize
            language: Language code ('en', 'hi', 'kn')
        
        Returns:
            Audio bytes (WAV format) or None if error
        """
        if not self.cartesia_client:
            logger.error("Cartesia client not initialized")
            return None
        
        try:
            # Determine language
            language = language or config.detect_tts_language(text)
            voice_id = config.get_cartesia_voice_id(language)
            
            # Generate audio
            audio_bytes = BytesIO()
            output_format = config.CARTESIA_OUTPUT_FORMAT
            
            bytes_iter = self.cartesia_client.tts.bytes(
                model_id=config.CARTESIA_MODEL,
                transcript=text,
                voice={
                    "mode": "id",
                    "id": voice_id,
                },
                language=language,
                output_format=output_format,
            )
            
            for chunk in bytes_iter:
                audio_bytes.write(chunk)
            
            return audio_bytes.getvalue()
        
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return None


def save_uploaded_audio(file_obj) -> Optional[str]:
    """
    Save uploaded audio file to temporary location
    
    Args:
        file_obj: File object from request.files
    
    Returns:
        Path to saved file or None if error
    """
    try:
        # Create temporary file with appropriate extension
        suffix = ".wav"
        if hasattr(file_obj, 'filename'):
            name = file_obj.filename.lower()
            if '.mp3' in name:
                suffix = ".mp3"
            elif '.flac' in name:
                suffix = ".flac"
            elif '.ogg' in name:
                suffix = ".ogg"
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        file_obj.save(temp_file.name)
        return temp_file.name
    
    except Exception as e:
        logger.error(f"Error saving audio file: {e}")
        return None


def cleanup_audio_file(file_path: str) -> bool:
    """Delete temporary audio file"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
        return True
    except Exception as e:
        logger.warning(f"Error cleaning up audio file: {e}")
        return False
