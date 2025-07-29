"""
Chatbot Agent Module

This module provides an intelligent chatbot agent that can handle conversations,
maintain context, and integrate with the healthcare management system.
"""

import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from database.connection import get_db_session
from database.models import ChatbotConversation, ChatbotMessage, ChatbotContext, Patient
from config.llm_config import llm_config
from utils.logger import log_agent_event

logger = logging.getLogger(__name__)

@dataclass
class ChatbotResponse:
    """Structured response from chatbot"""
    message: str
    intent: str
    confidence: float
    entities: Dict[str, Any]
    actions: List[Dict[str, Any]]
    context_update: Dict[str, Any]
    suggestions: List[str]
    response_time: float = 0.0

class ChatbotAgent:
    """Intelligent chatbot agent with context management"""
    
    def __init__(self, tools: Dict[str, Any]):
        self.tools = tools
        self.llm_client = llm_config.get_default_llm()
        self.system_prompt = self._get_system_prompt()
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the chatbot"""
        return """You are an intelligent healthcare assistant chatbot. Your role is to:

1. Help users with healthcare-related queries
2. Assist with patient information and medical records
3. Provide triage guidance and emergency response
4. Schedule appointments and manage healthcare workflows
5. Maintain conversation context and provide personalized responses

Key capabilities:
- Patient lookup and information retrieval
- Medical record management
- Appointment scheduling
- Vital signs monitoring
- Emergency response coordination
- Triage assessment

Always be professional, empathetic, and prioritize patient safety. If you detect an emergency situation, immediately escalate to appropriate medical staff.

Available tools:
- patient_lookup: Find patient information
- medical_records: Access medical records
- schedule_appointment: Book appointments
- submit_vital_signs: Record patient vitals
- create_alert: Generate alerts for urgent situations
- triage_assessment: Perform initial patient assessment

