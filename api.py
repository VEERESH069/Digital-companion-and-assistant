"""
Flask API server for Pre-Visit Voice Agent
Handles REST endpoints for voice agent sessions and conversation management
"""

import os
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from functools import wraps
from io import BytesIO

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize database
from database import init_db, get_db
from models import ConversationSession, ClinicalData

# Initialize voice agent modules
from previsit_agent import LLMEngine, init_openai_client
from audio_processor import AudioProcessor, save_uploaded_audio, cleanup_audio_file

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv("CORS_ORIGINS", "*").split(","),
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
    }
})

# Initialize database
db = init_db(os.getenv("DATABASE_URL"))

# Initialize AI engines
llm_engine = None
audio_processor = None
cartesia_client = None


def init_cartesia_client():
    """Initialize Cartesia client for TTS"""
    global cartesia_client
    try:
        from cartesia import Cartesia
        api_key = os.getenv("CARTESIA_API_KEY")
        if api_key:
            cartesia_client = Cartesia(api_key=api_key)
            logger.info("Cartesia client initialized successfully")
        else:
            logger.warning("CARTESIA_API_KEY not set - TTS will not be available")
    except ImportError:
        logger.warning("Cartesia library not available - TTS will not be available")
    except Exception as e:
        logger.warning(f"Failed to initialize Cartesia client: {e}")


def init_ai_engines():
    """Initialize AI engines on startup"""
    global llm_engine, audio_processor, cartesia_client
    try:
        init_openai_client(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("LLM_MODEL", "gpt-4-turbo"),
        )
        llm_engine = LLMEngine()
        
        # Initialize Cartesia client
        init_cartesia_client()
        
        # Initialize audio processor
        audio_processor = AudioProcessor(cartesia_client=cartesia_client)
        
        logger.info("AI engines initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI engines: {e}")
        raise


# ============= MIDDLEWARE =============

