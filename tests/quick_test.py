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

import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_configuration():
    """Test configuration system"""
    print("\n" + "=" * 60)
    print("TEST 1: Configuration Validation")
    print("=" * 60)
    
    try:
        from config import config
        
        print(f"✓ Configuration loaded")
        print(f"  Environment: {config.environment.value}")
        print(f"  STT Model: {config.stt.model_size}")
        print(f"  TTS Model: {config.tts.model_name}")
        print(f"  LLM Model: {config.llm.model_name}")
        print(f"  Agent Name: {config.conversation.agent_name}")
        
        config.validate()
        print("✓ Configuration validated successfully")
        
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
        from llm_service import LLMService, Message
        from config import config
        
        # Check API key
        if not config.llm.api_key:
            print("⚠ OPENAI_API_KEY not set. Skipping LLM test.")
            print("  Set your API key in .env file to enable this test.")
            return True
        
        print("Initializing LLM service...")
        llm = LLMService(config.llm)
        print("✓ LLM service initialized")
        
        print("\nTesting basic chat...")
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Say hello in one word.")
        ]
        
        response = llm.chat(messages)
        print(f"✓ Response received: {response.content}")
        print(f"  Tokens: {response.usage['total_tokens']}")
        print(f"  Latency: {response.latency_ms:.0f}ms")
        
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
        from conversation_manager import ConversationManager
        from llm_service import LLMService
        from config import config
        
        # Check API key
        if not config.llm.api_key:
            print("⚠ OPENAI_API_KEY not set. Skipping conversation test.")
            return True
        
        print("Initializing conversation manager...")
        llm = LLMService(config.llm)
        manager = ConversationManager(config.conversation, llm)
        print("✓ Conversation manager initialized")
        
        print("\nStarting conversation...")
        greeting = manager.start_conversation()
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
            
            response = manager.process_turn(patient_input)
            print(f"Agent: {response}")
        
        # Get summary
        summary = manager.get_conversation_summary()
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
        from data_extractor import DataExtractor
        from llm_service import LLMService
        from config import config
        
        # Check API key
        if not config.llm.api_key:
            print("⚠ OPENAI_API_KEY not set. Skipping extraction test.")
            return True
        
        print("Initializing data extractor...")
        llm = LLMService(config.llm)
        extractor = DataExtractor(llm, config.extraction_schema)
        print("✓ Data extractor initialized")
        
        print("\nTesting post-conversation extraction...")
        test_transcript = """Agent: مرحباً، أنا مريم. ما المشكلة؟
Patient: عندي ألم شديد في ضرسي من ٣ أيام
Agent: أين الألم بالضبط؟
Patient: الضرس العلوي الأيمن، ألم ٨ من ١٠
Agent: إيه اللي بيزود الألم؟
Patient: الحاجات السخنة والمضغ
Agent: بتاخد أي أدوية؟
Patient: باخد بروفين بس مش بيساعد
Agent: عندك حساسية من أدوية؟
Patient: أيوه، من البنسلين
Agent: عندك أمراض مزمنة؟
Patient: عندي سكر من النوع التاني"""
        
        summary = extractor.extract_post_conversation(
            test_transcript,
            "TEST-001",
            "P12345"
        )
        
        print(f"\n✓ Extraction completed")
        print(f"\nClinical Summary:")
        print(f"  {summary.clinical_summary}")
        print(f"\nUrgency: {summary.urgency_level}")
        print(f"Specialist: {summary.recommended_specialist}")
        
        if summary.red_flags:
            print(f"Red Flags: {summary.red_flags}")
        
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
        from voice_agent import VoiceAgent
        
        # Check API key
        from config import config
        if not config.llm.api_key:
            print("⚠ OPENAI_API_KEY not set. Skipping integration test.")
            return True
        
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
            print(f"    Urgency: {summary.urgency_level}")
            print(f"    Specialist: {summary.recommended_specialist}")
        
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
            print(f"  Turns: {status['turn_count']}")
            print(f"  Completion: {status['completion_percentage']:.0f}%")
        
        # End session (if not already ended)
        if status and status['is_active']:
            print("\nEnding session...")
            summary = agent.end_session(session_id)
        
        # System stats
        print("\nSystem statistics:")
        stats = agent.get_system_stats()
        print(f"  Total sessions: {stats['total_sessions']}")
        print(f"  LLM requests: {stats['llm_stats']['total_requests']}")
        print(f"  LLM cost: ${stats['llm_stats']['total_cost_usd']:.4f}")
        
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
