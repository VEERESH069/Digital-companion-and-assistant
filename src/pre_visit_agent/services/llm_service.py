"""
LLM Service - GPT-4o mini Integration
======================================

This module provides the conversational AI engine using GPT-4o mini for
natural conversation management and intelligent data collection.

Key Features:
1. Multi-provider support (OpenAI, Anthropic, fallback)
2. Streaming responses for low latency
3. Function calling for structured data extraction
4. Automatic retry logic with exponential backoff

Technical Specifications:
- Primary Model: GPT-4o mini
- Latency: 500ms first token, 20 tokens/second streaming
- Fallback: Claude Haiku 4.5
"""

import os
import time
import json
import logging
from typing import List, Dict, Optional, Generator, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum

from pre_visit_agent.config.config import LLMConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MessageRole(Enum):
    """Message roles in conversation"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class Message:
    """
    Represents a single message in the conversation.
    
    Attributes:
        role: Message role (system, user, assistant) - can be str or MessageRole enum
        content: Message content
        name: Optional name for function messages
        function_call: Optional function call data
    """
    role: Union[str, MessageRole]  # Accept both str and MessageRole enum
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict] = None
    
    def __post_init__(self):
        """Convert MessageRole enum to string if needed"""
        if isinstance(self.role, MessageRole):
            self.role = self.role.value
    
    def to_dict(self) -> Dict:
        """Convert to API-compatible dictionary"""
        result = {"role": self.role, "content": self.content}
        if self.name:
            result["name"] = self.name
        if self.function_call:
            result["function_call"] = self.function_call
        return result


@dataclass
class LLMResponse:
    """
    Represents an LLM response.
    
    Attributes:
        content: Response text content
        finish_reason: Why the model stopped generating
        usage: Token usage statistics
        function_call: Function call data if present
        model: Model name used
        latency_ms: Response latency in milliseconds
    """
    content: str
    finish_reason: str
    usage: Dict[str, int]
    function_call: Optional[Dict] = None
    model: Optional[str] = None
    latency_ms: Optional[float] = None


class LLMService:
    """
    Language Model Service for conversational AI.
    
    Provides:
    - Natural conversation generation
    - Structured data extraction via function calling
    - Multi-provider support with automatic fallback
    - Token usage tracking and cost monitoring
    """
    
    def __init__(self, config: LLMConfig):
        """
        Initialize the LLM service.
        
        Args:
            config: LLMConfig instance with API credentials and settings
        """
        self.config = config
        self.client = None
        self.fallback_client = None
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.request_count = 0
        
        logger.info(f"Initializing LLM Service with {config.provider}/{config.model_name}")
        
        # Initialize primary client
        self._init_client()
        
        # Initialize fallback client if configured
        if config.fallback_provider and config.fallback_api_key:
            self._init_fallback_client()
    
    def _init_client(self):
        """Initialize the primary LLM client"""
        try:
            if self.config.provider == "openai":
                from openai import OpenAI
                
                self.client = OpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.api_base_url,
                    timeout=self.config.timeout,
                    max_retries=self.config.max_retries
                )
                logger.info("OpenAI client initialized")
                
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
                
        except ImportError:
            logger.error(f"{self.config.provider} library not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize client: {e}")
            raise
    
    def _init_fallback_client(self):
        """Initialize the fallback LLM client"""
        try:
            if self.config.fallback_provider == "anthropic":
                from anthropic import Anthropic
                
                self.fallback_client = Anthropic(
                    api_key=self.config.fallback_api_key,
                    timeout=self.config.timeout
                )
                logger.info("Anthropic fallback client initialized")
                
        except ImportError:
            logger.warning("Anthropic library not installed, fallback unavailable")
        except Exception as e:
            logger.warning(f"Failed to initialize fallback client: {e}")
    
    def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        functions: Optional[List[Dict]] = None
    ) -> LLMResponse:
        """
        Generate a chat completion.
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (overrides config)
            max_tokens: Maximum tokens to generate (overrides config)
            stream: Whether to stream the response
            functions: Function definitions for function calling
            
        Returns:
            LLMResponse with generated content
            
        Example:
            >>> llm = LLMService(config)
            >>> messages = [
            ...     Message(role="system", content="You are a helpful assistant"),
            ...     Message(role="user", content="Hello!")
            ... ]
            >>> response = llm.chat(messages)
            >>> print(response.content)
        """
        start_time = time.time()
        
        # Use config defaults if not specified
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        stream = stream if stream is not None else self.config.stream
        
        try:
            # Convert messages to API format
            api_messages = [msg.to_dict() for msg in messages]
            
            # Prepare request parameters
            request_params = {
                "model": self.config.model_name,
                "messages": api_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": self.config.top_p,
                "stream": False  # Handle streaming separately
            }
            
            # Add functions if provided
            if functions:
                request_params["functions"] = functions
                request_params["function_call"] = "auto"
            
            # Make API call
            if self.config.provider == "openai":
                response = self.client.chat.completions.create(**request_params)
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
            
            # Parse response
            choice = response.choices[0]
            content = choice.message.content or ""
            finish_reason = choice.finish_reason
            
            # Extract function call if present
            function_call = None
            if hasattr(choice.message, 'function_call') and choice.message.function_call:
                function_call = {
                    "name": choice.message.function_call.name,
                    "arguments": json.loads(choice.message.function_call.arguments)
                }
            
            # Track usage
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            self.total_tokens_used += usage["total_tokens"]
            self.request_count += 1
            
            # Calculate cost (GPT-4o mini pricing)
            cost = (
                usage["prompt_tokens"] * 0.15 / 1_000_000 +  # $0.15 per 1M input tokens
                usage["completion_tokens"] * 0.60 / 1_000_000  # $0.60 per 1M output tokens
            )
            self.total_cost += cost
            
            latency_ms = (time.time() - start_time) * 1000
            
            logger.debug(
                f"LLM Response: {usage['total_tokens']} tokens, "
                f"${cost:.6f}, {latency_ms:.0f}ms"
            )
            
            return LLMResponse(
                content=content,
                finish_reason=finish_reason,
                usage=usage,
                function_call=function_call,
                model=self.config.model_name,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            
            # Try fallback if available
            if self.fallback_client:
                logger.info("Attempting fallback provider...")
                return self._chat_fallback(messages, temperature, max_tokens)
            
            raise
    
    def chat_streaming(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        callback: Optional[Callable[[str], None]] = None
    ) -> Generator[str, None, None]:
        """
        Generate a streaming chat completion.
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            callback: Optional callback function for each chunk
            
        Yields:
            String chunks of the response
            
        Example:
            >>> for chunk in llm.chat_streaming(messages):
            ...     print(chunk, end="", flush=True)
        """
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        try:
            api_messages = [msg.to_dict() for msg in messages]
            
            request_params = {
                "model": self.config.model_name,
                "messages": api_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": self.config.top_p,
                "stream": True
            }
            
            if self.config.provider == "openai":
                stream = self.client.chat.completions.create(**request_params)
                
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        
                        if callback:
                            callback(content)
                        
                        yield content
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
                
        except Exception as e:
            logger.error(f"Streaming chat failed: {e}")
            raise
    
    def _chat_fallback(
        self,
        messages: List[Message],
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """
        Fallback to alternative provider.
        
        Args:
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            LLMResponse from fallback provider
        """
        try:
            if self.config.fallback_provider == "anthropic":
                # Convert messages to Anthropic format
                system_messages = [m for m in messages if m.role == "system"]
                other_messages = [m for m in messages if m.role != "system"]
                
                system_prompt = "\n".join(m.content for m in system_messages)
                
                # Anthropic API format
                anthropic_messages = []
                for msg in other_messages:
                    anthropic_messages.append({
                        "role": "user" if msg.role == "user" else "assistant",
                        "content": msg.content
                    })
                
                response = self.fallback_client.messages.create(
                    model=self.config.fallback_model,
                    system=system_prompt,
                    messages=anthropic_messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                content = response.content[0].text
                
                usage = {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
                
                logger.info(f"Fallback successful: {usage['total_tokens']} tokens")
                
                return LLMResponse(
                    content=content,
                    finish_reason=response.stop_reason,
                    usage=usage,
                    model=self.config.fallback_model
                )
            else:
                raise ValueError("No fallback provider configured")
                
        except Exception as e:
            logger.error(f"Fallback also failed: {e}")
            raise
    
    def extract_structured_data(
        self,
        messages: List[Message],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract structured data using function calling.
        
        Args:
            messages: Conversation messages to extract from
            schema: JSON schema defining the expected structure
            
        Returns:
            Dictionary with extracted data
            
        Example:
            >>> schema = {
            ...     "type": "object",
            ...     "properties": {
            ...         "chief_complaint": {"type": "string"},
            ...         "severity": {"type": "integer"}
            ...     }
            ... }
            >>> data = llm.extract_structured_data(messages, schema)
        """
        # Define function for extraction
        function_def = {
            "name": "extract_patient_data",
            "description": "Extract structured patient information from conversation",
            "parameters": schema
        }
        
        response = self.chat(messages, functions=[function_def])
        
        if response.function_call:
            return response.function_call["arguments"]
        else:
            # Parse from response content if function calling didn't work
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                logger.warning("Failed to extract structured data")
                return {}
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Returns:
            Dictionary with token usage and cost metrics
        """
        avg_tokens_per_request = (
            self.total_tokens_used / self.request_count 
            if self.request_count > 0 else 0
        )
        
        return {
            "total_requests": self.request_count,
            "total_tokens": self.total_tokens_used,
            "total_cost_usd": self.total_cost,
            "avg_tokens_per_request": avg_tokens_per_request,
            "avg_cost_per_request": (
                self.total_cost / self.request_count 
                if self.request_count > 0 else 0
            )
        }
    
    def reset_stats(self):
        """Reset usage statistics"""
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.request_count = 0
        logger.info("Usage statistics reset")


# Example usage
if __name__ == "__main__":
    from config import config
    
    print("Testing LLM Service...")
    
    # Initialize service
    llm = LLMService(config.llm)
    
    # Test basic chat
    print("\n=== Test 1: Basic Chat ===")
    messages = [
        Message(role="system", content="You are a helpful dental assistant named Mariam."),
        Message(role="user", content="Hello, I have a toothache.")
    ]
    
    response = llm.chat(messages)
    print(f"Response: {response.content}")
    print(f"Tokens: {response.usage['total_tokens']}")
    print(f"Latency: {response.latency_ms:.0f}ms")
    
    # Test streaming
    print("\n=== Test 2: Streaming Chat ===")
    print("Response: ", end="", flush=True)
    for chunk in llm.chat_streaming(messages):
        print(chunk, end="", flush=True)
    print()
    
    # Test structured extraction
    print("\n=== Test 3: Structured Data Extraction ===")
    extraction_messages = [
        Message(
            role="system",
            content="Extract patient information from the conversation."
        ),
        Message(
            role="user",
            content="I have severe pain in my upper right molar for 3 days. It's an 8 out of 10."
        )
    ]
    
    schema = {
        "type": "object",
        "properties": {
            "chief_complaint": {"type": "string"},
            "duration": {"type": "string"},
            "severity": {"type": "integer", "minimum": 1, "maximum": 10},
            "location": {"type": "string"}
        },
        "required": ["chief_complaint", "severity"]
    }
    
    extracted = llm.extract_structured_data(extraction_messages, schema)
    print(f"Extracted: {json.dumps(extracted, indent=2, ensure_ascii=False)}")
    
    # Usage stats
    print("\n=== Usage Statistics ===")
    stats = llm.get_usage_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