Respond naturally and conversationally while maintaining medical accuracy and confidentiality."""

    def process_message(self, session_id: str, message: str, user_id: Optional[str] = None, 
                       patient_id: Optional[str] = None) -> ChatbotResponse:
        """Process a user message and return a response"""
        start_time = time.time()
        
        try:
            # Get or create conversation context
            context = self._get_or_create_context(session_id, user_id, patient_id)
            
            # Analyze user intent and extract entities
            intent_analysis = self._analyze_intent(message, context)
            
            # Generate response using LLM
            response = self._generate_response(message, intent_analysis, context)
            
            # Update context
            self._update_context(session_id, message, response, context)
            
            # Log conversation
            self._log_conversation(session_id, message, response, intent_analysis)
            
            response_time = time.time() - start_time
            response.response_time = response_time
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return ChatbotResponse(
                message="I apologize, but I'm experiencing technical difficulties. Please try again or contact support.",
                intent="error",
                confidence=0.0,
                entities={},
                actions=[],
                context_update={},
                suggestions=["Try rephrasing your question", "Contact technical support"]
            )

    def _get_or_create_context(self, session_id: str, user_id: Optional[str], 
                              patient_id: Optional[str]) -> Dict[str, Any]:
        """Get or create conversation context"""
        with get_db_session() as session:
            # Try to get existing context
            context_record = session.query(ChatbotContext).filter(
                ChatbotContext.session_id == session_id
            ).first()
            
            if context_record:
                # Update last activity
                context_record.last_activity = datetime.utcnow()
                session.commit()
                return context_record.context_data
            
            # Create new context
            new_context = {
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
            
            context_record = ChatbotContext(
                session_id=session_id,
                user_id=user_id,
                patient_id=patient_id,
                context_data=new_context
            )
            session.add(context_record)
            session.commit()
            
            return new_context

    def _analyze_intent(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user intent and extract entities"""
        prompt = f"""Analyze the following user message and extract intent and entities:

Message: "{message}"
Context: {json.dumps(context, indent=2)}

Return ONLY a valid JSON object with this exact structure:
{{
    "intent": "patient_lookup|appointment_scheduling|medical_records|emergency|general_help|vital_signs|triage_assessment",
    "confidence": 0.0-1.0,
    "entities": {{}},
    "urgency": "low|medium|high|critical"
}}

Focus on healthcare-related intents and entities. Ensure the response is valid JSON."""

        try:
            # Use the LLM with proper API
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_client.invoke(messages)
            
            # Clean the response content
            content = response.content.strip()
            
            # Try to extract JSON from the response
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # Parse the response
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract intent from the text
                logger.warning(f"Failed to parse JSON from LLM response: {content}")
                # Simple intent detection based on keywords
                message_lower = message.lower()
                if any(word in message_lower for word in ['patient', 'lookup', 'find', 'search']):
                    intent = "patient_lookup"
                elif any(word in message_lower for word in ['appointment', 'schedule', 'book']):
                    intent = "appointment_scheduling"
                elif any(word in message_lower for word in ['medical', 'record', 'history']):
                    intent = "medical_records"
                elif any(word in message_lower for word in ['emergency', 'urgent', 'critical']):
                    intent = "emergency"
                elif any(word in message_lower for word in ['vital', 'signs', 'heart', 'blood', 'temperature']):
                    intent = "vital_signs"
                else:
                    intent = "general_help"
                
                result = {
                    "intent": intent,
                    "confidence": 0.6,
                    "entities": {},
                    "urgency": "low"
                }
            
            # Validate the result
            if not isinstance(result, dict):
                raise ValueError("Response is not a dictionary")
            
            # Ensure required fields exist
            result.setdefault("intent", "general_help")
            result.setdefault("confidence", 0.5)
            result.setdefault("entities", {})
            result.setdefault("urgency", "low")
            
            return result
            
        except Exception as e:
            logger.error(f"Intent analysis failed: {str(e)}")
            try:
                logger.error(f"Raw response content: {getattr(response, 'content', 'No content')}")
            except:
                logger.error("Could not log raw response content")
            return {
                "intent": "general_help",
                "confidence": 0.5,
                "entities": {},
                "urgency": "low"
            }

    def _generate_response(self, message: str, intent_analysis: Dict[str, Any], 
                          context: Dict[str, Any]) -> ChatbotResponse:
        """Generate chatbot response based on intent and context"""
        
        intent = intent_analysis.get("intent", "general_help")
        confidence = intent_analysis.get("confidence", 0.5)
        entities = intent_analysis.get("entities", {})
        urgency = intent_analysis.get("urgency", "low")
        
        # Handle emergency situations immediately
        if urgency == "critical":
            return self._handle_emergency(message, context)
        
        # Route to appropriate handler based on intent
        if intent == "patient_lookup":
            return self._handle_patient_lookup(entities, context)
        elif intent == "appointment_scheduling":
            return self._handle_appointment_scheduling(entities, context)
        elif intent == "medical_records":
            return self._handle_medical_records(entities, context)
        elif intent == "vital_signs":
            return self._handle_vital_signs(entities, context)
        elif intent == "triage_assessment":
            return self._handle_triage_assessment(entities, context)
        else:
            return self._handle_general_help(message, context)

    def _handle_emergency(self, message: str, context: Dict[str, Any]) -> ChatbotResponse:
        """Handle emergency situations"""
        # Create emergency alert
        alert_data = {
            "alert_type": "emergency",
            "severity": "critical",
            "title": "Emergency Situation Detected",
            "message": f"Emergency situation reported: {message}",
            "source": "chatbot"
        }
        
        if context.get("patient_id"):
            alert_data["patient_id"] = context["patient_id"]
        
        # Use alert tool to create emergency response
        if "create_alert" in self.tools:
            self.tools["create_alert"].execute(alert_data)
        
        return ChatbotResponse(
            message="🚨 EMERGENCY DETECTED! I've immediately alerted the emergency response team. Please stay calm and provide any additional details about the situation. Medical staff will respond immediately.",
            intent="emergency",
            confidence=1.0,
            entities={},
            actions=[{"type": "emergency_alert", "data": alert_data}],
            context_update={"system_state": "emergency_mode"},
            suggestions=["Describe the emergency in detail", "Provide patient information if available"]
        )

    def _handle_patient_lookup(self, entities: Dict[str, Any], context: Dict[str, Any]) -> ChatbotResponse:
        """Handle patient lookup requests"""
        patient_name = entities.get("patient_name")
        mrn = entities.get("mrn")
        
        if not patient_name and not mrn:
            return ChatbotResponse(
                message="I'd be happy to help you find patient information. Could you please provide the patient's name or Medical Record Number (MRN)?",
                intent="patient_lookup",
                confidence=0.8,
                entities=entities,
                actions=[],
                context_update={"current_topic": "patient_lookup"},
                suggestions=["Provide patient name", "Provide MRN", "Search by other criteria"]
            )
        
        # Use patient lookup tool
        if "patient_lookup" in self.tools:
            search_criteria = {}
            if patient_name:
                search_criteria["name"] = patient_name
            if mrn:
                search_criteria["mrn"] = mrn
            
            result = self.tools["patient_lookup"].execute(search_criteria)
            
            if result.get("success") and result.get("data"):
                patient_data = result["data"]
                context["last_patient_lookup"] = patient_data
                
                return ChatbotResponse(
                    message=f"I found the patient information:\n\n**Name:** {patient_data.get('first_name', '')} {patient_data.get('last_name', '')}\n**MRN:** {patient_data.get('mrn', '')}\n**Status:** {patient_data.get('status', '')}\n**Admission Date:** {patient_data.get('admission_date', 'N/A')}\n\nWhat would you like to know about this patient?",
                    intent="patient_lookup",
                    confidence=0.9,
                    entities=entities,
                    actions=[{"type": "patient_found", "data": patient_data}],
                    context_update={"current_topic": "patient_details", "last_patient_lookup": patient_data},
                    suggestions=["View medical records", "Check appointments", "View vital signs", "Schedule appointment"]
                )
            else:
                return ChatbotResponse(
                    message="I couldn't find a patient with the provided information. Could you please verify the name or MRN and try again?",
                    intent="patient_lookup",
                    confidence=0.7,
                    entities=entities,
                    actions=[],
                    context_update={"current_topic": "patient_lookup"},
                    suggestions=["Check spelling", "Provide MRN instead", "Search with different criteria"]
                )
        
        return ChatbotResponse(
            message="I'm sorry, but the patient lookup feature is currently unavailable. Please try again later or contact support.",
            intent="patient_lookup",
            confidence=0.5,
            entities=entities,
            actions=[],
            context_update={},
            suggestions=["Try again later", "Contact support"]
        )

    def _handle_appointment_scheduling(self, entities: Dict[str, Any], context: Dict[str, Any]) -> ChatbotResponse:
        """Handle appointment scheduling requests"""
        patient_id = entities.get("patient_id") or context.get("patient_id")
        
        if not patient_id:
            return ChatbotResponse(
                message="To schedule an appointment, I need to know which patient you're referring to. Could you please provide the patient's name or MRN first?",
                intent="appointment_scheduling",
                confidence=0.8,
                entities=entities,
                actions=[],
                context_update={"current_topic": "appointment_scheduling"},
                suggestions=["Provide patient name", "Provide MRN", "Look up patient first"]
            )
        
        # Check if we have appointment details
        appointment_type = entities.get("appointment_type")
        preferred_date = entities.get("date")
        doctor = entities.get("doctor")
        
        if not appointment_type:
            return ChatbotResponse(
                message="I can help you schedule an appointment. What type of appointment would you like to schedule? (e.g., consultation, follow-up, procedure)",
                intent="appointment_scheduling",
                confidence=0.8,
                entities=entities,
                actions=[],
                context_update={"current_topic": "appointment_scheduling", "patient_id": patient_id},
                suggestions=["Consultation", "Follow-up", "Procedure", "Emergency"]
            )
        
        # Use appointment scheduling tool
        if "schedule_appointment" in self.tools:
            appointment_data = {
                "patient_id": patient_id,
                "appointment_type": appointment_type,
                "scheduled_date": preferred_date,
                "doctor_id": doctor
            }
            
            result = self.tools["schedule_appointment"].execute(appointment_data)
            
            if result.get("success"):
                return ChatbotResponse(
                    message=f"Great! I've successfully scheduled your {appointment_type} appointment. The appointment has been confirmed and added to the system.",
                    intent="appointment_scheduling",
                    confidence=0.9,
                    entities=entities,
                    actions=[{"type": "appointment_scheduled", "data": result.get("data")}],
                    context_update={"current_topic": "appointment_confirmed"},
                    suggestions=["View appointment details", "Schedule another appointment", "Check patient records"]
                )
            else:
                return ChatbotResponse(
                    message=f"I encountered an issue scheduling the appointment: {result.get('error', 'Unknown error')}. Please try again or contact the scheduling department.",
                    intent="appointment_scheduling",
                    confidence=0.7,
                    entities=entities,
                    actions=[],
                    context_update={},
                    suggestions=["Try again", "Contact scheduling", "Check availability"]
                )
        
        return ChatbotResponse(
            message="I'm sorry, but the appointment scheduling feature is currently unavailable. Please contact the scheduling department directly.",
            intent="appointment_scheduling",
            confidence=0.5,
            entities=entities,
            actions=[],
            context_update={},
            suggestions=["Contact scheduling department", "Try again later"]
        )

    def _handle_medical_records(self, entities: Dict[str, Any], context: Dict[str, Any]) -> ChatbotResponse:
        """Handle medical records requests"""
        patient_id = entities.get("patient_id") or context.get("patient_id")
        
        if not patient_id:
            return ChatbotResponse(
                message="To access medical records, I need to know which patient you're referring to. Could you please provide the patient's name or MRN?",
                intent="medical_records",
                confidence=0.8,
                entities=entities,
                actions=[],
                context_update={"current_topic": "medical_records"},
                suggestions=["Provide patient name", "Provide MRN", "Look up patient first"]
            )
        
        # Use medical records tool
        if "medical_records" in self.tools:
            result = self.tools["medical_records"].execute({"patient_id": patient_id})
            
            if result.get("success") and result.get("data"):
                records = result["data"]
                return ChatbotResponse(
                    message=f"I found {len(records)} medical records for this patient. Here's a summary of the most recent records:\n\n" + 
                           "\n".join([f"• {record.get('record_type', 'Unknown')}: {record.get('title', 'No title')} ({record.get('created_at', 'Unknown date')})" 
                                     for record in records[:5]]),
                    intent="medical_records",
                    confidence=0.9,
                    entities=entities,
                    actions=[{"type": "records_retrieved", "data": records}],
                    context_update={"current_topic": "medical_records", "patient_id": patient_id},
                    suggestions=["View specific record", "Create new record", "Update record", "View all records"]
                )
            else:
                return ChatbotResponse(
                    message="I couldn't retrieve the medical records at this time. Please try again or contact the medical records department.",
                    intent="medical_records",
                    confidence=0.7,
                    entities=entities,
                    actions=[],
                    context_update={},
                    suggestions=["Try again", "Contact medical records", "Check patient ID"]
                )
        
        return ChatbotResponse(
            message="I'm sorry, but the medical records feature is currently unavailable. Please contact the medical records department.",
            intent="medical_records",
            confidence=0.5,
            entities=entities,
            actions=[],
            context_update={},
            suggestions=["Contact medical records", "Try again later"]
        )

    def _handle_vital_signs(self, entities: Dict[str, Any], context: Dict[str, Any]) -> ChatbotResponse:
        """Handle vital signs requests"""
        patient_id = entities.get("patient_id") or context.get("patient_id")
        
        if not patient_id:
            return ChatbotResponse(
                message="To access vital signs, I need to know which patient you're referring to. Could you please provide the patient's name or MRN?",
                intent="vital_signs",
                confidence=0.8,
                entities=entities,
                actions=[],
                context_update={"current_topic": "vital_signs"},
                suggestions=["Provide patient name", "Provide MRN", "Look up patient first"]
            )
        
        # Check if this is a submission or retrieval request
        if entities.get("action") == "submit":
            # Handle vital signs submission
            vital_data = {
                "patient_id": patient_id,
                "heart_rate": entities.get("heart_rate"),
                "systolic_bp": entities.get("systolic_bp"),
                "diastolic_bp": entities.get("diastolic_bp"),
                "temperature": entities.get("temperature"),
                "oxygen_saturation": entities.get("oxygen_saturation")
            }
            
            if "submit_vital_signs" in self.tools:
                result = self.tools["submit_vital_signs"].execute(vital_data)
                
                if result.get("success"):
                    return ChatbotResponse(
                        message="Vital signs have been successfully recorded. The system will automatically check for any abnormal values and generate alerts if necessary.",
                        intent="vital_signs",
                        confidence=0.9,
                        entities=entities,
                        actions=[{"type": "vitals_submitted", "data": vital_data}],
                        context_update={"current_topic": "vital_signs_submitted"},
                        suggestions=["View current vitals", "Check for alerts", "Submit more vitals"]
                    )
                else:
                    return ChatbotResponse(
                        message=f"I encountered an issue recording the vital signs: {result.get('error', 'Unknown error')}. Please try again.",
                        intent="vital_signs",
                        confidence=0.7,
                        entities=entities,
                        actions=[],
                        context_update={},
                        suggestions=["Try again", "Check data format", "Contact support"]
                    )
        else:
            # Handle vital signs retrieval
            return ChatbotResponse(
                message="I can help you with vital signs. Would you like to submit new vital signs or view the current vital signs for this patient?",
                intent="vital_signs",
                confidence=0.8,
                entities=entities,
                actions=[],
                context_update={"current_topic": "vital_signs", "patient_id": patient_id},
                suggestions=["Submit new vitals", "View current vitals", "Check vital trends"]
            )

    def _handle_triage_assessment(self, entities: Dict[str, Any], context: Dict[str, Any]) -> ChatbotResponse:
        """Handle triage assessment requests"""
        patient_id = entities.get("patient_id") or context.get("patient_id")
        symptoms = entities.get("symptoms", [])
        
        if not patient_id:
            return ChatbotResponse(
                message="To perform a triage assessment, I need to know which patient you're referring to. Could you please provide the patient's name or MRN?",
                intent="triage_assessment",
                confidence=0.8,
                entities=entities,
                actions=[],
                context_update={"current_topic": "triage_assessment"},
                suggestions=["Provide patient name", "Provide MRN", "Look up patient first"]
            )
        
        if not symptoms:
            return ChatbotResponse(
                message="I can help you perform a triage assessment. Please describe the patient's symptoms or chief complaint.",
                intent="triage_assessment",
                confidence=0.8,
                entities=entities,
                actions=[],
                context_update={"current_topic": "triage_assessment", "patient_id": patient_id},
                suggestions=["Describe symptoms", "Provide chief complaint", "List vital signs"]
            )
        
        # Use triage assessment tool
        if "triage_assessment" in self.tools:
            triage_data = {
                "patient_id": patient_id,
                "symptoms": symptoms,
                "vital_signs": entities.get("vital_signs", {})
            }
            
            result = self.tools["triage_assessment"].execute(triage_data)
            
            if result.get("success"):
                triage_result = result.get("data", {})
                return ChatbotResponse(
                    message=f"Triage assessment completed:\n\n**Triage Level:** {triage_result.get('triage_level', 'Unknown')}\n**Assessment:** {triage_result.get('assessment', 'No assessment available')}\n**Recommendations:** {triage_result.get('recommendations', 'No recommendations available')}",
                    intent="triage_assessment",
                    confidence=0.9,
                    entities=entities,
                    actions=[{"type": "triage_completed", "data": triage_result}],
                    context_update={"current_topic": "triage_completed", "triage_result": triage_result},
                    suggestions=["Schedule appointment", "Create medical record", "Monitor patient", "Escalate to doctor"]
                )
            else:
                return ChatbotResponse(
                    message=f"I encountered an issue performing the triage assessment: {result.get('error', 'Unknown error')}. Please try again or contact medical staff.",
                    intent="triage_assessment",
                    confidence=0.7,
                    entities=entities,
                    actions=[],
                    context_update={},
                    suggestions=["Try again", "Contact medical staff", "Provide more details"]
                )
        
        return ChatbotResponse(
            message="I'm sorry, but the triage assessment feature is currently unavailable. Please contact medical staff for immediate assistance.",
            intent="triage_assessment",
            confidence=0.5,
            entities=entities,
            actions=[],
            context_update={},
            suggestions=["Contact medical staff", "Try again later"]
        )

    def _handle_general_help(self, message: str, context: Dict[str, Any]) -> ChatbotResponse:
        """Handle general help and conversation"""
        prompt = f"""You are a helpful healthcare assistant. The user said: "{message}"

Context: {json.dumps(context, indent=2)}

Provide a helpful, professional response that guides the user toward healthcare-related assistance. Keep responses concise and actionable."""

        try:
            # Use the LLM with proper API
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_client.invoke(messages)
            
            bot_message = response.content
            
            return ChatbotResponse(
                message=bot_message,
                intent="general_help",
                confidence=0.6,
                entities={},
                actions=[],
                context_update={"current_topic": "general_help"},
                suggestions=["Patient lookup", "Schedule appointment", "Medical records", "Emergency help"]
            )
            
        except Exception as e:
            logger.error(f"General help generation failed: {str(e)}")
            return ChatbotResponse(
                message="I'm here to help with healthcare-related questions. You can ask me about patient information, appointments, medical records, or any other healthcare needs. How can I assist you today?",
                intent="general_help",
                confidence=0.5,
                entities={},
                actions=[],
                context_update={"current_topic": "general_help"},
                suggestions=["Patient lookup", "Schedule appointment", "Medical records", "Emergency help"]
            )

    def _update_context(self, session_id: str, user_message: str, response: ChatbotResponse, 
                       context: Dict[str, Any]):
        """Update conversation context"""
        with get_db_session() as session:
            context_record = session.query(ChatbotContext).filter(
                ChatbotContext.session_id == session_id
            ).first()
            
            if context_record:
                # Update context with new information
                context_record.context_data.update(response.context_update)
                context_record.context_data["conversation_history"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_message": user_message,
                    "bot_response": response.message,
                    "intent": response.intent
                })
                
                # Keep only last 10 messages in history
                if len(context_record.context_data["conversation_history"]) > 10:
                    context_record.context_data["conversation_history"] = \
                        context_record.context_data["conversation_history"][-10:]
                
                context_record.last_activity = datetime.utcnow()
                session.commit()

    def _log_conversation(self, session_id: str, user_message: str, response: ChatbotResponse, 
                         intent_analysis: Dict[str, Any]):
        """Log conversation for analysis"""
        with get_db_session() as session:
            # Get or create conversation
            conversation = session.query(ChatbotConversation).filter(
                ChatbotConversation.session_id == session_id,
                ChatbotConversation.status == 'active'
            ).first()
            
            if not conversation:
                conversation = ChatbotConversation(
                    session_id=session_id,
                    conversation_type='general'
                )
                session.add(conversation)
                session.commit()
            
            # Add user message
            user_msg = ChatbotMessage(
                conversation_id=conversation.id,
                message_type='user',
                content=user_message,
                intent=intent_analysis.get('intent'),
                confidence=intent_analysis.get('confidence'),
                entities=intent_analysis.get('entities'),
                response_time=getattr(response, 'response_time', 0.0)
            )
            session.add(user_msg)
            
            # Add bot response
            bot_msg = ChatbotMessage(
                conversation_id=conversation.id,
                message_type='bot',
                content=response.message,
                intent=response.intent,
                confidence=response.confidence,
                entities=response.entities,
                response_time=getattr(response, 'response_time', 0.0)
            )
            session.add(bot_msg)
            
            session.commit()

    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        with get_db_session() as session:
            conversation = session.query(ChatbotConversation).filter(
                ChatbotConversation.session_id == session_id,
                ChatbotConversation.status == 'active'
            ).first()
            
            if not conversation:
                return []
            
            messages = session.query(ChatbotMessage).filter(
                ChatbotMessage.conversation_id == conversation.id
            ).order_by(ChatbotMessage.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": str(msg.id),
                    "type": msg.message_type,
                    "content": msg.content,
                    "intent": msg.intent,
                    "confidence": msg.confidence,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in reversed(messages)
            ]

    def close_conversation(self, session_id: str):
        """Close a conversation session"""
        with get_db_session() as session:
            conversation = session.query(ChatbotConversation).filter(
                ChatbotConversation.session_id == session_id,
                ChatbotConversation.status == 'active'
            ).first()
            
            if conversation:
                conversation.status = 'closed'
                conversation.closed_at = datetime.utcnow()
                session.commit()
            
            # Also close context
            context = session.query(ChatbotContext).filter(
                ChatbotContext.session_id == session_id
            ).first()
            
            if context:
                session.delete(context)
                session.commit() 