"""
Scheduling Agent

This agent handles appointment scheduling, resource management, calendar coordination,
and scheduling optimization for healthcare facilities.
"""

from typing import Dict, List, Any, Optional
from langchain_core.tools import BaseTool
from agents.base_agent import BaseHealthcareAgent
from utils.logger import log_agent_event
from database.models import Appointment, Patient, AppointmentStatus
from database.connection import get_db_session
from datetime import datetime, timedelta
import json

class SchedulingAgent(BaseHealthcareAgent):
    """AI agent for appointment and resource scheduling"""
    def __init__(self, tools: Dict[str, Any]):
        system_prompt = """You are a Scheduling Agent responsible for managing appointments and resource allocation.

Your responsibilities include:
1. Scheduling patient appointments
2. Allocating resources efficiently
3. Coordinating with other agents and staff
4. Handling scheduling conflicts
5. Ensuring optimal use of resources

Always strive for efficiency and patient satisfaction."""
        scheduling_tools = [
            tools.get('database', None),
            tools.get('medical', None),
            tools.get('notification', None),
            tools.get('validation', None)
        ]
        scheduling_tools = [tool for tool in scheduling_tools if tool is not None]
        super().__init__("SchedulingAgent", system_prompt, scheduling_tools)
        self.logger = log_agent_event
    
    def schedule_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a new appointment"""
        try:
            # Prepare scheduling input
            scheduling_input = self._prepare_scheduling_input(appointment_data)
            
            # Execute appointment scheduling
            result = self.execute(scheduling_input)
            
            if result['success']:
                # Parse scheduling result
                scheduling_result = self._parse_scheduling_result(result['result'])
                
                # Create appointment in database
                appointment_record = self._create_appointment_record(appointment_data, scheduling_result, result['result'])
                
                # Log appointment scheduling
                self.logger("SchedulingAgent", "appointment_scheduled", 
                           f"Appointment scheduled for patient {appointment_data.get('patient_id', 'unknown')}")
                
                return {
                    'success': True,
                    'appointment': scheduling_result,
                    'appointment_id': appointment_record.get('id') if appointment_record else None,
                    'assessment': result['result']
                }
            else:
                self.logger("SchedulingAgent", "scheduling_failed", 
                           f"Appointment scheduling failed: {result.get('error', 'Unknown error')}")
                return result
                
        except Exception as e:
            self.logger("SchedulingAgent", "scheduling_error", f"Appointment scheduling error: {str(e)}")
            return {
                'success': False,
                'error': f"Appointment scheduling failed: {str(e)}"
            }
    
    def _prepare_scheduling_input(self, appointment_data: Dict[str, Any]) -> str:
        """Prepare input for appointment scheduling"""
        input_parts = []
        
        # Patient information
        if 'patient_id' in appointment_data:
            input_parts.append(f"Patient ID: {appointment_data['patient_id']}")
        
        if 'patient_name' in appointment_data:
            input_parts.append(f"Patient Name: {appointment_data['patient_name']}")
        
        if 'age' in appointment_data:
            input_parts.append(f"Age: {appointment_data['age']}")
        
        # Appointment details
        if 'appointment_type' in appointment_data:
            input_parts.append(f"Appointment Type: {appointment_data['appointment_type']}")
        
        if 'department' in appointment_data:
            input_parts.append(f"Department: {appointment_data['department']}")
        
        if 'doctor_id' in appointment_data:
            input_parts.append(f"Requested Doctor: {appointment_data['doctor_id']}")
        
        if 'urgency' in appointment_data:
            input_parts.append(f"Urgency: {appointment_data['urgency']}")
        
        if 'preferred_date' in appointment_data:
            input_parts.append(f"Preferred Date: {appointment_data['preferred_date']}")
        
        if 'preferred_time' in appointment_data:
            input_parts.append(f"Preferred Time: {appointment_data['preferred_time']}")
        
        if 'duration' in appointment_data:
            input_parts.append(f"Estimated Duration: {appointment_data['duration']} minutes")
        
        # Medical context
        if 'reason' in appointment_data:
            input_parts.append(f"Reason for Visit: {appointment_data['reason']}")
        
        if 'symptoms' in appointment_data:
            symptoms = appointment_data['symptoms']
            if isinstance(symptoms, list):
                symptoms_str = ", ".join(symptoms)
            else:
                symptoms_str = str(symptoms)
            input_parts.append(f"Symptoms: {symptoms_str}")
        
        if 'medical_history' in appointment_data:
            history = appointment_data['medical_history']
            if isinstance(history, list):
                history_str = ", ".join(history)
            else:
                history_str = str(history)
            input_parts.append(f"Medical History: {history_str}")
        
        # Special requirements
        if 'special_requirements' in appointment_data:
            requirements = appointment_data['special_requirements']
            if isinstance(requirements, list):
                requirements_str = ", ".join(requirements)
            else:
                requirements_str = str(requirements)
            input_parts.append(f"Special Requirements: {requirements_str}")
        
        # Additional context
        if 'additional_context' in appointment_data:
            input_parts.append(f"Additional Context: {appointment_data['additional_context']}")
        
        # Create scheduling prompt
        scheduling_prompt = f"""
