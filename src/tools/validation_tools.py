"""
Validation Tools

This module provides data validation, input verification, and quality checks
for healthcare data and system inputs.
"""

from typing import Dict, List, Any, Optional, Union
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, validator
import logging
import re
from datetime import datetime, date
import uuid

class PatientDataInput(BaseModel):
    """Input for patient data validation"""
    patient_data: Dict[str, Any] = Field(description="Patient data to validate")

class VitalSignsInput(BaseModel):
    """Input for vital signs validation"""
    vital_signs: Dict[str, Any] = Field(description="Vital signs data to validate")

class MedicalRecordInput(BaseModel):
    """Input for medical record validation"""
    medical_record: Dict[str, Any] = Field(description="Medical record data to validate")

class PatientDataValidationTool(BaseTool):
    """Tool for validating patient data"""
    name: str = "validate_patient_data"
    description: str = "Validate patient data for completeness and accuracy"
    args_schema: type[BaseModel] = PatientDataInput
    
    def _run(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate patient data"""
        try:
            validation_result = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'validated_fields': []
            }
            
            # Required fields validation
            required_fields = ['first_name', 'last_name', 'date_of_birth', 'gender', 'mrn']
            for field in required_fields:
                if field not in patient_data or not patient_data[field]:
                    validation_result['errors'].append(f"Missing required field: {field}")
                    validation_result['is_valid'] = False
                else:
                    validation_result['validated_fields'].append(field)
            
            # Name validation
            if 'first_name' in patient_data and patient_data['first_name']:
                if not self._validate_name(patient_data['first_name']):
                    validation_result['errors'].append("Invalid first name format")
                    validation_result['is_valid'] = False
            
            if 'last_name' in patient_data and patient_data['last_name']:
                if not self._validate_name(patient_data['last_name']):
                    validation_result['errors'].append("Invalid last name format")
                    validation_result['is_valid'] = False
            
            # Date of birth validation
            if 'date_of_birth' in patient_data and patient_data['date_of_birth']:
                dob_validation = self._validate_date_of_birth(patient_data['date_of_birth'])
                if not dob_validation['is_valid']:
                    validation_result['errors'].append(dob_validation['error'])
                    validation_result['is_valid'] = False
            
            # Gender validation
            if 'gender' in patient_data and patient_data['gender']:
                if not self._validate_gender(patient_data['gender']):
                    validation_result['errors'].append("Invalid gender value")
                    validation_result['is_valid'] = False
            
            # MRN validation
            if 'mrn' in patient_data and patient_data['mrn']:
                if not self._validate_mrn(patient_data['mrn']):
                    validation_result['errors'].append("Invalid MRN format")
                    validation_result['is_valid'] = False
            
            # Email validation
            if 'email' in patient_data and patient_data['email']:
                if not self._validate_email(patient_data['email']):
                    validation_result['warnings'].append("Invalid email format")
            
            # Phone validation
            if 'phone' in patient_data and patient_data['phone']:
                if not self._validate_phone(patient_data['phone']):
                    validation_result['warnings'].append("Invalid phone number format")
            
            # Age validation
            if 'date_of_birth' in patient_data and patient_data['date_of_birth']:
                age = self._calculate_age(patient_data['date_of_birth'])
                if age and (age < 0 or age > 150):
                    validation_result['warnings'].append(f"Unusual age: {age} years")
            
            return validation_result
            
        except Exception as e:
            logging.error(f"Patient data validation failed: {str(e)}")
            return {
                'is_valid': False,
                'error': f"Validation failed: {str(e)}",
                'errors': [],
                'warnings': []
            }
    
    def _validate_name(self, name: str) -> bool:
        """Validate name format"""
        if not name or len(name.strip()) < 1:
            return False
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        name_pattern = r'^[A-Za-z\s\'-]+$'
        return bool(re.match(name_pattern, name.strip()))
    
    def _validate_date_of_birth(self, dob: Union[str, date]) -> Dict[str, Any]:
        """Validate date of birth"""
        try:
            if isinstance(dob, str):
                dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
            else:
                dob_date = dob
            
            # Check if date is in the past
            if dob_date >= date.today():
                return {
                    'is_valid': False,
                    'error': 'Date of birth must be in the past'
                }
            
            # Check if date is reasonable (not too far in the past)
            if dob_date < date(1900, 1, 1):
                return {
                    'is_valid': False,
                    'error': 'Date of birth seems too far in the past'
                }
            
            return {'is_valid': True}
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': f'Invalid date format: {str(e)}'
            }
    
    def _validate_gender(self, gender: str) -> bool:
        """Validate gender value"""
        valid_genders = ['male', 'female', 'other', 'unknown']
        return gender.lower() in valid_genders
    
    def _validate_mrn(self, mrn: str) -> bool:
        """Validate Medical Record Number format"""
        if not mrn or len(mrn.strip()) < 3:
            return False
        
        # Basic MRN validation (alphanumeric, 3-20 characters)
        mrn_pattern = r'^[A-Za-z0-9]{3,20}$'
        return bool(re.match(mrn_pattern, mrn.strip()))
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        if not email:
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email.strip()))
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Check if it's a valid length (7-15 digits)
        return 7 <= len(digits_only) <= 15
    
    def _calculate_age(self, dob: Union[str, date]) -> Optional[int]:
        """Calculate age from date of birth"""
        try:
            if isinstance(dob, str):
                dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
            else:
                dob_date = dob
            
            today = date.today()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            return age
            
        except Exception:
            return None

class VitalSignsValidationTool(BaseTool):
    """Tool for validating vital signs data"""
    name: str = "validate_vital_signs"
    description: str = "Validate vital signs data for accuracy and reasonable ranges"
    args_schema: type[BaseModel] = VitalSignsInput
    
    def _run(self, vital_signs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate vital signs data"""
        try:
            validation_result = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'validated_fields': []
            }
            
            # Required fields
            if 'patient_id' not in vital_signs or not vital_signs['patient_id']:
                validation_result['errors'].append("Missing required field: patient_id")
                validation_result['is_valid'] = False
            else:
                validation_result['validated_fields'].append('patient_id')
            
            # Validate each vital sign
            vital_sign_ranges = {
                'heart_rate': {'min': 30, 'max': 200, 'unit': 'bpm'},
                'systolic_bp': {'min': 60, 'max': 250, 'unit': 'mmHg'},
                'diastolic_bp': {'min': 40, 'max': 150, 'unit': 'mmHg'},
                'temperature': {'min': 90.0, 'max': 110.0, 'unit': '°F'},
                'oxygen_saturation': {'min': 70.0, 'max': 100.0, 'unit': '%'},
                'respiratory_rate': {'min': 6, 'max': 50, 'unit': 'breaths/min'},
                'blood_glucose': {'min': 20, 'max': 600, 'unit': 'mg/dL'},
                'pain_level': {'min': 0, 'max': 10, 'unit': 'scale'}
            }
            
            for vital, value in vital_signs.items():
                if vital in vital_sign_ranges and value is not None:
                    ranges = vital_sign_ranges[vital]
                    
                    # Check if value is numeric
                    try:
                        numeric_value = float(value)
                    except (ValueError, TypeError):
                        validation_result['errors'].append(f"Invalid {vital}: must be numeric")
                        validation_result['is_valid'] = False
                        continue
                    
                    # Check range
                    if numeric_value < ranges['min']:
                        validation_result['warnings'].append(
                            f"{vital} ({numeric_value} {ranges['unit']}) is below normal range ({ranges['min']}-{ranges['max']})"
                        )
                    elif numeric_value > ranges['max']:
                        validation_result['warnings'].append(
                            f"{vital} ({numeric_value} {ranges['unit']}) is above normal range ({ranges['min']}-{ranges['max']})"
                        )
                    
                    validation_result['validated_fields'].append(vital)
            
            # Check for reasonable combinations
            if 'systolic_bp' in vital_signs and 'diastolic_bp' in vital_signs:
                systolic = vital_signs['systolic_bp']
                diastolic = vital_signs['diastolic_bp']
                
                if systolic is not None and diastolic is not None:
                    try:
                        systolic_val = float(systolic)
                        diastolic_val = float(diastolic)
                        
                        if systolic_val <= diastolic_val:
                            validation_result['errors'].append("Systolic BP must be greater than diastolic BP")
                            validation_result['is_valid'] = False
                        
                        if systolic_val - diastolic_val < 20:
                            validation_result['warnings'].append("Pulse pressure seems low")
                        
                    except (ValueError, TypeError):
                        pass
            
            return validation_result
            
        except Exception as e:
            logging.error(f"Vital signs validation failed: {str(e)}")
            return {
                'is_valid': False,
                'error': f"Validation failed: {str(e)}",
                'errors': [],
                'warnings': []
            }

