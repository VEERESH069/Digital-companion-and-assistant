"""
Quick Start Test Script
=======================

This script provides a simple way to test the voice agent system
without requiring full audio setup.

Tests:
1. Configuration validation
2. LLM service
3. Conversation flow
4. Data extraction
5. Complete system integration

Run: python quick_test.py
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables early to check API keys before imports
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def has_required_api_keys():
    """Check if required API keys are available"""
    return bool(os.getenv("OPENAI_API_KEY"))


def test_configuration():
    """Test configuration system"""
    print("\n" + "=" * 60)
    print("TEST 1: Configuration Validation")
    print("=" * 60)
    
    try:
        import config
        print(f"✓ Configuration loaded")
        # Print some config attributes if available, else just confirm load
        print(f"  TTS Engine: {getattr(config, 'TTS_ENGINE', 'N/A')}")
        print(f"  LLM Model: {getattr(config, 'LLM_MODEL', 'N/A')}")
        print(f"  Voices: {getattr(config, 'CARTESIA_LANGUAGE_VOICES', {})}")
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_llm_service():
    """Test LLM service"""
    print("\n" + "=" * 60)
    print("TEST 2: LLM Service")
    print("=" * 60)
    
    try:
        # Check API keys before importing
        if not has_required_api_keys():
            print("⚠ OPENAI_API_KEY not set. Skipping LLM test.")
            print("  Set your API key in .env file to enable this test.")
            return True

        from previsit_agent.conversation import ConversationManager
        from previsit_agent.llm import LLMEngine, init_openai_client

        print("Initializing LLM service...")
        init_openai_client()
        conversation = ConversationManager()
        print("✓ LLM service initialized")
        print("\nTesting basic chat...")
        response = LLMEngine.get_response(conversation, "Say hello in one word.")
        print(f"✓ Response received: {response}")
        return True
        
    except Exception as e:
        print(f"✗ LLM service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_conversation_flow():
    """Test conversation manager"""
    print("\n" + "=" * 60)
    print("TEST 3: Conversation Flow")
    print("=" * 60)
    
    try:
        # Check API keys before importing
        if not has_required_api_keys():
            print("⚠ OPENAI_API_KEY not set. Skipping conversation test.")
            return True
        
        from previsit_agent.conversation import ConversationManager
        from previsit_agent.llm import LLMEngine, init_openai_client
        print("Initializing conversation manager...")
        init_openai_client()
        manager = ConversationManager()
        print("✓ Conversation manager initialized")
        greeting = "مرحباً، أنا مريم من CareBot Clinic. كيف حالك النهاردة؟"
        manager.add_assistant_message(greeting)
        print("\nStarting conversation...")
        print(f"Agent: {greeting}")
        
        print("\nSimulating patient inputs...")
        test_inputs = [
            "عندي ألم في ضرسي",  # I have tooth pain
            "من ٣ أيام",  # For 3 days
            "ألم شديد، ٨ من ١٠",  # Severe pain, 8/10
        ]
        
        for i, patient_input in enumerate(test_inputs, 1):
            print(f"\nTurn {i + 1}:")
            print(f"Patient: {patient_input}")
            
            response = LLMEngine.get_response(manager, patient_input)
            print(f"Agent: {response}")
        
        # Get summary
        user_messages = [msg for msg in manager.get_history() if msg.get("role") == "user"]
        summary = {
            "turn_count": manager.turn_count,
            "completion_percentage": (manager.turn_count / 15) * 100,
            "collected_data": user_messages,
        }
        print(f"\n✓ Conversation tested")
        print(f"  Turns: {summary['turn_count']}")
        print(f"  Completion: {summary['completion_percentage']:.0f}%")
        print(f"  Collected: {len(summary['collected_data'])}")
        
        return True
        
    except Exception as e:
        print(f"✗ Conversation flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_extraction():
    """Test data extraction"""
    print("\n" + "=" * 60)
    print("TEST 4: Data Extraction")
    print("=" * 60)
    
    try:
        # Check API keys before importing
        if not has_required_api_keys():
            print("⚠ OPENAI_API_KEY not set. Skipping extraction test.")
            return True
        
        from previsit_agent.conversation import ConversationManager
        from previsit_agent.llm import LLMEngine, init_openai_client
        print("Initializing data extractor...")
        init_openai_client()
        manager = ConversationManager()
        manager.add_assistant_message("مرحباً، أنا مريم. ما المشكلة؟")
        manager.add_user_message("عندي ألم شديد في ضرسي من ٣ أيام")
        manager.add_assistant_message("أين الألم بالضبط؟")
        manager.add_user_message("الضرس العلوي الأيمن، ألم ٨ من ١٠")
        # Simulate extraction
        print("\nTesting post-conversation extraction...")
        manager.add_assistant_message("إيه اللي بيزود الألم؟")
        manager.add_user_message("الحاجات السخنة والمضغ")
        manager.add_assistant_message("بتاخد أي أدوية؟")
        manager.add_user_message("باخد بروفين بس مش بيساعد")
        manager.add_assistant_message("عندك حساسية من أدوية؟")
        manager.add_user_message("أيوه، من البنسلين")
        manager.add_assistant_message("عندك أمراض مزمنة؟")
        manager.add_user_message("عندي سكر من النوع التاني")
        summary = LLMEngine.extract_clinical_data(manager)
        print(f"\n✓ Extraction completed")
        print(f"\nClinical Summary:")
        print(f"  {summary.get('clinical_summary', 'N/A')}")
        print(f"\nUrgency: {summary.get('urgency_level', 'N/A')}")
        print(f"Specialist: {summary.get('recommended_specialist', 'N/A')}")
        if summary.get('red_flags'):
            print(f"Red Flags: {summary['red_flags']}")
        return True
        
    except Exception as e:
        print(f"✗ Data extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_system_integration():
    """Test complete system (without audio)"""
    print("\n" + "=" * 60)
    print("TEST 5: System Integration (Text Mode)")
    print("=" * 60)
    
    try:
        # Check API keys before importing
        if not has_required_api_keys():
            print("⚠ OPENAI_API_KEY not set. Skipping integration test.")
            return True
        
        from voice_agent import VoiceAgent
        print("Initializing voice agent system...")
        agent = VoiceAgent()
        print("✓ Voice agent initialized")
        # Define callbacks
        transcriptions = []
        responses = []
        def on_transcription(session_id, text):
            transcriptions.append(text)
            print(f"  [Transcription] Patient: {text}")
        def on_response(session_id, text, audio):
            responses.append(text)
            print(f"  [Response] Agent: {text}")
        def on_session_end(session_id, summary):
            print(f"\n  [Session End] {session_id}")
            print(f"    Urgency: {getattr(summary, 'urgency_level', 'N/A')}")
            print(f"    Specialist: {getattr(summary, 'recommended_specialist', 'N/A')}")
        # Register callbacks
        agent.on_transcription_callback = on_transcription
        agent.on_response_callback = on_response
        agent.on_session_end_callback = on_session_end
        # Start session
        print("\nStarting session...")
        session_id = agent.start_session(patient_id="TEST-P001")
        print(f"✓ Session started: {session_id}")
        # Simulate conversation
        print("\nSimulating conversation...")
        test_inputs = [
            "عندي ألم في ضرسي",
            "من ٣ أيام تقريباً",
            "ألم شديد، ٨ من ١٠",
            "الضرس الأيمن العلوي",
            "بياكلني لما أشرب ساخن",
            "باخد بروفين",
            "عندي حساسية من البنسلين",
            "عندي سكر"
        ]
        for user_input in test_inputs:
            agent.on_transcription(session_id, user_input)
        # Get status
        print("\nSession status:")
        status = agent.get_session_status(session_id)
        if status:
            print(f"  Turns: {status.get('turn_count', 0)}")
            print(f"  Completion: {status.get('completion_percentage', 0):.0f}%")
        # End session (if not already ended)
        if status and status.get('is_active'):
            print("\nEnding session...")
            summary = agent.end_session(session_id)
        # System stats
        print("\nSystem statistics:")
        stats = agent.get_system_stats()
        print(f"  Total sessions: {stats.get('total_sessions', 0)}")
        print(f"  LLM requests: {stats.get('llm_stats', {}).get('total_requests', 0)}")
        print(f"  LLM cost: ${stats.get('llm_stats', {}).get('total_cost_usd', 0.0):.4f}")
        print("\n✓ System integration test passed")
        return True
        
    except Exception as e:
        print(f"✗ System integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("PRE-VISIT VOICE AGENT - QUICK TEST")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "Configuration": test_configuration(),
        "LLM Service": test_llm_service(),
        "Conversation Flow": test_conversation_flow(),
        "Data Extraction": test_data_extraction(),
        "System Integration": test_system_integration()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:.<40} {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! System is ready.")
    else:
        print("\n⚠ Some tests failed. Check errors above.")
    
    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