def log_request(f):
    """Decorator to log all API requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            response = f(*args, **kwargs)
            response_time = int((time.time() - start_time) * 1000)
            status_code = 200
            
            # Log to database
            db.log_api_access(
                endpoint=request.path,
                method=request.method,
                status_code=status_code,
                response_time_ms=response_time,
                ip_address=request.remote_addr,
            )
            
            logger.info(f"{request.method} {request.path} - {status_code} ({response_time}ms)")
            return response
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            status_code = 500
            
            db.log_api_access(
                endpoint=request.path,
                method=request.method,
                status_code=status_code,
                response_time_ms=response_time,
                error_message=str(e),
                ip_address=request.remote_addr,
            )
            
            logger.error(f"{request.method} {request.path} - {status_code} - {str(e)}")
            raise
    
    return decorated_function


def verify_api_key(f):
    """Decorator to verify API key for protected endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("Authorization", "").replace("Bearer ", "")
        valid_key = os.getenv("API_KEY")
        
        if valid_key and api_key != valid_key:
            return jsonify({"error": "Unauthorized"}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


# ============= HEALTH & INFO ENDPOINTS =============

@app.route("/health", methods=["GET"])
@log_request
def health_check():
    """Health check endpoint"""
    db_ok = db.health_check()
    
    return jsonify({
        "status": "healthy" if db_ok else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "ok" if db_ok else "error",
        "version": os.getenv("APP_VERSION", "1.0.0"),
    }), 200 if db_ok else 503


@app.route("/api/info", methods=["GET"])
@log_request
def api_info():
    """Get API information"""
    return jsonify({
        "service": "Pre-Visit Voice Agent API",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": os.getenv("FLASK_ENV", "production"),
        "llm_model": os.getenv("LLM_MODEL", "gpt-4-turbo"),
        "endpoints": {
            "sessions": "/api/sessions",
            "messages": "/api/sessions/{session_id}/messages",
            "clinical": "/api/sessions/{session_id}/clinical",
            "export": "/api/sessions/{session_id}/export",
        }
    }), 200


# ============= SESSION ENDPOINTS =============

@app.route("/api/sessions", methods=["POST"])
@log_request
def create_session():
    """
    Create a new conversation session
    
    Request body:
    {
        "patient_id": "P123456",
        "language": "en"  # Optional: ar, en, hi
    }
    """
    try:
        # Try to get JSON data, handle various error cases
        try:
            data = request.get_json(force=False)
        except Exception as e:
            # Handle bad JSON or missing content type
            if "415" in str(e) or "Unsupported Media Type" in str(e):
                return jsonify({"error": "Missing or invalid Content-Type header"}), 415
            elif "400" in str(e) or "Bad Request" in str(e):
                return jsonify({"error": "Malformed JSON"}), 400
            raise
        
        if not data:
            data = {}
        
        patient_id = data.get("patient_id")
        if not patient_id:
            return jsonify({"error": "patient_id is required"}), 400
        
        language = data.get("language", "en")
        if language not in ["ar", "en", "hi"]:
            return jsonify({"error": "Invalid language. Must be ar, en, or hi"}), 400
        
        # Create session in database
        session = db.create_session(patient_id=patient_id, language=language)
        
        return jsonify({
            "success": True,
            "session": session.to_dict()
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/sessions/<session_id>", methods=["GET"])
@log_request
def get_session(session_id: str):
    """Get session information"""
    try:
        session = db.get_session_by_id(session_id)
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        # Get associated messages
        messages = db.get_messages(session_id)
        
        # Get clinical data if exists
        clinical = db.get_clinical_data(session_id)
        
        return jsonify({
            "session": session.to_dict(),
            "messages_count": len(messages),
            "clinical_data": clinical.to_dict() if clinical else None,
            "status": session.status,
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving session: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/patients/<patient_id>/sessions", methods=["GET"])
@log_request
def get_patient_sessions(patient_id: str):
    """Get all sessions for a patient"""
    try:
        limit = request.args.get("limit", 10, type=int)
        sessions = db.get_sessions_by_patient(patient_id, limit=limit)
        
        return jsonify({
            "patient_id": patient_id,
            "sessions": [s.to_dict() for s in sessions],
            "count": len(sessions),
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving patient sessions: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/sessions/<session_id>", methods=["PUT"])
@log_request
def end_session(session_id: str):
    """
    End a conversation session
    
    Request body:
    {
        "status": "completed"  # or "abandoned"
    }
    """
    try:
        data = request.get_json() or {}
        status = data.get("status", "completed")
        
        if status not in ["completed", "abandoned"]:
            return jsonify({"error": "Invalid status"}), 400
        
        session = db.end_session(session_id, status=status)
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify({
            "success": True,
            "session": session.to_dict(),
        }), 200
    
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        return jsonify({"error": str(e)}), 500


# ============= MESSAGE ENDPOINTS =============

@app.route("/api/sessions/<session_id>/messages", methods=["POST"])
@log_request
def add_message(session_id: str):
    """
    Add a message to a conversation
    
    Request body:
    {
        "role": "user",  # or "assistant"
        "content": "I have a toothache",
        "turn_number": 1,
        "confidence": 0.95  # Optional
    }
    """
    try:
        session = db.get_session_by_id(session_id)
        if not session or session.status != "active":
            return jsonify({"error": "Session not found or inactive"}), 404
        
        data = request.get_json() or {}
        
        role = data.get("role")
        content = data.get("content")
        turn_number = data.get("turn_number")
        confidence = data.get("confidence")
        
        if not role or not content or turn_number is None:
            return jsonify({"error": "role, content, and turn_number are required"}), 400
        
        if role not in ["user", "assistant", "system"]:
            return jsonify({"error": "Invalid role"}), 400
        
        # Add message to database
        message = db.add_message(
            session_id=session_id,
            role=role,
            content=content,
            turn_number=turn_number,
            confidence=confidence,
        )
        
        # If this is a user message, generate AI response
        ai_response = None
        if role == "user" and llm_engine:
            try:
                # Get conversation history
                messages = db.get_messages(session_id)
                
                # Prepare history for LLM
                history = [
                    {"role": m.role, "content": m.content}
                    for m in messages
                ]
                
                # Generate response
                ai_response = llm_engine.generate_response(
                    messages=history,
                    language=session.language,
                )
                
                # Add AI response to database
                db.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=ai_response,
                    turn_number=turn_number + 1,
                )
            except Exception as e:
                logger.warning(f"Failed to generate AI response: {e}")
                ai_response = None
        
        return jsonify({
            "success": True,
            "message": message.to_dict(),
            "ai_response": ai_response,
        }), 201
    
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/sessions/<session_id>/messages", methods=["GET"])
@log_request
def get_messages(session_id: str):
    """Get all messages for a session"""
    try:
        session = db.get_session_by_id(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        messages = db.get_messages(session_id)
        
        return jsonify({
            "session_id": session_id,
            "messages": [m.to_dict() for m in messages],
            "count": len(messages),
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving messages: {e}")
        return jsonify({"error": str(e)}), 500


# ============= CLINICAL DATA ENDPOINTS =============

@app.route("/api/sessions/<session_id>/clinical", methods=["POST"])
@log_request
def save_clinical_data(session_id: str):
    """
    Save clinical data extracted from conversation
    
    Request body:
    {
        "chief_complaint": "toothache",
        "pain_severity": 7,
        "duration": "3 days",
        "urgency_level": "MEDIUM",
        "recommended_specialist": "Dentist",
        ...
    }
    """
    try:
        session = db.get_session_by_id(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        data = request.get_json() or {}
        
        # Save clinical data
        clinical = db.save_clinical_data(session_id=session_id, clinical_info=data)
        
        return jsonify({
            "success": True,
            "clinical_data": clinical.to_dict(),
        }), 201
    
    except Exception as e:
        logger.error(f"Error saving clinical data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/sessions/<session_id>/clinical", methods=["GET"])
@log_request
def get_clinical_data(session_id: str):
    """Get clinical data for a session"""
    try:
        session = db.get_session_by_id(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        clinical = db.get_clinical_data(session_id)
        
        return jsonify({
            "session_id": session_id,
            "clinical_data": clinical.to_dict() if clinical else None,
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving clinical data: {e}")
        return jsonify({"error": str(e)}), 500


# ============= EXPORT ENDPOINTS =============

@app.route("/api/sessions/<session_id>/export", methods=["GET"])
@log_request
def export_session_json(session_id: str):
    """Export complete session as JSON"""
    try:
        export_data = db.export_session_as_json(session_id)
        
        if not export_data:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify(export_data), 200
    
    except Exception as e:
        logger.error(f"Error exporting session: {e}")
        return jsonify({"error": str(e)}), 500


# ============= AUDIO ENDPOINTS =============

@app.route("/api/sessions/<session_id>/audio", methods=["POST"])
@log_request
def process_audio(session_id: str):
    """
    Process audio: transcribe to text, generate AI response, synthesize response audio
    
    Expects multipart/form-data with 'audio' file
    
    Returns:
        {
            "success": true,
            "user_text": "...",
            "ai_response_text": "...",
            "audio_url": "/api/sessions/{id}/audio/{audio_id}",
            "message": {...},
            "ai_message": {...}
        }
    """
    try:
        session = db.get_session_by_id(session_id)
        if not session or session.status != "active":
            return jsonify({"error": "Session not found or inactive"}), 404
        
        # Get audio file from request
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        if not audio_file or audio_file.filename == '':
            return jsonify({"error": "Invalid audio file"}), 400
        
        # Save uploaded audio
        audio_path = save_uploaded_audio(audio_file)
        if not audio_path:
            return jsonify({"error": "Failed to save audio file"}), 500
        
        try:
            # Transcribe audio to text
            if not audio_processor:
                return jsonify({"error": "Audio processor not available"}), 503
            
            user_text, detected_lang = audio_processor.transcribe_audio(audio_path, language=session.language)
            
            if not user_text:
                return jsonify({"error": "Failed to transcribe audio"}), 400
            
            logger.info(f"Transcribed audio: '{user_text}' (lang={detected_lang})")
            
            # Save user message
            messages = db.get_messages(session_id)
            turn_number = len(messages) + 1
            
            user_message = db.add_message(
                session_id=session_id,
                role="user",
                content=user_text,
                turn_number=turn_number,
            )
            
            # Generate AI response
            ai_response_text = None
            ai_message = None
            
            if llm_engine:
                try:
                    # Prepare history for LLM
                    all_messages = db.get_messages(session_id)
                    history = [
                        {"role": m.role, "content": m.content}
                        for m in all_messages
                    ]
                    
                    # Generate response
                    ai_response_text = llm_engine.generate_response(
                        messages=history,
                        language=session.language,
                    )
                    
                    # Save AI response message
                    ai_message = db.add_message(
                        session_id=session_id,
                        role="assistant",
                        content=ai_response_text,
                        turn_number=turn_number + 1,
                    )
                    
                    logger.info(f"Generated AI response: '{ai_response_text}'")
                
                except Exception as e:
                    logger.warning(f"Failed to generate AI response: {e}")
                    ai_response_text = "I encountered an issue processing your request. Please try again."
            
            # Synthesize response audio
            response_audio_url = None
            if ai_response_text and audio_processor:
                try:
                    audio_bytes = audio_processor.synthesize_speech(
                        ai_response_text,
                        language=session.language
                    )
                    
                    if audio_bytes:
                        # Store audio in temporary location and return URL
                        response_audio_url = f"/api/sessions/{session_id}/audio/response/{turn_number + 1}"
                        logger.info(f"Synthesized response audio ({len(audio_bytes)} bytes)")
                    
                except Exception as e:
                    logger.warning(f"Failed to synthesize response audio: {e}")
            
            return jsonify({
                "success": True,
                "user_text": user_text,
                "detected_language": detected_lang,
                "ai_response_text": ai_response_text,
                "audio_url": response_audio_url,
                "message": user_message.to_dict(),
                "ai_message": ai_message.to_dict() if ai_message else None,
            }), 200
        
        finally:
            # Clean up audio file
            cleanup_audio_file(audio_path)
    
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/sessions/<session_id>/audio/synthesize", methods=["POST"])
@log_request
def synthesize_audio(session_id: str):
    """
    Synthesize text to speech
    
    Request body:
    {
        "text": "Hello, how are you?"
    }
    
    Returns: Audio file (WAV format)
    """
    try:
        session = db.get_session_by_id(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        data = request.get_json() or {}
        text = data.get("text")
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        if not audio_processor:
            return jsonify({"error": "Audio processor not available"}), 503
        
        # Synthesize audio
        audio_bytes = audio_processor.synthesize_speech(
            text,
            language=session.language
        )
        
        if not audio_bytes:
            return jsonify({"error": "Failed to synthesize audio"}), 500
        
        # Return audio file
        audio_io = BytesIO(audio_bytes)
        return send_file(
            audio_io,
            mimetype="audio/wav",
            as_attachment=True,
            download_name=f"response_{session_id}.wav"
        )
    
    except Exception as e:
        logger.error(f"Error synthesizing audio: {e}")
        return jsonify({"error": str(e)}), 500


# ============= ADMIN ENDPOINTS =============

@app.route("/api/admin/stats", methods=["GET"])
@verify_api_key
@log_request
def admin_stats():
    """Get system statistics (admin only)"""
    try:
        # This would require additional queries
        # For now, return basic info
        return jsonify({
            "database": db.database_url.split("@")[-1] if "@" in db.database_url else "SQLite",
            "health": "ok" if db.health_check() else "error",
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        return jsonify({"error": str(e)}), 500


# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


# ============= STARTUP & SHUTDOWN =============

@app.before_request
def before_request():
    """Called before each request"""
    request.start_time = time.time()


@app.teardown_request
def teardown_request(exception=None):
    """Called after each request"""
    pass


# ============= ERROR HANDLERS =============

@app.errorhandler(400)
def bad_request(error):
    """Handle bad requests"""
    return jsonify({"error": "Bad request", "message": str(error)}), 400


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Not found", "message": str(error)}), 404


@app.errorhandler(415)
def unsupported_media_type(error):
    """Handle unsupported media type"""
    return jsonify({"error": "Unsupported media type", "message": str(error)}), 415


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    return jsonify({"error": "Internal server error", "message": str(error)}), 500


def create_app():
    """Create and configure Flask app"""
    init_ai_engines()
    return app


# ============= RUN SERVER =============

if __name__ == "__main__":
    # Development server
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    
    init_ai_engines()
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
        use_reloader=debug,
    )
