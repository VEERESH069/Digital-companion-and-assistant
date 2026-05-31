"""
Database initialization and session management
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from models import (
    Base,
    ConversationSession,
    ConversationMessage,
    ClinicalData,
    AuditLog,
)

logger = logging.getLogger(__name__)


class Database:
    """Database management class for handling all DB operations"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database connection
        
        Args:
            database_url: Database URL. If None, uses environment variable or SQLite fallback
        """
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL",
                "sqlite:///./conversations.db"  # Fallback to SQLite for development
            )
        
        self.database_url = database_url
        
        # Create engine with appropriate settings
        if "sqlite" in database_url:
            # SQLite settings
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            # PostgreSQL or other databases
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,   # Recycle connections every hour
            )
        
        # Create all tables
        Base.metadata.create_all(bind=self.engine)
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        
        logger.info(f"Database initialized: {database_url.split('@')[-1] if '@' in database_url else 'SQLite'}")
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    # ========== CONVERSATION SESSION OPERATIONS ==========
    
    def create_session(
        self,
        patient_id: str,
        language: str = "en",
    ) -> ConversationSession:
        """Create a new conversation session"""
        db = self.get_session()
        try:
            from datetime import datetime as dt
            import uuid
            
            conversation_id = f"CONV-{dt.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            session = ConversationSession(
                patient_id=patient_id,
                conversation_id=conversation_id,
                language=language,
                status="active",
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            logger.info(f"Created session: {session.session_id} for patient: {patient_id}")
            return session
        finally:
            db.close()
    
    def get_session_by_id(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve a session by ID"""
        db = self.get_session()
        try:
            return db.query(ConversationSession).filter(
                ConversationSession.session_id == session_id
            ).first()
        finally:
            db.close()
    
    def get_sessions_by_patient(self, patient_id: str, limit: int = 10) -> List[ConversationSession]:
        """Get all sessions for a patient"""
        db = self.get_session()
        try:
            return db.query(ConversationSession).filter(
                ConversationSession.patient_id == patient_id
            ).order_by(desc(ConversationSession.created_at)).limit(limit).all()
        finally:
            db.close()
    
    def end_session(self, session_id: str, status: str = "completed") -> Optional[ConversationSession]:
        """End a conversation session"""
        db = self.get_session()
        try:
            session = db.query(ConversationSession).filter(
                ConversationSession.session_id == session_id
            ).first()
            
            if session:
                session.status = status
                session.ended_at = datetime.now(timezone.utc)
                db.commit()
                logger.info(f"Ended session: {session_id}")
                return session
            return None
        finally:
            db.close()
    
    # ========== MESSAGE OPERATIONS ==========
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        turn_number: int,
        confidence: Optional[float] = None,
    ) -> ConversationMessage:
        """Add a message to a conversation"""
        db = self.get_session()
        try:
            message = ConversationMessage(
                session_id=session_id,
                role=role,
                content=content,
                turn_number=turn_number,
                confidence=confidence,
            )
            
            db.add(message)
            
            # Update session turn count and updated_at
            session = db.query(ConversationSession).filter(
                ConversationSession.session_id == session_id
            ).first()
            if session:
                session.turn_count = turn_number
                session.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            db.refresh(message)
            logger.debug(f"Added message to session {session_id}: turn {turn_number}")
            return message
        finally:
            db.close()
    
    def get_messages(self, session_id: str) -> List[ConversationMessage]:
        """Get all messages for a session"""
        db = self.get_session()
        try:
            return db.query(ConversationMessage).filter(
                ConversationMessage.session_id == session_id
            ).order_by(ConversationMessage.turn_number).all()
        finally:
            db.close()
    
    # ========== CLINICAL DATA OPERATIONS ==========
    
    def save_clinical_data(
        self,
        session_id: str,
        clinical_info: Dict[str, Any],
    ) -> ClinicalData:
        """Save extracted clinical data for a session"""
        db = self.get_session()
        try:
            # Check if clinical data exists for this session
            clinical_data = db.query(ClinicalData).filter(
                ClinicalData.session_id == session_id
            ).first()
            
            if clinical_data:
                # Update existing
                for key, value in clinical_info.items():
                    if hasattr(clinical_data, key):
                        setattr(clinical_data, key, value)
            else:
                # Create new
                clinical_data = ClinicalData(
                    session_id=session_id,
                    **clinical_info
                )
                db.add(clinical_data)
            
            db.commit()
            db.refresh(clinical_data)
            logger.info(f"Saved clinical data for session: {session_id}")
            return clinical_data
        finally:
            db.close()
    
    def get_clinical_data(self, session_id: str) -> Optional[ClinicalData]:
        """Get clinical data for a session"""
        db = self.get_session()
        try:
            return db.query(ClinicalData).filter(
                ClinicalData.session_id == session_id
            ).first()
        finally:
            db.close()
    
    # ========== EXPORT OPERATIONS ==========
    
    def export_session_as_json(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export complete session as JSON"""
        db = self.get_session()
        try:
            session = db.query(ConversationSession).filter(
                ConversationSession.session_id == session_id
            ).first()
            
            if not session:
                return None
            
            messages = db.query(ConversationMessage).filter(
                ConversationMessage.session_id == session_id
            ).order_by(ConversationMessage.turn_number).all()
            
            clinical = db.query(ClinicalData).filter(
                ClinicalData.session_id == session_id
            ).first()
            
            return {
                "session": session.to_dict(),
                "conversation_history": [m.to_dict() for m in messages],
                "clinical_data": clinical.to_dict() if clinical else None,
            }
        finally:
            db.close()
    
    # ========== AUDIT LOG OPERATIONS ==========
    
    def log_api_access(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        session_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Log API access for security audit"""
        db = self.get_session()
        try:
            log = AuditLog(
                endpoint=endpoint,
                method=method,
                session_id=session_id,
                patient_id=patient_id,
                status_code=status_code,
                response_time_ms=response_time_ms,
                error_message=error_message,
                ip_address=ip_address,
            )
            
            db.add(log)
            db.commit()
            return log
        finally:
            db.close()
    
    # ========== HEALTH & MAINTENANCE ==========
    
    def health_check(self) -> bool:
        """Check if database is accessible"""
        try:
            db = self.get_session()
            db.execute("SELECT 1")
            db.close()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def clear_abandoned_sessions(self, hours: int = 24) -> int:
        """Clear sessions that ended more than X hours ago"""
        from datetime import timedelta
        
        db = self.get_session()
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            deleted = db.query(ConversationSession).filter(
                ConversationSession.status == "abandoned",
                ConversationSession.ended_at < cutoff_time,
            ).delete()
            
            db.commit()
            logger.info(f"Cleared {deleted} abandoned sessions")
            return deleted
        finally:
            db.close()


# Global database instance
_db: Optional[Database] = None


def init_db(database_url: Optional[str] = None) -> Database:
    """Initialize global database instance"""
    global _db
    _db = Database(database_url)
    return _db


def get_db() -> Database:
    """Get global database instance"""
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db
