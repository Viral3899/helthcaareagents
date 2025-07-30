#!/usr/bin/env python3
"""
Test script to check chatbot session creation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import init_database, get_db_session
from database.models import ChatbotConversation, ChatbotContext, ChatbotMessage
from datetime import datetime
import uuid

def test_session_creation():
    """Test chatbot session creation"""
    try:
        print("Initializing database...")
        init_database()
        print("Database initialized successfully")
        
        print("Testing session creation...")
        session_id = str(uuid.uuid4())
        
        session_gen = get_db_session()
        session = next(session_gen)
        try:
            # Create conversation
            conversation = ChatbotConversation(
                session_id=session_id,
                user_id='test_user',
                patient_id=None,
                status="active",
                message_count=0
            )
            session.add(conversation)
            session.flush()  # Get the ID
            
            # Create initial context
            context = ChatbotContext(
                session_id=session_id,
                context_data={
                    "session_start": datetime.utcnow().isoformat(),
                    "user_id": 'test_user',
                    "patient_id": None
                },
                metadata={
                    "created_by": "test",
                    "initial_message": "Hello"
                }
            )
            session.add(context)
            
            # Process initial message
            message = ChatbotMessage(
                conversation_id=conversation.id,
                message_type='user',
                content="Hello",
                intent="greeting",
                confidence=1.0,
                entities=[],
                created_at=datetime.utcnow()
            )
            session.add(message)
            
            # Add bot response message
            bot_message = ChatbotMessage(
                conversation_id=conversation.id,
                message_type='bot',
                content="Hello! I'm your healthcare assistant. How can I help you today?",
                intent="greeting",
                confidence=1.0,
                entities=[],
                created_at=datetime.utcnow()
            )
            session.add(bot_message)
            conversation.message_count = 2
            
            session.commit()
            print("Session created successfully!")
            
            # Verify the session was created
            created_conversation = session.query(ChatbotConversation).filter(
                ChatbotConversation.session_id == session_id
            ).first()
            
            if created_conversation:
                print(f"Conversation found: {created_conversation.id}")
                print(f"Message count: {created_conversation.message_count}")
                
                messages = session.query(ChatbotMessage).filter(
                    ChatbotMessage.conversation_id == created_conversation.id
                ).all()
                
                print(f"Messages found: {len(messages)}")
                for msg in messages:
                    print(f"  - {msg.message_type}: {msg.content}")
            else:
                print("ERROR: Conversation not found!")
        finally:
            session.close()
                
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_session_creation() 