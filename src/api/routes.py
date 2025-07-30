"""
API Routes Module

This module defines all API endpoints for the healthcare management system,
including patient management, monitoring, alerts, and agent interactions.
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from database.connection import get_db_session
from database.models import (
    Patient, MedicalRecord, Appointment, VitalSigns, Alert, 
    Treatment, TriageAssessment, EmergencyResponse
)
from utils.validators import (
    validate_patient_data, validate_vital_signs, validate_appointment,
    validate_medical_record, validate_alert, validate_treatment
)
from utils.logger import log_api_event, log_patient_event, log_agent_event

# Create API blueprint
api_bp = Blueprint('api', __name__)

def get_request_data() -> Dict[str, Any]:
    """Get request data with error handling"""
    try:
        if request.is_json:
            return request.get_json()
        elif request.form:
            return dict(request.form)
        else:
            return {}
    except Exception as e:
        return {"error": f"Invalid request data: {str(e)}"}

def create_response(success: bool, data: Any = None, message: str = "", status_code: int = 200) -> tuple:
    """Create standardized API response"""
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    return jsonify(response), status_code

# Health and System Endpoints
@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    start_time = time.time()
    
    try:
        # Check database connection
        with get_db_session() as session:
            session.execute("SELECT 1")
        
        duration = time.time() - start_time
        log_api_event('/health', 'GET', 200, duration)
        
        return create_response(True, {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }, "System is healthy")
        
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/health', 'GET', 500, duration)
        return create_response(False, message=f"Health check failed: {str(e)}", status_code=500)

@api_bp.route('/system/info', methods=['GET'])
def system_info():
    """Get system information"""
    start_time = time.time()
    
    try:
        info = {
            "service": "Healthcare Management System",
            "version": "1.0.0",
            "agents": list(current_app.config.get('AGENTS', {}).keys()),
            "tools": list(current_app.config.get('TOOLS', {}).keys()),
            "database_tables": [
                "patients", "medical_records", "appointments", "vital_signs",
                "alerts", "treatments", "triage_assessments", "emergency_responses"
            ]
        }
        
        duration = time.time() - start_time
        log_api_event('/system/info', 'GET', 200, duration)
        
        return create_response(True, info, "System information retrieved")
        
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/system/info', 'GET', 500, duration)
        return create_response(False, message=f"Failed to get system info: {str(e)}", status_code=500)

# Patient Management Endpoints
@api_bp.route('/patients', methods=['GET'])
def get_patients():
    """Get patients with optional search and pagination"""
    start_time = time.time()
    
    try:
        search = request.args.get('search')
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        
        with get_db_session() as session:
            query = session.query(Patient)
            
            if search:
                search_filter = or_(
                    Patient.first_name.ilike(f"%{search}%"),
                    Patient.last_name.ilike(f"%{search}%"),
                    Patient.contact_number.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
            
            total_count = query.count()
            patients = query.offset(offset).limit(limit).all()
            
            patient_data = []
            for patient in patients:
                patient_data.append({
                    "id": patient.id,
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "date_of_birth": patient.date_of_birth.isoformat(),
                    "gender": patient.gender,
                    "contact_number": patient.contact_number,
                    "email": patient.email,
                    "created_at": patient.created_at.isoformat()
                })
            
            duration = time.time() - start_time
            log_api_event('/patients', 'GET', 200, duration)
            
            return create_response(True, {
                "patients": patient_data,
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }, "Patients retrieved successfully")
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/patients', 'GET', 500, duration)
        return create_response(False, message=f"Failed to retrieve patients: {str(e)}", status_code=500)

@api_bp.route('/patients', methods=['POST'])
def create_patient():
    """Create a new patient"""
    start_time = time.time()
    
    try:
        data = get_request_data()
        
        # Validate patient data
        validation_result = validate_patient_data(data)
        if not validation_result["valid"]:
            return create_response(False, message=validation_result["errors"], status_code=400)
        
        with get_db_session() as session:
            # Create new patient
            new_patient = Patient(
                first_name=data['first_name'],
                last_name=data['last_name'],
                date_of_birth=datetime.fromisoformat(data['date_of_birth']),
                gender=data['gender'],
                contact_number=data['contact_number'],
                email=data.get('email'),
                address=data.get('address'),
                emergency_contact=data.get('emergency_contact'),
                insurance_info=data.get('insurance_info')
            )
            
            session.add(new_patient)
            session.commit()
            session.refresh(new_patient)
            
            duration = time.time() - start_time
            log_patient_event(new_patient.id, "created", "Patient created successfully")
            log_api_event('/patients', 'POST', 201, duration)
            
            return create_response(True, {
                "id": new_patient.id,
                "first_name": new_patient.first_name,
                "last_name": new_patient.last_name,
                "created_at": new_patient.created_at.isoformat()
            }, "Patient created successfully", 201)
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/patients', 'POST', 500, duration)
        return create_response(False, message=f"Failed to create patient: {str(e)}", status_code=500)

@api_bp.route('/patients/<patient_id>', methods=['GET'])
def get_patient(patient_id: str):
    """Get a specific patient by ID"""
    start_time = time.time()
    
    try:
        with get_db_session() as session:
            patient = session.query(Patient).filter(Patient.id == patient_id).first()
            
            if not patient:
                return create_response(False, message="Patient not found", status_code=404)
            
            patient_data = {
                "id": patient.id,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "date_of_birth": patient.date_of_birth.isoformat(),
                "gender": patient.gender,
                "contact_number": patient.contact_number,
                "email": patient.email,
                "address": patient.address,
                "emergency_contact": patient.emergency_contact,
                "insurance_info": patient.insurance_info,
                "created_at": patient.created_at.isoformat(),
                "updated_at": patient.updated_at.isoformat() if patient.updated_at else None
            }
            
            duration = time.time() - start_time
            log_api_event(f'/patients/{patient_id}', 'GET', 200, duration)
            
            return create_response(True, patient_data, "Patient retrieved successfully")
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event(f'/patients/{patient_id}', 'GET', 500, duration)
        return create_response(False, message=f"Failed to retrieve patient: {str(e)}", status_code=500)

@api_bp.route('/patients/<patient_id>', methods=['PUT'])
def update_patient(patient_id: str):
    """Update a patient's information"""
    start_time = time.time()
    
    try:
        data = get_request_data()
        
        with get_db_session() as session:
            patient = session.query(Patient).filter(Patient.id == patient_id).first()
            
            if not patient:
                return create_response(False, message="Patient not found", status_code=404)
            
            # Update fields if provided
            for field, value in data.items():
                if hasattr(patient, field):
                    setattr(patient, field, value)
            
            patient.updated_at = datetime.utcnow()
            session.commit()
            
            duration = time.time() - start_time
            log_patient_event(patient_id, "updated", "Patient information updated")
            log_api_event(f'/patients/{patient_id}', 'PUT', 200, duration)
            
            return create_response(True, {"id": patient.id}, "Patient updated successfully")
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event(f'/patients/{patient_id}', 'PUT', 500, duration)
        return create_response(False, message=f"Failed to update patient: {str(e)}", status_code=500)

