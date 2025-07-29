"""
Chatbot API Schemas

This module defines Pydantic schemas for the chatbot API endpoints,
ensuring proper data validation and documentation.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum

class MessageType(str, Enum):
    """Message type enumeration"""
    USER = "user"
    BOT = "bot"
    SYSTEM = "system"

class IntentType(str, Enum):
    """Intent type enumeration"""
    PATIENT_LOOKUP = "patient_lookup"
    APPOINTMENT_SCHEDULING = "appointment_scheduling"
    MEDICAL_RECORDS = "medical_records"
    VITAL_SIGNS = "vital_signs"
    TRIAGE_ASSESSMENT = "triage_assessment"
    EMERGENCY = "emergency"
    GENERAL_HELP = "general_help"
    ERROR = "error"

class UrgencyLevel(str, Enum):
    """Urgency level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ConversationStatus(str, Enum):
    """Conversation status enumeration"""
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"

class ConversationType(str, Enum):
    """Conversation type enumeration"""
    GENERAL = "general"
    TRIAGE = "triage"
    EMERGENCY = "emergency"
    APPOINTMENT = "appointment"
    MEDICAL_RECORDS = "medical_records"

# Request Schemas

class ChatMessageRequest(BaseModel):
    """Schema for chat message request"""
    message: str = Field(..., min_length=1, max_length=1000, description="User message content")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: Optional[str] = Field(None, description="User identifier")
    patient_id: Optional[str] = Field(None, description="Patient ID for context")
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

class CreateSessionRequest(BaseModel):
    """Schema for creating a new chat session"""
    user_id: Optional[str] = Field(None, description="User identifier")
    patient_id: Optional[str] = Field(None, description="Patient ID for context")
    conversation_type: ConversationType = Field(ConversationType.GENERAL, description="Type of conversation")

class UpdateContextRequest(BaseModel):
    """Schema for updating conversation context"""
    context_data: Optional[Dict[str, Any]] = Field(None, description="Context data to update")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    system_state: Optional[Dict[str, Any]] = Field(None, description="System state")

# Response Schemas

class ChatbotResponse(BaseModel):
    """Schema for chatbot response"""
    session_id: str = Field(..., description="Session ID")
    message: str = Field(..., description="Bot response message")
    intent: IntentType = Field(..., description="Detected intent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Actions to perform")
    suggestions: List[str] = Field(default_factory=list, description="Suggested next actions")
    response_time: float = Field(..., description="Response time in seconds")

class MessageSchema(BaseModel):
    """Schema for individual message"""
    id: str = Field(..., description="Message ID")
    type: MessageType = Field(..., description="Message type")
    content: str = Field(..., description="Message content")
    intent: Optional[str] = Field(None, description="Detected intent")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Intent confidence")
    entities: Optional[Dict[str, Any]] = Field(None, description="Extracted entities")
    response_time: Optional[float] = Field(None, description="Response time")
    created_at: datetime = Field(..., description="Message creation timestamp")

