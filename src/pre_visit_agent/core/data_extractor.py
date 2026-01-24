"""
Data Extraction Layer - Real-time and Post-Conversation
========================================================

This module implements asynchronous data extraction from conversations
without interrupting the natural flow of dialogue.

Key Features:
1. Real-time Extraction - Triggered every 2-3 turns during conversation
2. Post-Conversation Extraction - Comprehensive analysis after call ends
3. Confidence Scoring - Track certainty of extracted data
4. Red Flag Detection - Identify urgent symptoms
5. Structured Schema - Prepare data for EHR integration

Purpose:
"One agent speaks and collects, another fills in forms dynamically
or checks if info is provided for after-call filling"

Extraction Workflow:
┌──────────────┐
│ Conversation │
│   Running    │
└──────┬───────┘
       │
       ├──→ [Every 2-3 turns] → Real-time Extraction → Update Patient Data
       │
       └──→ [Call Ends] → Post-Call Extraction → Final Summary → Doctor Briefing


"""

import logging
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

from pre_visit_agent.services.llm_service import LLMService, Message
from pre_visit_agent.core.conversation_manager import PatientData
from pre_visit_agent.config.config import ExtractionSchema

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UrgencyLevel(Enum):
    """Patient urgency classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


@dataclass
class ExtractionResult:
    """
    Result of data extraction process.
    
    Attributes:
        extracted_data: Dictionary of extracted field values
        confidence_scores: Confidence for each field (0.0 to 1.0)
        needs_clarification: List of fields needing follow-up
        red_flags: List of urgent symptoms or concerns
        extraction_timestamp: When extraction occurred
    """
    extracted_data: Dict[str, Any]
    confidence_scores: Dict[str, float]
    needs_clarification: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)
    extraction_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ClinicalSummary:
    """
    Comprehensive clinical summary for doctor.
    
    Attributes:
        patient_id: Patient identifier
        conversation_id: Conversation identifier
        timestamp: Summary generation time
        clinical_data: Structured patient data
        confidence_scores: Confidence for each field
        clinical_summary: Natural language summary for doctor
        red_flags: Urgent concerns requiring attention
        urgency_level: Overall urgency classification
        recommended_specialist: Suggested specialist type
        routing_decision: Appointment routing information
    """
    patient_id: str
    conversation_id: str
    timestamp: str
    clinical_data: Dict[str, Any]
    confidence_scores: Dict[str, float]
    clinical_summary: str
    red_flags: List[str]
    urgency_level: str
    recommended_specialist: Optional[str] = None
    routing_decision: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class DataExtractor:
    """
    Extracts structured patient data from conversational text.
    
    Implements both real-time (during conversation) and post-conversation
    extraction for optimal data quality.
    """
    
    def __init__(self, llm_service: LLMService, schema: ExtractionSchema):
        """
        Initialize the data extractor.
        
        Args:
            llm_service: LLM service for extraction
            schema: Extraction schema definition
        """
        self.llm = llm_service
        self.schema = schema
        self.extraction_count = 0
        
        logger.info("Data extractor initialized")
    
    def extract_real_time(
        self,
        conversation_history: List[Message],
        current_patient_data: PatientData
    ) -> ExtractionResult:
        """
        Extract data in real-time during conversation.
        
        Called every 2-3 turns to update patient data without
        interrupting the conversation flow.
        
        Args:
            conversation_history: Recent conversation messages
            current_patient_data: Currently collected patient data
            
        Returns:
            ExtractionResult with updated data and confidence scores
            
        Example:
            >>> extractor = DataExtractor(llm, schema)
            >>> result = extractor.extract_real_time(history, patient_data)
            >>> if result.needs_clarification:
            ...     # Mark fields for follow-up
        """
        logger.debug("Performing real-time extraction...")
        
        # Format conversation for extraction
        conversation_text = self._format_conversation(conversation_history)
        
        # Build extraction prompt
        prompt = f"""Extract structured patient data from this conversation between a dental assistant and patient.

Conversation:
{conversation_text}

Current Data (what we already have):
{json.dumps(current_patient_data.to_dict(), indent=2, ensure_ascii=False)}

Instructions:
1. Extract ONLY new or updated information from the conversation
2. Assign confidence scores (0.0 to 1.0) based on clarity
3. Flag fields needing clarification if patient's answer was vague
4. Identify any red flags (severe symptoms, urgent conditions)