# Vital Signs Endpoints
@api_bp.route('/vital-signs', methods=['POST'])
def submit_vital_signs():
    """Submit vital signs for a patient"""
    start_time = time.time()
    
    try:
        data = get_request_data()
        
        # Validate vital signs data
        validation_result = validate_vital_signs(data)
        if not validation_result["valid"]:
            return create_response(False, message=validation_result["errors"], status_code=400)
        
        with get_db_session() as session:
            # Check if patient exists
            patient = session.query(Patient).filter(Patient.id == data['patient_id']).first()
            if not patient:
                return create_response(False, message="Patient not found", status_code=404)
            
            # Create vital signs record
            vital_signs = VitalSigns(
                patient_id=data['patient_id'],
                temperature=data.get('temperature'),
                blood_pressure_systolic=data.get('blood_pressure_systolic'),
                blood_pressure_diastolic=data.get('blood_pressure_diastolic'),
                heart_rate=data.get('heart_rate'),
                respiratory_rate=data.get('respiratory_rate'),
                oxygen_saturation=data.get('oxygen_saturation'),
                notes=data.get('notes')
            )
            
            session.add(vital_signs)
            session.commit()
            session.refresh(vital_signs)
            
            duration = time.time() - start_time
            log_patient_event(data['patient_id'], "vital_signs_submitted", "Vital signs recorded")
            log_api_event('/vital-signs', 'POST', 201, duration)
            
            return create_response(True, {
                "id": vital_signs.id,
                "patient_id": vital_signs.patient_id,
                "recorded_at": vital_signs.recorded_at.isoformat()
            }, "Vital signs recorded successfully", 201)
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/vital-signs', 'POST', 500, duration)
        return create_response(False, message=f"Failed to record vital signs: {str(e)}", status_code=500)

