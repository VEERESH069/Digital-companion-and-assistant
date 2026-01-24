"""
Pre-Visit Voice Agent
====================

A real-time voice agent for conducting pre-visit patient interviews
in Egyptian Arabic, collecting medical data for dental appointments.

System Components:
- STT: Whisper-based speech-to-text
- TTS: Coqui XTTS v2 voice synthesis
- LLM: GPT-4o mini conversational AI
- Data Extraction: Real-time and post-call analysis
"""

__version__ = "1.0.0"
__author__ = "EnsanAI"

from .core.conversation_manager import ConversationManager
from .core.data_extractor import DataExtractor
from .services.stt_service import RealTimeSTT
from .services.tts_service import TTSService
from .services.llm_service import LLMService

__all__ = [
    "ConversationManager",
    "DataExtractor",
    "RealTimeSTT",
    "TTSService",
    "LLMService",
]
