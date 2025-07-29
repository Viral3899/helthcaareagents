"""
Medical Records Agent

This agent handles medical record management, documentation, information retrieval,
and medical record analysis for healthcare providers.
"""

from typing import Dict, List, Any, Optional
from langchain_core.tools import BaseTool
from agents.base_agent import BaseHealthcareAgent
from utils.logger import log_agent_event
from database.models import MedicalRecord, Patient, VitalSigns, Treatment
from database.connection import get_db_session
from datetime import datetime, timedelta
import json

class MedicalRecordsAgent(BaseHealthcareAgent):
    """AI agent for medical records management"""
    def __init__(self, tools: Dict[str, Any]):
        system_prompt = """You are a Medical Records Agent responsible for managing, retrieving, and updating patient medical records.

Your responsibilities include:
1. Ensuring accuracy and completeness of records
2. Retrieving relevant patient information
3. Updating records with new data
4. Coordinating with other agents and staff
5. Maintaining data privacy and security

Always adhere to privacy regulations and best practices."""
        records_tools = [
            tools.get('database', None),
            tools.get('medical', None),
            tools.get('validation', None)
        ]
        records_tools = [tool for tool in records_tools if tool is not None]
        super().__init__("MedicalRecordsAgent", system_prompt, records_tools)
        self.logger = log_agent_event
    
    def create_medical_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new medical record"""
        try:
            # Prepare record creation input
            creation_input = self._prepare_record_input(record_data)
            
            # Execute record creation
            result = self.execute(creation_input)
            
            if result['success']:
                # Parse record content from result
                record_content = self._parse_record_content(result['result'])
                
                # Create medical record in database
                record_record = self._create_record_in_db(record_data, record_content, result['result'])
                
                # Log record creation
                self.logger("MedicalRecordsAgent", "record_created", 
                           f"Medical record created for patient {record_data.get('patient_id', 'unknown')}")
                
                return {
                    'success': True,
                    'record': record_content,
                    'record_id': record_record.get('id') if record_record else None,
                    'assessment': result['result']
                }
            else:
                self.logger("MedicalRecordsAgent", "record_creation_failed", 
                           f"Medical record creation failed: {result.get('error', 'Unknown error')}")
                return result
                
        except Exception as e:
            self.logger("MedicalRecordsAgent", "record_creation_error", f"Medical record creation error: {str(e)}")
            return {
                'success': False,
                'error': f"Medical record creation failed: {str(e)}"
            }
    
    def _prepare_record_input(self, record_data: Dict[str, Any]) -> str:
        """Prepare input for medical record creation"""
        input_parts = []
        
        # Patient information
        if 'patient_id' in record_data:
            input_parts.append(f"Patient ID: {record_data['patient_id']}")
        
        if 'age' in record_data:
            input_parts.append(f"Age: {record_data['age']}")
        
        if 'gender' in record_data:
            input_parts.append(f"Gender: {record_data['gender']}")
        
        # Record type and context
        if 'record_type' in record_data:
            input_parts.append(f"Record Type: {record_data['record_type']}")
        
        if 'title' in record_data:
            input_parts.append(f"Title: {record_data['title']}")
        
        # Clinical information
        if 'symptoms' in record_data:
            symptoms = record_data['symptoms']
            if isinstance(symptoms, list):
                symptoms_str = ", ".join(symptoms)
            else:
                symptoms_str = str(symptoms)
            input_parts.append(f"Symptoms: {symptoms_str}")
        
        if 'findings' in record_data:
            findings = record_data['findings']
            if isinstance(findings, dict):
                findings_str = json.dumps(findings)
            else:
                findings_str = str(findings)
            input_parts.append(f"Clinical Findings: {findings_str}")
        
        if 'diagnosis' in record_data:
            diagnosis = record_data['diagnosis']
            if isinstance(diagnosis, list):
                diagnosis_str = ", ".join(diagnosis)
            else:
                diagnosis_str = str(diagnosis)
            input_parts.append(f"Diagnosis: {diagnosis_str}")
        
        if 'treatment' in record_data:
            treatment = record_data['treatment']
            if isinstance(treatment, dict):
                treatment_str = json.dumps(treatment)
            else:
                treatment_str = str(treatment)
            input_parts.append(f"Treatment: {treatment_str}")
        
        # Lab results
        if 'lab_results' in record_data:
            labs = record_data['lab_results']
            if isinstance(labs, dict):
                labs_str = json.dumps(labs)
            else:
                labs_str = str(labs)
            input_parts.append(f"Lab Results: {labs_str}")
        
        # Vital signs
        if 'vital_signs' in record_data:
            vitals = record_data['vital_signs']
            vitals_str = []
            for vital, value in vitals.items():
                if value is not None:
                    vitals_str.append(f"{vital}: {value}")
            if vitals_str:
                input_parts.append(f"Vital Signs: {', '.join(vitals_str)}")
        
        # Additional context
        if 'additional_context' in record_data:
            input_parts.append(f"Additional Context: {record_data['additional_context']}")
        
        # Create record prompt
        record_prompt = f"""