Return JSON with this EXACT structure:
{{
  "extracted_data": {{
    "chief_complaint": "string or null",
    "duration": "string or null",
    "severity": "integer 1-10 or null",
    "location": "string or null",
    "triggers": ["array of strings or empty"],
    "current_medications": ["array of strings or empty"],
    "allergies": ["array of strings or empty"],
    "previous_dental_work": "string or null",
    "medical_conditions": ["array of strings or empty"]
  }},
  "confidence": {{
    "chief_complaint": 0.0-1.0,
    "duration": 0.0-1.0,
    ...
  }},
  "needs_clarification": [
    "field_name - reason why clarification needed"
  ],
  "red_flags": [
    "description of concerning symptom"
  ]
}}

Be conservative with confidence scores. Only mark as 1.0 if explicitly stated and clear.
"""
        
        # Call LLM for extraction
        messages = [Message(role="user", content=prompt)]
        
        try:
            response = self.llm.chat(messages, temperature=0.3, max_tokens=800)
            
            # Parse JSON response
            result_data = self._parse_extraction_response(response.content)
            
            result = ExtractionResult(
                extracted_data=result_data.get("extracted_data", {}),
                confidence_scores=result_data.get("confidence", {}),
                needs_clarification=result_data.get("needs_clarification", []),
                red_flags=result_data.get("red_flags", [])
            )
            
            self.extraction_count += 1
            logger.debug(f"Real-time extraction complete: {len(result.extracted_data)} fields")
            
            return result
            
        except Exception as e:
            logger.error(f"Real-time extraction failed: {e}")
            # Return empty result on failure
            return ExtractionResult(extracted_data={}, confidence_scores={})
    
    def extract_post_conversation(
        self,
        full_transcript: str,
        conversation_id: str,
        patient_id: str = "UNKNOWN"
    ) -> ClinicalSummary:
        """
        Comprehensive extraction after conversation ends.
        
        Performs final validation, fills gaps, and generates
        doctor-ready clinical summary.
        
        Args:
            full_transcript: Complete conversation transcript
            conversation_id: Conversation identifier
            patient_id: Patient identifier
            
        Returns:
            ClinicalSummary with complete patient data and doctor briefing
            
        Example:
            >>> summary = extractor.extract_post_conversation(
            ...     transcript, "CONV-001", "P12345"
            ... )
            >>> print(summary.clinical_summary)
            >>> print(summary.urgency_level)
        """
        logger.info("Performing post-conversation extraction...")
        
        prompt = f"""You are reviewing a complete patient intake conversation for a dental clinic.
Extract all clinical information and prepare a structured summary for the dentist.

Full Conversation:
{full_transcript}

Tasks:
1. Extract all required data fields with HIGH accuracy
2. Identify any contradictions in patient statements
3. Flag urgent symptoms requiring immediate attention
4. Classify overall urgency level (low/medium/high/emergency)
5. Recommend appropriate specialist if needed
6. Provide clinical summary paragraph for dentist

Return JSON with this EXACT structure:
{{
  "clinical_data": {{
    "chief_complaint": "string",
    "duration": "string",
    "severity": integer 1-10,
    "location": "string",
    "triggers": ["array"],
    "current_medications": ["array"],
    "allergies": ["array"],
    "previous_dental_work": "string",
    "medical_conditions": ["array"]
  }},
  "confidence_scores": {{
    "chief_complaint": 0.0-1.0,
    ...
  }},
  "clinical_summary": "Natural language paragraph for dentist with clinical insights",
  "red_flags": [
    "Specific urgent concern with clinical reasoning"
  ],
  "urgency_level": "low|medium|high|emergency",
  "recommended_specialist": "endodontist|periodontist|oral_surgeon|general_dentist|emergency_dentist",
  "routing_decision": {{
    "needs_triage": boolean,
    "pre_scheduled": boolean,
    "appointment_confirmed": boolean
  }}
}}

