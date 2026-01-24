"""
Voice Agent Orchestrator - Main System Integration
===================================================

This module ties together all layers into a cohesive voice agent system:
- Layer 1: Voice Infrastructure (STT + TTS)
- Layer 2: Conversational AI (LLM + State Machine)
- Layer 3: Data Extraction (Real-time + Post-conversation)
- Layer 4: Integration (CareBot, EHR, Routing)

System Architecture:
┌─────────────────────────────────────────────────────────────┐
│                    Voice Agent System                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Audio Input → STT → Conversation Manager → LLM → TTS       │
│                         ↓                                    │
│                   Data Extractor                            │
│                         ↓                                    │
│               Patient Data Storage                          │
│                         ↓                                    │
│            Routing Engine → CareBot/EHR                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Scalability Features:
1. Async Processing - Non-blocking operations
2. Queue Management - Handle multiple concurrent conversations
3. Resource Pooling - Shared GPU for STT/TTS
4. Caching - Pre-generated common phrases
5. Fallback Mechanisms - Graceful degradation
"""

import logging
import asyncio
import json
import time
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

from pre_visit_agent.config.config import AppConfig, config
from pre_visit_agent.services.stt_service import RealTimeSTT
from pre_visit_agent.services.tts_service import TTSService
from pre_visit_agent.services.llm_service import LLMService
from pre_visit_agent.core.conversation_manager import ConversationManager
from pre_visit_agent.core.data_extractor import DataExtractor, RoutingEngine, ClinicalSummary

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ConversationSession:
    """
    Represents a single conversation session.
    
    Attributes:
        session_id: Unique session identifier
        patient_id: Patient identifier (optional)
        start_time: Session start timestamp
        conversation_manager: Conversation state manager
        audio_buffer: Buffer for audio chunks
        is_active: Whether session is currently active
    """
    session_id: str
    patient_id: Optional[str]
    start_time: datetime
    conversation_manager: ConversationManager
    audio_buffer: list
    is_active: bool = True
    
    def to_dict(self) -> Dict:
        """Convert session metadata to dictionary"""
        return {
            "session_id": self.session_id,
            "patient_id": self.patient_id,
            "start_time": self.start_time.isoformat(),
            "is_active": self.is_active,
            "turn_count": self.conversation_manager.turn_count
        }


