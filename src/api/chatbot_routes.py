"""
Chatbot API Routes Module

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

def get_request_data() -> Dict[str, Any]:
    """Get request data with error handling"""
    try:
        if request.is_json:
            return request.get_json()
        elif request.form:
            return dict(request.form)
        else:
            return {}
    except Exception as e:
        return {"error": f"Invalid request data: {str(e)}"}

def create_response(success: bool, data: Any = None, message: str = "", status_code: int = 200) -> tuple:
    """Create standardized API response"""
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
    """Process a chat message and return response"""
    start_time = datetime.utcnow()
    
    try:
        data = get_request_data()
        
        # Validate required fields
        if not data.get('message'):
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
        
        # Process message
        response = chatbot_agent.process_message(session_id, message, user_id, patient_id)
        
        # Prepare response data
        response_data = {
            "session_id": session_id,
            "message": response.message,
            "intent": response.intent,
            "confidence": response.confidence,
            "entities": response.entities,
            "actions": response.actions,
            "suggestions": response.suggestions,
            "response_time": getattr(response, 'response_time', 0.0)
        }
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event('/chatbot/chat', 'POST', 200, duration)
        log_chatbot_event(session_id, 'message_processed', f"Processed message: {message[:50]}...")
        
        return create_response(True, response_data, "Message processed successfully")
        
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event('/chatbot/chat', 'POST', 500, duration)
        return create_response(False, message=f"Chat processing failed: {str(e)}", status_code=500)

@chatbot_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations for a user"""
    start_time = datetime.utcnow()
    
    try:
        user_id = request.args.get('user_id')
        session_id = request.args.get('session_id')
        status = request.args.get('status', 'active')
        limit = min(request.args.get('limit', 20, type=int), 100)
        
        with get_db_session() as session:
            query = session.query(ChatbotConversation)
            
            if user_id:
                query = query.filter(ChatbotConversation.user_id == user_id)
            if session_id:
                query = query.filter(ChatbotConversation.session_id == session_id)
            if status:
                query = query.filter(ChatbotConversation.status == status)
            
            conversations = query.order_by(desc(ChatbotConversation.updated_at)).limit(limit).all()
            
            conversation_data = []
            for conv in conversations:
                # Get message count
                message_count = session.query(ChatbotMessage).filter(
                    ChatbotMessage.conversation_id == conv.id
                ).count()
                
                conversation_data.append({
                    "id": str(conv.id),
                    "session_id": conv.session_id,
                    "user_id": conv.user_id,
                    "patient_id": str(conv.patient_id) if conv.patient_id else None,
                    "conversation_type": conv.conversation_type,
                    "status": conv.status,
                    "message_count": message_count,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "closed_at": conv.closed_at.isoformat() if conv.closed_at else None,
                    "conversation_metadata": conv.conversation_metadata
                })
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            log_api_event('/chatbot/conversations', 'GET', 200, duration)
            
            return create_response(True, conversation_data, f"Retrieved {len(conversation_data)} conversations")
            
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event('/chatbot/conversations', 'GET', 500, duration)
        return create_response(False, message=f"Failed to retrieve conversations: {str(e)}", status_code=500)