Clinical Summary Guidelines:
- Start with chief complaint and severity
- Include relevant medical history (diabetes, allergies, etc.)
- Note concerning patterns (night pain, swelling, fever)
- Provide clinical interpretation (possible pulpitis, abscess, etc.)
- Keep concise but informative (3-5 sentences)
"""
        
        messages = [Message(role="user", content=prompt)]
        
        try:
            response = self.llm.chat(messages, temperature=0.2, max_tokens=1500)
            
            # Parse response
            result_data = self._parse_extraction_response(response.content)
            
            summary = ClinicalSummary(
                patient_id=patient_id,
                conversation_id=conversation_id,
                timestamp=datetime.now().isoformat(),
                clinical_data=result_data.get("clinical_data", {}),
                confidence_scores=result_data.get("confidence_scores", {}),
                clinical_summary=result_data.get("clinical_summary", ""),
                red_flags=result_data.get("red_flags", []),
                urgency_level=result_data.get("urgency_level", "medium"),
                recommended_specialist=result_data.get("recommended_specialist"),
                routing_decision=result_data.get("routing_decision", {})
            )
            
            logger.info(f"Post-conversation extraction complete: {summary.urgency_level} urgency")
            
            return summary
            
        except Exception as e:
            logger.error(f"Post-conversation extraction failed: {e}")
            raise
    
    def _format_conversation(self, messages: List[Message]) -> str:
        """
        Format conversation messages for extraction.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Formatted conversation string
        """
        formatted = []
        for msg in messages:
            if msg.role == "user":
                formatted.append(f"Patient: {msg.content}")
            elif msg.role == "assistant":
                formatted.append(f"Agent: {msg.content}")
        
        return "\n".join(formatted)
    
    def _parse_extraction_response(self, response_content: str) -> Dict:
        """
        Parse LLM extraction response.
        
        Args:
            response_content: Raw LLM response
            
        Returns:
            Parsed dictionary
        """
        try:
            # Try to find JSON in response
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_content[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Try parsing entire response
                return json.loads(response_content)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction response: {e}")
            logger.debug(f"Response: {response_content}")
            return {}
    
    def update_patient_data(
        self,
        patient_data: PatientData,
        extraction_result: ExtractionResult
    ) -> PatientData:
        """
        Update patient data with extraction results.
        
        Args:
            patient_data: Current patient data
            extraction_result: New extraction results
            
        Returns:
            Updated PatientData object
        """
        extracted = extraction_result.extracted_data
        confidence = extraction_result.confidence_scores
        
        # Update fields if extracted and confidence is sufficient
        for field, value in extracted.items():
            if value is not None and value != [] and value != "":
                field_confidence = confidence.get(field, 0.0)
                
                # Only update if new data has higher confidence or field is empty
                current_confidence = patient_data.confidence_scores.get(field, 0.0)
                
                if field_confidence >= 0.5 and field_confidence >= current_confidence:
                    setattr(patient_data, field, value)
                    patient_data.confidence_scores[field] = field_confidence
                    logger.debug(f"Updated {field} (confidence: {field_confidence:.2f})")
        
        return patient_data


class RoutingEngine:
    """
    Determines appropriate specialist and appointment routing.
    
    Implements business logic for:
    - Specialist selection based on symptoms
    - Urgency-based prioritization
    - Emergency escalation
    """
    
    # Routing rules
    SPECIALIST_KEYWORDS = {
        "endodontist": ["root canal", "pulp", "nerve", "abscess"],
        "periodontist": ["gum", "bleeding", "periodontal", "gum disease"],
        "oral_surgeon": ["wisdom tooth", "extraction", "surgical", "impacted"],
        "orthodontist": ["braces", "alignment", "crooked teeth", "bite"],
        "cosmetic_dentist": ["whitening", "veneer", "cosmetic", "smile"],
    }
    
    URGENCY_RULES = {
        "emergency": ["trauma", "accident", "knocked out", "severe bleeding", "fever + swelling"],
        "high": ["severity >= 8", "swelling", "infection", "unbearable"],
        "medium": ["severity >= 5", "persistent pain", "difficulty eating"],
        "low": ["routine", "cleaning", "checkup", "preventive"]
    }
    
    @staticmethod
    def route_patient(clinical_summary: ClinicalSummary) -> Dict[str, Any]:
        """
        Determine patient routing based on clinical summary.
        
        Args:
            clinical_summary: Clinical summary with patient data
            
        Returns:
            Routing decision dictionary
        """
        chief_complaint = clinical_summary.clinical_data.get("chief_complaint", "").lower()
        severity = clinical_summary.clinical_data.get("severity", 0)
        urgency = clinical_summary.urgency_level
        
        # Determine specialist
        specialist = "general_dentist"  # Default
        
        for spec_type, keywords in RoutingEngine.SPECIALIST_KEYWORDS.items():
            if any(keyword in chief_complaint for keyword in keywords):
                specialist = spec_type
                break
        
        # Override for emergencies
        if urgency == "emergency" or severity >= 9:
            specialist = "emergency_dentist"
        
        routing = {
            "recommended_specialist": specialist,
            "urgency_level": urgency,
            "priority_score": severity * 10,  # 0-100 scale
            "needs_immediate_attention": urgency in ["emergency", "high"],
            "estimated_wait_time": RoutingEngine._estimate_wait_time(urgency),
            "appointment_type": RoutingEngine._determine_appointment_type(severity, urgency)
        }
        
        return routing
    
    @staticmethod
    def _estimate_wait_time(urgency: str) -> str:
        """Estimate wait time based on urgency"""
        wait_times = {
            "emergency": "Same day",
            "high": "Within 24 hours",
            "medium": "Within 3-5 days",
            "low": "Within 1-2 weeks"
        }
        return wait_times.get(urgency, "Unknown")
    
    @staticmethod
    def _determine_appointment_type(severity: int, urgency: str) -> str:
        """Determine appointment type"""
        if urgency == "emergency" or severity >= 9:
            return "emergency"
        elif severity >= 7:
            return "urgent"
        elif severity >= 4:
            return "standard"
        else:
            return "routine"


# Example usage
if __name__ == "__main__":
    from pre_visit_agent.config.config import AppConfig
    from pre_visit_agent.services.llm_service import LLMService
    
    print("Testing Data Extraction...")
    
    # Initialize configuration
    config = AppConfig()
    
    # Initialize services
    llm = LLMService(config.llm)
    extractor = DataExtractor(llm, config.extraction_schema)
    
    # Test real-time extraction
    print("\n=== Test 1: Real-time Extraction ===")
    
    test_conversation = [
        Message(role="assistant", content="مرحباً، أنا مريم. ما المشكلة؟"),
        Message(role="user", content="عندي ألم شديد في ضرسي من ٣ أيام"),
        Message(role="assistant", content="أفهم. أين الألم بالضبط؟"),
        Message(role="user", content="الضرس العلوي الأيمن، ألم ٨ من ١٠"),
    ]
    
    patient_data = PatientData()
    result = extractor.extract_real_time(test_conversation, patient_data)
    
    print(f"Extracted: {json.dumps(result.to_dict(), indent=2, ensure_ascii=False)}")
    
    # Test post-conversation extraction
    print("\n=== Test 2: Post-Conversation Extraction ===")
    
    full_transcript = """Agent: مرحباً، أنا مريم من العيادة. كيف يمكنني مساعدتك؟
