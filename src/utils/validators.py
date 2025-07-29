"""
Validators Utility

This module provides data validation functions for healthcare data,
including patient information, medical records, and system inputs.
"""

import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union, Tuple
from email_validator import validate_email, EmailNotValidError

class HealthcareValidators:
    """Collection of healthcare data validators"""
    
    @staticmethod
    def validate_patient_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate patient data"""
        errors = []
        
        # Required fields
        required_fields = ['first_name', 'last_name', 'date_of_birth', 'gender', 'mrn']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Name validation
        if 'first_name' in data and data['first_name']:
            if not HealthcareValidators._validate_name(data['first_name']):
                errors.append("Invalid first name format")
        
        if 'last_name' in data and data['last_name']:
            if not HealthcareValidators._validate_name(data['last_name']):
                errors.append("Invalid last name format")
        
        # Date of birth validation
        if 'date_of_birth' in data and data['date_of_birth']:
            dob_valid, dob_error = HealthcareValidators._validate_date_of_birth(data['date_of_birth'])
            if not dob_valid:
                errors.append(dob_error)
        
        # Gender validation
        if 'gender' in data and data['gender']:
            if not HealthcareValidators._validate_gender(data['gender']):
                errors.append("Invalid gender value")
        
        # MRN validation
        if 'mrn' in data and data['mrn']:
            if not HealthcareValidators._validate_mrn(data['mrn']):
                errors.append("Invalid MRN format")
        
        # Email validation
        if 'email' in data and data['email']:
            if not HealthcareValidators._validate_email(data['email']):
                errors.append("Invalid email format")
        
        # Phone validation
        if 'phone' in data and data['phone']:
            if not HealthcareValidators._validate_phone(data['phone']):
                errors.append("Invalid phone number format")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_vital_signs(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate vital signs data"""
        errors = []
        
        # Required fields
        if 'patient_id' not in data or not data['patient_id']:
            errors.append("Missing required field: patient_id")
        
        # Vital signs ranges
        vital_ranges = {
            'heart_rate': (30, 200),
            'systolic_bp': (60, 250),
            'diastolic_bp': (40, 150),
            'temperature': (90.0, 110.0),
            'oxygen_saturation': (70.0, 100.0),
            'respiratory_rate': (6, 50),
            'blood_glucose': (20, 600),
            'pain_level': (0, 10)
        }
        
        for vital, (min_val, max_val) in vital_ranges.items():
            if vital in data and data[vital] is not None:
                try:
                    value = float(data[vital])
                    if value < min_val or value > max_val:
                        errors.append(f"{vital} value {value} is outside normal range ({min_val}-{max_val})")
                except (ValueError, TypeError):
                    errors.append(f"{vital} must be a numeric value")
        
        # Blood pressure consistency
        if 'systolic_bp' in data and 'diastolic_bp' in data:
            try:
                systolic = float(data['systolic_bp'])
                diastolic = float(data['diastolic_bp'])
                if systolic <= diastolic:
                    errors.append("Systolic blood pressure must be greater than diastolic")
            except (ValueError, TypeError):
                pass
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_medical_record(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate medical record data"""
        errors = []
        
        # Required fields
        required_fields = ['patient_id', 'record_type', 'title', 'content']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Record type validation
        if 'record_type' in data and data['record_type']:
            valid_types = [
                'diagnosis', 'treatment', 'lab_result', 'procedure', 
                'consultation', 'note', 'prescription', 'imaging',
                'progress_note', 'discharge_summary'
            ]
            if data['record_type'].lower() not in valid_types:
                errors.append(f"Invalid record type: {data['record_type']}")
        
        # Content validation
        if 'content' in data and data['content']:
            content = data['content']
            if len(content.strip()) < 10:
                errors.append("Medical record content too short (minimum 10 characters)")
            
            if len(content) > 10000:
                errors.append("Medical record content too long (maximum 10,000 characters)")
        
        # Title validation
        if 'title' in data and data['title']:
            title = data['title']
            if len(title.strip()) < 3:
                errors.append("Medical record title too short (minimum 3 characters)")
            
            if len(title) > 200:
                errors.append("Medical record title too long (maximum 200 characters)")
        
        # Doctor ID validation
        if 'doctor_id' in data and data['doctor_id']:
            if not HealthcareValidators._validate_doctor_id(data['doctor_id']):
                errors.append("Invalid doctor ID format")
        
        # Department validation
        if 'department' in data and data['department']:
            valid_departments = [
                'cardiology', 'pulmonology', 'neurology', 'orthopedics',
                'emergency', 'internal_medicine', 'pediatrics', 'surgery',
                'radiology', 'laboratory', 'pharmacy', 'nursing'
            ]
            if data['department'].lower() not in valid_departments:
                errors.append(f"Invalid department: {data['department']}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_appointment(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate appointment data"""
        errors = []
        
        # Required fields
        required_fields = ['patient_id', 'doctor_id', 'scheduled_date']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Date validation
        if 'scheduled_date' in data and data['scheduled_date']:
            date_valid, date_error = HealthcareValidators._validate_future_date(data['scheduled_date'])
            if not date_valid:
                errors.append(date_error)
        
        # Duration validation
        if 'duration' in data and data['duration']:
            try:
                duration = int(data['duration'])
                if duration < 15 or duration > 240:
                    errors.append("Duration must be between 15 and 240 minutes")
            except (ValueError, TypeError):
                errors.append("Duration must be a numeric value")
        
        # Appointment type validation
        if 'appointment_type' in data and data['appointment_type']:
            valid_types = ['consultation', 'follow_up', 'procedure', 'emergency', 'routine_check']
            if data['appointment_type'].lower() not in valid_types:
                errors.append(f"Invalid appointment type: {data['appointment_type']}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_alert(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate alert data"""
        errors = []
        
        # Required fields
        required_fields = ['patient_id', 'alert_type', 'severity', 'title', 'message']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Severity validation
        if 'severity' in data and data['severity']:
            valid_severities = ['low', 'medium', 'high', 'critical']
            if data['severity'].lower() not in valid_severities:
                errors.append(f"Invalid severity: {data['severity']}")
        
        # Alert type validation
        if 'alert_type' in data and data['alert_type']:
            valid_types = ['vital_signs', 'medication', 'appointment', 'emergency', 'system']
            if data['alert_type'].lower() not in valid_types:
                errors.append(f"Invalid alert type: {data['alert_type']}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_treatment(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate treatment data"""
        errors = []
        
        # Required fields
        required_fields = ['patient_id', 'doctor_id', 'treatment_type', 'description']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Treatment type validation
        if 'treatment_type' in data and data['treatment_type']:
            valid_types = ['medication', 'procedure', 'therapy', 'surgery', 'lifestyle']
            if data['treatment_type'].lower() not in valid_types:
                errors.append(f"Invalid treatment type: {data['treatment_type']}")
        
        # Date validation
        if 'start_date' in data and data['start_date']:
            start_valid, start_error = HealthcareValidators._validate_date(data['start_date'])
            if not start_valid:
                errors.append(start_error)
        
        if 'end_date' in data and data['end_date']:
            end_valid, end_error = HealthcareValidators._validate_date(data['end_date'])
            if not end_valid:
                errors.append(end_error)
        
        # Date range validation
        if 'start_date' in data and 'end_date' in data and data['start_date'] and data['end_date']:
            try:
                start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
                if start_date >= end_date:
                    errors.append("End date must be after start date")
            except (ValueError, TypeError):
                pass
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_doctor_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate doctor data"""
        errors = []
        
        # Required fields
        required_fields = ['first_name', 'last_name', 'specialty', 'license_number']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Name validation
        if 'first_name' in data and data['first_name']:
            if not HealthcareValidators._validate_name(data['first_name']):
                errors.append("Invalid first name format")
        
        if 'last_name' in data and data['last_name']:
            if not HealthcareValidators._validate_name(data['last_name']):
                errors.append("Invalid last name format")
        
        # Specialty validation
        if 'specialty' in data and data['specialty']:
            valid_specialties = [
                'cardiology', 'pulmonology', 'neurology', 'orthopedics',
                'emergency_medicine', 'internal_medicine', 'pediatrics',
                'surgery', 'radiology', 'laboratory', 'pharmacy', 'nursing'
            ]
            if data['specialty'].lower() not in valid_specialties:
                errors.append(f"Invalid specialty: {data['specialty']}")
        
        # License number validation
        if 'license_number' in data and data['license_number']:
            if not HealthcareValidators._validate_license_number(data['license_number']):
                errors.append("Invalid license number format")
        
        # Email validation
        if 'email' in data and data['email']:
            if not HealthcareValidators._validate_email(data['email']):
                errors.append("Invalid email format")
        
        # Phone validation
        if 'phone' in data and data['phone']:
            if not HealthcareValidators._validate_phone(data['phone']):
                errors.append("Invalid phone number format")
        
        return len(errors) == 0, errors
    
    # Helper validation methods
    
    @staticmethod
    def _validate_name(name: str) -> bool:
        """Validate name format"""
        if not name or len(name.strip()) < 1:
            return False
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        name_pattern = r'^[A-Za-z\s\'-]+$'
        return bool(re.match(name_pattern, name.strip()))
    
    @staticmethod
    def _validate_date_of_birth(dob: Union[str, date]) -> Tuple[bool, str]:
        """Validate date of birth"""
        try:
            if isinstance(dob, str):
                dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
            else:
                dob_date = dob
            
            # Check if date is in the past
            if dob_date >= date.today():
                return False, 'Date of birth must be in the past'
            
            # Check if date is reasonable (not too far in the past)
            if dob_date < date(1900, 1, 1):
                return False, 'Date of birth seems too far in the past'
            
            return True, ""
            
        except Exception as e:
            return False, f'Invalid date format: {str(e)}'
    
    @staticmethod
    def _validate_future_date(date_str: str) -> Tuple[bool, str]:
        """Validate future date"""
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            if date_obj <= datetime.utcnow():
                return False, 'Date must be in the future'
            return True, ""
        except Exception as e:
            return False, f'Invalid date format: {str(e)}'
    
    @staticmethod
    def _validate_date(date_str: str) -> Tuple[bool, str]:
        """Validate date format"""
        try:
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return True, ""
        except Exception as e:
            return False, f'Invalid date format: {str(e)}'
    
    @staticmethod
    def _validate_gender(gender: str) -> bool:
        """Validate gender value"""
        valid_genders = ['male', 'female', 'other', 'unknown']
        return gender.lower() in valid_genders
    
    @staticmethod
    def _validate_mrn(mrn: str) -> bool:
        """Validate Medical Record Number format"""
        if not mrn or len(mrn.strip()) < 3:
            return False
        
        # Basic MRN validation (alphanumeric, 3-20 characters)
        mrn_pattern = r'^[A-Za-z0-9]{3,20}$'
        return bool(re.match(mrn_pattern, mrn.strip()))
    
    @staticmethod
    def _validate_doctor_id(doctor_id: str) -> bool:
        """Validate doctor ID format"""
        if not doctor_id:
            return False
        
        # Basic doctor ID validation (alphanumeric, 3-10 characters)
        doctor_id_pattern = r'^[A-Za-z0-9]{3,10}$'
        return bool(re.match(doctor_id_pattern, doctor_id.strip()))
    
    @staticmethod
    def _validate_license_number(license: str) -> bool:
        """Validate medical license number format"""
        if not license:
            return False
        
        # Basic license validation (alphanumeric, 6-15 characters)
        license_pattern = r'^[A-Za-z0-9]{6,15}$'
        return bool(re.match(license_pattern, license.strip()))
    
    @staticmethod
    def _validate_email(email: str) -> bool:
        """Validate email format"""
        if not email:
            return False
        
        try:
            validate_email(email.strip())
            return True
        except EmailNotValidError:
            return False
    
    @staticmethod
    def _validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Check if it's a valid length (7-15 digits)
        return 7 <= len(digits_only) <= 15

class DataSanitizer:
    """Data sanitization utilities"""
    
    @staticmethod
    def sanitize_patient_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize patient data"""
        sanitized = data.copy()
        
        # Sanitize names
        if 'first_name' in sanitized:
            sanitized['first_name'] = sanitized['first_name'].strip().title()
        
        if 'last_name' in sanitized:
            sanitized['last_name'] = sanitized['last_name'].strip().title()
        
        # Sanitize email
        if 'email' in sanitized:
            sanitized['email'] = sanitized['email'].strip().lower()
        
        # Sanitize phone
        if 'phone' in sanitized:
            sanitized['phone'] = re.sub(r'\D', '', sanitized['phone'])
        
        # Sanitize MRN
        if 'mrn' in sanitized:
            sanitized['mrn'] = sanitized['mrn'].strip().upper()
        
        return sanitized
    
    @staticmethod
    def sanitize_medical_record(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize medical record data"""
        sanitized = data.copy()
        
        # Sanitize title
        if 'title' in sanitized:
            sanitized['title'] = sanitized['title'].strip()
        
        # Sanitize content
        if 'content' in sanitized:
            sanitized['content'] = sanitized['content'].strip()
        
        # Sanitize record type
        if 'record_type' in sanitized:
            sanitized['record_type'] = sanitized['record_type'].strip().lower()
        
        # Sanitize department
        if 'department' in sanitized:
            sanitized['department'] = sanitized['department'].strip().lower()
        
        return sanitized
    
    @staticmethod
    def sanitize_vital_signs(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize vital signs data"""
        sanitized = data.copy()
        
        # Convert numeric values
        numeric_fields = ['heart_rate', 'systolic_bp', 'diastolic_bp', 'temperature', 
                         'oxygen_saturation', 'respiratory_rate', 'blood_glucose', 'pain_level']
        
        for field in numeric_fields:
            if field in sanitized and sanitized[field] is not None:
                try:
                    sanitized[field] = float(sanitized[field])
                except (ValueError, TypeError):
                    sanitized[field] = None
        
        return sanitized

class ValidationResult:
    """Container for validation results"""
    
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a warning message"""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }
    
    def __str__(self) -> str:
        """String representation"""
        status = "VALID" if self.is_valid else "INVALID"
        result = f"Validation Result: {status}\n"
        
        if self.errors:
            result += f"Errors ({len(self.errors)}):\n"
            for error in self.errors:
                result += f"  - {error}\n"
        
        if self.warnings:
            result += f"Warnings ({len(self.warnings)}):\n"
            for warning in self.warnings:
                result += f"  - {warning}\n"
        
        return result

def validate_patient_data(data):
    return HealthcareValidators.validate_patient_data(data)

def validate_vital_signs(data):
    return HealthcareValidators.validate_vital_signs(data)

def validate_medical_record(data):
    return HealthcareValidators.validate_medical_record(data)

def validate_appointment(data):
    return HealthcareValidators.validate_appointment(data)

def validate_alert(data):
    return HealthcareValidators.validate_alert(data)

def validate_treatment(data):
    return HealthcareValidators.validate_treatment(data)

def validate_doctor_data(data):
    return HealthcareValidators.validate_doctor_data(data)

def validate_chatbot_message(data: Dict[str, Any]) -> ValidationResult:
    """Validate chatbot message data"""
    errors = []
    warnings = []
    
    # Check required fields
    if not data.get('message'):
        errors.append("Message content is required")
    
    if data.get('message') and len(data['message']) > 1000:
        errors.append("Message content cannot exceed 1000 characters")
    
    # Validate session_id if provided
    session_id = data.get('session_id')
    if session_id and not isinstance(session_id, str):
        errors.append("Session ID must be a string")
    
    # Validate user_id if provided
    user_id = data.get('user_id')
    if user_id and not isinstance(user_id, str):
        errors.append("User ID must be a string")
    
    # Validate patient_id if provided
    patient_id = data.get('patient_id')
    if patient_id and not isinstance(patient_id, str):
        errors.append("Patient ID must be a string")
    
    # Check for potential security issues
    message = data.get('message', '')
    if any(keyword in message.lower() for keyword in ['<script', 'javascript:', 'onload=']):
        warnings.append("Message contains potentially unsafe content")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )
