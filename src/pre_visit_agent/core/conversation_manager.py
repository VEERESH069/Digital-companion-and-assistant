"""
Conversation Manager - State Machine and Turn Logic
====================================================

This module implements the conversational AI state machine for natural,
empathetic patient data collection.

Key Features:
1. Dynamic State Management - Tracks what's collected vs. what's missing
2. Natural Flow - Avoids robotic sequential questioning
3. Empathetic Responses - Acknowledges pain and concerns
4. Context Awareness - Remembers conversation history
5. Intelligent Completion - Knows when to end gracefully

State Machine Flow:
┌─────────────┐
│  GREETING   │ → Build rapport, introduce purpose
└──────┬──────┘
       ↓
┌─────────────┐
│  DISCOVERY  │ → Collect required data naturally
└──────┬──────┘   (loops until complete)
       ↓
┌─────────────┐
│ COMPLETION  │ → Verify all info collected
└──────┬──────┘
       ↓
┌─────────────┐
│   CLOSING   │ → Thank patient, confirm appointment
└─────────────┘

Conversation Style Guidelines:
- SHORT responses (1-2 sentences max)
- ONE question at a time
- Natural follow-ups based on patient responses
- Empathy and validation
- Egyptian Arabic cultural sensitivity
"""

import logging
from typing import List, Dict, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from pre_visit_agent.services.llm_service import LLMService, Message, MessageRole
from pre_visit_agent.config.config import ConversationConfig, ExtractionSchema

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """States in the conversation flow"""
    GREETING = "greeting"
    DISCOVERY = "discovery"
    COMPLETION = "completion"
    CLOSING = "closing"
    ENDED = "ended"


@dataclass
class PatientData:
    """
    Collected patient information.
    
    Tracks both the data and confidence scores for each field.
    """
    # Required fields
    chief_complaint: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[int] = None
    location: Optional[str] = None
    triggers: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    medical_conditions: Optional[List[str]] = None
    
    # Optional fields
    previous_dental_work: Optional[str] = None
    
    # Confidence scores (0.0 to 1.0)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    def get_missing_required_fields(self, required_fields: List[str]) -> List[str]:
        """
        Get list of required fields that are still missing.
        
        Args:
            required_fields: List of required field names
            
        Returns:
            List of missing field names
        """
        missing = []
        for field in required_fields:
            value = getattr(self, field, None)
            if value is None or value == [] or value == "":
                missing.append(field)
        return missing
    
    def get_collected_fields(self, required_fields: List[str]) -> List[str]:
        """Get list of fields that have been collected"""
        collected = []
        for field in required_fields:
            value = getattr(self, field, None)
            if value is not None and value != [] and value != "":
                collected.append(field)
        return collected
    
    def is_complete(self, required_fields: List[str], min_confidence: float = 0.7) -> bool:
        """
        Check if all required data is collected with sufficient confidence.
        
        Args:
            required_fields: List of required field names
            min_confidence: Minimum confidence threshold
            
        Returns:
            True if all required fields are collected with good confidence
        """
        missing = self.get_missing_required_fields(required_fields)
        if missing:
            return False
        
        # Check confidence scores
        for field in required_fields:
            confidence = self.confidence_scores.get(field, 0.0)
            if confidence < min_confidence:
                return False
        
        return True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "chief_complaint": self.chief_complaint,
            "duration": self.duration,
            "severity": self.severity,
            "location": self.location,
            "triggers": self.triggers,
            "current_medications": self.current_medications,
            "allergies": self.allergies,
            "medical_conditions": self.medical_conditions,
            "previous_dental_work": self.previous_dental_work,
            "confidence_scores": self.confidence_scores
        }


