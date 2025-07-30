"""
Database Models for Healthcare Management System - MySQL Compatible

This module defines SQLAlchemy models for all healthcare-related entities
including patients, medical records, appointments, and monitoring data.
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Float, Boolean, 
    Text, ForeignKey, Enum, JSON, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import uuid
import enum

Base = declarative_base()

class TriageLevel(enum.Enum):
    """Triage levels for patient assessment"""
    IMMEDIATE = "1"
    EMERGENT = "2"
    URGENT = "3"
    LESS_URGENT = "4"
    NON_URGENT = "5"

class PatientStatus(enum.Enum):
    """Patient status enumeration"""
    ADMITTED = "admitted"
    DISCHARGED = "discharged"
    TRANSFERRED = "transferred"
    DECEASED = "deceased"
    PENDING = "pending"

class AppointmentStatus(enum.Enum):
    """Appointment status enumeration"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class AlertSeverity(enum.Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Patient(Base):
    """Patient information model"""
    __tablename__ = 'patients'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mrn = Column(String(50), unique=True, nullable=False, index=True)  # Medical Record Number
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    emergency_contact = Column(JSON)
    insurance_info = Column(JSON)
    allergies = Column(JSON)
    medications = Column(JSON)
    medical_history = Column(JSON)
    status = Column(Enum(PatientStatus), default=PatientStatus.PENDING)
    admission_date = Column(DateTime)
    discharge_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    medical_records = relationship("MedicalRecord", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    vital_signs = relationship("VitalSigns", back_populates="patient", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="patient", cascade="all, delete-orphan")
    treatments = relationship("Treatment", back_populates="patient", cascade="all, delete-orphan")
    triage_assessments = relationship("TriageAssessment", back_populates="patient", cascade="all, delete-orphan")
    emergency_responses = relationship("EmergencyResponse", back_populates="patient", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Patient(id={self.id}, mrn={self.mrn}, name={self.first_name} {self.last_name})>"

class MedicalRecord(Base):
    """Medical records model"""
    __tablename__ = 'medical_records'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey('patients.id'), nullable=False)
    record_type = Column(String(50), nullable=False)  # diagnosis, treatment, lab_result, etc.
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    doctor_id = Column(String(50))  # Doctor's ID or name
    department = Column(String(100))
    diagnosis_codes = Column(JSON)  # ICD-10 codes
    medications = Column(JSON)
    procedures = Column(JSON)
    attachments = Column(JSON)  # File attachments
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="medical_records")
    
    def __repr__(self):
        return f"<MedicalRecord(id={self.id}, patient_id={self.patient_id}, type={self.record_type})>"

class Appointment(Base):
    """Appointment scheduling model"""
    __tablename__ = 'appointments'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey('patients.id'), nullable=False)
    doctor_id = Column(String(50), nullable=False)
    department = Column(String(100))
    appointment_type = Column(String(50))  # consultation, follow_up, procedure, etc.
    scheduled_date = Column(DateTime, nullable=False)
    duration = Column(Integer)  # Duration in minutes
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    notes = Column(Text)
    room_number = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, patient_id={self.patient_id}, date={self.scheduled_date})>"

class VitalSigns(Base):
    """Patient vital signs monitoring model"""
    __tablename__ = 'vital_signs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey('patients.id'), nullable=False)
    heart_rate = Column(Float)
    systolic_bp = Column(Float)
    diastolic_bp = Column(Float)
    temperature = Column(Float)
    oxygen_saturation = Column(Float)
    respiratory_rate = Column(Float)
    blood_glucose = Column(Float)
    pain_level = Column(Integer)  # 0-10 scale
    recorded_at = Column(DateTime, default=datetime.utcnow)
    device_id = Column(String(50))  # Monitoring device ID
    notes = Column(Text)
    
    # Relationships
    patient = relationship("Patient", back_populates="vital_signs")
    triage_assessments = relationship("TriageAssessment", back_populates="vital_signs")
    
    def __repr__(self):
        return f"<VitalSigns(id={self.id}, patient_id={self.patient_id}, recorded_at={self.recorded_at})>"

class Alert(Base):
    """Alert system model"""
    __tablename__ = 'alerts'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey('patients.id'), nullable=False)
    alert_type = Column(String(50), nullable=False)  # vital_signs, medication, fall, etc.
    severity = Column(Enum(AlertSeverity), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    source = Column(String(100))  # monitoring_system, manual, ai_agent, etc.
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(50))
    acknowledged_at = Column(DateTime)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, patient_id={self.patient_id}, type={self.alert_type}, severity={self.severity})>"

class Treatment(Base):
    """Treatment plan model"""
    __tablename__ = 'treatments'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey('patients.id'), nullable=False)
    treatment_type = Column(String(100), nullable=False)
    diagnosis = Column(Text)
    treatment_plan = Column(Text, nullable=False)
    medications = Column(JSON)
    procedures = Column(JSON)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    status = Column(String(50), default='active')  # active, completed, discontinued
    doctor_id = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="treatments")
    
    def __repr__(self):
        return f"<Treatment(id={self.id}, patient_id={self.patient_id}, type={self.treatment_type})>"