@chatbot_bp.route('/conversations/<session_id>/messages', methods=['GET'])
def get_conversation_messages(session_id: str):
    """Get messages for a specific conversation"""
    start_time = datetime.utcnow()
    
    try:
        limit = min(request.args.get('limit', 50, type=int), 200)
        
        with get_db_session() as session:
            # Get conversation
            conversation = session.query(ChatbotConversation).filter(
                ChatbotConversation.session_id == session_id
            ).first()
            
            if not conversation:
                return create_response(False, message="Conversation not found", status_code=404)
            
            # Get messages
            messages = session.query(ChatbotMessage).filter(
                ChatbotMessage.conversation_id == conversation.id
            ).order_by(ChatbotMessage.created_at).limit(limit).all()
            
            message_data = [
                {
                    "id": str(msg.id),
                    "type": msg.message_type,
                    "content": msg.content,
                    "intent": msg.intent,
                    "confidence": msg.confidence,
                    "entities": msg.entities,
                    "response_time": msg.response_time,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            log_api_event(f'/chatbot/conversations/{session_id}/messages', 'GET', 200, duration)
            
            return create_response(True, message_data, f"Retrieved {len(message_data)} messages")
            
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event(f'/chatbot/conversations/{session_id}/messages', 'GET', 500, duration)
        return create_response(False, message=f"Failed to retrieve messages: {str(e)}", status_code=500)

@chatbot_bp.route('/conversations/<session_id>/close', methods=['POST'])
def close_conversation(session_id: str):
    """Close a conversation"""
    start_time = datetime.utcnow()
    
    try:
        # Get chatbot agent
        agents = current_app.config.get('AGENTS', {})
        chatbot_agent = agents.get('chatbot')
        
        if chatbot_agent:
            chatbot_agent.close_conversation(session_id)
        
        with get_db_session() as session:
            conversation = session.query(ChatbotConversation).filter(
                ChatbotConversation.session_id == session_id,
                ChatbotConversation.status == 'active'
            ).first()
            
            if conversation:
                conversation.status = 'closed'
                conversation.closed_at = datetime.utcnow()
                session.commit()
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event(f'/chatbot/conversations/{session_id}/close', 'POST', 200, duration)
        log_chatbot_event(session_id, 'conversation_closed', "Conversation closed by user")
        
        return create_response(True, message="Conversation closed successfully")
        
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event(f'/chatbot/conversations/{session_id}/close', 'POST', 500, duration)
        return create_response(False, message=f"Failed to close conversation: {str(e)}", status_code=500)

@chatbot_bp.route('/context/<session_id>', methods=['GET'])
def get_context(session_id: str):
    """Get conversation context for a session"""
    start_time = datetime.utcnow()
    
    try:
        with get_db_session() as session:
            context = session.query(ChatbotContext).filter(
                ChatbotContext.session_id == session_id
            ).first()
            
            if not context:
                return create_response(False, message="Context not found", status_code=404)
            
            context_data = {
                "session_id": context.session_id,
                "user_id": context.user_id,
                "patient_id": str(context.patient_id) if context.patient_id else None,
                "context_data": context.context_data,
                "conversation_history": context.conversation_history,
                "user_preferences": context.user_preferences,
                "system_state": context.system_state,
                "last_activity": context.last_activity.isoformat(),
                "created_at": context.created_at.isoformat(),
                "updated_at": context.updated_at.isoformat()
            }
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            log_api_event(f'/chatbot/context/{session_id}', 'GET', 200, duration)
            
            return create_response(True, context_data, "Context retrieved successfully")
            
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event(f'/chatbot/context/{session_id}', 'GET', 500, duration)
        return create_response(False, message=f"Failed to retrieve context: {str(e)}", status_code=500)

@chatbot_bp.route('/context/<session_id>', methods=['PUT'])
def update_context(session_id: str):
    """Update conversation context"""
    start_time = datetime.utcnow()
    
    try:
        data = get_request_data()
        
        with get_db_session() as session:
            context = session.query(ChatbotContext).filter(
                ChatbotContext.session_id == session_id
            ).first()
            
            if not context:
                return create_response(False, message="Context not found", status_code=404)
            
            # Update context fields
            if 'context_data' in data:
                context.context_data.update(data['context_data'])
            if 'user_preferences' in data:
                context.user_preferences = data['user_preferences']
            if 'system_state' in data:
                context.system_state = data['system_state']
            
            context.last_activity = datetime.utcnow()
            session.commit()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            log_api_event(f'/chatbot/context/{session_id}', 'PUT', 200, duration)
            log_chatbot_event(session_id, 'context_updated', "Context updated")
            
            return create_response(True, message="Context updated successfully")
            
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event(f'/chatbot/context/{session_id}', 'PUT', 500, duration)
        return create_response(False, message=f"Failed to update context: {str(e)}", status_code=500)

@chatbot_bp.route('/sessions', methods=['POST'])
def create_session():
    """Create a new chat session"""
    start_time = datetime.utcnow()
    
    try:
        data = get_request_data()
        user_id = data.get('user_id')
        patient_id = data.get('patient_id')
        
        session_id = str(uuid.uuid4())
        
        # Initialize context
        with get_db_session() as session:
            context = ChatbotContext(
                session_id=session_id,
                user_id=user_id,
                patient_id=patient_id,
                context_data={
                    "session_id": session_id,
                    "user_id": user_id,
                    "patient_id": patient_id,
                    "conversation_history": [],
                    "current_topic": None,
                    "user_preferences": {},
                    "system_state": "ready",
                    "last_patient_lookup": None,
                    "pending_actions": []
                }
            )
            session.add(context)
            session.commit()
        
        # Create conversation
        conversation = ChatbotConversation(
            session_id=session_id,
            user_id=user_id,
            patient_id=patient_id,
            conversation_type='general',
            status='active'
        )
        session.add(conversation)
        session.commit()
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "patient_id": patient_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event('/chatbot/sessions', 'POST', 201, duration)
        log_chatbot_event(session_id, 'session_created', "New chat session created")
        
        return create_response(True, session_data, "Session created successfully", 201)
        
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event('/chatbot/sessions', 'POST', 500, duration)
        return create_response(False, message=f"Failed to create session: {str(e)}", status_code=500)

@chatbot_bp.route('/analytics', methods=['GET'])
def get_chatbot_analytics():
    """Get chatbot analytics and usage statistics"""
    start_time = datetime.utcnow()
    
    try:
        with get_db_session() as session:
            # Get basic statistics
            total_conversations = session.query(ChatbotConversation).count()
            active_conversations = session.query(ChatbotConversation).filter(
                ChatbotConversation.status == 'active'
            ).count()
            total_messages = session.query(ChatbotMessage).count()
            
            # Get intent distribution
            intent_counts = session.query(
                ChatbotMessage.intent,
                session.query(ChatbotMessage).filter(ChatbotMessage.intent == ChatbotMessage.intent).count().label('count')
            ).filter(ChatbotMessage.intent.isnot(None)).group_by(ChatbotMessage.intent).all()
            
            # Get recent activity
            recent_messages = session.query(ChatbotMessage).order_by(
                desc(ChatbotMessage.created_at)
            ).limit(10).all()
            
            analytics_data = {
                "total_conversations": total_conversations,
                "active_conversations": active_conversations,
                "total_messages": total_messages,
                "intent_distribution": [
                    {"intent": intent, "count": count}
                    for intent, count in intent_counts
                ],
                "recent_activity": [
                    {
                        "id": str(msg.id),
                        "type": msg.message_type,
                        "intent": msg.intent,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in recent_messages
                ]
            }
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            log_api_event('/chatbot/analytics', 'GET', 200, duration)
            
            return create_response(True, analytics_data, "Analytics retrieved successfully")
            
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_api_event('/chatbot/analytics', 'GET', 500, duration)
        return create_response(False, message=f"Failed to retrieve analytics: {str(e)}", status_code=500) 