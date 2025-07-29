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
    """Get all patients with optional filtering"""
    start_time = time.time()
    
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')
        search = request.args.get('search')
        
        with get_db_session() as session:
            query = session.query(Patient)
            
            # Apply filters
            if status:
                query = query.filter(Patient.status == status)
            
            if search:
                search_filter = or_(
                    Patient.first_name.ilike(f'%{search}%'),
                    Patient.last_name.ilike(f'%{search}%'),
                    Patient.mrn.ilike(f'%{search}%')
                )
                query = query.filter(search_filter)
            
            # Pagination
            total = query.count()
            patients = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Convert to dict
            patient_data = []
            for patient in patients:
                patient_data.append({
                    "id": str(patient.id),
                    "mrn": patient.mrn,
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "date_of_birth": patient.date_of_birth.isoformat(),
                    "gender": patient.gender,
                    "status": patient.status.value,
                    "admission_date": patient.admission_date.isoformat() if patient.admission_date else None,
                    "created_at": patient.created_at.isoformat()
                })
            
            response_data = {
                "patients": patient_data,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page
                }
            }
            
            duration = time.time() - start_time
            log_api_event('/patients', 'GET', 200, duration)
            
            return create_response(True, response_data, f"Retrieved {len(patient_data)} patients")
            
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
        validation = validate_patient_data(data)
        if not validation.is_valid:
            duration = time.time() - start_time
            log_api_event('/patients', 'POST', 400, duration)
            return create_response(False, {
                "errors": validation.errors,
                "warnings": validation.warnings
            }, "Patient data validation failed", 400)
        
        with get_db_session() as session:
            # Check if MRN already exists
            existing_patient = session.query(Patient).filter(Patient.mrn == data['mrn']).first()
            if existing_patient:
                duration = time.time() - start_time
                log_api_event('/patients', 'POST', 409, duration)
                return create_response(False, message="Patient with this MRN already exists", status_code=409)
            
            # Create new patient
            patient = Patient(**data)
            session.add(patient)
            session.commit()
            session.refresh(patient)
            
            patient_data = {
                "id": str(patient.id),
                "mrn": patient.mrn,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "status": patient.status.value,
                "created_at": patient.created_at.isoformat()
            }
            
            duration = time.time() - start_time
            log_api_event('/patients', 'POST', 201, duration)
            log_patient_event(str(patient.id), "created", f"Patient {patient.mrn} created")
            
            return create_response(True, patient_data, "Patient created successfully", 201)
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/patients', 'POST', 500, duration)
        return create_response(False, message=f"Failed to create patient: {str(e)}", status_code=500)