class TriageAssessment(Base):
    """Triage assessment model"""
    __tablename__ = 'triage_assessments'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey('patients.id'), nullable=False)
    triage_level = Column(Enum(TriageLevel), nullable=False)
    chief_complaint = Column(Text, nullable=False)
    symptoms = Column(JSON)
    vital_signs_id = Column(String(36), ForeignKey('vital_signs.id'))
    assessment_notes = Column(Text)
    assigned_doctor = Column(String(50))
    wait_time_estimate = Column(Integer)  # Estimated wait time in minutes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="triage_assessments")
    vital_signs = relationship("VitalSigns", back_populates="triage_assessments")
    
    def __repr__(self):
        return f"<TriageAssessment(id={self.id}, patient_id={self.patient_id}, level={self.triage_level})>"

class EmergencyResponse(Base):
    """Emergency response tracking model"""
    __tablename__ = 'emergency_responses'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey('patients.id'), nullable=False)
    emergency_type = Column(String(100), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    description = Column(Text, nullable=False)
    response_team = Column(JSON)  # Team members assigned
    response_time = Column(Integer)  # Response time in seconds
    actions_taken = Column(JSON)
    outcome = Column(String(100))
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="emergency_responses")
    
    def __repr__(self):
        return f"<EmergencyResponse(id={self.id}, patient_id={self.patient_id}, type={self.emergency_type})>"

class ChatbotConversation(Base):
    """Chatbot conversation model for context keeping"""
    __tablename__ = 'chatbot_conversations'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(50))  # Optional user identification
    patient_id = Column(String(36), ForeignKey('patients.id'))  # Optional patient context
    conversation_type = Column(String(50), default='general')  # general, triage, emergency, etc.
    status = Column(String(20), default='active')  # active, closed, archived
    message_count = Column(Integer, default=0)  # Number of messages in conversation
    context_data = Column(JSON)  # Store conversation context
    conversation_metadata = Column(JSON)  # Additional metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime)
    
    # Relationships
    patient = relationship("Patient")
    messages = relationship("ChatbotMessage", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatbotConversation(id={self.id}, session_id={self.session_id}, type={self.conversation_type})>"

class ChatbotMessage(Base):
    """Individual chatbot message model"""
    __tablename__ = 'chatbot_messages'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey('chatbot_conversations.id'), nullable=False)
    message_type = Column(String(20), nullable=False)  # user, bot, system
    content = Column(Text, nullable=False)
    intent = Column(String(100))  # Detected user intent
    confidence = Column(Float)  # Intent confidence score
    entities = Column(JSON)  # Extracted entities
    context_snapshot = Column(JSON)  # Context at time of message
    response_time = Column(Float)  # Response time in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("ChatbotConversation", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatbotMessage(id={self.id}, type={self.message_type}, conversation_id={self.conversation_id})>"

class ChatbotContext(Base):
    """Persistent context storage for chatbot sessions"""
    __tablename__ = 'chatbot_contexts'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    user_id = Column(String(50))
    patient_id = Column(String(36), ForeignKey('patients.id'))
    context_data = Column(JSON, nullable=False)  # Main context storage
    conversation_history = Column(JSON)  # Recent conversation summary
    user_preferences = Column(JSON)  # User preferences and settings
    system_state = Column(JSON)  # Current system state
    last_activity = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient")
    
    def __repr__(self):
        return f"<ChatbotContext(id={self.id}, session_id={self.session_id})>"

# Create indexes for better performance
Index('idx_patients_mrn', Patient.mrn)
Index('idx_patients_status', Patient.status)
Index('idx_patients_name', Patient.last_name, Patient.first_name)
Index('idx_medical_records_patient', MedicalRecord.patient_id)
Index('idx_medical_records_type', MedicalRecord.record_type)
Index('idx_appointments_patient', Appointment.patient_id)
Index('idx_appointments_date', Appointment.scheduled_date)
Index('idx_appointments_status', Appointment.status)
Index('idx_appointments_patient_date', Appointment.patient_id, Appointment.scheduled_date)
Index('idx_vital_signs_patient', VitalSigns.patient_id)
Index('idx_vital_signs_recorded', VitalSigns.recorded_at)
Index('idx_vital_signs_patient_date', VitalSigns.patient_id, VitalSigns.recorded_at)
Index('idx_alerts_patient', Alert.patient_id)
Index('idx_alerts_severity', Alert.severity)
Index('idx_alerts_created', Alert.created_at)
Index('idx_alerts_patient_severity', Alert.patient_id, Alert.severity)
Index('idx_treatments_patient', Treatment.patient_id)
Index('idx_treatments_status', Treatment.status)
Index('idx_triage_patient', TriageAssessment.patient_id)
Index('idx_triage_level', TriageAssessment.triage_level)
Index('idx_emergency_patient', EmergencyResponse.patient_id)
Index('idx_emergency_type', EmergencyResponse.emergency_type)   