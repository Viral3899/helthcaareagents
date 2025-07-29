"""
Notification Tools

This module provides notification and alert tools for communicating with healthcare staff,
patients, and other stakeholders in the healthcare system.
"""

from typing import Dict, List, Any, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import logging
import json
from datetime import datetime
from database.models import Alert, AlertSeverity
from database.connection import get_db_session

class AlertInput(BaseModel):
    """Input for creating alerts"""
    patient_id: str = Field(description="Patient ID")
    alert_type: str = Field(description="Type of alert")
    severity: str = Field(description="Alert severity (low/medium/high/critical)")
    title: str = Field(description="Alert title")
    message: str = Field(description="Alert message")
    source: str = Field(description="Source of the alert")

class MessageInput(BaseModel):
    """Input for sending messages"""
    recipient: str = Field(description="Message recipient")
    message_type: str = Field(description="Type of message")
    content: str = Field(description="Message content")
    priority: str = Field(description="Message priority")

class CreateAlertTool(BaseTool):
    """Tool for creating system alerts"""
    name: str = "create_alert"
    description: str = "Create a new alert in the healthcare system"
    args_schema: type[BaseModel] = AlertInput
    
    def _run(self, patient_id: str, alert_type: str, severity: str, title: str, message: str, source: str) -> Dict[str, Any]:
        """Create a new alert"""
        try:
            with get_db_session() as session:
                # Map severity string to enum
                severity_map = {
                    'low': AlertSeverity.LOW,
                    'medium': AlertSeverity.MEDIUM,
                    'high': AlertSeverity.HIGH,
                    'critical': AlertSeverity.CRITICAL
                }
                
                alert_severity = severity_map.get(severity.lower(), AlertSeverity.MEDIUM)
                
                # Create alert
                alert = Alert(
                    patient_id=patient_id,
                    alert_type=alert_type,
                    severity=alert_severity,
                    title=title,
                    message=message,
                    source=source
                )
                
                session.add(alert)
                session.commit()
                session.refresh(alert)
                
                # Log alert creation
                logging.info(f"Alert created: {alert.id} - {title} for patient {patient_id}")
                
                return {
                    'success': True,
                    'alert_id': str(alert.id),
                    'alert_type': alert.alert_type,
                    'severity': alert.severity.value,
                    'title': alert.title,
                    'created_at': alert.created_at.isoformat()
                }
                
        except Exception as e:
            logging.error(f"Failed to create alert: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to create alert: {str(e)}"
            }

class SendMessageTool(BaseTool):
    """Tool for sending messages to healthcare staff"""
    name: str = "send_message"
    description: str = "Send a message to healthcare staff or patients"
    args_schema: type[BaseModel] = MessageInput
    
    def _run(self, recipient: str, message_type: str, content: str, priority: str) -> Dict[str, Any]:
        """Send a message"""
        try:
            # In a real system, this would integrate with email, SMS, or internal messaging
            message_data = {
                'recipient': recipient,
                'message_type': message_type,
                'content': content,
                'priority': priority,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'sent'
            }
            
            # Log message
            logging.info(f"Message sent to {recipient}: {content[:50]}...")
            
            return {
                'success': True,
                'message_id': f"msg_{datetime.utcnow().timestamp()}",
                'recipient': recipient,
                'message_type': message_type,
                'priority': priority,
                'sent_at': message_data['timestamp'],
                'status': 'sent'
            }
            
        except Exception as e:
            logging.error(f"Failed to send message: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to send message: {str(e)}"
            }

