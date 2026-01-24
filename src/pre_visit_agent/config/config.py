"""
Configuration Management for Pre-Visit Voice Agent
===================================================

This module centralizes all configuration parameters for the voice agent system.
Supports environment variables for production deployment and provides sensible defaults.

Configuration Sections:
1. STT Configuration - Whisper settings
2. TTS Configuration - Coqui XTTS settings
3. LLM Configuration - GPT-4o mini API settings
4. Conversation Configuration - State machine parameters
5. Data Extraction Configuration - Extraction triggers and schemas
6. Integration Configuration - CareBot and external system settings
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    # Look for .env in project root
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, skip
    pass


class Environment(Enum):
    """Deployment environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class STTConfig:
    """
    Speech-to-Text Configuration
    
    Attributes:
        model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large-v3')
        language: Primary language code ('ar' for Arabic, 'en' for English)
        dialect_prompt: Initial prompt to guide dialect recognition (Egyptian Arabic)
        min_duration: Minimum audio duration in seconds before transcription
        sample_rate: Audio sample rate in Hz (Whisper expects 16000)
        use_fp16: Enable FP16 precision for GPU acceleration (2x speedup)
        device: Compute device ('cuda' for GPU, 'cpu' for CPU)
    """
    model_size: str = "base"  # Default: 'base' for fast loading. Options: tiny, base, small, medium, large-v3
    language: str = "ar"  # Arabic
    dialect_prompt: str = "This is a conversation in Egyptian Arabic about dental care."
    min_duration: float = 1.5  # Seconds - balance between latency and accuracy
    sample_rate: int = 16000
    use_fp16: bool = True  # GPU optimization
    device: Optional[str] = None  # Auto-detect if None


@dataclass
class TTSConfig:
    """
    Text-to-Speech Configuration (Coqui XTTS v2)
    
    Attributes:
        model_name: XTTS model variant
        language: Target language for synthesis
        speaker_wav: Path to voice cloning sample (10-minute Egyptian Arabic speaker)
        output_sample_rate: Output audio quality (22050 Hz for natural sound)
        streaming: Enable streaming mode for reduced latency
        use_deepspeed: Enable DeepSpeed for faster inference
        device: Compute device
        cache_dir: Directory for caching pre-generated phrases
        common_phrases: List of phrases to pre-generate and cache
    """
    model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    language: str = "ar"  # Arabic
    speaker_wav: str = "./voice_samples/egyptian_receptionist.wav"
    output_sample_rate: int = 22050
    streaming: bool = True
    use_deepspeed: bool = False  # Set True if DeepSpeed is installed
    device: Optional[str] = None
    cache_dir: str = "./tts_cache"
    common_phrases: List[str] = field(default_factory=lambda: [
        "شكراً لك",  # Thank you
        "أنا أفهم",  # I understand
        "هل يمكنك توضيح ذلك؟",  # Can you clarify that?
        "ذلك يبدو مؤلماً",  # That sounds painful
        "سأقوم بتسجيل ذلك"  # I'll note that down
    ])


@dataclass
class LLMConfig:
    """
    Large Language Model Configuration (GPT-4o mini)
    
    Attributes:
        provider: LLM provider ('openai', 'anthropic', 'fallback')
        model_name: Specific model to use
        api_key: API key (from environment variable)
        max_tokens: Maximum tokens per response
        temperature: Sampling temperature (0.7 for balanced creativity)
        top_p: Nucleus sampling parameter
        stream: Enable streaming responses
        timeout: API request timeout in seconds
        max_retries: Number of retry attempts on failure
        fallback_provider: Backup LLM provider
        fallback_model: Backup model name
    """
    provider: str = "openai"
    model_name: str = "gpt-4o-mini"
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    api_base_url: Optional[str] = None  # For custom endpoints
    max_tokens: int = 500  # Keep responses concise
    temperature: float = 0.7
    top_p: float = 0.95
    stream: bool = True
    timeout: int = 30
    max_retries: int = 3
    
    # Fallback configuration
    fallback_provider: str = "anthropic"
    fallback_model: str = "claude-haiku-4.5"
    fallback_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))


@dataclass
class ConversationConfig:
    """
    Conversation Manager Configuration
    
    Attributes:
        agent_name: Name of the virtual assistant
        max_turns: Maximum conversation turns before forced completion
        history_window: Number of recent messages to include in context
        extraction_interval: Run data extraction every N turns
        completion_threshold: Minimum confidence score to consider field complete
        required_fields: List of mandatory data fields
        optional_fields: List of optional data fields
        enable_empathy: Enable empathetic response generation
        response_max_sentences: Maximum sentences per agent response
    """
    agent_name: str = "Mariam"
    clinic_name: str = "CareBot Clinic"
    max_turns: int = 15
    target_turns: int = 12  # Target conversation length for natural flow
    history_window: int = 6  # Last 6 messages
    extraction_interval: int = 2  # Extract every 2-3 turns
    completion_threshold: float = 0.7
    
    required_fields: List[str] = field(default_factory=lambda: [
        "chief_complaint",
        "duration",
        "severity",
        "location",
        "triggers",
        "current_medications",
        "allergies",
        "medical_conditions"
    ])
    
    optional_fields: List[str] = field(default_factory=lambda: [
        "previous_dental_work"
    ])
    
    enable_empathy: bool = True
    response_max_sentences: int = 2