Please schedule an appointment for this patient:

{chr(10).join(input_parts)}

Based on the above information, please:
1. Determine optimal appointment timing
2. Assign appropriate provider and room
3. Consider urgency and patient needs
4. Suggest alternative times if needed
5. Provide scheduling recommendations
6. Consider resource availability

Format your response as:
RECOMMENDED_DATE: [optimal appointment date]
RECOMMENDED_TIME: [optimal appointment time]
ASSIGNED_DOCTOR: [assigned doctor ID]
ASSIGNED_ROOM: [assigned room number]
DURATION: [appointment duration in minutes]
PRIORITY: [high/medium/low priority]
ALTERNATIVES: [alternative appointment times if needed]
NOTES: [scheduling notes and recommendations]
"""
        
        return scheduling_prompt
    
    def _parse_scheduling_result(self, result: str) -> Dict[str, Any]:
        """Parse scheduling result from agent output"""
        try:
            scheduling = {
                'recommended_date': '',
                'recommended_time': '',
                'assigned_doctor': '',
                'assigned_room': '',
                'duration': 30,
                'priority': 'medium',
                'alternatives': [],
                'notes': ''
            }
            
            lines = result.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('RECOMMENDED_DATE:'):
                    date = line.split(':', 1)[1].strip()
                    scheduling['recommended_date'] = date
                elif line.startswith('RECOMMENDED_TIME:'):
                    time = line.split(':', 1)[1].strip()
                    scheduling['recommended_time'] = time
                elif line.startswith('ASSIGNED_DOCTOR:'):
                    doctor = line.split(':', 1)[1].strip()
                    scheduling['assigned_doctor'] = doctor
                elif line.startswith('ASSIGNED_ROOM:'):
                    room = line.split(':', 1)[1].strip()
                    scheduling['assigned_room'] = room
                elif line.startswith('DURATION:'):
                    duration_str = line.split(':', 1)[1].strip()
                    try:
                        scheduling['duration'] = int(duration_str)
                    except ValueError:
                        pass
                elif line.startswith('PRIORITY:'):
                    priority = line.split(':', 1)[1].strip().lower()
                    scheduling['priority'] = priority
                elif line.startswith('ALTERNATIVES:'):
                    current_section = 'alternatives'
                elif line.startswith('NOTES:'):
                    notes = line.split(':', 1)[1].strip()
                    scheduling['notes'] = notes
                elif line and current_section and line.startswith('-'):
                    item = line[1:].strip()
                    if current_section in scheduling:
                        scheduling[current_section].append(item)
            
            return scheduling
            
        except Exception as e:
            self.logger("SchedulingAgent", "parse_error", f"Failed to parse scheduling result: {str(e)}")
            return {
                'recommended_date': datetime.now().strftime('%Y-%m-%d'),
                'recommended_time': '09:00',
                'assigned_doctor': 'DR001',
                'assigned_room': '101',
                'duration': 30,
                'priority': 'medium',
                'alternatives': [],
                'notes': 'Standard appointment scheduling'
            }
    
    def _create_appointment_record(self, appointment_data: Dict[str, Any], scheduling_result: Dict[str, Any], assessment_result: str) -> Optional[Dict[str, Any]]:
        """Create appointment record in database"""
        try:
            with get_db_session() as session:
                # Combine date and time
                scheduled_datetime_str = f"{scheduling_result['recommended_date']} {scheduling_result['recommended_time']}"
                scheduled_datetime = datetime.strptime(scheduled_datetime_str, '%Y-%m-%d %H:%M')
                
                appointment = Appointment(
                    patient_id=appointment_data['patient_id'],
                    doctor_id=scheduling_result['assigned_doctor'],
                    department=appointment_data.get('department', ''),
                    appointment_type=appointment_data.get('appointment_type', 'consultation'),
                    scheduled_date=scheduled_datetime,
                    duration=scheduling_result['duration'],
                    status=AppointmentStatus.SCHEDULED,
                    notes=f"{scheduling_result['notes']}\n\n{assessment_result}",
                    room_number=scheduling_result['assigned_room']
                )
                
                session.add(appointment)
                session.commit()
                session.refresh(appointment)
                
                return {
                    'id': str(appointment.id),
                    'scheduled_date': appointment.scheduled_date.isoformat(),
                    'doctor_id': appointment.doctor_id,
                    'room_number': appointment.room_number,
                    'status': appointment.status.value
                }
                
        except Exception as e:
            self.logger("SchedulingAgent", "database_error", f"Failed to create appointment record: {str(e)}")
            return None
    
    def reschedule_appointment(self, appointment_id: str, new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reschedule an existing appointment"""
        try:
            with get_db_session() as session:
                appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
                
                if not appointment:
                    return {
                        'success': False,
                        'error': 'Appointment not found'
                    }
                
                # Prepare rescheduling input
                rescheduling_input = self._prepare_rescheduling_input(appointment, new_data)
                
                # Execute rescheduling
                result = self.execute(rescheduling_input)
                
                if result['success']:
                    # Parse rescheduling result
                    rescheduling_result = self._parse_scheduling_result(result['result'])
                    
                    # Update appointment
                    if rescheduling_result['recommended_date'] and rescheduling_result['recommended_time']:
                        scheduled_datetime_str = f"{rescheduling_result['recommended_date']} {rescheduling_result['recommended_time']}"
                        scheduled_datetime = datetime.strptime(scheduled_datetime_str, '%Y-%m-%d %H:%M')
                        appointment.scheduled_date = scheduled_datetime
                    
                    if rescheduling_result['assigned_doctor']:
                        appointment.doctor_id = rescheduling_result['assigned_doctor']
                    
                    if rescheduling_result['assigned_room']:
                        appointment.room_number = rescheduling_result['assigned_room']
                    
                    if rescheduling_result['duration']:
                        appointment.duration = rescheduling_result['duration']
                    
                    appointment.notes = f"Rescheduled: {rescheduling_result['notes']}\n\n{result['result']}"
                    appointment.updated_at = datetime.utcnow()
                    
                    session.commit()
                    
                    self.logger("SchedulingAgent", "appointment_rescheduled", 
                               f"Appointment {appointment_id} rescheduled successfully")
                    
                    return {
                        'success': True,
                        'appointment_id': appointment_id,
                        'new_schedule': rescheduling_result,
                        'updated_at': appointment.updated_at.isoformat()
                    }
                else:
                    return result
                
        except Exception as e:
            self.logger("SchedulingAgent", "reschedule_error", f"Failed to reschedule appointment: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to reschedule appointment: {str(e)}"
            }
    
    def _prepare_rescheduling_input(self, appointment: Appointment, new_data: Dict[str, Any]) -> str:
        """Prepare input for appointment rescheduling"""
        input_parts = []
        
        # Current appointment information
        input_parts.append(f"Current Appointment ID: {appointment.id}")
        input_parts.append(f"Current Date/Time: {appointment.scheduled_date.isoformat()}")
        input_parts.append(f"Current Doctor: {appointment.doctor_id}")
        input_parts.append(f"Current Room: {appointment.room_number}")
        input_parts.append(f"Current Duration: {appointment.duration} minutes")
        
        # New requirements
        if 'new_preferred_date' in new_data:
            input_parts.append(f"New Preferred Date: {new_data['new_preferred_date']}")
        
        if 'new_preferred_time' in new_data:
            input_parts.append(f"New Preferred Time: {new_data['new_preferred_time']}")
        
        if 'new_urgency' in new_data:
            input_parts.append(f"New Urgency: {new_data['new_urgency']}")
        
        if 'reason_for_reschedule' in new_data:
            input_parts.append(f"Reason for Reschedule: {new_data['reason_for_reschedule']}")
        
        if 'new_requirements' in new_data:
            requirements = new_data['new_requirements']
            if isinstance(requirements, list):
                requirements_str = ", ".join(requirements)
            else:
                requirements_str = str(requirements)
            input_parts.append(f"New Requirements: {requirements_str}")
        
        # Create rescheduling prompt
        rescheduling_prompt = f"""
Please reschedule this appointment:

{chr(10).join(input_parts)}

Based on the above information, please:
1. Determine new optimal appointment timing
2. Consider availability of current provider
3. Suggest alternative providers if needed
4. Maintain appointment quality and patient care
5. Provide rescheduling recommendations

Format your response as:
RECOMMENDED_DATE: [new optimal appointment date]
RECOMMENDED_TIME: [new optimal appointment time]
ASSIGNED_DOCTOR: [assigned doctor ID]
ASSIGNED_ROOM: [assigned room number]
DURATION: [appointment duration in minutes]
PRIORITY: [high/medium/low priority]
ALTERNATIVES: [alternative appointment times if needed]
NOTES: [rescheduling notes and recommendations]
"""
        
        return rescheduling_prompt
    
    def get_available_slots(self, doctor_id: Optional[str] = None, date: Optional[str] = None) -> Dict[str, Any]:
        """Get available appointment slots"""
        try:
            with get_db_session() as session:
                # Get existing appointments
                query = session.query(Appointment)
                
                if doctor_id:
                    query = query.filter(Appointment.doctor_id == doctor_id)
                
                if date:
                    date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                    query = query.filter(
                        Appointment.scheduled_date >= date_obj,
                        Appointment.scheduled_date < date_obj + timedelta(days=1)
                    )
                
                existing_appointments = query.all()
                
                # Generate available slots (simplified - in real system would check provider schedules)
                available_slots = self._generate_available_slots(existing_appointments, doctor_id, date)
                
                return {
                    'success': True,
                    'available_slots': available_slots,
                    'existing_appointments': len(existing_appointments)
                }
                
        except Exception as e:
            self.logger("SchedulingAgent", "slots_error", f"Failed to get available slots: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to get available slots: {str(e)}"
            }
    
    def _generate_available_slots(self, existing_appointments: List[Appointment], doctor_id: Optional[str], date: Optional[str]) -> List[Dict[str, Any]]:
        """Generate available appointment slots"""
        # Simplified slot generation - in real system would check provider schedules
        base_date = datetime.now().date()
        if date:
            base_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Standard business hours: 9 AM to 5 PM
        start_hour = 9
        end_hour = 17
        slot_duration = 30  # minutes
        
        available_slots = []
        
        for hour in range(start_hour, end_hour):
            for minute in [0, 30]:
                slot_time = datetime.combine(base_date, datetime.min.time().replace(hour=hour, minute=minute))
                
                # Check if slot conflicts with existing appointments
                slot_end = slot_time + timedelta(minutes=slot_duration)
                conflict = False
                
                for appointment in existing_appointments:
                    appointment_end = appointment.scheduled_date + timedelta(minutes=appointment.duration)
                    if (slot_time < appointment_end and slot_end > appointment.scheduled_date):
                        conflict = True
                        break
                
                if not conflict:
                    available_slots.append({
                        'time': slot_time.strftime('%H:%M'),
                        'datetime': slot_time.isoformat(),
                        'duration': slot_duration,
                        'available': True
                    })
        
        return available_slots
    
    def get_scheduling_statistics(self, doctor_id: Optional[str] = None) -> Dict[str, Any]:
        """Get scheduling statistics"""
        try:
            with get_db_session() as session:
                # Base query
                appointments_query = session.query(Appointment)
                
                if doctor_id:
                    appointments_query = appointments_query.filter(Appointment.doctor_id == doctor_id)
                
                # Get appointment statistics
                total_appointments = appointments_query.count()
                
                # Get appointments by status
                status_counts = {}
                for status in AppointmentStatus:
                    count = appointments_query.filter(Appointment.status == status).count()
                    status_counts[status.value] = count
                
                # Get appointments by type
                type_counts = {}
                appointment_types = session.query(Appointment.appointment_type).distinct().all()
                for appt_type in appointment_types:
                    count = appointments_query.filter(Appointment.appointment_type == appt_type[0]).count()
                    type_counts[appt_type[0]] = count
                
                # Get recent appointments (next 7 days)
                next_week = datetime.utcnow() + timedelta(days=7)
                upcoming_appointments = appointments_query.filter(
                    Appointment.scheduled_date >= datetime.utcnow(),
                    Appointment.scheduled_date <= next_week
                ).count()
                
                # Get today's appointments
                today = datetime.utcnow().date()
                today_appointments = appointments_query.filter(
                    Appointment.scheduled_date >= today,
                    Appointment.scheduled_date < today + timedelta(days=1)
                ).count()
                
                return {
                    'success': True,
                    'statistics': {
                        'total_appointments': total_appointments,
                        'upcoming_appointments_7d': upcoming_appointments,
                        'today_appointments': today_appointments,
                        'by_status': status_counts,
                        'by_type': type_counts
                    }
                }
                
        except Exception as e:
            self.logger("SchedulingAgent", "stats_error", f"Failed to get scheduling statistics: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to get scheduling statistics: {str(e)}"
            }
    
    def cancel_appointment(self, appointment_id: str, reason: str = 'Patient request') -> Dict[str, Any]:
        """Cancel an appointment"""
        try:
            with get_db_session() as session:
                appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
                
                if not appointment:
                    return {
                        'success': False,
                        'error': 'Appointment not found'
                    }
                
                # Update appointment status
                appointment.status = AppointmentStatus.CANCELLED
                appointment.notes = f"Cancelled: {reason}\n\n{appointment.notes or ''}"
                appointment.updated_at = datetime.utcnow()
                
                session.commit()
                
                self.logger("SchedulingAgent", "appointment_cancelled", 
                           f"Appointment {appointment_id} cancelled: {reason}")
                
                return {
                    'success': True,
                    'appointment_id': appointment_id,
                    'cancelled_at': appointment.updated_at.isoformat(),
                    'reason': reason
                }
                
        except Exception as e:
            self.logger("SchedulingAgent", "cancel_error", f"Failed to cancel appointment: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to cancel appointment: {str(e)}"
            }