class VoiceAgent:
    """
    Main Voice Agent Orchestrator.
    
    Coordinates all system components to deliver end-to-end
    conversational voice agent functionality.
    
    Features:
    - Real-time speech-to-text transcription
    - Natural conversational AI
    - Text-to-speech synthesis
    - Automatic data extraction
    - Patient routing and triage
    - Integration with external systems
    """
    
    def __init__(self, app_config: Optional[AppConfig] = None):
        """
        Initialize the voice agent system.
        
        Args:
            app_config: Application configuration (uses global if None)
        """
        self.config = app_config or config
        
        logger.info("Initializing Voice Agent System...")
        logger.info(f"Environment: {self.config.environment.value}")
        
        # Validate configuration
        self.config.validate()
        
        # Initialize services
        logger.info("Loading STT service...")
        self.stt = RealTimeSTT(
            model_size=self.config.stt.model_size,
            language=self.config.stt.language,
            dialect_prompt=self.config.stt.dialect_prompt,
            min_duration=self.config.stt.min_duration
        )
        
        logger.info("Loading TTS service...")
        self.tts = TTSService(self.config.tts)
        
        logger.info("Loading LLM service...")
        self.llm = LLMService(self.config.llm)
        
        logger.info("Loading Data Extractor...")
        self.data_extractor = DataExtractor(
            self.llm,
            self.config.extraction_schema
        )
        
        # Session management
        self.active_sessions: Dict[str, ConversationSession] = {}
        self.session_counter = 0
        
        # Callbacks
        self.on_transcription_callback: Optional[Callable] = None
        self.on_response_callback: Optional[Callable] = None
        self.on_session_end_callback: Optional[Callable] = None
        
        logger.info("✓ Voice Agent System initialized successfully")
    
    def start_session(self, patient_id: Optional[str] = None) -> str:
        """
        Start a new conversation session.
        
        Args:
            patient_id: Optional patient identifier
            
        Returns:
            Session ID
            
        Example:
            >>> agent = VoiceAgent()
            >>> session_id = agent.start_session(patient_id="P12345")
            >>> print(f"Session started: {session_id}")
        """
        self.session_counter += 1
        session_id = f"SESSION-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{self.session_counter}"
        
        logger.info(f"Starting session: {session_id}")
        
        # Create conversation manager
        conversation_manager = ConversationManager(
            self.config.conversation,
            self.llm
        )
        
        # Create session
        session = ConversationSession(
            session_id=session_id,
            patient_id=patient_id,
            start_time=datetime.now(),
            conversation_manager=conversation_manager,
            audio_buffer=[]
        )
        
        self.active_sessions[session_id] = session
        
        # Generate greeting
        greeting_text = conversation_manager.start_conversation()
        logger.info(f"Agent: {greeting_text}")
        
        # Synthesize greeting
        greeting_audio = self.tts.synthesize(greeting_text, emotion="professional")
        
        # Trigger callback
        if self.on_response_callback:
            self.on_response_callback(session_id, greeting_text, greeting_audio)
        
        return session_id
    
    def process_audio_chunk(
        self,
        session_id: str,
        audio_chunk: np.ndarray
    ):
        """
        Process incoming audio chunk for transcription.
        
        Args:
            session_id: Active session identifier
            audio_chunk: Audio data (16kHz, mono, float32)
            
        Note:
            Audio is queued for STT processing. Transcription
            happens asynchronously and triggers conversation turn.
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return
        
        # Add to STT queue
        self.stt.add_audio_chunk(audio_chunk)
    
    def on_transcription(self, session_id: str, transcribed_text: str):
        """
        Handle transcribed text from STT.
        
        This is called automatically when STT completes transcription.
        
        Args:
            session_id: Active session identifier
            transcribed_text: Transcribed patient speech
            
        Workflow:
        1. Process conversation turn
        2. Trigger data extraction (if needed)
        3. Generate response
        4. Synthesize speech
        5. Return audio to caller
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return
        
        session = self.active_sessions[session_id]
        conversation_manager = session.conversation_manager
        
        logger.info(f"Patient: {transcribed_text}")
        
        # Trigger callback
        if self.on_transcription_callback:
            self.on_transcription_callback(session_id, transcribed_text)
        
        # Process conversation turn
        response_text = conversation_manager.process_turn(transcribed_text)
        logger.info(f"Agent: {response_text}")
        
        # Real-time data extraction (every N turns)
        if conversation_manager.turn_count % self.config.conversation.extraction_interval == 0:
            logger.debug("Triggering real-time data extraction...")
            extraction_result = self.data_extractor.extract_real_time(
                conversation_manager.conversation_history,
                conversation_manager.patient_data
            )
            
            # Update patient data
            conversation_manager.patient_data = self.data_extractor.update_patient_data(
                conversation_manager.patient_data,
                extraction_result
            )
            
            # Log extraction results
            if extraction_result.needs_clarification:
                logger.info(f"Needs clarification: {extraction_result.needs_clarification}")
            if extraction_result.red_flags:
                logger.warning(f"Red flags detected: {extraction_result.red_flags}")
        
        # Synthesize response
        # Detect emotion based on patient input
        emotion = "empathetic" if any(
            word in transcribed_text.lower() 
            for word in ["ألم", "pain", "hurt", "صعب", "difficult"]
        ) else "neutral"
        
        response_audio = self.tts.synthesize(response_text, emotion=emotion)
        
        # Trigger callback
        if self.on_response_callback:
            self.on_response_callback(session_id, response_text, response_audio)
        
        # Check if conversation should end
        if conversation_manager.is_conversation_complete():
            logger.info("Conversation complete, ending session...")
            self.end_session(session_id)
    
    def end_session(self, session_id: str) -> ClinicalSummary:
        """
        End a conversation session and generate final summary.
        
        Args:
            session_id: Session to end
            
        Returns:
            ClinicalSummary with complete patient data and routing
            
        Workflow:
        1. End conversation gracefully
        2. Perform post-conversation extraction
        3. Generate clinical summary
        4. Determine routing
        5. Save to database/EHR
        6. Notify relevant parties
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        session.is_active = False
        
        conversation_manager = session.conversation_manager
        
        logger.info(f"Ending session: {session_id}")
        
        # Get closing message
        closing_message = conversation_manager.end_conversation()
        closing_audio = self.tts.synthesize(closing_message, emotion="professional")
        
        # Trigger callback for closing message
        if self.on_response_callback:
            self.on_response_callback(session_id, closing_message, closing_audio)
        
        # Get full transcript
        full_transcript = conversation_manager.get_full_transcript()
        
        # Post-conversation extraction
        logger.info("Performing post-conversation extraction...")
        clinical_summary = self.data_extractor.extract_post_conversation(
            full_transcript,
            conversation_manager.conversation_id,
            session.patient_id or "UNKNOWN"
        )
        
        # Determine routing
        routing = RoutingEngine.route_patient(clinical_summary)
        clinical_summary.routing_decision = routing
        
        logger.info(f"Routing: {routing['recommended_specialist']} ({routing['urgency_level']})")
        
        # Save session data
        self._save_session_data(session, clinical_summary, full_transcript)
        
        # Trigger session end callback
        if self.on_session_end_callback:
            self.on_session_end_callback(session_id, clinical_summary)
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        logger.info(f"Session {session_id} ended successfully")
        
        return clinical_summary
    
    def _save_session_data(
        self,
        session: ConversationSession,
        clinical_summary: ClinicalSummary,
        transcript: str
    ):
        """
        Save session data to storage.
        
        Args:
            session: Conversation session
            clinical_summary: Clinical summary
            transcript: Full conversation transcript
            
        Note:
            In production, this would save to database/EHR.
            For now, saves to local JSON files.
        """
        # Create sessions directory
        sessions_dir = Path(self.config.data_dir) / "sessions"
        sessions_dir.mkdir(exist_ok=True, parents=True)
        
        session_file = sessions_dir / f"{session.session_id}.json"
        
        # Prepare session data
        session_data = {
            "session_metadata": session.to_dict(),
            "clinical_summary": clinical_summary.to_dict(),
            "conversation_summary": session.conversation_manager.get_conversation_summary(),
            "full_transcript": transcript,
            "saved_at": datetime.now().isoformat()
        }
        
        # Save to file
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Session data saved to: {session_file}")
    
    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """
        Get current session status.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session status dictionary or None if not found
        """
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        summary = session.conversation_manager.get_conversation_summary()
        
        return {
            "session_id": session_id,
            "patient_id": session.patient_id,
            "is_active": session.is_active,
            "turn_count": session.conversation_manager.turn_count,
            "state": session.conversation_manager.state.value,
            "completion_percentage": summary["completion_percentage"],
            "missing_fields": summary["missing_fields"]
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system-wide statistics.
        
        Returns:
            Dictionary with system metrics
        """
        return {
            "active_sessions": len(self.active_sessions),
            "total_sessions": self.session_counter,
            "llm_stats": self.llm.get_usage_stats(),
            "tts_cache_stats": self.tts.get_cache_stats(),
            "environment": self.config.environment.value
        }
    
    def shutdown(self):
        """
        Gracefully shutdown the voice agent system.
        
        Closes all active sessions and releases resources.
        """
        logger.info("Shutting down Voice Agent System...")
        
        # End all active sessions
        for session_id in list(self.active_sessions.keys()):
            try:
                self.end_session(session_id)
            except Exception as e:
                logger.error(f"Error ending session {session_id}: {e}")
        
        # Stop STT service
        self.stt.stop()
        
        logger.info("✓ Voice Agent System shutdown complete")


