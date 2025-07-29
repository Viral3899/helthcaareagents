"""
Triage Agent

This agent handles patient triage assessment and assigns appropriate triage levels
based on symptoms, vital signs, and medical history.
"""

from typing import Dict, List, Any, Optional
from langchain_core.tools import BaseTool
from agents.base_agent import BaseHealthcareAgent
from utils.logger import log_agent_event
from database.models import TriageLevel, TriageAssessment
from database.connection import get_db_session

class TriageAgent(BaseHealthcareAgent):
    """AI agent for patient triage assessment"""
    
    def __init__(self, tools: Dict[str, Any]):
        system_prompt = """You are a Triage Agent responsible for assessing patients and assigning appropriate triage levels.

Your responsibilities include:
1. Analyzing patient symptoms and vital signs
2. Determining triage urgency level (1-5)
3. Identifying potential emergencies
4. Recommending immediate actions
5. Estimating wait times

Triage Levels:
- Level 1 (Immediate): Life-threatening conditions requiring immediate attention
- Level 2 (Emergent): Serious conditions requiring attention within 15 minutes
- Level 3 (Urgent): Conditions requiring attention within 30 minutes
- Level 4 (Less Urgent): Conditions requiring attention within 60 minutes
- Level 5 (Non-urgent): Conditions requiring attention within 120 minutes

Always prioritize patient safety and err on the side of caution when in doubt."""

        triage_tools = [
            tools.get('database', None),
            tools.get('medical', None),
            tools.get('validation', None)
        ]
        triage_tools = [tool for tool in triage_tools if tool is not None]
        super().__init__("TriageAgent", system_prompt, triage_tools)
        self.logger = log_agent_event

    def assess_patient(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            assessment_input = self._prepare_assessment_input(patient_data)
            result = self.execute(assessment_input)
            if result['success']:
                triage_level = self._parse_triage_level(result['result'])
                assessment_record = self._create_assessment_record(patient_data, triage_level, result['result'])
                self.logger("TriageAgent", "assessment_completed", 
                           f"Patient {patient_data.get('patient_id', 'unknown')} assigned triage level {triage_level}")
                return {
                    'success': True,
                    'triage_level': triage_level,
                    'assessment': result['result'],
                    'assessment_id': assessment_record.get('id') if assessment_record else None,
                    'wait_time_estimate': self._get_wait_time_estimate(triage_level)
                }
            else:
                self.logger("TriageAgent", "assessment_failed", 
                           f"Triage assessment failed: {result.get('error', 'Unknown error')}")
                return result
        except Exception as e:
            self.logger("TriageAgent", "assessment_error", f"Triage assessment error: {str(e)}")
            return {
                'success': False,
                'error': f"Triage assessment failed: {str(e)}"
            }
    
    def _prepare_assessment_input(self, patient_data: Dict[str, Any]) -> str:
        """Prepare input for triage assessment"""
        input_parts = []
        
        # Patient information
        if 'patient_id' in patient_data:
            input_parts.append(f"Patient ID: {patient_data['patient_id']}")
        
        if 'age' in patient_data:
            input_parts.append(f"Age: {patient_data['age']}")
        
        if 'gender' in patient_data:
            input_parts.append(f"Gender: {patient_data['gender']}")
        
        # Chief complaint
        if 'chief_complaint' in patient_data:
            input_parts.append(f"Chief Complaint: {patient_data['chief_complaint']}")
        
        # Symptoms
        if 'symptoms' in patient_data:
            symptoms = patient_data['symptoms']
            if isinstance(symptoms, list):
                symptoms_str = ", ".join(symptoms)
            else:
                symptoms_str = str(symptoms)
            input_parts.append(f"Symptoms: {symptoms_str}")
        
        # Vital signs
        if 'vital_signs' in patient_data:
            vitals = patient_data['vital_signs']
            vitals_str = []
            for vital, value in vitals.items():
                if value is not None:
                    vitals_str.append(f"{vital}: {value}")
            if vitals_str:
                input_parts.append(f"Vital Signs: {', '.join(vitals_str)}")
        
        # Medical history
        if 'medical_history' in patient_data:
            history = patient_data['medical_history']
            if isinstance(history, list):
                history_str = ", ".join(history)
            else:
                history_str = str(history)
            input_parts.append(f"Medical History: {history_str}")
        
        # Allergies
        if 'allergies' in patient_data:
            allergies = patient_data['allergies']
            if isinstance(allergies, list):
                allergies_str = ", ".join(allergies)
            else:
                allergies_str = str(allergies)
            input_parts.append(f"Allergies: {allergies_str}")
        
        # Current medications
        if 'medications' in patient_data:
            meds = patient_data['medications']
            if isinstance(meds, list):
                meds_str = ", ".join(meds)
            else:
                meds_str = str(meds)
            input_parts.append(f"Current Medications: {meds_str}")
        
        # Mechanism of injury (if applicable)
        if 'mechanism_of_injury' in patient_data:
            input_parts.append(f"Mechanism of Injury: {patient_data['mechanism_of_injury']}")
        
        # Pain assessment
        if 'pain_level' in patient_data:
            input_parts.append(f"Pain Level (0-10): {patient_data['pain_level']}")
        
        # Additional context
        if 'additional_context' in patient_data:
            input_parts.append(f"Additional Context: {patient_data['additional_context']}")
        
        # Create assessment prompt
        assessment_prompt = f"""
Please assess this patient and provide a triage recommendation:

{chr(10).join(input_parts)}

Based on the above information, please:
1. Assign a triage level (1-5) with justification
2. Identify any immediate concerns or red flags
3. Recommend any immediate actions needed
4. Provide a brief assessment summary

Format your response as:
TRIAGE_LEVEL: [1-5]
JUSTIFICATION: [explanation]
IMMEDIATE_CONCERNS: [list any red flags]
RECOMMENDED_ACTIONS: [immediate actions needed]
ASSESSMENT_SUMMARY: [brief summary]
"""
        
        return assessment_prompt
    
    def _parse_triage_level(self, result: str) -> int:
        """Parse triage level from agent result"""
        try:
            # Look for triage level in the result
            lines = result.split('\n')
            for line in lines:
                if line.strip().startswith('TRIAGE_LEVEL:'):
                    level_str = line.split(':')[1].strip()
                    # Extract number from the level
                    import re
                    level_match = re.search(r'\d+', level_str)
                    if level_match:
                        level = int(level_match.group())
                        return max(1, min(5, level))  # Ensure level is between 1-5
            
            # Default to level 3 if parsing fails
            return 3
            
        except Exception as e:
            self.logger("TriageAgent", "parse_error", f"Failed to parse triage level: {str(e)}")
            return 3
    
    def _create_assessment_record(self, patient_data: Dict[str, Any], triage_level: int, assessment_result: str) -> Optional[Dict[str, Any]]:
        """Create triage assessment record in database"""
        try:
            with get_db_session() as session:
                assessment = TriageAssessment(
                    patient_id=patient_data['patient_id'],
                    triage_level=TriageLevel(triage_level),
                    chief_complaint=patient_data.get('chief_complaint', ''),
                    symptoms=patient_data.get('symptoms', []),
                    assessment_notes=assessment_result,
                    wait_time_estimate=self._get_wait_time_estimate(triage_level)
                )
                
                session.add(assessment)
                session.commit()
                session.refresh(assessment)
                
                return {
                    'id': str(assessment.id),
                    'triage_level': triage_level,
                    'created_at': assessment.created_at.isoformat()
                }
                
        except Exception as e:
            self.logger("TriageAgent", "database_error", f"Failed to create assessment record: {str(e)}")
            return None
    
    def _get_wait_time_estimate(self, triage_level: int) -> int:
        """Get estimated wait time based on triage level"""
        wait_times = {
            1: 0,      # Immediate
            2: 15,     # Emergent
            3: 30,     # Urgent
            4: 60,     # Less Urgent
            5: 120     # Non-urgent
        }
        return wait_times.get(triage_level, 30)
    
    def get_triage_statistics(self) -> Dict[str, Any]:
        """Get triage statistics"""
        try:
            with get_db_session() as session:
                # Get counts by triage level
                level_counts = {}
                for level in range(1, 6):
                    count = session.query(TriageAssessment).filter(
                        TriageAssessment.triage_level == TriageLevel(level)
                    ).count()
                    level_counts[f"level_{level}"] = count
                
                # Get total assessments
                total_assessments = session.query(TriageAssessment).count()
                
                # Get recent assessments (last 24 hours)
                from datetime import datetime, timedelta
                yesterday = datetime.utcnow() - timedelta(days=1)
                recent_count = session.query(TriageAssessment).filter(
                    TriageAssessment.created_at >= yesterday
                ).count()
                
                return {
                    'success': True,
                    'statistics': {
                        'total_assessments': total_assessments,
                        'recent_assessments_24h': recent_count,
                        'by_level': level_counts
                    }
                }
                
        except Exception as e:
            self.logger("TriageAgent", "stats_error", f"Failed to get triage statistics: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to get triage statistics: {str(e)}"
            }