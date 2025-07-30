#!/usr/bin/env python3
"""
Test chatbot application functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import create_app
from database.connection import init_database
import json

def test_chatbot_app():
    """Test the chatbot application"""
    try:
        print("Initializing database...")
        init_database()
        print("Database initialized")
        
        print("Creating Flask app...")
        app = create_app()
        print("Flask app created successfully")
        
        # Test the session creation endpoint
        with app.test_client() as client:
            print("Testing session creation endpoint...")
            response = client.post('/api/chatbot/sessions', 
                                json={'user_id': 'test_user', 'patient_id': None})
            
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.get_json()}")
            
            if response.status_code == 201:
                print("✅ Session creation endpoint works!")
                session_data = response.get_json()
                session_id = session_data['data']['session_id']
                
                # Test the chat endpoint
                print("Testing chat endpoint...")
                chat_response = client.post('/api/chatbot/chat',
                                         json={
                                             'session_id': session_id,
                                             'message': 'Find patient information',
                                             'user_id': 'test_user'
                                         })
                
                print(f"Chat response status: {chat_response.status_code}")
                print(f"Chat response data: {chat_response.get_json()}")
                
                if chat_response.status_code == 200:
                    print("✅ Chat endpoint works!")
                else:
                    print("❌ Chat endpoint failed")
            else:
                print("❌ Session creation endpoint failed")
                
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chatbot_app() 