"""
Treatment Agent

This agent handles treatment planning, medication management, care coordination,
and treatment outcome monitoring for patients.
"""

from typing import Dict, List, Any, Optional
from langchain_core.tools import BaseTool
from agents.base_agent import BaseHealthcareAgent
from utils.logger import log_agent_event
from database.models import Treatment, MedicalRecord, Alert, AlertSeverity
from database.connection import get_db_session
from datetime import datetime, timedelta
import json

class TreatmentAgent(BaseHealthcareAgent):
    """AI agent for treatment planning and management"""
    def __init__(self, tools: Dict[str, Any]):
        system_prompt = """You are a Treatment Agent responsible for creating, managing, and optimizing patient treatment plans.

Your responsibilities include:
1. Analyzing patient data and medical history
2. Recommending evidence-based treatments
3. Coordinating with other agents and medical staff
4. Monitoring treatment progress and outcomes
5. Adjusting treatment plans as needed

Always prioritize patient well-being and adhere to best medical practices."""
        treatment_tools = [
            tools.get('database', None),
            tools.get('medical', None),
            tools.get('notification', None),
            tools.get('validation', None)
        ]
        treatment_tools = [tool for tool in treatment_tools if tool is not None]
        super().__init__("TreatmentAgent", system_prompt, treatment_tools)
        self.logger = log_agent_event
    
    def create_treatment_plan(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive treatment plan for a patient"""
        try:
            # Prepare treatment planning input
            planning_input = self._prepare_treatment_input(patient_data)
            
            # Execute treatment planning
            result = self.execute(planning_input)
            
            if result['success']:
                # Parse treatment plan from result
                treatment_plan = self._parse_treatment_plan(result['result'])
                
                # Create treatment record
                treatment_record = self._create_treatment_record(patient_data, treatment_plan, result['result'])
                
                # Create medical record for treatment plan
                medical_record = self._create_medical_record(patient_data, treatment_plan, result['result'])
                
                # Log treatment planning
                self.logger("TreatmentAgent", "treatment_plan_created", 
                           f"Treatment plan created for patient {patient_data.get('patient_id', 'unknown')}")
                
                return {
                    'success': True,
                    'treatment_plan': treatment_plan,
                    'treatment_id': treatment_record.get('id') if treatment_record else None,
                    'medical_record_id': medical_record.get('id') if medical_record else None,
                    'assessment': result['result']
                }
            else:
                self.logger("TreatmentAgent", "treatment_planning_failed", 
                           f"Treatment planning failed: {result.get('error', 'Unknown error')}")
                return result
                
        except Exception as e:
            self.logger("TreatmentAgent", "treatment_planning_error", f"Treatment planning error: {str(e)}")
            return {
                'success': False,
                'error': f"Treatment planning failed: {str(e)}"
            }
    
    def _prepare_treatment_input(self, patient_data: Dict[str, Any]) -> str:
        """Prepare input for treatment planning"""
        input_parts = []
        
        # Patient information
        if 'patient_id' in patient_data:
            input_parts.append(f"Patient ID: {patient_data['patient_id']}")
        
        if 'age' in patient_data:
            input_parts.append(f"Age: {patient_data['age']}")
        
        if 'gender' in patient_data:
            input_parts.append(f"Gender: {patient_data['gender']}")
        
        # Diagnoses
        if 'diagnoses' in patient_data:
            diagnoses = patient_data['diagnoses']
            if isinstance(diagnoses, list):
                diagnoses_str = ", ".join(diagnoses)
            else:
                diagnoses_str = str(diagnoses)
            input_parts.append(f"Diagnoses: {diagnoses_str}")
        
        # Medical history
        if 'medical_history' in patient_data:
            history = patient_data['medical_history']
            if isinstance(history, list):
                history_str = ", ".join(history)
            else:
                history_str = str(history)
            input_parts.append(f"Medical History: {history_str}")
        
        # Current medications
        if 'current_medications' in patient_data:
            meds = patient_data['current_medications']
            if isinstance(meds, list):
                meds_str = ", ".join(meds)
            else:
                meds_str = str(meds)
            input_parts.append(f"Current Medications: {meds_str}")
        
        # Allergies
        if 'allergies' in patient_data:
            allergies = patient_data['allergies']
            if isinstance(allergies, list):
                allergies_str = ", ".join(allergies)
            else:
                allergies_str = str(allergies)
            input_parts.append(f"Allergies: {allergies_str}")
        
        # Vital signs
        if 'vital_signs' in patient_data:
            vitals = patient_data['vital_signs']
            vitals_str = []
            for vital, value in vitals.items():
                if value is not None:
                    vitals_str.append(f"{vital}: {value}")
            if vitals_str:
                input_parts.append(f"Current Vital Signs: {', '.join(vitals_str)}")
        
        # Lab results
        if 'lab_results' in patient_data:
            labs = patient_data['lab_results']
            if isinstance(labs, dict):
                labs_str = json.dumps(labs)
                input_parts.append(f"Lab Results: {labs_str}")
        
        # Treatment goals
        if 'treatment_goals' in patient_data:
            goals = patient_data['treatment_goals']
            if isinstance(goals, list):
                goals_str = ", ".join(goals)
            else:
                goals_str = str(goals)
            input_parts.append(f"Treatment Goals: {goals_str}")
        
        # Additional context
        if 'additional_context' in patient_data:
            input_parts.append(f"Additional Context: {patient_data['additional_context']}")
        
        # Create treatment planning prompt
        treatment_prompt = f"""
Please create a comprehensive treatment plan for this patient:

{chr(10).join(input_parts)}

Based on the above patient information, please develop a treatment plan that includes:
1. Recommended medications with dosages and schedules
2. Non-pharmacological interventions
3. Monitoring requirements and frequency
4. Expected outcomes and timelines
5. Potential side effects and management
6. Follow-up schedule and criteria
7. Patient education and self-care instructions

Format your response as:
TREATMENT_TYPE: [primary treatment category]
MEDICATIONS: [list of medications with dosages and schedules]
INTERVENTIONS: [non-pharmacological treatments]
MONITORING: [required monitoring and frequency]
TIMELINE: [expected treatment duration and milestones]
SIDE_EFFECTS: [potential side effects and management]
FOLLOW_UP: [follow-up schedule and criteria]
EDUCATION: [patient education topics]
ASSESSMENT: [brief treatment plan summary]
"""
        
        return treatment_prompt
    
    def _parse_treatment_plan(self, result: str) -> Dict[str, Any]:
        """Parse treatment plan from agent result"""
        try:
            treatment_plan = {
                'treatment_type': '',
                'medications': [],
                'interventions': [],
                'monitoring': [],
                'timeline': '',
                'side_effects': [],
                'follow_up': [],
                'education': [],
                'assessment': ''
            }
            
            lines = result.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('TREATMENT_TYPE:'):
                    treatment_type = line.split(':', 1)[1].strip()
                    treatment_plan['treatment_type'] = treatment_type
                elif line.startswith('MEDICATIONS:'):
                    current_section = 'medications'
                elif line.startswith('INTERVENTIONS:'):
                    current_section = 'interventions'
                elif line.startswith('MONITORING:'):
                    current_section = 'monitoring'
                elif line.startswith('TIMELINE:'):
                    timeline = line.split(':', 1)[1].strip()
                    treatment_plan['timeline'] = timeline
                elif line.startswith('SIDE_EFFECTS:'):
                    current_section = 'side_effects'
                elif line.startswith('FOLLOW_UP:'):
                    current_section = 'follow_up'
                elif line.startswith('EDUCATION:'):
                    current_section = 'education'
                elif line.startswith('ASSESSMENT:'):
                    assessment = line.split(':', 1)[1].strip()
                    treatment_plan['assessment'] = assessment
                elif line and current_section and line.startswith('-'):
                    item = line[1:].strip()
                    if current_section in treatment_plan:
                        treatment_plan[current_section].append(item)
            
            return treatment_plan
            
        except Exception as e:
            self.logger("TreatmentAgent", "parse_error", f"Failed to parse treatment plan: {str(e)}")
            return {
                'treatment_type': 'General Treatment',
                'medications': [],
                'interventions': [],
                'monitoring': ['Regular vital signs monitoring'],
                'timeline': 'As prescribed by physician',
                'side_effects': [],
                'follow_up': ['Regular follow-up appointments'],
                'education': ['General health education'],
                'assessment': 'Treatment plan created successfully'
            }
    
    def _create_treatment_record(self, patient_data: Dict[str, Any], treatment_plan: Dict[str, Any], assessment_result: str) -> Optional[Dict[str, Any]]:
        """Create treatment record in database"""
        try:
            with get_db_session() as session:
                treatment = Treatment(
                    patient_id=patient_data['patient_id'],
                    treatment_type=treatment_plan['treatment_type'],
                    diagnosis=patient_data.get('diagnoses', ''),
                    treatment_plan=assessment_result,
                    medications=treatment_plan['medications'],
                    procedures=treatment_plan['interventions'],
                    start_date=datetime.utcnow(),
                    status='active',
                    doctor_id=patient_data.get('doctor_id', ''),
                    notes=treatment_plan['assessment']
                )
                
                session.add(treatment)
                session.commit()
                session.refresh(treatment)
                
                return {
                    'id': str(treatment.id),
                    'treatment_type': treatment.treatment_type,
                    'status': treatment.status,
                    'created_at': treatment.created_at.isoformat()
                }
                
        except Exception as e:
            self.logger("TreatmentAgent", "database_error", f"Failed to create treatment record: {str(e)}")
            return None
    
    def _create_medical_record(self, patient_data: Dict[str, Any], treatment_plan: Dict[str, Any], assessment_result: str) -> Optional[Dict[str, Any]]:
        """Create medical record for treatment plan"""
        try:
            with get_db_session() as session:
                record = MedicalRecord(
                    patient_id=patient_data['patient_id'],
                    record_type='treatment_plan',
                    title=f"Treatment Plan: {treatment_plan['treatment_type']}",
                    content=assessment_result,
                    doctor_id=patient_data.get('doctor_id', ''),
                    department=patient_data.get('department', ''),
                    medications=treatment_plan['medications'],
                    procedures=treatment_plan['interventions']
                )
                
                session.add(record)
                session.commit()
                session.refresh(record)
                
                return {
                    'id': str(record.id),
                    'record_type': record.record_type,
                    'title': record.title,
                    'created_at': record.created_at.isoformat()
                }
                
        except Exception as e:
            self.logger("TreatmentAgent", "medical_record_error", f"Failed to create medical record: {str(e)}")
            return None
    
    def update_treatment_plan(self, treatment_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing treatment plan"""
        try:
            with get_db_session() as session:
                treatment = session.query(Treatment).filter(Treatment.id == treatment_id).first()
                
                if not treatment:
                    return {
                        'success': False,
                        'error': 'Treatment not found'
                    }
                
                # Update treatment fields
                for field, value in updates.items():
                    if hasattr(treatment, field):
                        setattr(treatment, field, value)
                
                treatment.updated_at = datetime.utcnow()
                session.commit()
                
                self.logger("TreatmentAgent", "treatment_updated", 
                           f"Treatment {treatment_id} updated successfully")
                
                return {
                    'success': True,
                    'treatment_id': treatment_id,
                    'updated_at': treatment.updated_at.isoformat()
                }
                
        except Exception as e:
            self.logger("TreatmentAgent", "update_error", f"Failed to update treatment: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to update treatment: {str(e)}"
            }
    
    def get_treatment_statistics(self, patient_id: Optional[str] = None) -> Dict[str, Any]:
        """Get treatment statistics"""
        try:
            with get_db_session() as session:
                # Base query
                treatment_query = session.query(Treatment)
                
                if patient_id:
                    treatment_query = treatment_query.filter(Treatment.patient_id == patient_id)
                
                # Get treatment statistics
                total_treatments = treatment_query.count()
                active_treatments = treatment_query.filter(Treatment.status == 'active').count()
                completed_treatments = treatment_query.filter(Treatment.status == 'completed').count()
                
                # Get treatments by type
                treatment_types = session.query(Treatment.treatment_type).distinct().all()
                type_counts = {}
                for treatment_type in treatment_types:
                    count = treatment_query.filter(Treatment.treatment_type == treatment_type[0]).count()
                    type_counts[treatment_type[0]] = count
                
                # Get recent treatments (last 30 days)
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                recent_treatments = treatment_query.filter(
                    Treatment.created_at >= thirty_days_ago
                ).count()
                
                return {
                    'success': True,
                    'statistics': {
                        'total_treatments': total_treatments,
                        'active_treatments': active_treatments,
                        'completed_treatments': completed_treatments,
                        'recent_treatments_30d': recent_treatments,
                        'by_type': type_counts
                    }
                }
                
        except Exception as e:
            self.logger("TreatmentAgent", "stats_error", f"Failed to get treatment statistics: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to get treatment statistics: {str(e)}"
            }
    
    def check_medication_interactions(self, medications: List[str]) -> Dict[str, Any]:
        """Check for potential medication interactions"""
        try:
            # Prepare interaction check input
            interaction_input = f"""
Please check for potential interactions between these medications:

Medications: {', '.join(medications)}

Please identify:
1. Any known drug-drug interactions
2. Potential side effects when taken together
3. Recommendations for monitoring
4. Alternative medication options if needed

Format your response as:
INTERACTIONS: [list any drug interactions found]
SIDE_EFFECTS: [potential side effects]
MONITORING: [recommended monitoring]
ALTERNATIVES: [alternative options if needed]
SAFETY: [overall safety assessment]
"""
            
            # Execute interaction check
            result = self.execute(interaction_input)
            
            if result['success']:
                # Parse interaction results
                interaction_result = self._parse_interaction_result(result['result'])
                
                return {
                    'success': True,
                    'interactions': interaction_result,
                    'assessment': result['result']
                }
            else:
                return result
                
        except Exception as e:
            self.logger("TreatmentAgent", "interaction_error", f"Medication interaction check failed: {str(e)}")
            return {
                'success': False,
                'error': f"Medication interaction check failed: {str(e)}"
            }
    
    def _parse_interaction_result(self, result: str) -> Dict[str, Any]:
        """Parse medication interaction results"""
        try:
            interaction_data = {
                'interactions': [],
                'side_effects': [],
                'monitoring': [],
                'alternatives': [],
                'safety': 'unknown'
            }
            
            lines = result.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('INTERACTIONS:'):
                    current_section = 'interactions'
                elif line.startswith('SIDE_EFFECTS:'):
                    current_section = 'side_effects'
                elif line.startswith('MONITORING:'):
                    current_section = 'monitoring'
                elif line.startswith('ALTERNATIVES:'):
                    current_section = 'alternatives'
                elif line.startswith('SAFETY:'):
                    safety = line.split(':', 1)[1].strip()
                    interaction_data['safety'] = safety
                elif line and current_section and line.startswith('-'):
                    item = line[1:].strip()
                    if current_section in interaction_data:
                        interaction_data[current_section].append(item)
            
            return interaction_data
            
        except Exception as e:
            self.logger("TreatmentAgent", "parse_interaction_error", f"Failed to parse interaction result: {str(e)}")
            return {
                'interactions': [],
                'side_effects': [],
                'monitoring': ['Regular monitoring recommended'],
                'alternatives': [],
                'safety': 'unknown'
            }