class ConversationManager:
    """
    Manages the conversation state machine and turn-by-turn dialogue.
    
    Responsibilities:
    - Track conversation state and history
    - Build dynamic system prompts
    - Determine next response
    - Manage data collection progress
    - Detect conversation completion
    """
    
    def __init__(self, config: ConversationConfig, llm_service: LLMService):
        """
        Initialize the conversation manager.
        
        Args:
            config: ConversationConfig with conversation parameters
            llm_service: LLM service for generating responses
        """
        self.config = config
        self.llm = llm_service
        
        # Conversation state
        self.state = ConversationState.GREETING
        self.turn_count = 0
        self.conversation_history: List[Message] = []
        
        # Patient data
        self.patient_data = PatientData()
        
        # Metadata
        self.conversation_id = f"CONV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.session_id = self.conversation_id  # Alias for compatibility
        self.start_time = datetime.now()
        
        logger.info(f"Conversation initialized: {self.conversation_id}")
    
    def start_conversation(self) -> str:
        """
        Start the conversation with greeting.
        
        Returns:
            Greeting message from agent
        """
        self.state = ConversationState.GREETING
        
        greeting_prompt = self._build_system_prompt()
        
        # Add initial greeting instruction
        messages = [
            Message(role="system", content=greeting_prompt),
            Message(
                role="user",
                content="[Patient just answered the phone]"
            )
        ]
        
        response = self.llm.chat(messages, max_tokens=150)
        
        # Store in history
        self.conversation_history.append(
            Message(role="assistant", content=response.content)
        )
        
        self.turn_count += 1
        self.state = ConversationState.DISCOVERY
        
        return response.content
    
    def process_turn(self, patient_input: str) -> str:
        """
        Process a single conversation turn.
        
        This is the core method called for each patient response.
        
        Args:
            patient_input: Patient's spoken input (transcribed)
            
        Returns:
            Agent's response
            
        Workflow:
        1. Add patient input to history
        2. Update state and collected data
        3. Build dynamic prompt with current state
        4. Generate response via LLM
        5. Check completion criteria
        6. Return response
        """
        logger.info(f"Turn {self.turn_count + 1}: Processing patient input")
        
        # 1. Add to history
        self.conversation_history.append(
            Message(role="user", content=patient_input)
        )
        
        # 2. Check current state
        missing_fields = self.patient_data.get_missing_required_fields(
            self.config.required_fields
        )
        collected_fields = self.patient_data.get_collected_fields(
            self.config.required_fields
        )
        
        logger.debug(f"Missing: {missing_fields}")
        logger.debug(f"Collected: {collected_fields}")
        
        # 3. Build dynamic prompt
        system_prompt = self._build_system_prompt()
        
        # Get recent history (last N messages)
        recent_history = self.conversation_history[-self.config.history_window:]
        
        # Build message list for LLM
        messages = [Message(role="system", content=system_prompt)] + recent_history
        
        # 4. Generate response
        response = self.llm.chat(messages, max_tokens=200)
        
        # 5. Add response to history
        self.conversation_history.append(
            Message(role="assistant", content=response.content)
        )
        
        self.turn_count += 1
        
        # 6. Check completion
        if self._should_complete():
            self.state = ConversationState.COMPLETION
            logger.info("Conversation nearing completion")
        
        if self.turn_count >= self.config.max_turns:
            self.state = ConversationState.CLOSING
            logger.info("Max turns reached, initiating closing")
        
        return response.content
    
    def _build_system_prompt(self) -> str:
        """
        Build dynamic system prompt based on current state.
        
        The prompt changes every turn to reflect:
        - What data has been collected
        - What data is still needed
        - Current conversation phase
        
        Returns:
            System prompt string
        """
        # Base role definition
        prompt = f"""# ROLE DEFINITION
You are {self.config.agent_name}, a friendly dental clinic assistant conducting a pre-visit consultation call.
Your goal is to gather comprehensive medical and dental information BEFORE the patient's visit.
You speak Egyptian Arabic naturally and make patients feel comfortable sharing their dental concerns.

# CURRENT CONVERSATION STATE
Turn: {self.turn_count + 1}
Phase: {self.state.value}

"""
        
        # Required data to collect
        prompt += """# REQUIRED DATA TO COLLECT
"""
        missing = self.patient_data.get_missing_required_fields(self.config.required_fields)
        collected = self.patient_data.get_collected_fields(self.config.required_fields)
        
        if collected:
            prompt += "\n## Already Collected:\n"
            for field in collected:
                value = getattr(self.patient_data, field, None)
                prompt += f"- {field}: {value}\n"
        
        if missing:
            prompt += "\n## Still Need:\n"
            for field in missing:
                prompt += f"- {field}\n"
        
        # Conversation style guidelines
        prompt += """
# CONVERSATION STYLE GUIDELINES

## Natural Flow (NOT Sequential)
❌ BAD: "Question 1... Question 2... Question 3..."
✓ GOOD: Let conversation flow naturally based on patient responses

## Empathy and Validation
- Acknowledge pain/discomfort: "ده أكيد مزعج" (That must be bothersome)
- Show understanding: "أنا فاهمة، ده صعب" (I understand, that's difficult)
- Validate responses: "شكراً إنك شاركتني المعلومة دي" (Thank you for sharing that)

## Response Length
- Keep responses SHORT: 1-2 sentences maximum per turn
- Don't overwhelm with multiple questions at once
- One topic at a time

## Follow-up Intelligence
- If answer is unclear: Ask gentle clarification
- If concerning symptom: Probe deeper with empathy
- If patient seems tired: Be efficient but still warm

## Cultural Sensitivity
- Egyptian communication style (warmer, more relational)
- Code-switching between Arabic/English is natural
- Medical terms can be in English if patient understands

"""
        
        # State-specific instructions
        if self.state == ConversationState.GREETING:
            prompt += """
# CURRENT TASK: GREETING
Introduce yourself warmly, explain the purpose of the call, and start building rapport.
Keep it brief and friendly. Then transition naturally to asking about their dental concern.
"""
        
        elif self.state == ConversationState.DISCOVERY:
            prompt += f"""
# CURRENT TASK: DISCOVERY
Based on what's still needed, decide:
1. What's the most natural next topic to explore?
2. Can I weave this into the conversation flow?
3. Is the patient giving clear answers or do I need to clarify?

{f'Priority: Focus on collecting {missing[0]}' if missing else 'Almost done! Just verify everything is clear.'}
"""
        
        elif self.state == ConversationState.COMPLETION:
            prompt += """
# CURRENT TASK: COMPLETION
Verify that you have all the necessary information. If anything seems unclear or missing,
politely ask for clarification. Once satisfied, prepare to close the conversation.
"""
        
        elif self.state == ConversationState.CLOSING:
            prompt += """
# CURRENT TASK: CLOSING
Thank the patient warmly for sharing their information, and end the call gracefully.
Reassure them that the doctor will be well-prepared with all this information before their visit.
Confirm that the consultation information has been recorded.
"""
        
        # Response strategy
        prompt += """
# RESPONSE STRATEGY
1. Acknowledge what the patient just said
2. If they shared important information, validate it
3. Ask ONE follow-up question if needed
4. Keep it conversational and warm

Remember: SHORT responses (1-2 sentences max). Natural flow. Show empathy.
"""
        
        return prompt
    
    def _should_complete(self) -> bool:
        """
        Determine if conversation should move to completion phase.
        
        Returns:
            True if ready to complete
        """
        # Check if all required fields are collected
        missing = self.patient_data.get_missing_required_fields(
            self.config.required_fields
        )
        
        # If no missing fields and we've had at least 5 turns
        if len(missing) == 0 and self.turn_count >= 5:
            return True
        
        # If we're approaching max turns and have most data
        if self.turn_count >= self.config.max_turns - 2 and len(missing) <= 2:
            return True
        
        return False
    
    def is_conversation_complete(self) -> bool:
        """
        Check if conversation is complete and should end.
        
        Returns:
            True if conversation should end
        """
        # All required fields collected
        if self.patient_data.is_complete(
            self.config.required_fields,
            self.config.completion_threshold
        ):
            return True
        
        # Max turns reached (graceful exit)
        if self.turn_count >= self.config.max_turns:
            logger.warning("Max turns reached, ending conversation")
            return True
        
        # Explicitly in ended state
        if self.state == ConversationState.ENDED:
            return True
        
        return False
    
    def get_conversation_summary(self) -> Dict:
        """
        Get a summary of the conversation.
        
        Returns:
            Dictionary with conversation metadata and collected data
        """
        duration = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "conversation_id": self.conversation_id,
            "start_time": self.start_time.isoformat(),
            "duration_seconds": duration,
            "turn_count": self.turn_count,
            "state": self.state.value,
            "collected_data": self.patient_data.to_dict(),
            "missing_fields": self.patient_data.get_missing_required_fields(
                self.config.required_fields
            ),
            "completion_percentage": (
                len(self.patient_data.get_collected_fields(self.config.required_fields)) /
                len(self.config.required_fields) * 100
            )
        }
    
    def get_full_transcript(self) -> str:
        """
        Get full conversation transcript.
        
        Returns:
            Formatted transcript string
        """
        transcript = f"Conversation ID: {self.conversation_id}\n"
        transcript += f"Date: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        transcript += "=" * 50 + "\n\n"
        
        for msg in self.conversation_history:
            role = "Agent" if msg.role == "assistant" else "Patient"
            transcript += f"{role}: {msg.content}\n\n"
        
        return transcript
    
    def end_conversation(self) -> str:
        """
        End the conversation gracefully.
        
        Returns:
            Final closing message
        """
        self.state = ConversationState.ENDED
        
        summary = self.get_conversation_summary()
        logger.info(
            f"Conversation ended: {summary['turn_count']} turns, "
            f"{summary['completion_percentage']:.0f}% complete"
        )
        
        return "شكراً لوقتك. نتطلع لرؤيتك قريباً!"  # Thank you for your time. Looking forward to seeing you soon!


