"""
Data Generator Utility

This module provides utilities for generating synthetic healthcare data
for testing, development, and demonstration purposes.
"""

import random
import json
from datetime import datetime, date, timedelta, UTC
from typing import Dict, List, Any, Optional
from pathlib import Path
import uuid
from faker import Faker

# Initialize Faker for generating realistic data
fake = Faker()

class HealthcareDataGenerator:
    """Generator for synthetic healthcare data"""
    
    def __init__(self):
        self.fake = Faker()
        
        # Medical specialties
        self.specialties = [
            'Cardiology', 'Pulmonology', 'Neurology', 'Orthopedics',
            'Emergency Medicine', 'Internal Medicine', 'Pediatrics',
            'Surgery', 'Radiology', 'Laboratory', 'Pharmacy', 'Nursing'
        ]
        
        # Common conditions
        self.conditions = [
            'Hypertension', 'Diabetes', 'Asthma', 'Heart Disease',
            'Pneumonia', 'Stroke', 'Cancer', 'Arthritis', 'Depression',
            'Anxiety', 'Obesity', 'Chronic Kidney Disease'
        ]
        
        # Common medications
        self.medications = [
            'Aspirin', 'Metformin', 'Lisinopril', 'Atorvastatin',
            'Amlodipine', 'Omeprazole', 'Albuterol', 'Ibuprofen',
            'Acetaminophen', 'Warfarin', 'Insulin', 'Morphine'
        ]
        
        # ICD-10 codes for common conditions
        self.icd_codes = {
            'Hypertension': 'I10',
            'Diabetes': 'E11.9',
            'Asthma': 'J45.909',
            'Heart Disease': 'I25.10',
            'Pneumonia': 'J18.9',
            'Stroke': 'I63.9',
            'Cancer': 'C80.1',
            'Arthritis': 'M15.9',
            'Depression': 'F32.9',
            'Anxiety': 'F41.9',
            'Obesity': 'E66.9',
            'Chronic Kidney Disease': 'N18.9'
        }
    
    def generate_patient(self, patient_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate a synthetic patient record"""
        if patient_id is None:
            patient_id = str(uuid.uuid4())
        
        # Generate realistic age
        age = random.randint(18, 95)
        birth_date = date.today() - timedelta(days=age*365 + random.randint(0, 365))
        
        # Generate contact information
        phone = self.fake.phone_number()
        email = self.fake.email()
        
        # Generate address
        address = {
            'street': self.fake.street_address(),
            'city': self.fake.city(),
            'state': self.fake.state_abbr(),
            'zip_code': self.fake.zipcode(),
            'country': 'USA'
        }
        
        # Generate emergency contact
        emergency_contact = {
            'name': self.fake.name(),
            'relationship': random.choice(['Spouse', 'Child', 'Parent', 'Sibling', 'Friend']),
            'phone': self.fake.phone_number(),
            'email': self.fake.email()
        }
        
        # Generate insurance information
        insurance = {
            'provider': random.choice(['Blue Cross', 'Aetna', 'Cigna', 'UnitedHealth', 'Kaiser']),
            'policy_number': self.fake.ean13(),
            'group_number': self.fake.ean8(),
            'expiry_date': (date.today() + timedelta(days=random.randint(100, 1000))).isoformat()
        }
        
        patient = {
            'id': patient_id,
            'mrn': f"MRN{random.randint(100000, 999999)}",
            'first_name': self.fake.first_name(),
            'last_name': self.fake.last_name(),
            'date_of_birth': birth_date.isoformat(),
            'gender': random.choice(['male', 'female']),
            'age': age,
            'phone': phone,
            'email': email,
            'address': address,
            'emergency_contact': emergency_contact,
            'insurance': insurance,
            'blood_type': random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']),
            'allergies': self._generate_allergies(),
            'medical_history': self._generate_medical_history(),
            'created_at': datetime.now(UTC).isoformat(),
            'updated_at': datetime.now(UTC).isoformat()
        }
        
        return patient
    
    def generate_vital_signs(self, patient_id: str, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate synthetic vital signs"""
        if timestamp is None:
            timestamp = datetime.now(UTC)
        
        # Generate realistic vital signs with some variation
        vital_signs = {
            'id': str(uuid.uuid4()),
            'patient_id': patient_id,
            'heart_rate': random.randint(60, 100),
            'systolic_bp': random.randint(110, 140),
            'diastolic_bp': random.randint(70, 90),
            'temperature': round(random.uniform(97.0, 99.5), 1),
            'oxygen_saturation': random.randint(95, 100),
            'respiratory_rate': random.randint(12, 20),
            'blood_glucose': random.randint(80, 120),
            'pain_level': random.randint(0, 10),
            'recorded_at': timestamp.isoformat(),
            'created_at': datetime.now(UTC).isoformat()
        }
        
        return vital_signs
    
    def generate_medical_record(self, patient_id: str, doctor_id: str, record_type: str = 'consultation') -> Dict[str, Any]:
        """Generate a synthetic medical record"""
        
        # Generate content based on record type
        if record_type == 'diagnosis':
            condition = random.choice(self.conditions)
            content = f"Diagnosis: {condition}. Patient presents with typical symptoms. Recommended treatment plan includes medication and lifestyle modifications."
            diagnosis_codes = [self.icd_codes.get(condition, 'R69')]
        elif record_type == 'treatment':
            medication = random.choice(self.medications)
            content = f"Treatment prescribed: {medication}. Dosage: {random.randint(1, 3)} tablets daily. Follow-up in 2 weeks."
            diagnosis_codes = []
        elif record_type == 'lab_result':
            content = f"Laboratory results reviewed. All values within normal range. No immediate action required."
            diagnosis_codes = []
        else:
            content = f"Patient consultation completed. General health assessment performed. No immediate concerns identified."
            diagnosis_codes = []
        
        medical_record = {
            'id': str(uuid.uuid4()),
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'record_type': record_type,
            'title': f"{record_type.title()} - {datetime.now(UTC).strftime('%Y-%m-%d')}",
            'content': content,
            'department': random.choice(self.specialties),
            'diagnosis_codes': diagnosis_codes,
            'medications': [random.choice(self.medications)] if record_type == 'treatment' else [],
            'created_at': datetime.now(UTC).isoformat(),
            'updated_at': datetime.now(UTC).isoformat()
        }
        
        return medical_record
    
    def generate_appointment(self, patient_id: str, doctor_id: str) -> Dict[str, Any]:
        """Generate a synthetic appointment"""
        
        # Generate appointment date (within next 30 days)
        appointment_date = datetime.now(UTC) + timedelta(days=random.randint(1, 30))
        
        # Generate appointment time (business hours)
        hour = random.randint(9, 17)
        minute = random.choice([0, 15, 30, 45])
        appointment_time = appointment_date.replace(hour=hour, minute=minute)
        
        appointment = {
            'id': str(uuid.uuid4()),
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'department': random.choice(self.specialties),
            'appointment_type': random.choice(['consultation', 'follow_up', 'procedure', 'emergency', 'routine_check']),
            'scheduled_date': appointment_time.isoformat(),
            'duration': random.choice([15, 30, 45, 60]),
            'status': random.choice(['scheduled', 'confirmed', 'completed', 'cancelled']),
            'notes': f"Appointment scheduled for {random.choice(['consultation', 'follow_up', 'procedure', 'emergency', 'routine_check'])}",
            'room_number': f"{random.randint(100, 999)}",
            'created_at': datetime.now(UTC).isoformat(),
            'updated_at': datetime.now(UTC).isoformat()
        }
        
        return appointment
    
    def generate_alert(self, patient_id: str, alert_type: str = 'vital_signs') -> Dict[str, Any]:
        """Generate a synthetic alert"""
        
        alert_types = {
            'vital_signs': {
                'title': 'Abnormal Vital Signs',
                'message': 'Patient vital signs outside normal range. Please review.',
                'severity': random.choice(['low', 'medium', 'high'])
            },
            'medication': {
                'title': 'Medication Alert',
                'message': 'Medication interaction detected. Review required.',
                'severity': random.choice(['medium', 'high'])
            },
            'appointment': {
                'title': 'Appointment Reminder',
                'message': 'Upcoming appointment reminder.',
                'severity': 'low'
            },
            'emergency': {
                'title': 'Emergency Alert',
                'message': 'Emergency situation detected. Immediate attention required.',
                'severity': 'critical'
            }
        }
        
        alert_info = alert_types.get(alert_type, alert_types['vital_signs'])
        
        alert = {
            'id': str(uuid.uuid4()),
            'patient_id': patient_id,
            'alert_type': alert_type,
            'severity': alert_info['severity'],
            'title': alert_info['title'],
            'message': alert_info['message'],
            'source': 'system',
            'is_active': True,
            'created_at': datetime.now(UTC).isoformat(),
            'updated_at': datetime.now(UTC).isoformat()
        }
        
        return alert
    
    def generate_treatment(self, patient_id: str, doctor_id: str) -> Dict[str, Any]:
        """Generate a synthetic treatment record"""
        
        treatment_types = ['medication', 'procedure', 'therapy', 'surgery', 'lifestyle']
        treatment_type = random.choice(treatment_types)
        
        if treatment_type == 'medication':
            medication = random.choice(self.medications)
            description = f"Prescribed {medication} for treatment"
            dosage = f"{random.randint(1, 3)} tablets daily"
        elif treatment_type == 'procedure':
            procedures = ['Blood Test', 'X-Ray', 'MRI', 'CT Scan', 'EKG']
            procedure = random.choice(procedures)
            description = f"Performed {procedure}"
            dosage = "N/A"
        else:
            description = f"{treatment_type.title()} treatment provided"
            dosage = "As prescribed"
        
        treatment = {
            'id': str(uuid.uuid4()),
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'treatment_type': treatment_type,
            'description': description,
            'dosage': dosage,
            'start_date': datetime.now(UTC).isoformat(),
            'end_date': (datetime.now(UTC) + timedelta(days=random.randint(7, 90))).isoformat(),
            'status': random.choice(['active', 'completed', 'discontinued']),
            'notes': f"Treatment notes for {treatment_type}",
            'created_at': datetime.now(UTC).isoformat(),
            'updated_at': datetime.now(UTC).isoformat()
        }
        
        return treatment
    
    def generate_doctor(self, doctor_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate a synthetic doctor record"""
        if doctor_id is None:
            doctor_id = f"DR{random.randint(1000, 9999)}"
        
        doctor = {
            'id': doctor_id,
            'first_name': self.fake.first_name(),
            'last_name': self.fake.last_name(),
            'specialty': random.choice(self.specialties),
            'email': self.fake.email(),
            'phone': self.fake.phone_number(),
            'license_number': f"MD{random.randint(100000, 999999)}",
            'experience_years': random.randint(1, 30),
            'is_active': True,
            'created_at': datetime.now(UTC).isoformat(),
            'updated_at': datetime.now(UTC).isoformat()
        }
        
        return doctor
    
    def generate_synthetic_dataset(self, num_patients: int = 100, num_doctors: int = 20) -> Dict[str, Any]:
        """Generate a complete synthetic dataset"""
        
        dataset = {
            'patients': [],
            'doctors': [],
            'vital_signs': [],
            'medical_records': [],
            'appointments': [],
            'alerts': [],
            'treatments': []
        }
        
        # Generate doctors
        doctor_ids = []
        for i in range(num_doctors):
            doctor = self.generate_doctor()
            dataset['doctors'].append(doctor)
            doctor_ids.append(doctor['id'])
        
        # Generate patients and related data
        for i in range(num_patients):
            patient = self.generate_patient()
            dataset['patients'].append(patient)
            
            # Generate 1-3 vital signs records per patient
            num_vitals = random.randint(1, 3)
            for j in range(num_vitals):
                vital_signs = self.generate_vital_signs(patient['id'])
                dataset['vital_signs'].append(vital_signs)
            
            # Generate 1-5 medical records per patient
            num_records = random.randint(1, 5)
            for j in range(num_records):
                record_type = random.choice(['diagnosis', 'treatment', 'lab_result', 'consultation'])
                doctor_id = random.choice(doctor_ids)
                medical_record = self.generate_medical_record(patient['id'], doctor_id, record_type)
                dataset['medical_records'].append(medical_record)
            
            # Generate 0-3 appointments per patient
            num_appointments = random.randint(0, 3)
            for j in range(num_appointments):
                doctor_id = random.choice(doctor_ids)
                appointment = self.generate_appointment(patient['id'], doctor_id)
                dataset['appointments'].append(appointment)
            
            # Generate 0-2 alerts per patient
            num_alerts = random.randint(0, 2)
            for j in range(num_alerts):
                alert_type = random.choice(['vital_signs', 'medication', 'appointment'])
                alert = self.generate_alert(patient['id'], alert_type)
                dataset['alerts'].append(alert)
            
            # Generate 0-2 treatments per patient
            num_treatments = random.randint(0, 2)
            for j in range(num_treatments):
                doctor_id = random.choice(doctor_ids)
                treatment = self.generate_treatment(patient['id'], doctor_id)
                dataset['treatments'].append(treatment)
        
        return dataset
    
    def _generate_allergies(self) -> List[str]:
        """Generate random allergies"""
        all_allergies = ['Penicillin', 'Peanuts', 'Latex', 'Shellfish', 'Dairy', 'Eggs', 'Sulfa drugs']
        num_allergies = random.randint(0, 2)
        return random.sample(all_allergies, num_allergies)
    
    def _generate_medical_history(self) -> List[str]:
        """Generate random medical history"""
        all_conditions = ['Hypertension', 'Diabetes', 'Asthma', 'Heart Disease', 'None']
        num_conditions = random.randint(0, 2)
        return random.sample(all_conditions, num_conditions)

def save_synthetic_data(dataset: Dict[str, Any], output_file: str) -> None:
    """Save synthetic dataset to JSON file"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(dataset, f, indent=2, default=str)
    
    print(f"Synthetic data saved to {output_file}")

def load_synthetic_data(input_file: str) -> Dict[str, Any]:
    """Load synthetic dataset from JSON file"""
    with open(input_file, 'r') as f:
        return json.load(f)

def generate_sample_data_files() -> None:
    """Generate sample data files for the healthcare system"""
    generator = HealthcareDataGenerator()
    
    # Generate small dataset for testing
    small_dataset = generator.generate_synthetic_dataset(num_patients=50, num_doctors=10)
    save_synthetic_data(small_dataset, "data/synthetic_patients.json")
    
    # Generate medical codes data
    medical_codes = {
        "icd10": generator.icd_codes,
        "cpt": {
            "99213": "Office/outpatient visit established patient, 20-29 minutes",
            "99214": "Office/outpatient visit established patient, 30-39 minutes",
            "99215": "Office/outpatient visit established patient, 40-54 minutes",
            "99203": "Office/outpatient visit new patient, 30-44 minutes",
            "99204": "Office/outpatient visit new patient, 45-59 minutes",
            "99205": "Office/outpatient visit new patient, 60-74 minutes"
        }
    }
    save_synthetic_data(medical_codes, "data/medical_codes.json")
    
    # Generate medications data
    medications_data = {
        "interactions": {
            "warfarin": ["aspirin", "ibuprofen", "heparin"],
            "aspirin": ["warfarin", "ibuprofen", "heparin"],
            "ibuprofen": ["warfarin", "aspirin"],
            "heparin": ["warfarin", "aspirin"],
            "metformin": ["insulin", "glipizide"],
            "insulin": ["metformin", "glipizide"],
            "glipizide": ["metformin", "insulin"]
        },
        "contraindications": {
            "warfarin": ["pregnancy", "bleeding_disorders"],
            "aspirin": ["bleeding_disorders", "stomach_ulcers"],
            "ibuprofen": ["kidney_disease", "stomach_ulcers"],
            "metformin": ["kidney_disease", "heart_failure"],
            "insulin": ["hypoglycemia"]
        }
    }
    save_synthetic_data(medications_data, "data/medications.json")
    
    print("Sample data files generated successfully!")

if __name__ == "__main__":
    generate_sample_data_files()
