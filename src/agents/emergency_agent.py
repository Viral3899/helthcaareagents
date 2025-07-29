"""
Emergency Agent

This agent handles emergency response coordination, critical patient situations,
and rapid response protocols for life-threatening conditions.
"""

from typing import Dict, List, Any, Optional
from langchain_core.tools import BaseTool
from agents.base_agent import BaseHealthcareAgent
from utils.logger import log_agent_event
from database.models import AlertSeverity, EmergencyResponse
from database.connection import get_db_session
from datetime import datetime

class EmergencyAgent(BaseHealthcareAgent):
    """AI agent for emergency response coordination"""
    
    def __init__(self, tools: Dict[str, Any]):
        system_prompt = """You are an Emergency Agent responsible for detecting, prioritizing, and coordinating emergency responses for patients.

Your responsibilities include:
1. Identifying emergency situations from patient data
2. Prioritizing emergency cases
3. Coordinating with other agents and medical staff
4. Recommending immediate interventions
5. Ensuring rapid response and patient safety

Always act with urgency and prioritize life-threatening conditions."""

        # Get emergency-specific tools
        emergency_tools = [
            tools.get('database', None),
            tools.get('medical', None),
            tools.get('notification', None),
            tools.get('validation', None)
        ]
        emergency_tools = [tool for tool in emergency_tools if tool is not None]
        
        super().__init__("EmergencyAgent", system_prompt, emergency_tools)
        self.logger = log_agent_event
    
    def handle_emergency(self, emergency_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle emergency situation and coordinate response"""
        try:
            # Prepare emergency input
            emergency_input = self._prepare_emergency_input(emergency_data)
            
            # Execute emergency response
            result = self.execute(emergency_input)
            
            if result['success']:
                # Parse emergency response from result
                response_plan = self._parse_emergency_response(result['result'])
                
                # Create emergency response record
                response_record = self._create_emergency_record(emergency_data, response_plan, result['result'])
                
                # Log emergency response
                self.logger("EmergencyAgent", "emergency_handled", 
                           f"Emergency response initiated for patient {emergency_data.get('patient_id', 'unknown')}")
                
                return {
                    'success': True,
                    'response_plan': response_plan,
                    'assessment': result['result'],
                    'response_id': response_record.get('id') if response_record else None,
                    'severity': response_plan.get('severity', 'medium'),
                    'response_time': response_plan.get('response_time', 300)
                }
            else:
                self.logger("EmergencyAgent", "emergency_failed", 
                           f"Emergency response failed: {result.get('error', 'Unknown error')}")
                return result
                
        except Exception as e:
            self.logger("EmergencyAgent", "emergency_error", f"Emergency response error: {str(e)}")
            return {
                'success': False,
                'error': f"Emergency response failed: {str(e)}"
            }
    
    def _prepare_emergency_input(self, emergency_data: Dict[str, Any]) -> str:
        """Prepare input for emergency response"""
        input_parts = []
        
        # Patient information
        if 'patient_id' in emergency_data:
            input_parts.append(f"Patient ID: {emergency_data['patient_id']}")
        
        if 'age' in emergency_data:
            input_parts.append(f"Age: {emergency_data['age']}")
        
        if 'gender' in emergency_data:
            input_parts.append(f"Gender: {emergency_data['gender']}")
        
        # Emergency details
        if 'emergency_type' in emergency_data:
            input_parts.append(f"Emergency Type: {emergency_data['emergency_type']}")
        
        if 'description' in emergency_data:
            input_parts.append(f"Description: {emergency_data['description']}")
        
        if 'location' in emergency_data:
            input_parts.append(f"Location: {emergency_data['location']}")
        
        # Vital signs
        if 'vital_signs' in emergency_data:
            vitals = emergency_data['vital_signs']
            vitals_str = []
            for vital, value in vitals.items():
                if value is not None:
                    vitals_str.append(f"{vital}: {value}")
            if vitals_str:
                input_parts.append(f"Current Vital Signs: {', '.join(vitals_str)}")
        
        # Medical history
        if 'medical_history' in emergency_data:
            history = emergency_data['medical_history']
            if isinstance(history, list):
                history_str = ", ".join(history)
            else:
                history_str = str(history)
            input_parts.append(f"Medical History: {history_str}")
        
        # Allergies
        if 'allergies' in emergency_data:
            allergies = emergency_data['allergies']
            if isinstance(allergies, list):
                allergies_str = ", ".join(allergies)
            else:
                allergies_str = str(allergies)
            input_parts.append(f"Allergies: {allergies_str}")
        
        # Current medications
        if 'medications' in emergency_data:
            meds = emergency_data['medications']
            if isinstance(meds, list):
                meds_str = ", ".join(meds)
            else:
                meds_str = str(meds)
            input_parts.append(f"Current Medications: {meds_str}")
        
        # Additional context
        if 'additional_context' in emergency_data:
            input_parts.append(f"Additional Context: {emergency_data['additional_context']}")
        
        # Create emergency response prompt
        emergency_prompt = f"""
EMERGENCY SITUATION - IMMEDIATE RESPONSE REQUIRED:

{chr(10).join(input_parts)}

Based on the above emergency information, please:
1. Assess the emergency severity (critical/high/medium/low)
2. Determine immediate response actions needed
3. Identify required medical team members
4. Estimate response time requirements
5. Recommend specific interventions
6. Provide emergency protocol guidance

Format your response as:
SEVERITY: [critical/high/medium/low]
IMMEDIATE_ACTIONS: [list of immediate actions]
REQUIRED_TEAM: [list of required medical staff]
RESPONSE_TIME: [estimated response time in seconds]
INTERVENTIONS: [specific medical interventions]
PROTOCOL: [emergency protocol to follow]
ASSESSMENT: [brief emergency assessment]
"""
        
        return emergency_prompt
    
    def _parse_emergency_response(self, result: str) -> Dict[str, Any]:
        """Parse emergency response from agent result"""
        try:
            response_plan = {
                'severity': 'medium',
                'immediate_actions': [],
                'required_team': [],
                'response_time': 300,
                'interventions': [],
                'protocol': '',
                'assessment': ''
            }
            
            lines = result.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('SEVERITY:'):
                    severity = line.split(':', 1)[1].strip().lower()
                    response_plan['severity'] = severity
                elif line.startswith('IMMEDIATE_ACTIONS:'):
                    current_section = 'immediate_actions'
                elif line.startswith('REQUIRED_TEAM:'):
                    current_section = 'required_team'
                elif line.startswith('RESPONSE_TIME:'):
                    time_str = line.split(':', 1)[1].strip()
                    try:
                        response_plan['response_time'] = int(time_str)
                    except ValueError:
                        pass
                elif line.startswith('INTERVENTIONS:'):
                    current_section = 'interventions'
                elif line.startswith('PROTOCOL:'):
                    protocol = line.split(':', 1)[1].strip()
                    response_plan['protocol'] = protocol
                elif line.startswith('ASSESSMENT:'):
                    assessment = line.split(':', 1)[1].strip()
                    response_plan['assessment'] = assessment
                elif line and current_section and line.startswith('-'):
                    item = line[1:].strip()
                    if current_section in response_plan:
                        response_plan[current_section].append(item)
            
            return response_plan
            
        except Exception as e:
            self.logger("EmergencyAgent", "parse_error", f"Failed to parse emergency response: {str(e)}")
            return {
                'severity': 'medium',
                'immediate_actions': ['Assess patient immediately'],
                'required_team': ['Emergency physician', 'Nurse'],
                'response_time': 300,
                'interventions': ['Basic life support'],
                'protocol': 'Standard emergency protocol',
                'assessment': 'Emergency situation requiring immediate attention'
            }
    
    def _create_emergency_record(self, emergency_data: Dict[str, Any], response_plan: Dict[str, Any], assessment_result: str) -> Optional[Dict[str, Any]]:
        """Create emergency response record in database"""
        try:
            with get_db_session() as session:
                # Map severity string to enum
                severity_map = {
                    'critical': AlertSeverity.CRITICAL,
                    'high': AlertSeverity.HIGH,
                    'medium': AlertSeverity.MEDIUM,
                    'low': AlertSeverity.LOW
                }
                
                severity = severity_map.get(response_plan['severity'], AlertSeverity.MEDIUM)
                
                emergency_response = EmergencyResponse(
                    patient_id=emergency_data['patient_id'],
                    emergency_type=emergency_data.get('emergency_type', 'Unknown'),
                    severity=severity,
                    description=emergency_data.get('description', ''),
                    response_team=response_plan.get('required_team', []),
                    response_time=response_plan.get('response_time', 300),
                    actions_taken=response_plan.get('immediate_actions', []),
                    outcome='In Progress'
                )
                
                session.add(emergency_response)
                session.commit()
                session.refresh(emergency_response)
                
                return {
                    'id': str(emergency_response.id),
                    'severity': response_plan['severity'],
                    'response_time': response_plan['response_time'],
                    'created_at': emergency_response.created_at.isoformat()
                }
                
        except Exception as e:
            self.logger("EmergencyAgent", "database_error", f"Failed to create emergency record: {str(e)}")
            return None
    
    def get_emergency_statistics(self) -> Dict[str, Any]:
        """Get emergency response statistics"""
        try:
            with get_db_session() as session:
                # Get counts by severity
                severity_counts = {}
                for severity in AlertSeverity:
                    count = session.query(EmergencyResponse).filter(
                        EmergencyResponse.severity == severity
                    ).count()
                    severity_counts[severity.value] = count
                
                # Get total emergencies
                total_emergencies = session.query(EmergencyResponse).count()
                
                # Get recent emergencies (last 24 hours)
                from datetime import datetime, timedelta
                yesterday = datetime.utcnow() - timedelta(days=1)
                recent_count = session.query(EmergencyResponse).filter(
                    EmergencyResponse.created_at >= yesterday
                ).count()
                
                # Get average response time
                avg_response_time = session.query(
                    session.query(EmergencyResponse.response_time).scalar()
                ).scalar()
                
                return {
                    'success': True,
                    'statistics': {
                        'total_emergencies': total_emergencies,
                        'recent_emergencies_24h': recent_count,
                        'by_severity': severity_counts,
                        'average_response_time_seconds': avg_response_time or 0
                    }
                }
                
        except Exception as e:
            self.logger("EmergencyAgent", "stats_error", f"Failed to get emergency statistics: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to get emergency statistics: {str(e)}"
            }
    
    def update_emergency_outcome(self, emergency_id: str, outcome: str, resolved: bool = True) -> Dict[str, Any]:
        """Update emergency response outcome"""
        try:
            with get_db_session() as session:
                emergency = session.query(EmergencyResponse).filter(
                    EmergencyResponse.id == emergency_id
                ).first()
                
                if not emergency:
                    return {
                        'success': False,
                        'error': 'Emergency response not found'
                    }
                
                emergency.outcome = outcome
                if resolved:
                    emergency.resolved_at = datetime.utcnow()
                
                session.commit()
                
                self.logger("EmergencyAgent", "outcome_updated", 
                           f"Emergency {emergency_id} outcome updated to: {outcome}")
                
                return {
                    'success': True,
                    'outcome': outcome,
                    'resolved': resolved
                }
                
        except Exception as e:
            self.logger("EmergencyAgent", "update_error", f"Failed to update emergency outcome: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to update emergency outcome: {str(e)}"
            }