class MedicalRecordValidationTool(BaseTool):
    """Tool for validating medical record data"""
    name: str = "validate_medical_record"
    description: str = "Validate medical record data for completeness and accuracy"
    args_schema: type[BaseModel] = MedicalRecordInput
    
    def _run(self, medical_record: Dict[str, Any]) -> Dict[str, Any]:
        """Validate medical record data"""
        try:
            validation_result = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'validated_fields': []
            }
            
            # Required fields validation
            required_fields = ['patient_id', 'record_type', 'title', 'content']
            for field in required_fields:
                if field not in medical_record or not medical_record[field]:
                    validation_result['errors'].append(f"Missing required field: {field}")
                    validation_result['is_valid'] = False
                else:
                    validation_result['validated_fields'].append(field)
            
            # Record type validation
            if 'record_type' in medical_record and medical_record['record_type']:
                valid_types = [
                    'diagnosis', 'treatment', 'lab_result', 'procedure', 
                    'consultation', 'note', 'prescription', 'imaging',
                    'progress_note', 'discharge_summary'
                ]
                if medical_record['record_type'].lower() not in valid_types:
                    validation_result['warnings'].append(f"Unusual record type: {medical_record['record_type']}")
            
            # Content validation
            if 'content' in medical_record and medical_record['content']:
                content = medical_record['content']
                if len(content.strip()) < 10:
                    validation_result['warnings'].append("Medical record content seems too short")
                
                if len(content) > 10000:
                    validation_result['warnings'].append("Medical record content seems very long")
            
            # Title validation
            if 'title' in medical_record and medical_record['title']:
                title = medical_record['title']
                if len(title.strip()) < 3:
                    validation_result['warnings'].append("Medical record title seems too short")
                
                if len(title) > 200:
                    validation_result['warnings'].append("Medical record title seems too long")
            
            # Doctor ID validation
            if 'doctor_id' in medical_record and medical_record['doctor_id']:
                if not self._validate_doctor_id(medical_record['doctor_id']):
                    validation_result['warnings'].append("Invalid doctor ID format")
            
            # Department validation
            if 'department' in medical_record and medical_record['department']:
                valid_departments = [
                    'cardiology', 'pulmonology', 'neurology', 'orthopedics',
                    'emergency', 'internal_medicine', 'pediatrics', 'surgery',
                    'radiology', 'laboratory', 'pharmacy', 'nursing'
                ]
                if medical_record['department'].lower() not in valid_departments:
                    validation_result['warnings'].append(f"Unusual department: {medical_record['department']}")
            
            # Diagnosis codes validation
            if 'diagnosis_codes' in medical_record and medical_record['diagnosis_codes']:
                codes = medical_record['diagnosis_codes']
                if isinstance(codes, list):
                    for code in codes:
                        if not self._validate_icd_code(code):
                            validation_result['warnings'].append(f"Invalid ICD code format: {code}")
                else:
                    validation_result['warnings'].append("Diagnosis codes should be a list")
            
            # Medications validation
            if 'medications' in medical_record and medical_record['medications']:
                medications = medical_record['medications']
                if isinstance(medications, list):
                    for med in medications:
                        if not self._validate_medication_name(med):
                            validation_result['warnings'].append(f"Unusual medication name: {med}")
                else:
                    validation_result['warnings'].append("Medications should be a list")
            
            return validation_result
            
        except Exception as e:
            logging.error(f"Medical record validation failed: {str(e)}")
            return {
                'is_valid': False,
                'error': f"Validation failed: {str(e)}",
                'errors': [],
                'warnings': []
            }
    
    def _validate_doctor_id(self, doctor_id: str) -> bool:
        """Validate doctor ID format"""
        if not doctor_id:
            return False
        
        # Basic doctor ID validation (alphanumeric, 3-10 characters)
        doctor_id_pattern = r'^[A-Za-z0-9]{3,10}$'
        return bool(re.match(doctor_id_pattern, doctor_id.strip()))
    
    def _validate_icd_code(self, code: str) -> bool:
        """Validate ICD code format"""
        if not code:
            return False
        
        # Basic ICD-10 code validation
        icd_pattern = r'^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$'
        return bool(re.match(icd_pattern, code.strip().upper()))
    
    def _validate_medication_name(self, medication: str) -> bool:
        """Validate medication name format"""
        if not medication:
            return False
        
        # Check for valid characters (letters, numbers, spaces, hyphens)
        med_pattern = r'^[A-Za-z0-9\s\-\.]+$'
        return bool(re.match(med_pattern, medication.strip()))