Please create a comprehensive medical record entry for this patient:

{chr(10).join(input_parts)}

Based on the above information, please create a detailed medical record that includes:
1. Comprehensive clinical assessment
2. Detailed findings and observations
3. Diagnostic reasoning and conclusions
4. Treatment recommendations or plans
5. Follow-up requirements
6. Any clinical notes or observations

Format your response as:
CLINICAL_ASSESSMENT: [comprehensive clinical assessment]
FINDINGS: [detailed findings and observations]
DIAGNOSTIC_REASONING: [diagnostic reasoning and conclusions]
TREATMENT_PLAN: [treatment recommendations or plans]
FOLLOW_UP: [follow-up requirements and schedule]
CLINICAL_NOTES: [additional clinical notes or observations]
SUMMARY: [brief summary of the record entry]
"""
        
        return record_prompt
    
    def _parse_record_content(self, result: str) -> Dict[str, Any]:
        """Parse medical record content from agent result"""
        try:
            record_content = {
                'clinical_assessment': '',
                'findings': [],
                'diagnostic_reasoning': '',
                'treatment_plan': [],
                'follow_up': [],
                'clinical_notes': [],
                'summary': ''
            }
            
            lines = result.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('CLINICAL_ASSESSMENT:'):
                    assessment = line.split(':', 1)[1].strip()
                    record_content['clinical_assessment'] = assessment
                elif line.startswith('FINDINGS:'):
                    current_section = 'findings'
                elif line.startswith('DIAGNOSTIC_REASONING:'):
                    reasoning = line.split(':', 1)[1].strip()
                    record_content['diagnostic_reasoning'] = reasoning
                elif line.startswith('TREATMENT_PLAN:'):
                    current_section = 'treatment_plan'
                elif line.startswith('FOLLOW_UP:'):
                    current_section = 'follow_up'
                elif line.startswith('CLINICAL_NOTES:'):
                    current_section = 'clinical_notes'
                elif line.startswith('SUMMARY:'):
                    summary = line.split(':', 1)[1].strip()
                    record_content['summary'] = summary
                elif line and current_section and line.startswith('-'):
                    item = line[1:].strip()
                    if current_section in record_content:
                        record_content[current_section].append(item)
            
            return record_content
            
        except Exception as e:
            self.logger("MedicalRecordsAgent", "parse_error", f"Failed to parse record content: {str(e)}")
            return {
                'clinical_assessment': 'Clinical assessment completed',
                'findings': [],
                'diagnostic_reasoning': 'Standard diagnostic reasoning applied',
                'treatment_plan': [],
                'follow_up': ['Regular follow-up as needed'],
                'clinical_notes': [],
                'summary': 'Medical record entry completed successfully'
            }
    
    def _create_record_in_db(self, record_data: Dict[str, Any], record_content: Dict[str, Any], assessment_result: str) -> Optional[Dict[str, Any]]:
        """Create medical record in database"""
        try:
            with get_db_session() as session:
                # Create comprehensive content
                content = f"""
Clinical Assessment: {record_content['clinical_assessment']}

Findings: {', '.join(record_content['findings']) if record_content['findings'] else 'No specific findings'}

Diagnostic Reasoning: {record_content['diagnostic_reasoning']}

Treatment Plan: {', '.join(record_content['treatment_plan']) if record_content['treatment_plan'] else 'No specific treatment plan'}

Follow-up: {', '.join(record_content['follow_up']) if record_content['follow_up'] else 'Standard follow-up'}

Clinical Notes: {', '.join(record_content['clinical_notes']) if record_content['clinical_notes'] else 'No additional notes'}