class EmergencyNotificationTool(BaseTool):
    """Tool for sending emergency notifications"""
    name: str = "send_emergency_notification"
    description: str = "Send emergency notifications to appropriate staff"
    args_schema: type[BaseModel] = AlertInput
    
    def _run(self, emergency_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send emergency notification"""
        try:
            patient_id = emergency_data.get('patient_id', 'unknown')
            emergency_type = emergency_data.get('emergency_type', 'unknown')
            severity = emergency_data.get('severity', 'high')
            description = emergency_data.get('description', 'Emergency situation')
            
            # Determine notification recipients based on emergency type
            recipients = self._get_emergency_recipients(emergency_type, severity)
            
            # Create notification message
            message = self._create_emergency_message(emergency_data)
            
            notifications_sent = []
            
            # Send notifications to each recipient
            for recipient in recipients:
                notification = {
                    'recipient': recipient,
                    'message_type': 'emergency',
                    'content': message,
                    'priority': 'critical' if severity in ['critical', 'high'] else 'high',
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                notifications_sent.append(notification)
                
                # Log emergency notification
                logging.warning(f"Emergency notification sent to {recipient}: {emergency_type}")
            
            return {
                'success': True,
                'emergency_type': emergency_type,
                'severity': severity,
                'recipients': recipients,
                'notifications_sent': len(notifications_sent),
                'message': message,
                'sent_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Failed to send emergency notification: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to send emergency notification: {str(e)}"
            }
    
    def _get_emergency_recipients(self, emergency_type: str, severity: str) -> List[str]:
        """Get appropriate recipients for emergency type"""
        recipients = []
        
        # Always notify emergency response team for critical/high severity
        if severity in ['critical', 'high']:
            recipients.extend(['emergency_team', 'charge_nurse', 'attending_physician'])
        
        # Add specific recipients based on emergency type
        if emergency_type.lower() in ['cardiac', 'heart attack', 'chest pain']:
            recipients.extend(['cardiology_team', 'cardiologist'])
        elif emergency_type.lower() in ['respiratory', 'breathing', 'asthma']:
            recipients.extend(['respiratory_team', 'pulmonologist'])
        elif emergency_type.lower() in ['neurological', 'stroke', 'seizure']:
            recipients.extend(['neurology_team', 'neurologist'])
        elif emergency_type.lower() in ['trauma', 'injury']:
            recipients.extend(['trauma_team', 'surgeon'])
        else:
            recipients.extend(['general_medical_team', 'hospitalist'])
        
        # Remove duplicates
        return list(set(recipients))
    
    def _create_emergency_message(self, emergency_data: Dict[str, Any]) -> str:
        """Create emergency notification message"""
        patient_id = emergency_data.get('patient_id', 'unknown')
        emergency_type = emergency_data.get('emergency_type', 'unknown')
        severity = emergency_data.get('severity', 'high')
        description = emergency_data.get('description', 'Emergency situation')
        location = emergency_data.get('location', 'unknown')
        
        message = f"""
EMERGENCY ALERT - {severity.upper()} SEVERITY

Patient ID: {patient_id}
Emergency Type: {emergency_type}
Location: {location}
Description: {description}

IMMEDIATE RESPONSE REQUIRED
        """.strip()
        
        return message

class PatientNotificationTool(BaseTool):
    """Tool for sending notifications to patients"""
    name: str = "send_patient_notification"
    description: str = "Send notifications to patients about appointments, results, etc."
    args_schema: type[BaseModel] = MessageInput
    
    def _run(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send patient notification"""
        try:
            patient_id = patient_data.get('patient_id', 'unknown')
            notification_type = patient_data.get('notification_type', 'general')
            content = patient_data.get('content', '')
            priority = patient_data.get('priority', 'normal')
            
            # Get patient contact information (in real system, would query database)
            contact_info = self._get_patient_contact_info(patient_id)
            
            if not contact_info:
                return {
                    'success': False,
                    'error': f"No contact information found for patient {patient_id}"
                }
            
            # Create patient-specific message
            message = self._create_patient_message(patient_data, contact_info)
            
            # Send notification through appropriate channels
            channels_used = []
            
            if contact_info.get('email'):
                channels_used.append('email')
            
            if contact_info.get('phone'):
                channels_used.append('sms')
            
            if contact_info.get('preferred_contact'):
                channels_used.append(contact_info['preferred_contact'])
            
            return {
                'success': True,
                'patient_id': patient_id,
                'notification_type': notification_type,
                'priority': priority,
                'channels_used': channels_used,
                'message': message,
                'sent_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Failed to send patient notification: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to send patient notification: {str(e)}"
            }
    
    def _get_patient_contact_info(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient contact information"""
        try:
            with get_db_session() as session:
                from database.models import Patient
                patient = session.query(Patient).filter(Patient.id == patient_id).first()
                
                if patient:
                    return {
                        'email': patient.email,
                        'phone': patient.phone,
                        'name': f"{patient.first_name} {patient.last_name}",
                        'preferred_contact': 'email'  # Default preference
                    }
                
                return None
                
        except Exception as e:
            logging.error(f"Failed to get patient contact info: {str(e)}")
            return None
    
    def _create_patient_message(self, patient_data: Dict[str, Any], contact_info: Dict[str, Any]) -> str:
        """Create patient-specific notification message"""
        notification_type = patient_data.get('notification_type', 'general')
        content = patient_data.get('content', '')
        patient_name = contact_info.get('name', 'Patient')
        
        if notification_type == 'appointment_reminder':
            message = f"""
Dear {patient_name},

This is a reminder about your upcoming appointment.

{content}

Please arrive 15 minutes before your scheduled time.

If you need to reschedule, please contact us as soon as possible.

Best regards,
Healthcare Team
            """.strip()
        
        elif notification_type == 'test_results':
            message = f"""
Dear {patient_name},

Your test results are ready for review.

{content}

Please contact your healthcare provider to discuss these results.

Best regards,
Healthcare Team
            """.strip()
        
        elif notification_type == 'medication_reminder':
            message = f"""
Dear {patient_name},

This is a reminder to take your medication.

{content}

Please take your medication as prescribed.

Best regards,
Healthcare Team
            """.strip()
        
        else:
            message = f"""
Dear {patient_name},

{content}

Best regards,
Healthcare Team
            """.strip()
        
        return message

class StaffNotificationTool(BaseTool):
    """Tool for sending notifications to healthcare staff"""
    name: str = "send_staff_notification"
    description: str = "Send notifications to healthcare staff about patients, schedules, etc."
    args_schema: type[BaseModel] = MessageInput
    
    def _run(self, staff_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send staff notification"""
        try:
            staff_role = staff_data.get('staff_role', 'general')
            notification_type = staff_data.get('notification_type', 'general')
            content = staff_data.get('content', '')
            priority = staff_data.get('priority', 'normal')
            patient_id = staff_data.get('patient_id')
            
            # Get staff recipients based on role and notification type
            recipients = self._get_staff_recipients(staff_role, notification_type, patient_id)
            
            # Create staff-specific message
            message = self._create_staff_message(staff_data)
            
            notifications_sent = []
            
            # Send notifications to each recipient
            for recipient in recipients:
                notification = {
                    'recipient': recipient,
                    'message_type': notification_type,
                    'content': message,
                    'priority': priority,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                notifications_sent.append(notification)
                
                # Log staff notification
                logging.info(f"Staff notification sent to {recipient}: {notification_type}")
            
            return {
                'success': True,
                'staff_role': staff_role,
                'notification_type': notification_type,
                'priority': priority,
                'recipients': recipients,
                'notifications_sent': len(notifications_sent),
                'message': message,
                'sent_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Failed to send staff notification: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to send staff notification: {str(e)}"
            }
    
    def _get_staff_recipients(self, staff_role: str, notification_type: str, patient_id: Optional[str]) -> List[str]:
        """Get appropriate staff recipients"""
        recipients = []
        
        # Add recipients based on staff role
        if staff_role == 'nurse':
            recipients.extend(['charge_nurse', 'floor_nurses'])
        elif staff_role == 'doctor':
            recipients.extend(['attending_physician', 'resident_physicians'])
        elif staff_role == 'specialist':
            recipients.extend(['specialist_team', 'consulting_physicians'])
        else:
            recipients.extend(['general_staff', 'healthcare_team'])
        
        # Add recipients based on notification type
        if notification_type == 'patient_alert':
            recipients.extend(['patient_care_team', 'monitoring_staff'])
        elif notification_type == 'schedule_change':
            recipients.extend(['scheduling_staff', 'department_heads'])
        elif notification_type == 'emergency':
            recipients.extend(['emergency_team', 'rapid_response_team'])
        
        # Remove duplicates
        return list(set(recipients))
    
    def _create_staff_message(self, staff_data: Dict[str, Any]) -> str:
        """Create staff-specific notification message"""
        notification_type = staff_data.get('notification_type', 'general')
        content = staff_data.get('content', '')
        patient_id = staff_data.get('patient_id', 'unknown')
        priority = staff_data.get('priority', 'normal')
        
        if notification_type == 'patient_alert':
            message = f"""
PATIENT ALERT - {priority.upper()} PRIORITY

Patient ID: {patient_id}

{content}

Please review and take appropriate action.

Sent: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
        
        elif notification_type == 'schedule_change':
            message = f"""
SCHEDULE UPDATE

{content}

Please update your schedule accordingly.

Sent: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
        
        elif notification_type == 'emergency':
            message = f"""
EMERGENCY NOTIFICATION

{content}

IMMEDIATE ATTENTION REQUIRED

Sent: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
        
        else:
            message = f"""
STAFF NOTIFICATION

{content}

Sent: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
        
        return message