class ConversationSchema(BaseModel):
    """Schema for conversation"""
    id: str = Field(..., description="Conversation ID")
    session_id: str = Field(..., description="Session ID")
    user_id: Optional[str] = Field(None, description="User identifier")
    patient_id: Optional[str] = Field(None, description="Patient ID")
    conversation_type: ConversationType = Field(..., description="Conversation type")
    status: ConversationStatus = Field(..., description="Conversation status")
    message_count: int = Field(..., description="Number of messages")
    conversation_metadata: Optional[Dict[str, Any]] = Field(None, description="Conversation metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    closed_at: Optional[datetime] = Field(None, description="Closing timestamp")

class ContextSchema(BaseModel):
    """Schema for conversation context"""
    session_id: str = Field(..., description="Session ID")
    user_id: Optional[str] = Field(None, description="User identifier")
    patient_id: Optional[str] = Field(None, description="Patient ID")
    context_data: Dict[str, Any] = Field(..., description="Context data")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(None, description="Conversation history")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    system_state: Optional[Dict[str, Any]] = Field(None, description="System state")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class SessionSchema(BaseModel):
    """Schema for chat session"""
    session_id: str = Field(..., description="Session ID")
    user_id: Optional[str] = Field(None, description="User identifier")
    patient_id: Optional[str] = Field(None, description="Patient ID")
    created_at: datetime = Field(..., description="Creation timestamp")

class AnalyticsSchema(BaseModel):
    """Schema for chatbot analytics"""
    total_conversations: int = Field(..., description="Total number of conversations")
    active_conversations: int = Field(..., description="Number of active conversations")
    total_messages: int = Field(..., description="Total number of messages")
    intent_distribution: List[Dict[str, Any]] = Field(..., description="Intent distribution")
    recent_activity: List[Dict[str, Any]] = Field(..., description="Recent activity")

# Intent Analysis Schemas

class IntentAnalysis(BaseModel):
    """Schema for intent analysis"""
    intent: IntentType = Field(..., description="Detected intent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
    urgency: UrgencyLevel = Field(UrgencyLevel.LOW, description="Urgency level")

class EntitySchema(BaseModel):
    """Schema for extracted entities"""
    patient_name: Optional[str] = Field(None, description="Patient name")
    mrn: Optional[str] = Field(None, description="Medical record number")
    appointment_type: Optional[str] = Field(None, description="Appointment type")
    date: Optional[str] = Field(None, description="Date")
    doctor: Optional[str] = Field(None, description="Doctor name")
    symptoms: Optional[List[str]] = Field(None, description="Symptoms")
    vital_signs: Optional[Dict[str, Any]] = Field(None, description="Vital signs")
    patient_id: Optional[str] = Field(None, description="Patient ID")

# Action Schemas

class ActionSchema(BaseModel):
    """Schema for actions"""
    type: str = Field(..., description="Action type")
    data: Dict[str, Any] = Field(..., description="Action data")
    priority: Optional[str] = Field(None, description="Action priority")

class EmergencyAction(ActionSchema):
    """Schema for emergency actions"""
    type: str = Field("emergency_alert", description="Emergency action type")
    severity: UrgencyLevel = Field(..., description="Emergency severity")
    alert_message: str = Field(..., description="Alert message")

class PatientLookupAction(ActionSchema):
    """Schema for patient lookup actions"""
    type: str = Field("patient_lookup", description="Patient lookup action type")
    search_criteria: Dict[str, Any] = Field(..., description="Search criteria")

class AppointmentAction(ActionSchema):
    """Schema for appointment actions"""
    type: str = Field("appointment_scheduling", description="Appointment action type")
    appointment_data: Dict[str, Any] = Field(..., description="Appointment data")

# Error Schemas

class ErrorResponse(BaseModel):
    """Schema for error responses"""
    success: bool = Field(False, description="Success status")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

class ValidationError(BaseModel):
    """Schema for validation errors"""
    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Validation message")
    value: Optional[Any] = Field(None, description="Invalid value")

# API Response Schemas

class APIResponse(BaseModel):
    """Base API response schema"""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class ChatResponse(APIResponse):
    """Schema for chat API response"""
    data: ChatbotResponse = Field(..., description="Chat response data")

class ConversationsResponse(APIResponse):
    """Schema for conversations API response"""
    data: List[ConversationSchema] = Field(..., description="List of conversations")

class MessagesResponse(APIResponse):
    """Schema for messages API response"""
    data: List[MessageSchema] = Field(..., description="List of messages")

class ContextResponse(APIResponse):
    """Schema for context API response"""
    data: ContextSchema = Field(..., description="Context data")

class SessionResponse(APIResponse):
    """Schema for session API response"""
    data: SessionSchema = Field(..., description="Session data")

class AnalyticsResponse(APIResponse):
    """Schema for analytics API response"""
    data: AnalyticsSchema = Field(..., description="Analytics data")

# WebSocket Schemas (for real-time communication)

class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages"""
    type: str = Field(..., description="Message type")
    session_id: str = Field(..., description="Session ID")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")

class WebSocketChatMessage(WebSocketMessage):
    """Schema for WebSocket chat messages"""
    type: str = Field("chat_message", description="Chat message type")
    message: str = Field(..., description="Message content")
    user_id: Optional[str] = Field(None, description="User ID")

class WebSocketTypingIndicator(WebSocketMessage):
    """Schema for WebSocket typing indicators"""
    type: str = Field("typing_indicator", description="Typing indicator type")
    is_typing: bool = Field(..., description="Typing status")

# Configuration Schemas

class ChatbotConfig(BaseModel):
    """Schema for chatbot configuration"""
    max_message_length: int = Field(1000, description="Maximum message length")
    max_conversation_history: int = Field(50, description="Maximum conversation history")
    response_timeout: float = Field(30.0, description="Response timeout in seconds")
    enable_typing_indicators: bool = Field(True, description="Enable typing indicators")
    enable_suggestions: bool = Field(True, description="Enable response suggestions")
    emergency_keywords: List[str] = Field(default_factory=list, description="Emergency keywords")
    allowed_intents: List[IntentType] = Field(default_factory=list, description="Allowed intents")

# Health Check Schemas

class ChatbotHealthCheck(BaseModel):
    """Schema for chatbot health check"""
    status: str = Field(..., description="Health status")
    session_count: int = Field(..., description="Active session count")
    message_count: int = Field(..., description="Total message count")
    average_response_time: float = Field(..., description="Average response time")
    uptime: float = Field(..., description="Uptime in seconds")
    last_error: Optional[str] = Field(None, description="Last error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp") 