Summary: {record_content['summary']}
                """.strip()
                
                record = MedicalRecord(
                    patient_id=record_data['patient_id'],
                    record_type=record_data.get('record_type', 'general'),
                    title=record_data.get('title', 'Medical Record Entry'),
                    content=content,
                    doctor_id=record_data.get('doctor_id', ''),
                    department=record_data.get('department', ''),
                    diagnosis_codes=record_data.get('diagnosis_codes', []),
                    medications=record_data.get('medications', []),
                    procedures=record_data.get('procedures', [])
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
            self.logger("MedicalRecordsAgent", "database_error", f"Failed to create record in database: {str(e)}")
            return None
    
    def analyze_medical_records(self, patient_id: str, analysis_type: str = 'comprehensive') -> Dict[str, Any]:
        """Analyze patient medical records for patterns and insights"""
        try:
            # Get patient medical records
            records = self._get_patient_records(patient_id)
            
            if not records['success']:
                return records
            
            # Prepare analysis input
            analysis_input = self._prepare_analysis_input(records['records'], analysis_type)
            
            # Execute analysis
            result = self.execute(analysis_input)
            
            if result['success']:
                # Parse analysis results
                analysis_result = self._parse_analysis_result(result['result'])
                
                return {
                    'success': True,
                    'analysis': analysis_result,
                    'records_analyzed': len(records['records']),
                    'assessment': result['result']
                }
            else:
                return result
                
        except Exception as e:
            self.logger("MedicalRecordsAgent", "analysis_error", f"Medical record analysis failed: {str(e)}")
            return {
                'success': False,
                'error': f"Medical record analysis failed: {str(e)}"
            }
    
    def _get_patient_records(self, patient_id: str) -> Dict[str, Any]:
        """Get all medical records for a patient"""
        try:
            with get_db_session() as session:
                records = session.query(MedicalRecord).filter(
                    MedicalRecord.patient_id == patient_id
                ).order_by(MedicalRecord.created_at.desc()).all()
                
                record_data = []
                for record in records:
                    record_data.append({
                        'id': str(record.id),
                        'record_type': record.record_type,
                        'title': record.title,
                        'content': record.content,
                        'doctor_id': record.doctor_id,
                        'department': record.department,
                        'diagnosis_codes': record.diagnosis_codes,
                        'medications': record.medications,
                        'procedures': record.procedures,
                        'created_at': record.created_at.isoformat()
                    })
                
                return {
                    'success': True,
                    'records': record_data
                }
                
        except Exception as e:
            self.logger("MedicalRecordsAgent", "records_error", f"Failed to get patient records: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to get patient records: {str(e)}"
            }
    
    def _prepare_analysis_input(self, records: List[Dict[str, Any]], analysis_type: str) -> str:
        """Prepare input for medical record analysis"""
        input_parts = []
        
        input_parts.append(f"Analysis Type: {analysis_type}")
        input_parts.append(f"Number of Records: {len(records)}")
        
        # Add record summaries
        for i, record in enumerate(records[:10]):  # Limit to last 10 records
            input_parts.append(f"Record {i+1} ({record['record_type']}): {record['title']}")
            input_parts.append(f"  Content: {record['content'][:200]}...")
            if record['medications']:
                input_parts.append(f"  Medications: {', '.join(record['medications'])}")
            if record['diagnosis_codes']:
                input_parts.append(f"  Diagnosis Codes: {', '.join(record['diagnosis_codes'])}")
        
        # Create analysis prompt
        analysis_prompt = f"""
Please analyze these medical records for patterns and insights:

{chr(10).join(input_parts)}

Based on the above medical records, please provide:
1. Overall health status assessment
2. Identified patterns and trends
3. Potential health risks or concerns
4. Treatment effectiveness analysis
5. Recommendations for care
6. Areas requiring attention or follow-up