@dataclass
class ExtractionSchema:
    """
    Data Extraction Schema Definition
    
    Defines the structure for extracting patient information from conversations.
    Includes field types, validation rules, and confidence thresholds.
    """
    fields: Dict[str, Dict] = field(default_factory=lambda: {
        "chief_complaint": {
            "type": "string",
            "description": "Primary dental issue or reason for visit",
            "required": True,
            "examples": ["toothache", "broken tooth", "gum bleeding"]
        },
        "duration": {
            "type": "string",
            "description": "How long the issue has persisted",
            "required": True,
            "examples": ["3 days", "2 weeks", "started yesterday"]
        },
        "severity": {
            "type": "integer",
            "description": "Pain level from 1-10",
            "required": True,
            "min": 1,
            "max": 10
        },
        "location": {
            "type": "string",
            "description": "Specific tooth or area affected",
            "required": True,
            "examples": ["upper right molar", "front tooth", "lower left side"]
        },
        "triggers": {
            "type": "array",
            "description": "What makes the pain worse",
            "required": True,
            "examples": [["hot drinks", "cold food"], ["chewing", "pressure"]]
        },
        "current_medications": {
            "type": "array",
            "description": "Current medications patient is taking",
            "required": True,
            "examples": [["Ibuprofen 400mg"], ["No medications"]]
        },
        "allergies": {
            "type": "array",
            "description": "Drug allergies, especially to anesthetics",
            "required": True,
            "examples": [["Penicillin"], ["No known allergies"]]
        },
        "previous_dental_work": {
            "type": "string",
            "description": "Recent dental treatments or ongoing issues",
            "required": False,
            "examples": ["Root canal 6 months ago", "Regular cleanings only"]
        },
        "medical_conditions": {
            "type": "array",
            "description": "Relevant medical conditions",
            "required": True,
            "examples": [["Type 2 Diabetes", "Hypertension"], ["None"]]
        }
    })


@dataclass
class IntegrationConfig:
    """
    External Integration Configuration
    
    Attributes:
        enable_carebot_integration: Enable CareBot memory agent integration
        carebot_api_url: CareBot API endpoint
        carebot_api_key: CareBot authentication key
        enable_ehr_integration: Enable Electronic Health Record integration
        ehr_api_url: EHR system API endpoint
        database_url: PostgreSQL connection string for patient data
        redis_url: Redis connection for caching and queues
    """
    enable_carebot_integration: bool = False  # Stub for future
    carebot_api_url: Optional[str] = None
    carebot_api_key: str = field(default_factory=lambda: os.getenv("CAREBOT_API_KEY", ""))
    
    enable_ehr_integration: bool = False
    ehr_api_url: Optional[str] = None
    
    database_url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL", 
        "postgresql://localhost:5432/voice_agent"
    ))
    redis_url: str = field(default_factory=lambda: os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0"
    ))


@dataclass
class AppConfig:
    """
    Master Application Configuration
    
    Aggregates all configuration sections and provides environment-specific overrides.
    """
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    log_level: str = "INFO"
    
    # Sub-configurations
    stt: STTConfig = field(default_factory=STTConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    conversation: ConversationConfig = field(default_factory=ConversationConfig)
    extraction_schema: ExtractionSchema = field(default_factory=ExtractionSchema)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)
    
    # Paths
    data_dir: str = "./data"
    logs_dir: str = "./logs"
    cache_dir: str = "./cache"
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """
        Create configuration from environment variables.
        
        Returns:
            AppConfig instance with environment-specific settings
        """
        env = Environment(os.getenv("ENVIRONMENT", "development"))
        
        config = cls(
            environment=env,
            debug=env == Environment.DEVELOPMENT,
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )
        
        # Production optimizations
        if env == Environment.PRODUCTION:
            config.stt.model_size = "large-v3"
            config.llm.temperature = 0.6  # More deterministic in production
            config.conversation.max_turns = 12  # Shorter conversations
            config.debug = False
        
        return config
    
    def validate(self) -> bool:
        """
        Validate configuration settings.
        
        Returns:
            True if configuration is valid, raises ValueError otherwise
        """
        # Validate API keys
        if not self.llm.api_key and self.environment == Environment.PRODUCTION:
            raise ValueError("OPENAI_API_KEY is required in production")
        
        # Validate paths
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
        
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir, exist_ok=True)
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
        
        if not os.path.exists(self.tts.cache_dir):
            os.makedirs(self.tts.cache_dir, exist_ok=True)
        
        return True


# Global configuration instance
config = AppConfig.from_env()


if __name__ == "__main__":
    # Configuration validation and display
    print("Pre-Visit Voice Agent Configuration")
    print("=" * 50)
    print(f"Environment: {config.environment.value}")
    print(f"Debug Mode: {config.debug}")
    print(f"\nSTT Model: {config.stt.model_size}")
    print(f"STT Language: {config.stt.language}")
    print(f"\nTTS Model: {config.tts.model_name}")
    print(f"TTS Sample Rate: {config.tts.output_sample_rate}")
    print(f"\nLLM Provider: {config.llm.provider}")
    print(f"LLM Model: {config.llm.model_name}")
    print(f"\nAgent Name: {config.conversation.agent_name}")
    print(f"Max Turns: {config.conversation.max_turns}")
    print(f"Required Fields: {len(config.conversation.required_fields)}")
    
    try:
        config.validate()
        print("\n✓ Configuration validated successfully")
    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