Patient: عندي ألم في ضرسي
Agent: متى بدأ الألم؟
Patient: من ٣ أيام تقريباً
Agent: على مقياس من ١ ل ١٠، قد إيه الألم؟
Patient: ٨ من ١٠، شديد جداً
Agent: أي ضرس بالضبط؟
Patient: الضرس العلوي في الجهة اليمين
Agent: إيه اللي بيزود الألم؟
Patient: لما أشرب حاجة سخنة أو أمضغ عليه
Agent: بتاخد أي أدوية حالياً؟
Patient: باخد بروفين ٤٠٠ بس مش بيجيب نتيجة كبيرة
Agent: عندك حساسية من أي أدوية؟
Patient: أيوه، عندي حساسية من البنسلين
Agent: عندك أي أمراض مزمنة؟
Patient: عندي سكر من النوع التاني، باخد ميتفورمين
"""
    
    summary = extractor.extract_post_conversation(
        full_transcript,
        "CONV-TEST-001",
        "P12345"
    )
    
    print(f"\nClinical Summary:\n{summary.clinical_summary}")
    print(f"\nUrgency: {summary.urgency_level}")
    print(f"Specialist: {summary.recommended_specialist}")
    print(f"Red Flags: {summary.red_flags}")
    
    # Test routing
    print("\n=== Test 3: Patient Routing ===")
    routing = RoutingEngine.route_patient(summary)
    print(json.dumps(routing, indent=2))
