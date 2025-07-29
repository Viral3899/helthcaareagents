from typing import Dict, List, Any, Optional
from langgraph.graph import Graph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage
from agents.triage_agent import TriageAgent
from agents.medical_records_agent import MedicalRecordsAgent
from agents.monitoring_agent import MonitoringAgent
from agents.scheduling_agent import SchedulingAgent
import logging

class PatientAdmissionWorkflow:
    """LangGraph workflow for patient admission process"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize agents
        self.triage_agent = TriageAgent()
        self.records_agent = MedicalRecordsAgent()
        self.monitoring_agent = MonitoringAgent()
        self.scheduling_agent = SchedulingAgent()
        
        # Build workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> Graph:
        """Build the patient admission workflow graph"""
        
        def patient_registration(state):
            """Step 1: Register patient and create/update medical record"""
            try:
                patient_data = state.get('patient_data', {})
                self.logger.info(f"Starting patient registration for: {patient_data.get('first_name')} {patient_data.get('last_name')}")
                
                # Check if patient exists
                search_result = self.records_agent.search_patients_with_ai({
                    'name': f"{patient_data.get('first_name')} {patient_data.get('last_name')}",
                    'phone': patient_data.get('phone'),
                    'date_of_birth': patient_data.get('date_of_birth')
                })
                
                if search_result.get('success') and search_result.get('result'):
                    # Existing patient found
                    # Extract patient_id from search results (simplified)
                    patient_id = patient_data.get('patient_id') or 1  # Would extract from search results
                    state['patient_id'] = patient_id
                    state['registration_status'] = 'existing_patient'
                else:
                    # Create new patient record
                    patient_id = self.records_agent.create_patient_record(patient_data)
                    if patient_id:
                        state['patient_id'] = patient_id
                        state['registration_status'] = 'new_patient'
                    else:
                        state['registration_status'] = 'failed'
                        state['error'] = 'Failed to create patient record'
                
                return state
                
            except Exception as e:
                self.logger.error(f"Patient registration failed: {str(e)}")
                state['registration_status'] = 'failed'
                state['error'] = str(e)
                return state
        
        def triage_assessment(state):
            """Step 2: Perform triage assessment"""
            try:
                if state.get('registration_status') == 'failed':
                    return state
                
                patient_id = state['patient_id']
                triage_data = state.get('triage_data', {})
                triage_data['patient_id'] = patient_id
                
                self.logger.info(f"Performing triage assessment for patient {patient_id}")
                
                # Perform AI-powered triage assessment
                assessment_result = self.triage_agent.assess_patient(triage_data)
                
                if assessment_result.get('success'):
                    state['triage_result'] = assessment_result
                    state['triage_status'] = 'completed'
                    
                    # Extract triage level for workflow routing
                    triage_level = self._extract_triage_level_from_result(assessment_result)
                    state['triage_level'] = triage_level
                else:
                    state['triage_status'] = 'failed'
                    state['error'] = assessment_result.get('error', 'Triage assessment failed')
                
                return state
                
            except Exception as e:
                self.logger.error(f"Triage assessment failed: {str(e)}")
                state['triage_status'] = 'failed'
                state['error'] = str(e)
                return state
        
        def emergency_pathway(state):
            """Step 3a: Emergency pathway for high-priority patients"""
            try:
                patient_id = state['patient_id']
                self.logger.info(f"Activating emergency pathway for patient {patient_id}")
                
                # Immediate monitoring setup
                monitoring_result = self.monitoring_agent.setup_emergency_monitoring(patient_id)
                state['monitoring_setup'] = monitoring_result
                
                # Emergency scheduling
                emergency_appointment = {
                    'patient_id': patient_id,
                    'appointment_type': 'emergency',
                    'priority': 'immediate',
                    'department': 'Emergency Medicine'
                }
                
                scheduling_result = self.scheduling_agent.schedule_emergency_appointment(emergency_appointment)
                state['appointment_result'] = scheduling_result
                state['pathway'] = 'emergency'
                
                return state
                
            except Exception as e:
                self.logger.error(f"Emergency pathway failed: {str(e)}")
                state['error'] = str(e)
                return state
        
        def standard_pathway(state):
            """Step 3b: Standard pathway for routine patients"""
            try:
                patient_id = state['patient_id']
                self.logger.info(f"Processing standard pathway for patient {patient_id}")
                
                # Standard monitoring setup
                monitoring_result = self.monitoring_agent.setup_standard_monitoring(patient_id)
                state['monitoring_setup'] = monitoring_result
                
                # Regular appointment scheduling
                appointment_data = state.get('appointment_data', {})
                appointment_data['patient_id'] = patient_id
                
                scheduling_result = self.scheduling_agent.schedule_appointment(appointment_data)
                state['appointment_result'] = scheduling_result
                state['pathway'] = 'standard'
                
                return state
                
            except Exception as e:
                self.logger.error(f"Standard pathway failed: {str(e)}")
                state['error'] = str(e)
                return state
        
        def finalize_admission(state):
            """Step 4: Finalize admission process"""
            try:
                patient_id = state['patient_id']
                self.logger.info(f"Finalizing admission for patient {patient_id}")
                
                # Generate admission summary
                admission_summary = {
                    'patient_id': patient_id,
                    'registration_status': state.get('registration_status'),
                    'triage_level': state.get('triage_level'),
                    'pathway': state.get('pathway'),
                    'appointment_scheduled': state.get('appointment_result', {}).get('success', False),
                    'monitoring_active': state.get('monitoring_setup', {}).get('success', False),
                    'admission_time': state.get('admission_time'),
                    'next_steps': self._generate_next_steps(state)
                }
                
                state['admission_summary'] = admission_summary
                state['admission_status'] = 'completed'
                
                self.logger.info(f"Admission completed for patient {patient_id}")
                return state
                
            except Exception as e:
                self.logger.error(f"Admission finalization failed: {str(e)}")
                state['admission_status'] = 'failed'
                state['error'] = str(e)
                return state
        
        def route_after_triage(state):
            """Route patient based on triage level"""
            triage_level = state.get('triage_level', 5)
            
            if triage_level <= 2:  # Emergency/High priority
                return "emergency_pathway"
            else:  # Standard pathway
                return "standard_pathway"
        
        # Build the workflow graph
        workflow = Graph()
        
        # Add nodes
        workflow.add_node("patient_registration", patient_registration)
        workflow.add_node("triage_assessment", triage_assessment)
        workflow.add_node("emergency_pathway", emergency_pathway)
        workflow.add_node("standard_pathway", standard_pathway)
        workflow.add_node("finalize_admission", finalize_admission)
        
        # Add edges
        workflow.add_edge("patient_registration", "triage_assessment")
        workflow.add_conditional_edges(
            "triage_assessment",
            route_after_triage,
            {
                "emergency_pathway": "emergency_pathway",
                "standard_pathway": "standard_pathway"
            }
        )
        workflow.add_edge("emergency_pathway", "finalize_admission")
        workflow.add_edge("standard_pathway", "finalize_admission")
        workflow.add_edge("finalize_admission", END)
        
        # Set entry point
        workflow.set_entry_point("patient_registration")
        
        return workflow.compile()
    
    def _extract_triage_level_from_result(self, assessment_result: Dict[str, Any]) -> int:
        """Extract triage level from assessment result"""
        try:
            # This would parse the AI result to extract triage level
            result_text = str(assessment_result.get('ai_assessment', {}))
            
            if 'level 1' in result_text.lower() or 'immediate' in result_text.lower():
                return 1
            elif 'level 2' in result_text.lower() or 'emergent' in result_text.lower():
                return 2
            elif 'level 3' in result_text.lower() or 'urgent' in result_text.lower():
                return 3
            elif 'level 4' in result_text.lower():
                return 4
            else:
                return 5
        except Exception:
            return 3  # Default to urgent
    
    def _generate_next_steps(self, state: Dict[str, Any]) -> List[str]:
        """Generate next steps based on admission state"""
        next_steps = []
        
        pathway = state.get('pathway')
        triage_level = state.get('triage_level', 5)
        
        if pathway == 'emergency':
            next_steps.extend([
                "Immediate physician evaluation",
                "Continuous vital signs monitoring",
                "Prepare for potential interventions"
            ])
        else:
            next_steps.extend([
                "Proceed to scheduled appointment",
                "Complete intake documentation",
                "Begin routine monitoring"
            ])
        
        if triage_level <= 2:
            next_steps.append("High priority - expedite all processes")
        
        return next_steps
    
    def execute_admission(self, admission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete patient admission workflow"""
        try:
            self.logger.info("Starting patient admission workflow")
            
            # Initialize workflow state
            initial_state = {
                'patient_data': admission_data.get('patient_data', {}),
                'triage_data': admission_data.get('triage_data', {}),
                'appointment_data': admission_data.get('appointment_data', {}),
                'admission_time': admission_data.get('admission_time')
            }
            
            # Execute workflow
            final_state = self.workflow.invoke(initial_state)
            
            self.logger.info("Patient admission workflow completed")
            return {
                'success': True,
                'workflow_result': final_state,
                'admission_summary': final_state.get('admission_summary')
            }
            
        except Exception as e:
            self.logger.error(f"Patient admission workflow failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

