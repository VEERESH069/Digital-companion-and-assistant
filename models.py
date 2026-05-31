"""
SQLAlchemy database models for storing conversation sessions and data
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import json
import uuid

from sqlalchemy import Column, String, Text, DateTime, JSON, Float, Boolean, Integer, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ConversationSession(Base):
    """Stores conversation session metadata and status"""
    
    __tablename__ = "conversation_sessions"
    
    # Primary identifiers
    session_id = Column(String(50), primary_key=True, default=lambda: f"SESS-{uuid.uuid4().hex[:12].upper()}")
    conversation_id = Column(String(100), unique=True, nullable=False)
    patient_id = Column(String(50), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime, nullable=True)
    
    # Session metadata
    language = Column(String(10), default="en")  # ar, en, hi
    status = Column(String(20), default="active")  # active, completed, abandoned
    turn_count = Column(Integer, default=0)
    
    # Relationship
    messages = relationship("ConversationMessage", back_populates="session", cascade="all, delete-orphan")
    clinical_data = relationship("ClinicalData", uselist=False, back_populates="session", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        return {
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "patient_id": self.patient_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "language": self.language,
            "status": self.status,
            "turn_count": self.turn_count,
        }


class ConversationMessage(Base):
    """Stores individual messages in a conversation"""
    
    __tablename__ = "conversation_messages"
    
    # Primary key
    message_id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key
    session_id = Column(String(50), ForeignKey("conversation_sessions.session_id"), nullable=False, index=True)
    
    # Message content
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Metadata
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    turn_number = Column(Integer, nullable=False)
    
    # Optional: STT/TTS metadata
    confidence = Column(Float, nullable=True)  # Speech recognition confidence
    is_interrupted = Column(Boolean, default=False)
    
    # Relationship
    session = relationship("ConversationSession", back_populates="messages")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        return {
            "message_id": self.message_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "turn_number": self.turn_number,
            "confidence": self.confidence,
            "is_interrupted": self.is_interrupted,
        }


class ClinicalData(Base):
    """Stores extracted clinical information from conversation"""
    
    __tablename__ = "clinical_data"
    
    # Primary key
    clinical_data_id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key
    session_id = Column(String(50), ForeignKey("conversation_sessions.session_id"), unique=True, nullable=False)
    
    # Clinical information (JSON flexible storage)
    chief_complaint = Column(Text, nullable=True)
    duration = Column(String(100), nullable=True)
    pain_severity = Column(Integer, nullable=True)  # 0-10 scale
    location = Column(String(255), nullable=True)
    triggers = Column(JSON, nullable=True)  # List of triggers
    
    # Medical history
    current_medications = Column(JSON, nullable=True)  # List of medications
    allergies = Column(JSON, nullable=True)  # List of allergies
    medical_conditions = Column(JSON, nullable=True)  # List of conditions
    
    # Extracted structured data
    clinical_summary = Column(Text, nullable=True)
    red_flags = Column(JSON, nullable=True)  # List of red flags
    
    # Assessment
    urgency_level = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    recommended_specialist = Column(String(100), nullable=True)
    confidence_scores = Column(JSON, nullable=True)  # Dict of confidence scores
    
    # Routing
    needs_triage = Column(Boolean, default=False)
    pre_scheduled = Column(Boolean, default=True)
    appointment_confirmed = Column(Boolean, default=False)
    doctor_assigned = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship
    session = relationship("ConversationSession", back_populates="clinical_data")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        return {
            "clinical_data_id": self.clinical_data_id,
            "session_id": self.session_id,
            "chief_complaint": self.chief_complaint,
            "duration": self.duration,
            "pain_severity": self.pain_severity,
            "location": self.location,
            "triggers": self.triggers,
            "current_medications": self.current_medications,
            "allergies": self.allergies,
            "medical_conditions": self.medical_conditions,
            "clinical_summary": self.clinical_summary,
            "red_flags": self.red_flags,
            "urgency_level": self.urgency_level,
            "recommended_specialist": self.recommended_specialist,
            "confidence_scores": self.confidence_scores,
            "needs_triage": self.needs_triage,
            "appointment_confirmed": self.appointment_confirmed,
            "doctor_assigned": self.doctor_assigned,
        }


class AuditLog(Base):
    """Logs all API access for security and compliance"""
    
    __tablename__ = "audit_logs"
    
    # Primary key
    log_id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Request info
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE
    
    # Session info
    session_id = Column(String(50), nullable=True, index=True)
    patient_id = Column(String(50), nullable=True, index=True)
    
    # User/Authentication
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Response
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    
    # Error info
    error_message = Column(Text, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        return {
            "log_id": self.log_id,
            "timestamp": self.timestamp.isoformat(),
            "endpoint": self.endpoint,
            "method": self.method,
            "session_id": self.session_id,
            "patient_id": self.patient_id,
            "status_code": self.status_code,
            "response_time_ms": self.response_time_ms,
            "error_message": self.error_message,
        }