class DataQualityCheckTool(BaseTool):
    """Tool for performing data quality checks"""
    name: str = "check_data_quality"
    description: str = "Perform comprehensive data quality checks on healthcare data"
    
    def _run(self, data: Dict[str, Any], data_type: str = "general") -> Dict[str, Any]:
        """Perform data quality checks"""
        try:
            quality_result = {
                'overall_score': 100,
                'issues': [],
                'recommendations': [],
                'completeness': 0,
                'accuracy': 0,
                'consistency': 0
            }
            
            if data_type == "patient":
                return self._check_patient_data_quality(data)
            elif data_type == "vital_signs":
                return self._check_vital_signs_quality(data)
            elif data_type == "medical_record":
                return self._check_medical_record_quality(data)
            else:
                return self._check_general_data_quality(data)
            
        except Exception as e:
            logging.error(f"Data quality check failed: {str(e)}")
            return {
                'overall_score': 0,
                'error': f"Quality check failed: {str(e)}",
                'issues': [],
                'recommendations': []
            }
    
    def _check_patient_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check patient data quality"""
        result = {
            'overall_score': 100,
            'issues': [],
            'recommendations': [],
            'completeness': 0,
            'accuracy': 0,
            'consistency': 0
        }
        
        # Completeness check
        required_fields = ['first_name', 'last_name', 'date_of_birth', 'gender', 'mrn']
        optional_fields = ['email', 'phone', 'address', 'emergency_contact']
        
        present_required = sum(1 for field in required_fields if field in data and data[field])
        present_optional = sum(1 for field in optional_fields if field in data and data[field])
        
        completeness = (present_required / len(required_fields)) * 100
        result['completeness'] = completeness
        
        if completeness < 100:
            result['issues'].append(f"Missing required fields: {100 - completeness:.0f}%")
            result['overall_score'] -= 20
        
        # Accuracy check
        accuracy_issues = 0
        if 'email' in data and data['email']:
            if not self._validate_email(data['email']):
                accuracy_issues += 1
                result['issues'].append("Invalid email format")
        
        if 'phone' in data and data['phone']:
            if not self._validate_phone(data['phone']):
                accuracy_issues += 1
                result['issues'].append("Invalid phone format")
        
        result['accuracy'] = max(0, 100 - (accuracy_issues * 20))
        result['overall_score'] -= accuracy_issues * 10
        
        # Consistency check
        consistency_issues = 0
        if 'date_of_birth' in data and data['date_of_birth']:
            age = self._calculate_age(data['date_of_birth'])
            if age and (age < 0 or age > 150):
                consistency_issues += 1
                result['issues'].append("Unreasonable age")
        
        result['consistency'] = max(0, 100 - (consistency_issues * 20))
        result['overall_score'] -= consistency_issues * 10
        
        # Recommendations
        if completeness < 100:
            result['recommendations'].append("Complete missing required fields")
        
        if accuracy_issues > 0:
            result['recommendations'].append("Verify contact information accuracy")
        
        if consistency_issues > 0:
            result['recommendations'].append("Review data consistency")
        
        result['overall_score'] = max(0, result['overall_score'])
        return result
    
    def _check_vital_signs_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check vital signs data quality"""
        result = {
            'overall_score': 100,
            'issues': [],
            'recommendations': [],
            'completeness': 0,
            'accuracy': 0,
            'consistency': 0
        }
        
        # Completeness check
        vital_signs = ['heart_rate', 'systolic_bp', 'diastolic_bp', 'temperature', 'oxygen_saturation']
        present_vitals = sum(1 for vital in vital_signs if vital in data and data[vital] is not None)
        
        completeness = (present_vitals / len(vital_signs)) * 100
        result['completeness'] = completeness
        
        if completeness < 50:
            result['issues'].append("Very few vital signs recorded")
            result['overall_score'] -= 30
        elif completeness < 80:
            result['issues'].append("Some vital signs missing")
            result['overall_score'] -= 15
        
        # Accuracy check
        accuracy_issues = 0
        for vital, value in data.items():
            if value is not None:
                try:
                    float(value)
                except (ValueError, TypeError):
                    accuracy_issues += 1
                    result['issues'].append(f"Non-numeric {vital} value")
        
        result['accuracy'] = max(0, 100 - (accuracy_issues * 25))
        result['overall_score'] -= accuracy_issues * 15
        
        # Consistency check
        consistency_issues = 0
        if 'systolic_bp' in data and 'diastolic_bp' in data:
            try:
                systolic = float(data['systolic_bp'])
                diastolic = float(data['diastolic_bp'])
                if systolic <= diastolic:
                    consistency_issues += 1
                    result['issues'].append("Systolic BP should be greater than diastolic BP")
            except (ValueError, TypeError):
                pass
        
        result['consistency'] = max(0, 100 - (consistency_issues * 50))
        result['overall_score'] -= consistency_issues * 20
        
        # Recommendations
        if completeness < 80:
            result['recommendations'].append("Record more complete vital signs")
        
        if accuracy_issues > 0:
            result['recommendations'].append("Verify vital signs data accuracy")
        
        if consistency_issues > 0:
            result['recommendations'].append("Review blood pressure consistency")
        
        result['overall_score'] = max(0, result['overall_score'])
        return result
    
    def _check_medical_record_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check medical record data quality"""
        result = {
            'overall_score': 100,
            'issues': [],
            'recommendations': [],
            'completeness': 0,
            'accuracy': 0,
            'consistency': 0
        }
        
        # Completeness check
        required_fields = ['patient_id', 'record_type', 'title', 'content']
        present_required = sum(1 for field in required_fields if field in data and data[field])
        
        completeness = (present_required / len(required_fields)) * 100
        result['completeness'] = completeness
        
        if completeness < 100:
            result['issues'].append("Missing required medical record fields")
            result['overall_score'] -= 30
        
        # Content quality check
        if 'content' in data and data['content']:
            content = data['content']
            if len(content.strip()) < 20:
                result['issues'].append("Medical record content too brief")
                result['overall_score'] -= 20
            elif len(content) > 5000:
                result['issues'].append("Medical record content very long")
                result['overall_score'] -= 10
        
        result['accuracy'] = 100  # Assume content is accurate if present
        result['consistency'] = 100  # Assume consistency if required fields present
        
        # Recommendations
        if completeness < 100:
            result['recommendations'].append("Complete all required medical record fields")
        
        if 'content' in data and len(data['content'].strip()) < 20:
            result['recommendations'].append("Provide more detailed medical record content")
        
        result['overall_score'] = max(0, result['overall_score'])
        return result
    
    def _check_general_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check general data quality"""
        result = {
            'overall_score': 100,
            'issues': [],
            'recommendations': [],
            'completeness': 0,
            'accuracy': 0,
            'consistency': 0
        }
        
        # Basic checks
        if not data:
            result['issues'].append("Empty data")
            result['overall_score'] = 0
            return result
        
        # Check for null/empty values
        empty_fields = sum(1 for value in data.values() if value is None or value == "")
        total_fields = len(data)
        
        if total_fields > 0:
            completeness = ((total_fields - empty_fields) / total_fields) * 100
            result['completeness'] = completeness
            
            if completeness < 80:
                result['issues'].append(f"Many empty fields: {100 - completeness:.0f}%")
                result['overall_score'] -= 20
        
        result['accuracy'] = 100  # Assume accuracy for general data
        result['consistency'] = 100  # Assume consistency for general data
        
        # Recommendations
        if result['completeness'] < 80:
            result['recommendations'].append("Fill in missing data fields")
        
        result['overall_score'] = max(0, result['overall_score'])
        return result
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        if not email:
            return False
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email.strip()))
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        digits_only = re.sub(r'\D', '', phone)
        return 7 <= len(digits_only) <= 15
    
    def _calculate_age(self, dob: Union[str, date]) -> Optional[int]:
        """Calculate age from date of birth"""
        try:
            if isinstance(dob, str):
                dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
            else:
                dob_date = dob
            
            today = date.today()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            return age
        except Exception:
            return None

class ValidationTools:
    """Aggregate all validation tools for unified access"""
    def __init__(self):
        self.patient_data = PatientDataValidationTool()
        self.vital_signs = VitalSignsValidationTool()
        self.medical_record = MedicalRecordValidationTool()
        self.data_quality = DataQualityCheckTool()