# Example usage
if __name__ == "__main__":
    from config import config
    from llm_service import LLMService
    
    print("Testing Conversation Manager...")
    
    # Initialize services
    llm = LLMService(config.llm)
    manager = ConversationManager(config.conversation, llm)
    
    # Start conversation
    print("\n=== Starting Conversation ===")
    greeting = manager.start_conversation()
    print(f"Agent: {greeting}")
    
    # Simulate patient responses
    test_inputs = [
        "مرحباً، عندي ألم في ضرسي",  # Hello, I have pain in my tooth
        "من حوالي ٣ أيام، الألم شديد",  # About 3 days, severe pain
        "الضرس الأيمن العلوي، ألم ٨ من ١٠",  # Upper right molar, pain 8/10
        "بياكلني لما أشرب حاجة سخنة أو ألمس الضرس",  # Hurts when I drink something hot or touch the tooth
        "باخد بروفين بس مش بيجيب نتيجة كبيرة",  # Taking ibuprofen but not much relief
        "عندي حساسية من البنسلين",  # I'm allergic to penicillin
        "عندي سكر النوع التاني، باخد ميتفورمين",  # I have Type 2 diabetes, taking Metformin
    ]
    
    print("\n=== Conversation Flow ===")
    for i, patient_input in enumerate(test_inputs, 1):
        print(f"\nTurn {i}:")
        print(f"Patient: {patient_input}")
        
        response = manager.process_turn(patient_input)
        print(f"Agent: {response}")
        
        # Check if complete
        if manager.is_conversation_complete():
            print("\n✓ Conversation complete!")
            break
    
    # Summary
    print("\n=== Conversation Summary ===")
    summary = manager.get_conversation_summary()
    import json
    print(json.dumps(summary, indent=2, ensure_ascii=False))