# Example usage
if __name__ == "__main__":
    print("Voice Agent System - Example Usage")
    print("=" * 50)
    
    # Initialize system
    agent = VoiceAgent()
    
    # Define callbacks
    def on_transcription(session_id, text):
        print(f"\n[Transcription] Patient: {text}")
    
    def on_response(session_id, text, audio):
        print(f"[Response] Agent: {text}")
        print(f"[Audio] Generated {len(audio)} samples")
    
    def on_session_end(session_id, summary):
        print(f"\n[Session End] {session_id}")
        print(f"Urgency: {summary.urgency_level}")
        print(f"Specialist: {summary.recommended_specialist}")
        print(f"\nClinical Summary:")
        print(summary.clinical_summary)
    
    # Register callbacks
    agent.on_transcription_callback = on_transcription
    agent.on_response_callback = on_response
    agent.on_session_end_callback = on_session_end
    
    # Start session
    session_id = agent.start_session(patient_id="P12345")
    
    # Simulate conversation (in real use, audio comes from microphone/phone)
    print("\n" + "=" * 50)
    print("Simulating conversation...")
    print("=" * 50)
    
    test_inputs = [
        "عندي ألم في ضرسي",
        "من ٣ أيام تقريباً",
        "ألم شديد، ٨ من ١٠",
        "الضرس الأيمن العلوي",
        "بياكلني لما أشرب ساخن أو أمضغ",
        "باخد بروفين بس مش بيساعد كتير",
        "عندي حساسية من البنسلين",
        "عندي سكر من النوع التاني"
    ]
    
    for user_input in test_inputs:
        # In real implementation, this would be transcribed from audio
        agent.on_transcription(session_id, user_input)
        time.sleep(0.5)  # Simulate natural conversation pace
    
    # Get session status
    print("\n" + "=" * 50)
    print("Session Status:")
    print("=" * 50)
    status = agent.get_session_status(session_id)
    print(json.dumps(status, indent=2, ensure_ascii=False))
    
    # End session (if not already ended)
    if status and status["is_active"]:
        summary = agent.end_session(session_id)
    
    # System stats
    print("\n" + "=" * 50)
    print("System Statistics:")
    print("=" * 50)
    stats = agent.get_system_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # Shutdown
    agent.shutdown()
