#!/usr/bin/env python3
"""
Test script to verify chatbot fixes
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_chatbot_response():
    """Test the ChatbotResponse dataclass"""
    from agents.chatbot_agent import ChatbotResponse
    
    # Test creating a response with default response_time
    response = ChatbotResponse(
        message="Hello, how can I help you?",
        intent="general_help",
        confidence=0.8,
        entities={},
        actions=[],
        context_update={},
        suggestions=["Ask about patients", "Schedule appointment"]
    )
    
    print(f"✅ ChatbotResponse created successfully")
    print(f"   Message: {response.message}")
    print(f"   Intent: {response.intent}")
    print(f"   Response time: {response.response_time}")
    
    # Test accessing response_time attribute
    try:
        response_time = response.response_time
        print(f"✅ response_time attribute accessible: {response_time}")
    except AttributeError as e:
        print(f"❌ response_time attribute error: {e}")
        return False
    
    return True

def test_intent_analysis_fallback():
    """Test the intent analysis fallback mechanism"""
    from agents.chatbot_agent import ChatbotAgent
    
    # Create a mock tools dictionary
    tools = {}
    
    # Create chatbot agent
    agent = ChatbotAgent(tools)
    
    # Test intent analysis with various messages
    test_messages = [
        "I need to find patient John Smith",
        "Can you schedule an appointment for me?",
        "Show me the medical records",
        "This is an emergency situation",
        "What are the vital signs?",
        "Hello, how are you?"
    ]
    
    context = {"conversation_history": []}
    
    for message in test_messages:
        try:
            intent_analysis = agent._analyze_intent(message, context)
            print(f"✅ Intent analysis for '{message[:30]}...': {intent_analysis['intent']}")
        except Exception as e:
            print(f"❌ Intent analysis failed for '{message[:30]}...': {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("Testing chatbot fixes...")
    
    # Test 1: ChatbotResponse dataclass
    if test_chatbot_response():
        print("✅ ChatbotResponse test passed")
    else:
        print("❌ ChatbotResponse test failed")
        sys.exit(1)
    
    # Test 2: Intent analysis fallback
    if test_intent_analysis_fallback():
        print("✅ Intent analysis fallback test passed")
    else:
        print("❌ Intent analysis fallback test failed")
        sys.exit(1)
    
    print("\n🎉 All tests passed! The chatbot fixes are working correctly.")
    print("\nYou can now:")
    print("1. Start the application: python src/main.py")
    print("2. Access the chatbot UI: http://localhost:5000/chatbot")
    print("3. Test the chatbot functionality") 