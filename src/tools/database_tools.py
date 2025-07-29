from typing import Dict, List, Any, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import logging
from database.connection import get_db_session

def execute_query(query, params=None):
    """Execute a raw SQL query using SQLAlchemy session and return results as list of dicts."""
    results = []
    with get_db_session() as session:
        result_proxy = session.execute(query, params or ())
        for row in result_proxy:
            results.append(dict(row._mapping))
    return results

class PatientSearchInput(BaseModel):
    """Input for patient search tool"""
    search_criteria: Dict[str, Any] = Field(description="Search criteria for patients")

class VitalSignsInput(BaseModel):
    """Input for recording vital signs"""
    patient_id: int = Field(description="Patient ID")
    vital_signs: Dict[str, Any] = Field(description="Vital signs data")

class MedicalRecordInput(BaseModel):
    """Input for medical record operations"""
    patient_id: int = Field(description="Patient ID")
    record_data: Optional[Dict[str, Any]] = Field(default=None, description="Medical record data")

class PatientSearchTool(BaseTool):
    """Tool for searching patient records in the database"""
    name: str = "patient_search"
    description: str = "Search for patients in the healthcare database using various criteria"
    args_schema: type[BaseModel] = PatientSearchInput
    
    def _run(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search patients based on criteria"""
        try:
            base_query = "SELECT * FROM patients WHERE 1=1"
            params = []
            
            if search_criteria.get('name'):
                base_query += " AND (first_name ILIKE %s OR last_name ILIKE %s)"
                name_pattern = f"%{search_criteria['name']}%"
                params.extend([name_pattern, name_pattern])
            
            if search_criteria.get('phone'):
                base_query += " AND phone LIKE %s"
                params.append(f"%{search_criteria['phone']}%")
            
            if search_criteria.get('email'):
                base_query += " AND email ILIKE %s"
                params.append(f"%{search_criteria['email']}%")
            
            if search_criteria.get('patient_id'):
                base_query += " AND patient_id = %s"
                params.append(search_criteria['patient_id'])
            
            base_query += " ORDER BY last_name, first_name LIMIT 20"
            
            results = execute_query(base_query, params)
            return [dict(patient) for patient in results]
            
        except Exception as e:
            logging.error(f"Patient search failed: {str(e)}")
            return []

class GetPatientRecordTool(BaseTool):
    """Tool for retrieving complete patient medical records"""
    name: str = "get_patient_record"
    description: str = "Retrieve complete medical record for a specific patient"
    args_schema: type[BaseModel] = MedicalRecordInput
    
    def _run(self, patient_id: int, record_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get complete patient record"""
        try:
            # Get basic patient info
            patient_query = "SELECT * FROM patients WHERE patient_id = %s"
            patient_result = execute_query(patient_query, (patient_id,))
            
            if not patient_result:
                return {"error": "Patient not found"}
            
            patient = dict(patient_result[0])
            
            # Get medical records
            records_query = """
            SELECT mr.*, mc.name as condition_name, mc.icd_10_code,
                   d.first_name as doctor_first_name, d.last_name as doctor_last_name
            FROM medical_records mr
            LEFT JOIN medical_conditions mc ON mr.condition_id = mc.condition_id
            LEFT JOIN doctors d ON mr.doctor_id = d.doctor_id
            WHERE mr.patient_id = %s
            ORDER BY mr.visit_date DESC
            """
            medical_records = execute_query(records_query, (patient_id,))
            
            # Get current treatments
            treatments_query = """
            SELECT t.*, m.name as medication_name, m.generic_name,
                   d.first_name as doctor_first_name, d.last_name as doctor_last_name
            FROM treatments t
            LEFT JOIN medications m ON t.medication_id = m.medication_id
            LEFT JOIN doctors d ON t.doctor_id = d.doctor_id
            WHERE t.patient_id = %s AND t.status = 'ACTIVE'
            ORDER BY t.start_date DESC
            """
            treatments = execute_query(treatments_query, (patient_id,))
            
            # Get recent monitoring data
            monitoring_query = """
            SELECT * FROM monitoring_data 
            WHERE patient_id = %s 
            ORDER BY timestamp DESC 
            LIMIT 20
            """
            monitoring_data = execute_query(monitoring_query, (patient_id,))
            
            return {
                'patient_info': patient,
                'medical_records': [dict(record) for record in medical_records],
                'current_treatments': [dict(treatment) for treatment in treatments],
                'recent_monitoring': [dict(data) for data in monitoring_data]
            }
            
        except Exception as e:
            logging.error(f"Failed to retrieve patient record: {str(e)}")
            return {"error": str(e)}

class RecordVitalSignsTool(BaseTool):
    """Tool for recording patient vital signs"""
    name: str = "record_vital_signs"
    description: str = "Record vital signs for a patient in the monitoring system"
    args_schema: type[BaseModel] = VitalSignsInput
    
    def _run(self, patient_id: int, vital_signs: Dict[str, Any]) -> Dict[str, Any]:
        """Record vital signs in database"""
        try:
            results = []
            for measurement_type, value in vital_signs.items():
                if measurement_type in ['heart_rate', 'systolic_bp', 'diastolic_bp', 
                                      'temperature', 'oxygen_saturation', 'respiratory_rate']:
                    
                    query = """
                    INSERT INTO monitoring_data 
                    (patient_id, device_type, measurement_type, value, unit, timestamp)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    RETURNING monitoring_id
                    """
                    
                    unit_map = {
                        'heart_rate': 'bpm',
                        'systolic_bp': 'mmHg',
                        'diastolic_bp': 'mmHg',
                        'temperature': 'F',
                        'oxygen_saturation': '%',
                        'respiratory_rate': 'breaths/min'
                    }
                    
                    params = (
                        patient_id,
                        'Manual Entry',
                        measurement_type,
                        value,
                        unit_map.get(measurement_type, '')
                    )
                    
                    result = execute_query(query, params)
                    if result:
                        results.append({
                            'measurement_type': measurement_type,
                            'value': value,
                            'monitoring_id': result[0]['monitoring_id']
                        })
            
            return {
                'success': True,
                'recorded_measurements': results,
                'patient_id': patient_id
            }
            
        except Exception as e:
            logging.error(f"Failed to record vital signs: {str(e)}")
            return {'success': False, 'error': str(e)}

class GetTriageQueueTool(BaseTool):
    """Tool for getting current triage queue"""
    name: str = "get_triage_queue"
    description: str = "Get list of patients currently in triage queue"
    
    def _run(self) -> List[Dict[str, Any]]:
        """Get waiting patients in triage"""
        try:
            query = """
            SELECT t.*, p.first_name, p.last_name, d.first_name as doctor_first_name, 
                   d.last_name as doctor_last_name
            FROM triage_assessments t
            JOIN patients p ON t.patient_id = p.patient_id
            LEFT JOIN doctors d ON t.assigned_to_doctor = d.doctor_id
            WHERE t.status IN ('WAITING', 'ASSIGNED')
            ORDER BY t.triage_level ASC, t.arrival_time ASC
            """
            
            results = execute_query(query)
            return [dict(patient) for patient in results]
            
        except Exception as e:
            logging.error(f"Failed to get triage queue: {str(e)}")
            return []

class CheckDrugInteractionsTool(BaseTool):
    """Tool for checking drug interactions"""
    name: str = "check_drug_interactions"
    description: str = "Check for potential drug interactions for a patient"
    args_schema: type[BaseModel] = MedicalRecordInput
    
    def _run(self, patient_id: int, record_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check drug interactions for patient"""
        try:
            # Get patient's current medications
            current_meds_query = """
            SELECT m.name, m.generic_name, m.contraindications
            FROM treatments t
            JOIN medications m ON t.medication_id = m.medication_id
            WHERE t.patient_id = %s AND t.status = 'ACTIVE'
            """
            current_meds = execute_query(current_meds_query, (patient_id,))
            
            # Get patient allergies
            allergy_query = """
            SELECT DISTINCT unnest(allergies) as allergy 
            FROM medical_records 
            WHERE patient_id = %s AND allergies IS NOT NULL
            """
            allergies = execute_query(allergy_query, (patient_id,))
            patient_allergies = [allergy['allergy'] for allergy in allergies]
            
            # Simple interaction checking (in real system, would use comprehensive drug database)
            interactions = []
            contraindications = []
            
            for med in current_meds:
                # Check allergies
                med_name_lower = med['name'].lower()
                for allergy in patient_allergies:
                    if allergy.lower() in med_name_lower:
                        contraindications.append(f"Patient allergic to {allergy} - conflicts with {med['name']}")
                
                # Check contraindications
                if med['contraindications']:
                    contraindications.append(f"{med['name']}: {med['contraindications']}")
            
            return {
                'patient_id': patient_id,
                'current_medications': [dict(med) for med in current_meds],
                'allergies': patient_allergies,
                'interactions': interactions,
                'contraindications': contraindications,
                'safe_to_prescribe': len(interactions) == 0 and len(contraindications) == 0
            }
            
        except Exception as e:
            logging.error(f"Drug interaction check failed: {str(e)}")
            return {'error': str(e)}        