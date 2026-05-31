"""Conversation management module for handling multi-turn dialogue"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

import config


class ConversationManager:
    """Manages conversation history and state"""
    
    def __init__(self):
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": """أنت مريم، موظفة استقبال ودودة في عيادة كيربوت الطبية.

You are Mariam, a friendly receptionist at CareBot Clinic.
You're conducting a pre-visit consultation call to gather medical information.

Style Guidelines:
- Keep responses SHORT (1-2 sentences maximum)
- Ask ONE question at a time  
- Show empathy and understanding
- Speak calmly, warmly, and naturally like a human receptionist
- Speak slowly and clearly, never rushed
- Use natural conversational tone with gentle punctuation and short pauses
- Add appropriate pauses with punctuation (. , ! ?)
- Respond in the SAME language the patient uses

Required Information:
1. Chief complaint
2. Duration  
3. Pain severity 1-10
4. Location
5. Triggers
6. Current medications
7. Allergies
8. Medical conditions

Important:
- If diabetes + dental infection → high priority
- Note allergies for treatment planning"""}
        ]
        self.turn_count = 0
        self.assistant_turn_events: List[Dict[str, Any]] = []
        self.preferred_language = "en"
    
    def add_user_message(self, message: str):
        """Add user message to history"""
        self.history.append({"role": "user", "content": message})
    
    def add_assistant_message(self, message: str):
        """Add assistant message to history"""
        self.history.append({"role": "assistant", "content": message})
        self.turn_count += 1
    
    def get_history(self):
        """Get conversation history"""
        return self.history

    def set_preferred_language(self, language_code: Optional[str]):
        """Persist the user's preferred reply language for future turns."""
        normalized = config.normalize_language_code(language_code)
        if normalized in {"ar", "en", "hi"}:
            self.preferred_language = normalized

    def get_preferred_language(self) -> str:
        return getattr(self, "preferred_language", "en")

    def get_history_for_response(self):
        """Get prompt history with a strong reminder to answer in the selected language."""
        language_names = {
            "ar": "Arabic",
            "en": "English",
            "hi": "Hindi",
        }
        language_name = language_names.get(self.get_preferred_language(), "English")
        return self.history + [
            {
                "role": "system",
                "content": (
                    f"Respond only in {language_name}. "
                    f"If the user asks to switch languages, comply immediately and continue in {language_name}. "
                    f"Speak calmly, slowly, and clearly with short natural sentences and gentle pauses."
                ),
            }
        ]
    
    def is_complete(self) -> bool:
        """Check if conversation should end"""
        return self.turn_count >= config.MAX_CONVERSATION_TURNS

    def add_assistant_turn_event(
        self,
        generated_text: str,
        played_text: str,
        interrupted: bool,
        completed: bool,
    ):
        """Track assistant turn delivery state for observability/debugging."""
        self.assistant_turn_events.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "generated_text": generated_text,
                "played_text": played_text,
                "interrupted": interrupted,
                "completed": completed,
            }
        )
