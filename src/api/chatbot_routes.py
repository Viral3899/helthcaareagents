"""
Chatbot API Routes Module - FIXED VERSION

This module defines API endpoints for the chatbot functionality,
including conversation management, context keeping, and message processing.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.connection import get_db_session
from database.models import ChatbotConversation, ChatbotMessage, ChatbotContext
from utils.validators import validate_chatbot_message
from utils.logger import log_api_event, log_chatbot_event

# Create chatbot API blueprint
chatbot_bp = Blueprint('chatbot', __name__)

def serialize_context_data(data):
    """
    Safely serialize context data, removing non-JSON serializable objects
    """
    if not data:
        return {}
    
    if isinstance(data, dict):
        serialized = {}
        for key, value in data.items():
            try:
                # Test if value is JSON serializable
                json.dumps(value)
                serialized[key] = value
            except (TypeError, ValueError):
                # Skip non-serializable values or convert them
                if hasattr(value, '__dict__'):
                    serialized[key] = str(value)  # Convert to string representation
                else:
                    continue  # Skip non-serializable values
        return serialized
    
    try:
        json.dumps(data)
        return data
    except (TypeError, ValueError):
        return str(data) if data is not None else {}

def create_response(success: bool, data: Any = None, message: str = "", status_code: int = 200):
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    if data is not None:
        response["data"] = data
    return jsonify(response), status_code

@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    start_time = datetime.utcnow()
    try:
        data = request.get_json()
        if not data or not data.get('message'):
            return create_response(False, message="Message is required", status_code=400)
        
        message = data['message']
        session_id = data.get('session_id') or str(uuid.uuid4())
        user_id = data.get('user_id')
        patient_id = data.get('patient_id')
        
        # Get chatbot agent
        agents = current_app.config.get('AGENTS', {})
        chatbot_agent = agents.get('chatbot')
        if not chatbot_agent:
            return create_response(False, message="Chatbot agent not available", status_code=503)
        
        # Process message (sync call for Flask)
        response = chatbot_agent.process_message(session_id, message, user_id, patient_id)
        
        response_data = {
            "session_id": session_id,
            "message": response.message if hasattr(response, 'message') else str(response),
            "intent": getattr(response, 'intent', None),
            "confidence": getattr(response, 'confidence', None),
            "entities": getattr(response, 'entities', []),
            "actions": getattr(response, 'actions', []),
            "suggestions": getattr(response, 'suggestions', []),
            "response_time": getattr(response, 'response_time', 0.0)
        }
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event('/chatbot/chat', 'POST', 200, duration)
        log_chatbot_event(session_id, 'message_processed', f"Processed message: {message[:50]}...")
        
        return create_response(True, response_data, "Message processed successfully")
        
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event('/chatbot/chat', 'POST', 500, duration)
        current_app.logger.error(f"Chat processing error: {str(e)}", exc_info=True)
        return create_response(False, message=f"Chat processing failed: {str(e)}", status_code=500)

@chatbot_bp.route('/conversations', methods=['GET'])
def get_conversations():
    start_time = datetime.utcnow()
    try:
        user_id = request.args.get('user_id')
        patient_id = request.args.get('patient_id')
        limit = min(int(request.args.get('limit', 50)), 100)
        
        with get_db_session() as session:
            query = session.query(ChatbotConversation)
            
            if user_id:
                query = query.filter(ChatbotConversation.user_id == user_id)
            if patient_id:
                query = query.filter(ChatbotConversation.patient_id == patient_id)
                
            conversations = query.order_by(desc(ChatbotConversation.created_at)).limit(limit).all()
            
            conversation_data = []
            for conv in conversations:
                conversation_data.append({
                    "session_id": conv.session_id,
                    "user_id": conv.user_id,
                    "patient_id": conv.patient_id,
                    "status": conv.status,
                    "message_count": conv.message_count,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat() if conv.updated_at else None
                })
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            log_api_event('/chatbot/conversations', 'GET', 200, duration)
            
            return create_response(True, {
                "conversations": conversation_data,
                "total_count": len(conversation_data)
            }, "Conversations retrieved successfully")
            
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event('/chatbot/conversations', 'GET', 500, duration)
        current_app.logger.error(f"Get conversations error: {str(e)}", exc_info=True)
        return create_response(False, message=f"Failed to retrieve conversations: {str(e)}", status_code=500)

@chatbot_bp.route('/conversations/<session_id>/messages', methods=['GET'])
def get_conversation_messages(session_id):
    start_time = datetime.utcnow()
    try:
        limit = min(int(request.args.get('limit', 100)), 200)
        
        with get_db_session() as session:
            conversation = session.query(ChatbotConversation).filter(
                ChatbotConversation.session_id == session_id
            ).first()
            
            if not conversation:
                return create_response(False, message="Conversation not found", status_code=404)
            
            messages = session.query(ChatbotMessage)\
                .filter(ChatbotMessage.session_id == session_id)\
                .order_by(ChatbotMessage.timestamp)\
                .limit(limit)\
                .all()
            
            message_data = []
            for msg in messages:
                message_data.append({
                    "id": msg.id,
                    "session_id": msg.session_id,
                    "message": msg.message,
                    "response": msg.response,
                    "intent": msg.intent,
                    "confidence": msg.confidence,
                    "entities": serialize_context_data(msg.entities),  # Safe serialization
                    "timestamp": msg.timestamp.isoformat()
                })
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            log_api_event(f'/chatbot/conversations/{session_id}/messages', 'GET', 200, duration)
            
            return create_response(True, {
                "session_id": session_id,
                "messages": message_data,
                "total_count": len(message_data)
            }, "Messages retrieved successfully")
            
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event(f'/chatbot/conversations/{session_id}/messages', 'GET', 500, duration)
        current_app.logger.error(f"Get messages error: {str(e)}", exc_info=True)
        return create_response(False, message=f"Failed to retrieve messages: {str(e)}", status_code=500)

@chatbot_bp.route('/conversations/<session_id>/close', methods=['POST'])
def close_conversation(session_id):
    start_time = datetime.utcnow()
    db_session = None
    try:
        with get_db_session() as db_session:
            conversation = db_session.query(ChatbotConversation).filter(
                ChatbotConversation.session_id == session_id
            ).first()
            
            if not conversation:
                return create_response(False, message="Conversation not found", status_code=404)
                
            if conversation.status == "closed":
                return create_response(False, message="Conversation already closed", status_code=400)
            
            conversation.status = "closed"
            conversation.updated_at = datetime.utcnow()
            db_session.commit()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            log_api_event(f'/chatbot/conversations/{session_id}/close', 'POST', 200, duration)
            log_chatbot_event(session_id, 'conversation_closed', "Conversation closed")
            
            return create_response(True, {"session_id": session_id}, "Conversation closed successfully")
            
    except Exception as e:
        if db_session:
            db_session.rollback()
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event(f'/chatbot/conversations/{session_id}/close', 'POST', 500, duration)
        current_app.logger.error(f"Close conversation error: {str(e)}", exc_info=True)
        return create_response(False, message=f"Failed to close conversation: {str(e)}", status_code=500)

@chatbot_bp.route('/context/<session_id>', methods=['GET'])
def get_context(session_id):
    start_time = datetime.utcnow()
    try:
        with get_db_session() as session:
            context = session.query(ChatbotContext).filter(
                ChatbotContext.session_id == session_id
            ).first()
            
            if not context:
                return create_response(False, message="Context not found", status_code=404)
            
            # Safely serialize context data
            context_data = {
                "session_id": context.session_id,
                "context_data": serialize_context_data(context.context_data),
                "metadata": serialize_context_data(context.metadata),
                "created_at": context.created_at.isoformat(),
                "updated_at": context.updated_at.isoformat() if context.updated_at else None
            }
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            log_api_event(f'/chatbot/context/{session_id}', 'GET', 200, duration)
            
            return create_response(True, context_data, "Context retrieved successfully")
            
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event(f'/chatbot/context/{session_id}', 'GET', 500, duration)
        current_app.logger.error(f"Get context error: {str(e)}", exc_info=True)
        return create_response(False, message=f"Failed to retrieve context: {str(e)}", status_code=500)

@chatbot_bp.route('/context/<session_id>', methods=['PUT'])
def update_context(session_id):
    start_time = datetime.utcnow()
    db_session = None
    try:
        data = request.get_json()
        
        with get_db_session() as db_session:
            context = db_session.query(ChatbotContext).filter(
                ChatbotContext.session_id == session_id
            ).first()
            
            if not context:
                # Create new context with conversation_history initialized
                initial_context_data = {
                    "conversation_history": [],  # Initialize empty conversation history
                    "user_preferences": {},
                    "session_metadata": {
                        "created_at": datetime.utcnow().isoformat(),
                        "last_activity": datetime.utcnow().isoformat()
                    }
                }
                initial_context_data.update(data.get('context_data', {}))
                
                context = ChatbotContext(
                    session_id=session_id,
                    context_data=initial_context_data,
                    metadata=data.get('metadata', {})
                )
                db_session.add(context)
            else:
                # Update existing context, ensuring conversation_history exists
                existing_context = context.context_data or {}
                if 'conversation_history' not in existing_context:
                    existing_context['conversation_history'] = []
                
                # Merge new context data
                new_context_data = data.get('context_data', {})
                existing_context.update(new_context_data)
                
                context.context_data = existing_context
                context.metadata = data.get('metadata', context.metadata or {})
                context.updated_at = datetime.utcnow()
            
            db_session.commit()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            log_api_event(f'/chatbot/context/{session_id}', 'PUT', 200, duration)
            log_chatbot_event(session_id, 'context_updated', "Context updated")
            
            return create_response(True, {"session_id": session_id}, "Context updated successfully")
            
    except Exception as e:
        if db_session:
            db_session.rollback()
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event(f'/chatbot/context/{session_id}', 'PUT', 500, duration)
        current_app.logger.error(f"Update context error: {str(e)}", exc_info=True)
        return create_response(False, message=f"Failed to update context: {str(e)}", status_code=500)

@chatbot_bp.route('/sessions', methods=['POST'])
def create_session():
    start_time = datetime.utcnow()
    db_session = None
    try:
        data = request.get_json()
        session_id = str(uuid.uuid4())
        
        with get_db_session() as db_session:
            # Create conversation
            conversation = ChatbotConversation(
                session_id=session_id,
                user_id=data.get('user_id'),
                patient_id=data.get('patient_id'),
                status="active",
                message_count=0
            )
            db_session.add(conversation)
            
            # Create initial context with proper structure
            initial_context_data = {
                "session_start": datetime.utcnow().isoformat(),
                "user_id": data.get('user_id'),
                "patient_id": data.get('patient_id'),
                "conversation_history": [],  # Initialize empty conversation history
                "user_preferences": {},
                "current_topic": None,
                "last_intent": None
            }
            
            context = ChatbotContext(
                session_id=session_id,
                context_data=initial_context_data,
                metadata={
                    "created_by": "api",
                    "initial_message": data.get('initial_message'),
                    "session_type": "chat",
                    "platform": data.get('platform', 'web')
                }
            )
            db_session.add(context)
            
            # Process initial message if provided
            if data.get('initial_message'):
                # Add user message
                user_message = ChatbotMessage(
                    session_id=session_id,
                    message_type='user',
                    message=data['initial_message'],
                    intent="greeting",
                    confidence=1.0,
                    entities={},
                    timestamp=datetime.utcnow()
                )
                db_session.add(user_message)
                
                # Add bot response message
                bot_message = ChatbotMessage(
                    session_id=session_id,
                    message_type='bot',
                    message="Hello! I'm your healthcare assistant. How can I help you today?",
                    response="Hello! I'm your healthcare assistant. How can I help you today?",
                    intent="greeting_response",
                    confidence=1.0,
                    entities={},
                    timestamp=datetime.utcnow()
                )
                db_session.add(bot_message)
                
                conversation.message_count = 2
                
                # Update context with initial conversation
                initial_context_data["conversation_history"] = [
                    {
                        "role": "user",
                        "message": data['initial_message'],
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    {
                        "role": "assistant", 
                        "message": "Hello! I'm your healthcare assistant. How can I help you today?",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ]
                context.context_data = initial_context_data
            
            db_session.commit()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            log_api_event('/chatbot/sessions', 'POST', 201, duration)
            log_chatbot_event(session_id, 'session_created', "New session created")
            
            return create_response(True, {
                "session_id": session_id,
                "user_id": data.get('user_id'),
                "patient_id": data.get('patient_id'),
                "status": "active"
            }, "Session created successfully", 201)
            
    except Exception as e:
        if db_session:
            db_session.rollback()
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event('/chatbot/sessions', 'POST', 500, duration)
        current_app.logger.error(f"Create session error: {str(e)}", exc_info=True)
        return create_response(False, message=f"Failed to create session: {str(e)}", status_code=500)

@chatbot_bp.route('/analytics', methods=['GET'])
def get_chatbot_analytics():
    start_time = datetime.utcnow()
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        with get_db_session() as session:
            query = session.query(ChatbotConversation)
            
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    query = query.filter(ChatbotConversation.created_at >= start_dt)
                except ValueError:
                    return create_response(False, message="Invalid start_date format", status_code=400)
                    
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    query = query.filter(ChatbotConversation.created_at <= end_dt)
                except ValueError:
                    return create_response(False, message="Invalid end_date format", status_code=400)
            
            conversations = query.all()
            
            total_conversations = len(conversations)
            active_conversations = len([c for c in conversations if c.status == "active"])
            closed_conversations = len([c for c in conversations if c.status == "closed"])
            total_messages = sum(c.message_count for c in conversations)
            avg_messages = total_messages / total_conversations if total_conversations > 0 else 0
            
            analytics_data = {
                "total_conversations": total_conversations,
                "active_conversations": active_conversations,
                "closed_conversations": closed_conversations,
                "total_messages": total_messages,
                "average_messages_per_conversation": round(avg_messages, 2),
                "period": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            log_api_event('/chatbot/analytics', 'GET', 200, duration)
            
            return create_response(True, analytics_data, "Analytics retrieved successfully")
            
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event('/chatbot/analytics', 'GET', 500, duration)
        current_app.logger.error(f"Get analytics error: {str(e)}", exc_info=True)
        return create_response(False, message=f"Failed to retrieve analytics: {str(e)}", status_code=500)