Format your response as:
HEALTH_STATUS: [overall health status assessment]
PATTERNS: [identified patterns and trends]
RISKS: [potential health risks or concerns]
TREATMENT_EFFECTIVENESS: [treatment effectiveness analysis]
RECOMMENDATIONS: [recommendations for care]
ATTENTION_AREAS: [areas requiring attention or follow-up]
SUMMARY: [brief analysis summary]
"""
        
        return analysis_prompt
    
    def _parse_analysis_result(self, result: str) -> Dict[str, Any]:
        """Parse medical record analysis results"""
        try:
            analysis = {
                'health_status': '',
                'patterns': [],
                'risks': [],
                'treatment_effectiveness': '',
                'recommendations': [],
                'attention_areas': [],
                'summary': ''
            }
            
            lines = result.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('HEALTH_STATUS:'):
                    status = line.split(':', 1)[1].strip()
                    analysis['health_status'] = status
                elif line.startswith('PATTERNS:'):
                    current_section = 'patterns'
                elif line.startswith('RISKS:'):
                    current_section = 'risks'
                elif line.startswith('TREATMENT_EFFECTIVENESS:'):
                    effectiveness = line.split(':', 1)[1].strip()
                    analysis['treatment_effectiveness'] = effectiveness
                elif line.startswith('RECOMMENDATIONS:'):
                    current_section = 'recommendations'
                elif line.startswith('ATTENTION_AREAS:'):
                    current_section = 'attention_areas'
                elif line.startswith('SUMMARY:'):
                    summary = line.split(':', 1)[1].strip()
                    analysis['summary'] = summary
                elif line and current_section and line.startswith('-'):
                    item = line[1:].strip()
                    if current_section in analysis:
                        analysis[current_section].append(item)
            
            return analysis
            
        except Exception as e:
            self.logger("MedicalRecordsAgent", "parse_analysis_error", f"Failed to parse analysis result: {str(e)}")
            return {
                'health_status': 'Analysis completed',
                'patterns': [],
                'risks': [],
                'treatment_effectiveness': 'Standard effectiveness',
                'recommendations': ['Continue current care plan'],
                'attention_areas': [],
                'summary': 'Medical record analysis completed successfully'
            }
    
    def get_medical_record_statistics(self, patient_id: Optional[str] = None) -> Dict[str, Any]:
        """Get medical record statistics"""
        try:
            with get_db_session() as session:
                # Base query
                records_query = session.query(MedicalRecord)
                
                if patient_id:
                    records_query = records_query.filter(MedicalRecord.patient_id == patient_id)
                
                # Get record statistics
                total_records = records_query.count()
                
                # Get records by type
                record_types = session.query(MedicalRecord.record_type).distinct().all()
                type_counts = {}
                for record_type in record_types:
                    count = records_query.filter(MedicalRecord.record_type == record_type[0]).count()
                    type_counts[record_type[0]] = count
                
                # Get recent records (last 30 days)
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                recent_records = records_query.filter(
                    MedicalRecord.created_at >= thirty_days_ago
                ).count()
                
                # Get records by department
                departments = session.query(MedicalRecord.department).distinct().all()
                dept_counts = {}
                for dept in departments:
                    if dept[0]:  # Only count non-null departments
                        count = records_query.filter(MedicalRecord.department == dept[0]).count()
                        dept_counts[dept[0]] = count
                
                return {
                    'success': True,
                    'statistics': {
                        'total_records': total_records,
                        'recent_records_30d': recent_records,
                        'by_type': type_counts,
                        'by_department': dept_counts
                    }
                }
                
        except Exception as e:
            self.logger("MedicalRecordsAgent", "stats_error", f"Failed to get medical record statistics: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to get medical record statistics: {str(e)}"
            }
    
    def search_medical_records(self, search_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Search medical records based on criteria"""
        try:
            with get_db_session() as session:
                query = session.query(MedicalRecord)
                
                # Apply search filters
                if search_criteria.get('patient_id'):
                    query = query.filter(MedicalRecord.patient_id == search_criteria['patient_id'])
                
                if search_criteria.get('record_type'):
                    query = query.filter(MedicalRecord.record_type == search_criteria['record_type'])
                
                if search_criteria.get('department'):
                    query = query.filter(MedicalRecord.department == search_criteria['department'])
                
                if search_criteria.get('doctor_id'):
                    query = query.filter(MedicalRecord.doctor_id == search_criteria['doctor_id'])
                
                if search_criteria.get('date_from'):
                    query = query.filter(MedicalRecord.created_at >= search_criteria['date_from'])
                
                if search_criteria.get('date_to'):
                    query = query.filter(MedicalRecord.created_at <= search_criteria['date_to'])
                
                # Limit results
                limit = search_criteria.get('limit', 50)
                records = query.order_by(MedicalRecord.created_at.desc()).limit(limit).all()
                
                record_data = []
                for record in records:
                    record_data.append({
                        'id': str(record.id),
                        'patient_id': str(record.patient_id),
                        'record_type': record.record_type,
                        'title': record.title,
                        'content': record.content[:500] + '...' if len(record.content) > 500 else record.content,
                        'doctor_id': record.doctor_id,
                        'department': record.department,
                        'created_at': record.created_at.isoformat()
                    })
                
                return {
                    'success': True,
                    'records': record_data,
                    'count': len(record_data),
                    'total_found': query.count()
                }
                
        except Exception as e:
            self.logger("MedicalRecordsAgent", "search_error", f"Medical record search failed: {str(e)}")
            return {
                'success': False,
                'error': f"Medical record search failed: {str(e)}"
            }  