@api_bp.route('/vital-signs/<patient_id>', methods=['GET'])
def get_patient_vital_signs(patient_id: str):
    """Get vital signs history for a patient"""
    start_time = time.time()
    
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        with get_db_session() as session:
            # Check if patient exists
            patient = session.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return create_response(False, message="Patient not found", status_code=404)
            
            # Get vital signs history
            vital_signs = session.query(VitalSigns)\
                .filter(VitalSigns.patient_id == patient_id)\
                .order_by(desc(VitalSigns.recorded_at))\
                .limit(limit)\
                .all()
            
            vital_data = []
            for vital in vital_signs:
                vital_data.append({
                    "id": vital.id,
                    "temperature": vital.temperature,
                    "blood_pressure_systolic": vital.blood_pressure_systolic,
                    "blood_pressure_diastolic": vital.blood_pressure_diastolic,
                    "heart_rate": vital.heart_rate,
                    "respiratory_rate": vital.respiratory_rate,
                    "oxygen_saturation": vital.oxygen_saturation,
                    "notes": vital.notes,
                    "recorded_at": vital.recorded_at.isoformat()
                })
            
            duration = time.time() - start_time
            log_api_event(f'/vital-signs/{patient_id}', 'GET', 200, duration)
            
            return create_response(True, {
                "patient_id": patient_id,
                "vital_signs": vital_data,
                "total_count": len(vital_data)
            }, "Vital signs retrieved successfully")
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event(f'/vital-signs/{patient_id}', 'GET', 500, duration)
        return create_response(False, message=f"Failed to retrieve vital signs: {str(e)}", status_code=500)

