"""
Emergency Response Workflow

This module implements the emergency response workflow that coordinates
emergency situations, rapid response protocols, and critical patient care.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from agents.emergency_agent import EmergencyAgent
from agents.triage_agent import TriageAgent
from agents.monitoring_agent import MonitoringAgent
from utils.logger import log_workflow_event, log_emergency_event
from database.connection import get_db_session
from database.models import Patient, Alert, AlertSeverity, EmergencyResponse

class EmergencyResponseWorkflow:
    """Emergency response workflow coordinator"""
    
    def __init__(self, tools: Dict[str, Any]):
        self.tools = tools
        self.emergency_agent = EmergencyAgent(tools)
        self.triage_agent = TriageAgent(tools)
        self.monitoring_agent = MonitoringAgent(tools)
        self.logger = logging.getLogger(__name__)
    
    def handle_emergency(self, emergency_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle emergency situation"""
        try:
            patient_id = emergency_data.get('patient_id')
            emergency_type = emergency_data.get('emergency_type', 'unknown')
            severity = emergency_data.get('severity', 'high')
            description = emergency_data.get('description', 'Emergency situation')
            
            # Log emergency start
            log_workflow_event("emergency_response", "started", "Emergency response initiated", patient_id, emergency_data)
            
            # Step 1: Initial emergency assessment
            assessment_result = self._assess_emergency(emergency_data)
            
            # Step 2: Determine response level
            response_level = self._determine_response_level(assessment_result, severity)
            
            # Step 3: Activate emergency protocols
            activation_result = self._activate_emergency_protocols(patient_id, emergency_type, response_level)
            
            # Step 4: Coordinate response team
            coordination_result = self._coordinate_response_team(patient_id, emergency_type, response_level)
            
            # Step 5: Monitor and escalate if needed
            monitoring_result = self._monitor_emergency_situation(patient_id, emergency_type)
            
            # Step 6: Document emergency response
            documentation_result = self._document_emergency_response(patient_id, emergency_data, assessment_result)
            
            # Compile final result
            result = {
                'success': True,
                'emergency_id': f"EMG_{datetime.utcnow().timestamp()}",
                'patient_id': patient_id,
                'emergency_type': emergency_type,
                'severity': severity,
                'response_level': response_level,
                'assessment': assessment_result,
                'activation': activation_result,
                'coordination': coordination_result,
                'monitoring': monitoring_result,
                'documentation': documentation_result,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Log emergency completion
            log_workflow_event("emergency_response", "completed", "Emergency response completed", patient_id, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Emergency response workflow failed: {str(e)}")
            log_workflow_event("emergency_response", "failed", f"Emergency response failed: {str(e)}", patient_id, emergency_data)
            return {
                'success': False,
                'error': f"Emergency response failed: {str(e)}",
                'emergency_data': emergency_data
            }
    
    def _assess_emergency(self, emergency_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess emergency situation"""
        try:
            # Use emergency agent to assess the situation
            assessment_input = {
                'emergency_type': emergency_data.get('emergency_type'),
                'severity': emergency_data.get('severity'),
                'description': emergency_data.get('description'),
                'patient_symptoms': emergency_data.get('symptoms', []),
                'vital_signs': emergency_data.get('vital_signs', {}),
                'location': emergency_data.get('location', 'unknown')
            }
            
            assessment_result = self.emergency_agent.assess_emergency(assessment_input)
            
            return {
                'assessment_result': assessment_result,
                'risk_level': assessment_result.get('risk_level', 'unknown'),
                'immediate_actions': assessment_result.get('immediate_actions', []),
                'required_resources': assessment_result.get('required_resources', [])
            }
            
        except Exception as e:
            self.logger.error(f"Emergency assessment failed: {str(e)}")
            return {
                'assessment_result': {'error': str(e)},
                'risk_level': 'unknown',
                'immediate_actions': ['Contact emergency team'],
                'required_resources': ['Emergency response team']
            }
    
    def _determine_response_level(self, assessment_result: Dict[str, Any], severity: str) -> str:
        """Determine appropriate response level"""
        risk_level = assessment_result.get('risk_level', 'unknown')
        
        # Map severity and risk to response level
        if severity == 'critical' or risk_level == 'critical':
            return 'code_blue'
        elif severity == 'high' or risk_level == 'high':
            return 'rapid_response'
        elif severity == 'medium' or risk_level == 'medium':
            return 'urgent_care'
        else:
            return 'standard_emergency'
    
    def _activate_emergency_protocols(self, patient_id: str, emergency_type: str, response_level: str) -> Dict[str, Any]:
        """Activate emergency protocols"""
        try:
            # Create emergency alert
            alert_data = {
                'patient_id': patient_id,
                'alert_type': 'emergency',
                'severity': 'critical' if response_level == 'code_blue' else 'high',
                'title': f'Emergency: {emergency_type}',
                'message': f'Emergency situation detected. Response level: {response_level}',
                'source': 'emergency_workflow'
            }
            
            # Use emergency agent to create alert
            alert_result = self.emergency_agent.create_emergency_alert(alert_data)
            
            # Determine required protocols based on emergency type
            protocols = self._get_emergency_protocols(emergency_type, response_level)
            
            # Activate each protocol
            activated_protocols = []
            for protocol in protocols:
                try:
                    protocol_result = self.emergency_agent.activate_protocol(protocol, patient_id)
                    activated_protocols.append({
                        'protocol': protocol,
                        'result': protocol_result
                    })
                except Exception as e:
                    self.logger.error(f"Failed to activate protocol {protocol}: {str(e)}")
                    activated_protocols.append({
                        'protocol': protocol,
                        'result': {'success': False, 'error': str(e)}
                    })
            
            return {
                'alert_created': alert_result.get('success', False),
                'alert_id': alert_result.get('alert_id'),
                'response_level': response_level,
                'activated_protocols': activated_protocols,
                'total_protocols': len(protocols)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to activate emergency protocols: {str(e)}")
            return {
                'alert_created': False,
                'error': str(e),
                'activated_protocols': [],
                'total_protocols': 0
            }
    
    def _coordinate_response_team(self, patient_id: str, emergency_type: str, response_level: str) -> Dict[str, Any]:
        """Coordinate emergency response team"""
        try:
            # Determine required team members
            team_members = self._get_required_team_members(emergency_type, response_level)
            
            # Notify team members
            notifications_sent = []
            for member in team_members:
                try:
                    notification_data = {
                        'recipient': member,
                        'message_type': 'emergency',
                        'content': f'Emergency situation for patient {patient_id}. Type: {emergency_type}. Response level: {response_level}',
                        'priority': 'critical'
                    }
                    
                    notification_result = self.tools.get('notification', {}).get('send_message', lambda x: {'success': True})(notification_data)
                    notifications_sent.append({
                        'recipient': member,
                        'success': notification_result.get('success', False)
                    })
                except Exception as e:
                    self.logger.error(f"Failed to notify {member}: {str(e)}")
                    notifications_sent.append({
                        'recipient': member,
                        'success': False,
                        'error': str(e)
                    })
            
            # Coordinate with emergency agent
            coordination_result = self.emergency_agent.coordinate_response(patient_id, emergency_type, team_members)
            
            return {
                'team_members': team_members,
                'notifications_sent': notifications_sent,
                'coordination_result': coordination_result,
                'total_notifications': len(notifications_sent)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to coordinate response team: {str(e)}")
            return {
                'team_members': [],
                'notifications_sent': [],
                'error': str(e),
                'total_notifications': 0
            }
    
    def _monitor_emergency_situation(self, patient_id: str, emergency_type: str) -> Dict[str, Any]:
        """Monitor emergency situation"""
        try:
            # Set up continuous monitoring
            monitoring_config = {
                'patient_id': patient_id,
                'monitoring_type': 'emergency',
                'vital_signs_frequency': 30,  # seconds
                'alert_thresholds': {
                    'heart_rate': {'min': 50, 'max': 150},
                    'systolic_bp': {'min': 80, 'max': 200},
                    'oxygen_saturation': {'min': 90, 'max': 100}
                }
            }
            
            # Start monitoring
            monitoring_result = self.monitoring_agent.start_emergency_monitoring(monitoring_config)
            
            # Set up escalation triggers
            escalation_triggers = self._setup_escalation_triggers(patient_id, emergency_type)
            
            return {
                'monitoring_started': monitoring_result.get('success', False),
                'monitoring_id': monitoring_result.get('monitoring_id'),
                'escalation_triggers': escalation_triggers,
                'vital_signs_frequency': monitoring_config['vital_signs_frequency']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to monitor emergency situation: {str(e)}")
            return {
                'monitoring_started': False,
                'error': str(e),
                'escalation_triggers': []
            }
    
    def _document_emergency_response(self, patient_id: str, emergency_data: Dict[str, Any], assessment_result: Dict[str, Any]) -> Dict[str, Any]:
        """Document emergency response"""
        try:
            # Create emergency response record
            response_record = {
                'patient_id': patient_id,
                'emergency_type': emergency_data.get('emergency_type'),
                'severity': emergency_data.get('severity'),
                'description': emergency_data.get('description'),
                'assessment_result': assessment_result,
                'response_timestamp': datetime.utcnow().isoformat(),
                'status': 'active'
            }
            
            # Use emergency agent to document response
            documentation_result = self.emergency_agent.document_emergency_response(response_record)
            
            return {
                'documentation_created': documentation_result.get('success', False),
                'response_id': documentation_result.get('response_id'),
                'timestamp': response_record['response_timestamp']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to document emergency response: {str(e)}")
            return {
                'documentation_created': False,
                'error': str(e)
            }
    
    def _get_emergency_protocols(self, emergency_type: str, response_level: str) -> List[str]:
        """Get emergency protocols based on type and response level"""
        protocols = []
        
        # Base protocols for all emergencies
        protocols.extend(['patient_safety', 'communication', 'documentation'])
        
        # Type-specific protocols
        if emergency_type.lower() in ['cardiac', 'heart attack', 'chest pain']:
            protocols.extend(['cardiac_arrest', 'defibrillation', 'cardiac_monitoring'])
        elif emergency_type.lower() in ['respiratory', 'breathing', 'asthma']:
            protocols.extend(['respiratory_distress', 'oxygen_therapy', 'ventilation'])
        elif emergency_type.lower() in ['neurological', 'stroke', 'seizure']:
            protocols.extend(['stroke_protocol', 'neurological_assessment', 'imaging'])
        elif emergency_type.lower() in ['trauma', 'injury']:
            protocols.extend(['trauma_protocol', 'bleeding_control', 'immobilization'])
        
        # Response level specific protocols
        if response_level == 'code_blue':
            protocols.extend(['code_blue_activation', 'crash_cart', 'emergency_team'])
        elif response_level == 'rapid_response':
            protocols.extend(['rapid_response_team', 'vital_signs_monitoring'])
        
        return protocols
    
    def _get_required_team_members(self, emergency_type: str, response_level: str) -> List[str]:
        """Get required team members for emergency response"""
        team_members = []
        
        # Base team for all emergencies
        team_members.extend(['emergency_team', 'charge_nurse'])
        
        # Type-specific team members
        if emergency_type.lower() in ['cardiac', 'heart attack']:
            team_members.extend(['cardiologist', 'cardiology_team'])
        elif emergency_type.lower() in ['respiratory', 'breathing']:
            team_members.extend(['pulmonologist', 'respiratory_therapist'])
        elif emergency_type.lower() in ['neurological', 'stroke']:
            team_members.extend(['neurologist', 'neurology_team'])
        elif emergency_type.lower() in ['trauma', 'injury']:
            team_members.extend(['trauma_surgeon', 'trauma_team'])
        
        # Response level specific team members
        if response_level == 'code_blue':
            team_members.extend(['anesthesiologist', 'emergency_physician', 'respiratory_therapist'])
        elif response_level == 'rapid_response':
            team_members.extend(['hospitalist', 'critical_care_nurse'])
        
        return team_members
    
    def _setup_escalation_triggers(self, patient_id: str, emergency_type: str) -> List[Dict[str, Any]]:
        """Setup escalation triggers for emergency monitoring"""
        triggers = []
        
        # Vital signs triggers
        triggers.append({
            'type': 'vital_signs',
            'condition': 'heart_rate < 50 or heart_rate > 150',
            'action': 'escalate_to_critical_care',
            'priority': 'high'
        })
        
        triggers.append({
            'type': 'vital_signs',
            'condition': 'oxygen_saturation < 90',
            'action': 'escalate_to_respiratory_care',
            'priority': 'high'
        })
        
        triggers.append({
            'type': 'vital_signs',
            'condition': 'systolic_bp < 80 or systolic_bp > 200',
            'action': 'escalate_to_critical_care',
            'priority': 'high'
        })
        
        # Time-based triggers
        triggers.append({
            'type': 'time',
            'condition': 'no_improvement_after_15_minutes',
            'action': 'escalate_response_level',
            'priority': 'medium'
        })
        
        triggers.append({
            'type': 'time',
            'condition': 'no_improvement_after_30_minutes',
            'action': 'activate_code_blue',
            'priority': 'high'
        })
        
        return triggers
    
    def resolve_emergency(self, emergency_id: str, resolution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve emergency situation"""
        try:
            # Update emergency status
            resolution_result = self.emergency_agent.resolve_emergency(emergency_id, resolution_data)
            
            # Stop monitoring
            if resolution_data.get('patient_id'):
                monitoring_result = self.monitoring_agent.stop_emergency_monitoring(resolution_data['patient_id'])
            else:
                monitoring_result = {'success': False, 'error': 'No patient ID provided'}
            
            # Document resolution
            documentation_result = self._document_emergency_resolution(emergency_id, resolution_data)
            
            # Log resolution
            log_workflow_event("emergency_response", "resolved", "Emergency resolved", 
                             resolution_data.get('patient_id'), resolution_data)
            
            return {
                'success': True,
                'emergency_id': emergency_id,
                'resolution_result': resolution_result,
                'monitoring_stopped': monitoring_result.get('success', False),
                'documentation_updated': documentation_result.get('success', False),
                'resolution_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to resolve emergency: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to resolve emergency: {str(e)}",
                'emergency_id': emergency_id
            }
    
    def _document_emergency_resolution(self, emergency_id: str, resolution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Document emergency resolution"""
        try:
            resolution_record = {
                'emergency_id': emergency_id,
                'resolution_type': resolution_data.get('resolution_type', 'resolved'),
                'resolution_notes': resolution_data.get('notes', ''),
                'resolved_by': resolution_data.get('resolved_by', 'system'),
                'resolution_timestamp': datetime.utcnow().isoformat(),
                'outcome': resolution_data.get('outcome', 'successful')
            }
            
            # Use emergency agent to document resolution
            documentation_result = self.emergency_agent.document_emergency_resolution(resolution_record)
            
            return {
                'success': documentation_result.get('success', False),
                'resolution_id': documentation_result.get('resolution_id')
            }
            
        except Exception as e:
            self.logger.error(f"Failed to document emergency resolution: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }