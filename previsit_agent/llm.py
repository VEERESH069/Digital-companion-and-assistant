"""Large Language Model integration module"""

import os
import json
import re
import threading
import queue
import tempfile
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

import config
from .conversation import ConversationManager

# Global OpenAI client (initialized from main)
client = None


def init_openai_client():
    """Initialize OpenAI client"""
    global client
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not set in .env file")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return client


class LLMEngine:
    """Large Language Model Engine"""

    @staticmethod
    def stream_and_speak(conversation: ConversationManager, user_message: str, tts_engine) -> Optional[str]:
        """3-thread pipeline: LLM streams → sentence queue → Cartesia pre-fetches → playback.
        Zero gap between sentences because next audio is pre-fetched while current plays."""
        cancel_event = threading.Event()
        stop_speaking = cancel_event
        sentence_q: queue.Queue[Optional[str]] = queue.Queue()
        pcm_q: queue.Queue[Any] = queue.Queue(maxsize=100)
        full_response_box: List[str] = [""]

        # ── Thread 1: stream LLM tokens, split into sentences ──────────────
        def llm_worker():
            try:
                conversation.add_user_message(user_message)
                print("   🧠 Thinking...", end="", flush=True)
                stream = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=conversation.get_history_for_response(),  # type: ignore
                    temperature=config.LLM_TEMPERATURE,
                    max_tokens=config.LLM_MAX_TOKENS_RESPONSE,
                    stream=True
                )
                buf = ""
                for chunk in stream:
                    if stop_speaking.is_set():
                        break
                    token = chunk.choices[0].delta.content or ""
                    full_response_box[0] += token
                    buf += token
                    # Split on sentence-ending chars followed by space or end
                    parts = re.split(r'(?<=[.!?\u061f\u060c])\s+', buf)
                    for sentence in parts[:-1]:  # all but last (may be incomplete)
                        if stop_speaking.is_set():
                            break
                        s = sentence.strip()
                        if len(s) > 2:
                            sentence_q.put(s)
                    if stop_speaking.is_set():
                        break
                    buf = parts[-1]  # keep the incomplete tail
                if (not stop_speaking.is_set()) and buf.strip() and len(buf.strip()) > 2:
                    sentence_q.put(buf.strip())
            except Exception as e:
                print(f"\n   ✗ LLM error: {e}")
            finally:
                sentence_q.put(None)  # sentinel

        # ── Thread 2: for each sentence, fetch Cartesia PCM into pcm_q ─────
        def tts_worker():
            try:
                first = True
                while True:
                    sentence = sentence_q.get()
                    if sentence is None:
                        break
                    if cancel_event.is_set():
                        # drain sentence queue, don't fetch more
                        while not sentence_q.empty():
                            try:
                                sentence_q.get_nowait()
                            except:
                                break
                        break
                    if first:
                        print()  # newline after "Thinking..."
                        first = False
                    print(f"\n🔊 Agent: {sentence}")
                    tts_engine._fetch_pcm_to_queue(sentence, pcm_q)
            finally:
                pcm_q.put(None)  # sentinel

        llm_t = threading.Thread(target=llm_worker, daemon=True)
        tts_t = threading.Thread(target=tts_worker, daemon=True)
        llm_t.start()
        tts_t.start()

        # Main thread: play continuously from pcm_q (zero gaps between sentences)
        interrupted, delivered_sentences = tts_engine.play_continuous(pcm_q)

        if interrupted:
            cancel_event.set()

        tts_t.join(timeout=5)
        llm_t.join(timeout=5)

        full = full_response_box[0].strip()
        played = " ".join(delivered_sentences).strip()

        # Keep prompt history aligned with what patient actually heard.
        if played:
            conversation.add_assistant_message(played)

        conversation.add_assistant_turn_event(
            generated_text=full,
            played_text=played,
            interrupted=interrupted,
            completed=(not interrupted and bool(full) and full == played),
        )

        return played or None

    @staticmethod
    def get_response(conversation: ConversationManager, user_message: str) -> Optional[str]:
        """Get AI response (non-streaming, kept for internal use)"""
        try:
            conversation.add_user_message(user_message)
            
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=conversation.get_history_for_response(),  # type: ignore
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS_RESPONSE
            )
            
            ai_response = response.choices[0].message.content
            if ai_response:
                conversation.add_assistant_message(ai_response)
                return ai_response
            
            return "معلش، مفهمتش. ممكن تعيد تاني؟"
            
        except Exception as e:
            print(f"   ✗ LLM Error: {e}")
            return "Sorry, I encountered an error. Could you repeat that?"
    
    @staticmethod
    def extract_clinical_data(conversation: ConversationManager) -> dict:
        """Extract structured clinical data from conversation"""
        history = conversation.get_history()
        transcript = "\n".join([
            f"{'Agent' if msg['role'] == 'assistant' else 'Patient'}: {msg['content']}"
            for msg in history if msg['role'] != 'system'
        ])
        
        extraction_prompt = f"""
You are a clinical data extraction AI. Analyze the following medical conversation and extract structured clinical data. 

CONVERSATION:
{transcript}

Instructions:
- Carefully read the conversation and extract all relevant clinical information, even if the patient uses informal or non-medical language.
- If a field is not mentioned, set it to null or an empty list as appropriate.
- For lists (triggers, medications, allergies, medical_conditions, red_flags), always return a list (even if empty).
- For severity, ensure it is an integer between 1 and 10, or null if not specified.
- For confidence scores, use a float between 0.0 and 1.0 for each field, reflecting your certainty.
- For clinical_summary, write a concise 2-3 sentence summary in plain language.
- For urgency_level, choose only one of: LOW, MEDIUM, HIGH, CRITICAL.
- For recommended_specialist, use a specific type (e.g., General Dentist, Endodontist, Oral Surgeon).
- Do not invent data. Only extract what is present or implied in the conversation.
- Return ONLY valid, minified JSON (no comments, no extra text, no markdown, no explanation).

Example output:
{{"clinical_data":{{"chief_complaint":"Toothache","duration":"3 days","severity":7,"location":"lower left molar","triggers":["cold drinks"],"current_medications":["ibuprofen"],"allergies":[],"previous_dental_work":null,"medical_conditions":["diabetes"]}},"confidence_scores":{{"chief_complaint":0.95,"duration":0.9,"severity":0.8,"location":0.85,"triggers":0.7,"current_medications":0.8,"allergies":1.0,"previous_dental_work":0.5,"medical_conditions":0.9}},"clinical_summary":"The patient reports a 3-day toothache in the lower left molar, worsened by cold drinks. No allergies. Has diabetes.","red_flags":[],"urgency_level":"HIGH","recommended_specialist":"Endodontist"}}
"""

        try:
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0.1,
                max_tokens=config.LLM_MAX_TOKENS_EXTRACTION
            )
            
            result_text = response.choices[0].message.content or "{}"
            
            # Clean JSON
            result_text = result_text.strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            try:
                return json.loads(result_text)
            except Exception as parse_err:
                print(f"   ⚠ JSON parsing error: {parse_err}\n   Raw output: {result_text}")
                return get_default_clinical_data()
            
        except Exception as e:
            print(f"   ⚠ Extraction error: {e}")
            return get_default_clinical_data()


def get_default_clinical_data() -> dict:
    """Default clinical data structure"""
    return {
        "clinical_data": {
            "chief_complaint": None,
            "duration": None,
            "severity": None,
            "location": None,
            "triggers": [],
            "current_medications": [],
            "allergies": [],
            "previous_dental_work": None,
            "medical_conditions": []
        },
        "confidence_scores": {k: 0.0 for k in [
            "chief_complaint", "duration", "severity", "location",
            "triggers", "current_medications", "allergies",
            "previous_dental_work", "medical_conditions"
        ]},
        "clinical_summary": "Consultation completed. Data extraction pending review.",
        "red_flags": [],
        "urgency_level": "MEDIUM",
        "recommended_specialist": "General Dentist"
    }