# Alert Endpoints
@api_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get alerts with optional filtering"""
    start_time = time.time()
    
    try:
        status_filter = request.args.get('status')
        severity_filter = request.args.get('severity')
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        with get_db_session() as session:
            query = session.query(Alert)
            
            if status_filter:
                query = query.filter(Alert.status == status_filter)
            if severity_filter:
                query = query.filter(Alert.severity == severity_filter)
            
            alerts = query.order_by(desc(Alert.created_at)).limit(limit).all()
            
            alert_data = []
            for alert in alerts:
                alert_data.append({
                    "id": alert.id,
                    "patient_id": alert.patient_id,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "status": alert.status,
                    "source": alert.source,
                    "created_at": alert.created_at.isoformat(),
                    "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
                })
            
            duration = time.time() - start_time
            log_api_event('/alerts', 'GET', 200, duration)
            
            return create_response(True, {
                "alerts": alert_data,
                "total_count": len(alert_data)
            }, "Alerts retrieved successfully")
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/alerts', 'GET', 500, duration)
        return create_response(False, message=f"Failed to retrieve alerts: {str(e)}", status_code=500)

@api_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    start_time = time.time()
    
    try:
        with get_db_session() as session:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            
            if not alert:
                return create_response(False, message="Alert not found", status_code=404)
            
            if alert.status == "acknowledged":
                return create_response(False, message="Alert already acknowledged", status_code=400)
            
            alert.status = "acknowledged"
            alert.acknowledged_at = datetime.utcnow()
            session.commit()
            
            duration = time.time() - start_time
            log_api_event(f'/alerts/{alert_id}/acknowledge', 'POST', 200, duration)
            
            return create_response(True, {"id": alert.id}, "Alert acknowledged successfully")
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event(f'/alerts/{alert_id}/acknowledge', 'POST', 500, duration)
        return create_response(False, message=f"Failed to acknowledge alert: {str(e)}", status_code=500)

# Agent Endpoints
@api_bp.route('/agents/triage', methods=['POST'])
def triage_patient():
    """Process patient triage using AI agent"""
    start_time = time.time()
    
    try:
        data = get_request_data()
        
        # Get triage agent
        agents = current_app.config.get('AGENTS', {})
        triage_agent = agents.get('triage')
        
        if not triage_agent:
            return create_response(False, message="Triage agent not available", status_code=503)
        
        # Process triage
        triage_result = triage_agent.process_triage(
            patient_id=data['patient_id'],
            symptoms=data.get('symptoms', []),
            vital_signs=data.get('vital_signs'),
            chief_complaint=data['chief_complaint'],
            pain_level=data.get('pain_level')
        )
        
        with get_db_session() as session:
            # Save triage assessment
            assessment = TriageAssessment(
                patient_id=data['patient_id'],
                severity=triage_result.get('severity', 'medium'),
                priority=triage_result.get('priority', 'normal'),
                estimated_wait_time=triage_result.get('estimated_wait_time', 30),
                recommendations=triage_result.get('recommendations', []),
                notes=triage_result.get('notes', '')
            )
            
            session.add(assessment)
            session.commit()
            
            duration = time.time() - start_time
            log_agent_event('triage', data['patient_id'], "Triage assessment completed")
            log_api_event('/agents/triage', 'POST', 200, duration)
            
            return create_response(True, triage_result, "Triage assessment completed successfully")
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/agents/triage', 'POST', 500, duration)
        return create_response(False, message=f"Triage processing failed: {str(e)}", status_code=500)

@api_bp.route('/agents/emergency', methods=['POST'])
def emergency_response():
    """Process emergency response using AI agent"""
    start_time = time.time()
    
    try:
        data = get_request_data()
        
        # Get emergency agent
        agents = current_app.config.get('AGENTS', {})
        emergency_agent = agents.get('emergency')
        
        if not emergency_agent:
            return create_response(False, message="Emergency agent not available", status_code=503)
        
        # Process emergency
        emergency_result = emergency_agent.process_emergency(
            patient_id=data['patient_id'],
            emergency_type=data['emergency_type'],
            severity=data['severity'],
            location=data['location'],
            description=data['description']
        )
        
        with get_db_session() as session:
            # Save emergency response
            response = EmergencyResponse(
                patient_id=data['patient_id'],
                emergency_type=data['emergency_type'],
                severity=data['severity'],
                location=data['location'],
                description=data['description'],
                response_time=emergency_result.get('response_time', 0),
                actions_taken=emergency_result.get('actions_taken', []),
                status=emergency_result.get('status', 'active')
            )
            
            session.add(response)
            session.commit()
            
            duration = time.time() - start_time
            log_agent_event('emergency', data['patient_id'], "Emergency response initiated")
            log_api_event('/agents/emergency', 'POST', 200, duration)
            
            return create_response(True, emergency_result, "Emergency response initiated successfully")
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/agents/emergency', 'POST', 500, duration)
        return create_response(False, message=f"Emergency processing failed: {str(e)}", status_code=500)

# Appointment Endpoints
@api_bp.route('/appointments', methods=['GET'])
def get_appointments():
    """Get appointments with optional filtering"""
    start_time = time.time()
    
    try:
        patient_id = request.args.get('patient_id')
        doctor_id = request.args.get('doctor_id')
        date = request.args.get('date')
        
        with get_db_session() as session:
            query = session.query(Appointment)
            
            if patient_id:
                query = query.filter(Appointment.patient_id == patient_id)
            if doctor_id:
                query = query.filter(Appointment.doctor_id == doctor_id)
            if date:
                query = query.filter(Appointment.appointment_date == date)
            
            appointments = query.order_by(Appointment.appointment_date, Appointment.appointment_time).all()
            
            appointment_data = []
            for appointment in appointments:
                appointment_data.append({
                    "id": appointment.id,
                    "patient_id": appointment.patient_id,
                    "doctor_id": appointment.doctor_id,
                    "appointment_date": appointment.appointment_date.isoformat(),
                    "appointment_time": appointment.appointment_time.isoformat(),
                    "reason": appointment.reason,
                    "priority": appointment.priority,
                    "status": appointment.status,
                    "created_at": appointment.created_at.isoformat()
                })
            
            duration = time.time() - start_time
            log_api_event('/appointments', 'GET', 200, duration)
            
            return create_response(True, {
                "appointments": appointment_data,
                "total_count": len(appointment_data)
            }, "Appointments retrieved successfully")
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/appointments', 'GET', 500, duration)
        return create_response(False, message=f"Failed to retrieve appointments: {str(e)}", status_code=500)

@api_bp.route('/appointments', methods=['POST'])
def create_appointment():
    """Create a new appointment"""
    start_time = time.time()
    
    try:
        data = get_request_data()
        
        # Validate appointment data
        validation_result = validate_appointment(data)
        if not validation_result["valid"]:
            return create_response(False, message=validation_result["errors"], status_code=400)
        
        with get_db_session() as session:
            # Check if patient exists
            patient = session.query(Patient).filter(Patient.id == data['patient_id']).first()
            if not patient:
                return create_response(False, message="Patient not found", status_code=404)
            
            # Create appointment
            appointment = Appointment(
                patient_id=data['patient_id'],
                doctor_id=data['doctor_id'],
                appointment_date=datetime.fromisoformat(data['appointment_date']),
                appointment_time=datetime.fromisoformat(data['appointment_time']),
                reason=data['reason'],
                priority=data['priority']
            )
            
            session.add(appointment)
            session.commit()
            session.refresh(appointment)
            
            duration = time.time() - start_time
            log_patient_event(data['patient_id'], "appointment_created", "Appointment scheduled")
            log_api_event('/appointments', 'POST', 201, duration)
            
            return create_response(True, {
                "id": appointment.id,
                "patient_id": appointment.patient_id,
                "appointment_date": appointment.appointment_date.isoformat()
            }, "Appointment created successfully", 201)
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/appointments', 'POST', 500, duration)
        return create_response(False, message=f"Failed to create appointment: {str(e)}", status_code=500)

# Medical Records Endpoints
@api_bp.route('/medical-records/<patient_id>', methods=['GET'])
def get_medical_records(patient_id: str):
    """Get medical records for a patient"""
    start_time = time.time()
    
    try:
        record_type = request.args.get('record_type')
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        with get_db_session() as session:
            # Check if patient exists
            patient = session.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return create_response(False, message="Patient not found", status_code=404)
            
            query = session.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id)
            
            if record_type:
                query = query.filter(MedicalRecord.record_type == record_type)
            
            records = query.order_by(desc(MedicalRecord.date_recorded)).limit(limit).all()
            
            record_data = []
            for record in records:
                record_data.append({
                    "id": record.id,
                    "record_type": record.record_type,
                    "content": record.content,
                    "doctor_id": record.doctor_id,
                    "date_recorded": record.date_recorded.isoformat(),
                    "created_at": record.created_at.isoformat()
                })
            
            duration = time.time() - start_time
            log_api_event(f'/medical-records/{patient_id}', 'GET', 200, duration)
            
            return create_response(True, {
                "patient_id": patient_id,
                "records": record_data,
                "total_count": len(record_data)
            }, "Medical records retrieved successfully")
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event(f'/medical-records/{patient_id}', 'GET', 500, duration)
        return create_response(False, message=f"Failed to retrieve medical records: {str(e)}", status_code=500)

@api_bp.route('/medical-records', methods=['POST'])
def create_medical_record():
    """Create a new medical record"""
    start_time = time.time()
    
    try:
        data = get_request_data()
        
        # Validate medical record data
        validation_result = validate_medical_record(data)
        if not validation_result["valid"]:
            return create_response(False, message=validation_result["errors"], status_code=400)
        
        with get_db_session() as session:
            # Check if patient exists
            patient = session.query(Patient).filter(Patient.id == data['patient_id']).first()
            if not patient:
                return create_response(False, message="Patient not found", status_code=404)
            
            # Create medical record
            record = MedicalRecord(
                patient_id=data['patient_id'],
                record_type=data['record_type'],
                content=data['content'],
                doctor_id=data['doctor_id'],
                date_recorded=datetime.fromisoformat(data['date_recorded'])
            )
            
            session.add(record)
            session.commit()
            session.refresh(record)
            
            duration = time.time() - start_time
            log_patient_event(data['patient_id'], "medical_record_created", "Medical record added")
            log_api_event('/medical-records', 'POST', 201, duration)
            
            return create_response(True, {
                "id": record.id,
                "patient_id": record.patient_id,
                "record_type": record.record_type,
                "date_recorded": record.date_recorded.isoformat()
            }, "Medical record created successfully", 201)
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/medical-records', 'POST', 500, duration)
        return create_response(False, message=f"Failed to create medical record: {str(e)}", status_code=500)