@api_bp.route('/patients/<patient_id>', methods=['GET'])
def get_patient(patient_id: str):
    """Get patient by ID"""
    start_time = time.time()
    
    try:
        with get_db_session() as session:
            patient = session.query(Patient).filter(Patient.id == patient_id).first()
            
            if not patient:
                duration = time.time() - start_time
                log_api_event(f'/patients/{patient_id}', 'GET', 404, duration)
                return create_response(False, message="Patient not found", status_code=404)
            
            # Get related data
            vital_signs = session.query(VitalSigns).filter(VitalSigns.patient_id == patient_id).order_by(desc(VitalSigns.recorded_at)).limit(5).all()
            appointments = session.query(Appointment).filter(Appointment.patient_id == patient_id).order_by(desc(Appointment.scheduled_date)).limit(5).all()
            alerts = session.query(Alert).filter(and_(Alert.patient_id == patient_id, Alert.resolved == False)).all()
            
            patient_data = {
                "id": str(patient.id),
                "mrn": patient.mrn,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "date_of_birth": patient.date_of_birth.isoformat(),
                "gender": patient.gender,
                "phone": patient.phone,
                "email": patient.email,
                "address": patient.address,
                "emergency_contact": patient.emergency_contact,
                "insurance_info": patient.insurance_info,
                "allergies": patient.allergies,
                "medications": patient.medications,
                "medical_history": patient.medical_history,
                "status": patient.status.value,
                "admission_date": patient.admission_date.isoformat() if patient.admission_date else None,
                "discharge_date": patient.discharge_date.isoformat() if patient.discharge_date else None,
                "created_at": patient.created_at.isoformat(),
                "recent_vital_signs": [
                    {
                        "id": str(vs.id),
                        "heart_rate": vs.heart_rate,
                        "systolic_bp": vs.systolic_bp,
                        "diastolic_bp": vs.diastolic_bp,
                        "temperature": vs.temperature,
                        "oxygen_saturation": vs.oxygen_saturation,
                        "recorded_at": vs.recorded_at.isoformat()
                    } for vs in vital_signs
                ],
                "recent_appointments": [
                    {
                        "id": str(apt.id),
                        "doctor_id": apt.doctor_id,
                        "department": apt.department,
                        "appointment_type": apt.appointment_type,
                        "scheduled_date": apt.scheduled_date.isoformat(),
                        "status": apt.status.value
                    } for apt in appointments
                ],
                "active_alerts": [
                    {
                        "id": str(alert.id),
                        "alert_type": alert.alert_type,
                        "severity": alert.severity.value,
                        "title": alert.title,
                        "message": alert.message,
                        "created_at": alert.created_at.isoformat()
                    } for alert in alerts
                ]
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
    """Update patient information"""
    start_time = time.time()
    
    try:
        data = get_request_data()
        
        with get_db_session() as session:
            patient = session.query(Patient).filter(Patient.id == patient_id).first()
            
            if not patient:
                duration = time.time() - start_time
                log_api_event(f'/patients/{patient_id}', 'PUT', 404, duration)
                return create_response(False, message="Patient not found", status_code=404)
            
            # Update patient fields
            for field, value in data.items():
                if hasattr(patient, field):
                    setattr(patient, field, value)
            
            session.commit()
            session.refresh(patient)
            
            duration = time.time() - start_time
            log_api_event(f'/patients/{patient_id}', 'PUT', 200, duration)
            log_patient_event(patient_id, "updated", f"Patient {patient.mrn} updated")
            
            return create_response(True, message="Patient updated successfully")
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event(f'/patients/{patient_id}', 'PUT', 500, duration)
        return create_response(False, message=f"Failed to update patient: {str(e)}", status_code=500)

# Vital Signs Endpoints
@api_bp.route('/vital-signs', methods=['POST'])
def submit_vital_signs():
    """Submit patient vital signs"""
    start_time = time.time()
    
    try:
        data = get_request_data()
        
        # Validate vital signs data
        validation = validate_vital_signs(data)
        if not validation.is_valid:
            duration = time.time() - start_time
            log_api_event('/vital-signs', 'POST', 400, duration)
            return create_response(False, {
                "errors": validation.errors,
                "warnings": validation.warnings
            }, "Vital signs validation failed", 400)
        
        with get_db_session() as session:
            # Create vital signs record
            vital_signs = VitalSigns(**data)
            session.add(vital_signs)
            session.commit()
            session.refresh(vital_signs)
            
            # Check for abnormal values and create alerts
            alerts_created = []
            if vital_signs.heart_rate and (vital_signs.heart_rate < 60 or vital_signs.heart_rate > 100):
                alert = Alert(
                    patient_id=data['patient_id'],
                    alert_type='vital_signs',
                    severity='medium' if 50 <= vital_signs.heart_rate <= 110 else 'high',
                    title='Abnormal Heart Rate',
                    message=f'Patient heart rate is {vital_signs.heart_rate} bpm',
                    source='monitoring_system'
                )
                session.add(alert)
                alerts_created.append('heart_rate')
            
            if vital_signs.systolic_bp and (vital_signs.systolic_bp < 90 or vital_signs.systolic_bp > 140):
                alert = Alert(
                    patient_id=data['patient_id'],
                    alert_type='vital_signs',
                    severity='medium' if 80 <= vital_signs.systolic_bp <= 160 else 'high',
                    title='Abnormal Blood Pressure',
                    message=f'Patient systolic BP is {vital_signs.systolic_bp} mmHg',
                    source='monitoring_system'
                )
                session.add(alert)
                alerts_created.append('blood_pressure')
            
            if vital_signs.temperature and (vital_signs.temperature < 97.0 or vital_signs.temperature > 99.5):
                alert = Alert(
                    patient_id=data['patient_id'],
                    alert_type='vital_signs',
                    severity='medium' if 96.0 <= vital_signs.temperature <= 100.5 else 'high',
                    title='Abnormal Temperature',
                    message=f'Patient temperature is {vital_signs.temperature}°F',
                    source='monitoring_system'
                )
                session.add(alert)
                alerts_created.append('temperature')
            
            session.commit()
            
            response_data = {
                "vital_signs_id": str(vital_signs.id),
                "alerts_created": alerts_created
            }
            
            duration = time.time() - start_time
            log_api_event('/vital-signs', 'POST', 201, duration)
            log_patient_event(data['patient_id'], "vital_signs_submitted", f"Vital signs recorded, {len(alerts_created)} alerts created")
            
            return create_response(True, response_data, "Vital signs submitted successfully", 201)
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/vital-signs', 'POST', 500, duration)
        return create_response(False, message=f"Failed to submit vital signs: {str(e)}", status_code=500)

@api_bp.route('/vital-signs/<patient_id>', methods=['GET'])
def get_patient_vital_signs(patient_id: str):
    """Get patient vital signs history"""
    start_time = time.time()
    
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        with get_db_session() as session:
            vital_signs = session.query(VitalSigns).filter(
                VitalSigns.patient_id == patient_id
            ).order_by(desc(VitalSigns.recorded_at)).limit(limit).all()
            
            vital_data = [
                {
                    "id": str(vs.id),
                    "heart_rate": vs.heart_rate,
                    "systolic_bp": vs.systolic_bp,
                    "diastolic_bp": vs.diastolic_bp,
                    "temperature": vs.temperature,
                    "oxygen_saturation": vs.oxygen_saturation,
                    "respiratory_rate": vs.respiratory_rate,
                    "blood_glucose": vs.blood_glucose,
                    "pain_level": vs.pain_level,
                    "recorded_at": vs.recorded_at.isoformat(),
                    "device_id": vs.device_id,
                    "notes": vs.notes
                } for vs in vital_signs
            ]
            
            duration = time.time() - start_time
            log_api_event(f'/vital-signs/{patient_id}', 'GET', 200, duration)
            
            return create_response(True, vital_data, f"Retrieved {len(vital_data)} vital signs records")
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event(f'/vital-signs/{patient_id}', 'GET', 500, duration)
        return create_response(False, message=f"Failed to retrieve vital signs: {str(e)}", status_code=500)

# Alert Endpoints
@api_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get all alerts with optional filtering"""
    start_time = time.time()
    
    try:
        severity = request.args.get('severity')
        alert_type = request.args.get('type')
        resolved = request.args.get('resolved', type=bool)
        
        with get_db_session() as session:
            query = session.query(Alert)
            
            if severity:
                query = query.filter(Alert.severity == severity)
            if alert_type:
                query = query.filter(Alert.alert_type == alert_type)
            if resolved is not None:
                query = query.filter(Alert.resolved == resolved)
            
            alerts = query.order_by(desc(Alert.created_at)).all()
            
            alert_data = [
                {
                    "id": str(alert.id),
                    "patient_id": str(alert.patient_id),
                    "alert_type": alert.alert_type,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "message": alert.message,
                    "source": alert.source,
                    "acknowledged": alert.acknowledged,
                    "resolved": alert.resolved,
                    "created_at": alert.created_at.isoformat()
                } for alert in alerts
            ]
            
            duration = time.time() - start_time
            log_api_event('/alerts', 'GET', 200, duration)
            
            return create_response(True, alert_data, f"Retrieved {len(alert_data)} alerts")
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/alerts', 'GET', 500, duration)
        return create_response(False, message=f"Failed to retrieve alerts: {str(e)}", status_code=500)

@api_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    start_time = time.time()
    
    try:
        data = get_request_data()
        acknowledged_by = data.get('acknowledged_by', 'system')
        
        with get_db_session() as session:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            
            if not alert:
                duration = time.time() - start_time
                log_api_event(f'/alerts/{alert_id}/acknowledge', 'POST', 404, duration)
                return create_response(False, message="Alert not found", status_code=404)
            
            alert.acknowledged = True
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.utcnow()
            
            session.commit()
            
            duration = time.time() - start_time
            log_api_event(f'/alerts/{alert_id}/acknowledge', 'POST', 200, duration)
            
            return create_response(True, message="Alert acknowledged successfully")
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event(f'/alerts/{alert_id}/acknowledge', 'POST', 500, duration)
        return create_response(False, message=f"Failed to acknowledge alert: {str(e)}", status_code=500)

# Agent Endpoints
@api_bp.route('/agents/triage', methods=['POST'])
def triage_patient():
    """Perform patient triage using AI agent"""
    start_time = time.time()
    
    try:
        data = get_request_data()
        patient_id = data.get('patient_id')
        symptoms = data.get('symptoms', [])
        vital_signs = data.get('vital_signs', {})
        
        if not patient_id:
            duration = time.time() - start_time
            log_api_event('/agents/triage', 'POST', 400, duration)
            return create_response(False, message="Patient ID is required", status_code=400)
        
        # Get triage agent
        agents = current_app.config.get('AGENTS', {})
        triage_agent = agents.get('triage')
        
        if not triage_agent:
            duration = time.time() - start_time
            log_api_event('/agents/triage', 'POST', 503, duration)
            return create_response(False, message="Triage agent not available", status_code=503)
        
        # Execute triage
        triage_input = f"Patient ID: {patient_id}\nSymptoms: {symptoms}\nVital Signs: {vital_signs}"
        result = triage_agent.execute(triage_input)
        
        if result['success']:
            duration = time.time() - start_time
            log_api_event('/agents/triage', 'POST', 200, duration)
            log_agent_event('triage', 'executed', f"Triage completed for patient {patient_id}")
            
            return create_response(True, result['result'], "Triage completed successfully")
        else:
            duration = time.time() - start_time
            log_api_event('/agents/triage', 'POST', 500, duration)
            return create_response(False, message=f"Triage failed: {result['error']}", status_code=500)
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/agents/triage', 'POST', 500, duration)
        return create_response(False, message=f"Triage request failed: {str(e)}", status_code=500)

@api_bp.route('/agents/emergency', methods=['POST'])
def emergency_response():
    """Handle emergency using AI agent"""
    start_time = time.time()
    
    try:
        data = get_request_data()
        patient_id = data.get('patient_id')
        emergency_type = data.get('emergency_type')
        description = data.get('description')
        
        if not all([patient_id, emergency_type, description]):
            duration = time.time() - start_time
            log_api_event('/agents/emergency', 'POST', 400, duration)
            return create_response(False, message="Patient ID, emergency type, and description are required", status_code=400)
        
        # Get emergency agent
        agents = current_app.config.get('AGENTS', {})
        emergency_agent = agents.get('emergency')
        
        if not emergency_agent:
            duration = time.time() - start_time
            log_api_event('/agents/emergency', 'POST', 503, duration)
            return create_response(False, message="Emergency agent not available", status_code=503)
        
        # Execute emergency response
        emergency_input = f"Patient ID: {patient_id}\nEmergency Type: {emergency_type}\nDescription: {description}"
        result = emergency_agent.execute(emergency_input)
        
        if result['success']:
            duration = time.time() - start_time
            log_api_event('/agents/emergency', 'POST', 200, duration)
            log_agent_event('emergency', 'executed', f"Emergency response initiated for patient {patient_id}")
            
            return create_response(True, result['result'], "Emergency response initiated successfully")
        else:
            duration = time.time() - start_time
            log_api_event('/agents/emergency', 'POST', 500, duration)
            return create_response(False, message=f"Emergency response failed: {result['error']}", status_code=500)
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/agents/emergency', 'POST', 500, duration)
        return create_response(False, message=f"Emergency request failed: {str(e)}", status_code=500)

# Appointment Endpoints
@api_bp.route('/appointments', methods=['GET'])
def get_appointments():
    """Get all appointments with optional filtering"""
    start_time = time.time()
    
    try:
        patient_id = request.args.get('patient_id')
        status = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        with get_db_session() as session:
            query = session.query(Appointment)
            
            if patient_id:
                query = query.filter(Appointment.patient_id == patient_id)
            if status:
                query = query.filter(Appointment.status == status)
            if date_from:
                query = query.filter(Appointment.scheduled_date >= date_from)
            if date_to:
                query = query.filter(Appointment.scheduled_date <= date_to)
            
            appointments = query.order_by(Appointment.scheduled_date).all()
            
            appointment_data = [
                {
                    "id": str(apt.id),
                    "patient_id": str(apt.patient_id),
                    "doctor_id": apt.doctor_id,
                    "department": apt.department,
                    "appointment_type": apt.appointment_type,
                    "scheduled_date": apt.scheduled_date.isoformat(),
                    "duration": apt.duration,
                    "status": apt.status.value,
                    "room_number": apt.room_number
                } for apt in appointments
            ]
            
            duration = time.time() - start_time
            log_api_event('/appointments', 'GET', 200, duration)
            
            return create_response(True, appointment_data, f"Retrieved {len(appointment_data)} appointments")
            
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
        validation = validate_appointment(data)
        if not validation.is_valid:
            duration = time.time() - start_time
            log_api_event('/appointments', 'POST', 400, duration)
            return create_response(False, {
                "errors": validation.errors,
                "warnings": validation.warnings
            }, "Appointment data validation failed", 400)
        
        with get_db_session() as session:
            appointment = Appointment(**data)
            session.add(appointment)
            session.commit()
            session.refresh(appointment)
            
            appointment_data = {
                "id": str(appointment.id),
                "patient_id": str(appointment.patient_id),
                "doctor_id": appointment.doctor_id,
                "scheduled_date": appointment.scheduled_date.isoformat(),
                "status": appointment.status.value
            }
            
            duration = time.time() - start_time
            log_api_event('/appointments', 'POST', 201, duration)
            
            return create_response(True, appointment_data, "Appointment created successfully", 201)
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/appointments', 'POST', 500, duration)
        return create_response(False, message=f"Failed to create appointment: {str(e)}", status_code=500)

# Medical Records Endpoints
@api_bp.route('/medical-records/<patient_id>', methods=['GET'])
def get_medical_records(patient_id: str):
    """Get patient medical records"""
    start_time = time.time()
    
    try:
        record_type = request.args.get('type')
        
        with get_db_session() as session:
            query = session.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id)
            
            if record_type:
                query = query.filter(MedicalRecord.record_type == record_type)
            
            records = query.order_by(desc(MedicalRecord.created_at)).all()
            
            record_data = [
                {
                    "id": str(record.id),
                    "record_type": record.record_type,
                    "title": record.title,
                    "content": record.content,
                    "doctor_id": record.doctor_id,
                    "department": record.department,
                    "diagnosis_codes": record.diagnosis_codes,
                    "medications": record.medications,
                    "created_at": record.created_at.isoformat()
                } for record in records
            ]
            
            duration = time.time() - start_time
            log_api_event(f'/medical-records/{patient_id}', 'GET', 200, duration)
            
            return create_response(True, record_data, f"Retrieved {len(record_data)} medical records")
            
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
        validation = validate_medical_record(data)
        if not validation.is_valid:
            duration = time.time() - start_time
            log_api_event('/medical-records', 'POST', 400, duration)
            return create_response(False, {
                "errors": validation.errors,
                "warnings": validation.warnings
            }, "Medical record data validation failed", 400)
        
        with get_db_session() as session:
            record = MedicalRecord(**data)
            session.add(record)
            session.commit()
            session.refresh(record)
            
            record_data = {
                "id": str(record.id),
                "patient_id": str(record.patient_id),
                "record_type": record.record_type,
                "title": record.title,
                "created_at": record.created_at.isoformat()
            }
            
            duration = time.time() - start_time
            log_api_event('/medical-records', 'POST', 201, duration)
            
            return create_response(True, record_data, "Medical record created successfully", 201)
            
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/medical-records', 'POST', 500, duration)
        return create_response(False, message=f"Failed to create medical record: {str(e)}", status_code=500)

@api_bp.route('/docs', methods=['GET'])
def api_documentation():
    """API Documentation endpoint"""
    start_time = time.time()
    
    try:
        docs = {
            "title": "Healthcare Management System API",
            "version": "1.0.0",
            "description": "AI-powered healthcare management system with intelligent agents",
            "base_url": "/api",
            "endpoints": {
                "health": {
                    "url": "/health",
                    "method": "GET",
                    "description": "Health check endpoint",
                    "response": "System health status"
                },
                "system_info": {
                    "url": "/system/info",
                    "method": "GET",
                    "description": "Get system information",
                    "response": "System configuration and available components"
                },
                "patients": {
                    "url": "/patients",
                    "method": "GET",
                    "description": "Get all patients with optional filtering",
                    "parameters": {
                        "page": "Page number (default: 1)",
                        "per_page": "Items per page (default: 20, max: 100)",
                        "status": "Filter by patient status",
                        "search": "Search by name or MRN"
                    }
                },
                "create_patient": {
                    "url": "/patients",
                    "method": "POST",
                    "description": "Create a new patient",
                    "body": {
                        "mrn": "Medical Record Number (required)",
                        "first_name": "Patient first name (required)",
                        "last_name": "Patient last name (required)",
                        "date_of_birth": "Date of birth (YYYY-MM-DD)",
                        "gender": "Patient gender",
                        "phone": "Contact phone number",
                        "email": "Contact email",
                        "address": "Patient address",
                        "emergency_contact": "Emergency contact information",
                        "insurance_info": "Insurance details",
                        "allergies": "Known allergies",
                        "medications": "Current medications",
                        "medical_history": "Medical history"
                    }
                },
                "get_patient": {
                    "url": "/patients/{patient_id}",
                    "method": "GET",
                    "description": "Get patient by ID with related data",
                    "response": "Patient details with recent vital signs, appointments, and alerts"
                },
                "update_patient": {
                    "url": "/patients/{patient_id}",
                    "method": "PUT",
                    "description": "Update patient information",
                    "body": "Any patient fields to update"
                },
                "vital_signs": {
                    "url": "/vital-signs",
                    "method": "POST",
                    "description": "Submit patient vital signs",
                    "body": {
                        "patient_id": "Patient ID (required)",
                        "heart_rate": "Heart rate in BPM",
                        "systolic_bp": "Systolic blood pressure",
                        "diastolic_bp": "Diastolic blood pressure",
                        "temperature": "Body temperature in Fahrenheit",
                        "oxygen_saturation": "Oxygen saturation percentage",
                        "respiratory_rate": "Respiratory rate",
                        "blood_glucose": "Blood glucose level",
                        "pain_level": "Pain level (1-10)",
                        "device_id": "Monitoring device ID",
                        "notes": "Additional notes"
                    }
                },
                "get_vital_signs": {
                    "url": "/vital-signs/{patient_id}",
                    "method": "GET",
                    "description": "Get patient vital signs history",
                    "parameters": {
                        "limit": "Number of records to return (default: 50, max: 100)"
                    }
                },
                "alerts": {
                    "url": "/alerts",
                    "method": "GET",
                    "description": "Get all alerts with optional filtering",
                    "parameters": {
                        "severity": "Filter by alert severity (low, medium, high)",
                        "type": "Filter by alert type",
                        "resolved": "Filter by resolved status (true/false)"
                    }
                },
                "acknowledge_alert": {
                    "url": "/alerts/{alert_id}/acknowledge",
                    "method": "POST",
                    "description": "Acknowledge an alert",
                    "body": {
                        "acknowledged_by": "Name of person acknowledging (optional)"
                    }
                },
                "triage": {
                    "url": "/agents/triage",
                    "method": "POST",
                    "description": "Perform patient triage using AI agent",
                    "body": {
                        "patient_id": "Patient ID (required)",
                        "symptoms": "List of symptoms",
                        "vital_signs": "Current vital signs"
                    }
                },
                "emergency": {
                    "url": "/agents/emergency",
                    "method": "POST",
                    "description": "Handle emergency using AI agent",
                    "body": {
                        "patient_id": "Patient ID (required)",
                        "emergency_type": "Type of emergency (required)",
                        "description": "Emergency description (required)"
                    }
                },
                "appointments": {
                    "url": "/appointments",
                    "method": "GET",
                    "description": "Get all appointments with optional filtering",
                    "parameters": {
                        "patient_id": "Filter by patient ID",
                        "status": "Filter by appointment status",
                        "date_from": "Filter from date (YYYY-MM-DD)",
                        "date_to": "Filter to date (YYYY-MM-DD)"
                    }
                },
                "create_appointment": {
                    "url": "/appointments",
                    "method": "POST",
                    "description": "Create a new appointment",
                    "body": {
                        "patient_id": "Patient ID (required)",
                        "doctor_id": "Doctor ID (required)",
                        "department": "Department name",
                        "appointment_type": "Type of appointment",
                        "scheduled_date": "Scheduled date and time (required)",
                        "duration": "Appointment duration in minutes",
                        "room_number": "Room number"
                    }
                },
                "medical_records": {
                    "url": "/medical-records/{patient_id}",
                    "method": "GET",
                    "description": "Get patient medical records",
                    "parameters": {
                        "type": "Filter by record type"
                    }
                },
                "create_medical_record": {
                    "url": "/medical-records",
                    "method": "POST",
                    "description": "Create a new medical record",
                    "body": {
                        "patient_id": "Patient ID (required)",
                        "record_type": "Type of medical record (required)",
                        "title": "Record title (required)",
                        "content": "Record content (required)",
                        "doctor_id": "Doctor ID",
                        "department": "Department name",
                        "diagnosis_codes": "ICD diagnosis codes",
                        "medications": "Prescribed medications"
                    }
                }
            },
            "response_format": {
                "success": "Boolean indicating if the request was successful",
                "message": "Human-readable message",
                "data": "Response data (if applicable)",
                "timestamp": "ISO timestamp of the response"
            },
            "error_codes": {
                "400": "Bad Request - Invalid input data",
                "404": "Not Found - Resource not found",
                "409": "Conflict - Resource already exists",
                "500": "Internal Server Error - Server error"
            },
            "authentication": "Currently not required for development",
            "rate_limiting": "Not implemented in development mode"
        }
        
        duration = time.time() - start_time
        log_api_event('/docs', 'GET', 200, duration)
        
        return create_response(True, docs, "API documentation retrieved successfully")
        
    except Exception as e:
        duration = time.time() - start_time
        log_api_event('/docs', 'GET', 500, duration)
        return create_response(False, message=f"Failed to generate API documentation: {str(e)}", status_code=500)