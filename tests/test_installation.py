"""
Simple Installation Test
========================

Quick test to verify the package is installed correctly.
"""

import sys

def test_imports():
    """Test that all modules can be imported"""
    print("\n" + "="*60)
    print("Testing Package Installation")
    print("="*60 + "\n")
    
    tests_passed = 0
    tests_total = 0
    
    # Test core imports
    modules = [
        ("pre_visit_agent.config.config", "Config module"),
        ("pre_visit_agent.services.llm_service", "LLM service"),
        ("pre_visit_agent.services.stt_service", "STT service"),
        ("pre_visit_agent.services.tts_service", "TTS service"),
        ("pre_visit_agent.core.conversation_manager", "Conversation manager"),
        ("pre_visit_agent.core.data_extractor", "Data extractor"),
    ]
    
    for module_name, description in modules:
        tests_total += 1
        try:
            __import__(module_name)
            print(f"✓ {description:30s} OK")
            tests_passed += 1
        except Exception as e:
            print(f"✗ {description:30s} FAILED: {e}")
    
    print("\n" + "="*60)
    print(f"Results: {tests_passed}/{tests_total} tests passed")
    print("="*60 + "\n")
    
    if tests_passed == tests_total:
        print("🎉 Installation successful! All modules loaded correctly.\n")
        return True
    else:
        print("⚠️  Some modules failed to load. Check errors above.\n")
        return False


def test_config():
    """Test configuration loading"""
    print("\n" + "="*60)
    print("Testing Configuration")
    print("="*60 + "\n")
    
    try:
        from pre_visit_agent.config.config import AppConfig, Environment
        
        config = AppConfig()
        
        print(f"✓ Configuration loaded")
        print(f"  LLM Provider: {config.llm.provider}")
        print(f"  LLM Model: {config.llm.model_name}")
        print(f"  STT Model: {config.stt.model_size}")
        print(f"  API Key set: {'Yes' if config.llm.api_key else 'No'}")
        
        if not config.llm.api_key:
            print("\n⚠️  Warning: OPENAI_API_KEY not set in .env file")
            print("   Add your API key to .env to enable LLM tests\n")
        else:
            print("\n✓ OpenAI API key configured\n")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_simple():
    """Test LLM with a simple request"""
    print("\n" + "="*60)
    print("Testing LLM Service")
    print("="*60 + "\n")
    
    try:
        from pre_visit_agent.config.config import AppConfig
        from pre_visit_agent.services.llm_service import LLMService, Message, MessageRole
        
        config = AppConfig()
        
        if not config.llm.api_key:
            print("⚠️  Skipping LLM test - no API key configured")
            print("   Set OPENAI_API_KEY in .env to enable this test\n")
            return True
        
        print("Initializing LLM service...")
        llm = LLMService(config.llm)
        print("✓ LLM service initialized\n")
        
        print("Sending test request...")
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            Message(role=MessageRole.USER, content="Say 'Hello' in one word.")
        ]
        
        response = llm.chat(messages)
        
        print(f"✓ Response received: '{response.content}'")
        print(f"  Model: {response.model}")
        print(f"  Tokens: {response.usage.get('total_tokens', 'N/A')}")
        print(f"  Latency: {response.latency_ms:.0f}ms\n")
        
        print("✓ LLM service working correctly!\n")
        return True
        
    except Exception as e:
        print(f"✗ LLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("PRE-VISIT VOICE AGENT - Installation Test")
    print("="*60)
    
    all_passed = True
    
    # Test 1: Imports
    if not test_imports():
        all_passed = False
    
    # Test 2: Configuration
    if not test_config():
        all_passed = False
    
    # Test 3: LLM (optional, requires API key)
    if not test_llm_simple():
        all_passed = False
    
    # Final summary
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nNext steps:")
        print("  1. Your package is installed correctly")
        print("  2. Configuration is loaded")
        print("  3. LLM service is working")
        print("\nYou can now run the full voice agent!")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("\nPlease fix the errors above before proceeding.")
    print("="*60 + "\n")
    
    sys.exit(0 if all_passed else 1)
