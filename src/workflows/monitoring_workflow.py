"""
Monitoring Workflow

This module implements the patient monitoring workflow that handles continuous
monitoring, vital signs analysis, and automated alert generation.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from agents.monitoring_agent import MonitoringAgent
from agents.emergency_agent import EmergencyAgent
from utils.logger import log_workflow_event, log_alert_event
from database.connection import get_db_session
from database.models import Patient, VitalSigns, Alert, AlertSeverity

class MonitoringWorkflow:
    """Patient monitoring workflow coordinator"""
    
    def __init__(self, tools: Dict[str, Any]):
        self.tools = tools
        self.monitoring_agent = MonitoringAgent(tools)
        self.emergency_agent = EmergencyAgent(tools)
        self.logger = logging.getLogger(__name__)
    
    def start_patient_monitoring(self, patient_id: str, monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
        """Start monitoring for a patient"""
        try:
            # Log monitoring start
            log_workflow_event("monitoring", "started", f"Started monitoring for patient {patient_id}", patient_id, monitoring_config)
            
            # Step 1: Initialize monitoring
            init_result = self._initialize_monitoring(patient_id, monitoring_config)
            
            # Step 2: Set up monitoring parameters
            setup_result = self._setup_monitoring_parameters(patient_id, monitoring_config)
            
            # Step 3: Start continuous monitoring
            continuous_result = self._start_continuous_monitoring(patient_id, monitoring_config)
            
            # Step 4: Set up alert thresholds
            alert_result = self._setup_alert_thresholds(patient_id, monitoring_config)
            
            # Compile result
            result = {
                'success': True,
                'patient_id': patient_id,
                'monitoring_id': f"MON_{patient_id}_{datetime.utcnow().timestamp()}",
                'initialization': init_result,
                'setup': setup_result,
                'continuous_monitoring': continuous_result,
                'alert_setup': alert_result,
                'start_time': datetime.utcnow().isoformat(),
                'config': monitoring_config
            }
            
            # Log monitoring start completion
            log_workflow_event("monitoring", "initialized", f"Monitoring initialized for patient {patient_id}", patient_id, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to start patient monitoring: {str(e)}")
            log_workflow_event("monitoring", "failed", f"Failed to start monitoring: {str(e)}", patient_id, monitoring_config)
            return {
                'success': False,
                'error': f"Failed to start monitoring: {str(e)}",
                'patient_id': patient_id
            }
    
    def process_vital_signs(self, patient_id: str, vital_signs: Dict[str, Any]) -> Dict[str, Any]:
        """Process new vital signs data"""
        try:
            # Step 1: Validate vital signs
            validation_result = self._validate_vital_signs(vital_signs)
            
            # Step 2: Analyze vital signs
            analysis_result = self._analyze_vital_signs(patient_id, vital_signs)
            
            # Step 3: Check for abnormalities
            abnormality_result = self._check_abnormalities(patient_id, vital_signs, analysis_result)
            
            # Step 4: Generate alerts if needed
            alert_result = self._generate_alerts_if_needed(patient_id, vital_signs, abnormality_result)
            
            # Step 5: Update monitoring status
            status_result = self._update_monitoring_status(patient_id, vital_signs, analysis_result)
            
            # Compile result
            result = {
                'success': True,
                'patient_id': patient_id,
                'timestamp': datetime.utcnow().isoformat(),
                'validation': validation_result,
                'analysis': analysis_result,
                'abnormalities': abnormality_result,
                'alerts': alert_result,
                'status_update': status_result
            }
            
            # Log vital signs processing
            log_workflow_event("monitoring", "vital_signs_processed", f"Processed vital signs for patient {patient_id}", patient_id, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to process vital signs: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to process vital signs: {str(e)}",
                'patient_id': patient_id,
                'vital_signs': vital_signs
            }
    
    def check_monitoring_alerts(self, patient_id: str) -> Dict[str, Any]:
        """Check for monitoring alerts and escalate if needed"""
        try:
            # Step 1: Get current monitoring status
            status_result = self._get_monitoring_status(patient_id)
            
            # Step 2: Check for pending alerts
            alert_check_result = self._check_pending_alerts(patient_id)
            
            # Step 3: Assess escalation needs
            escalation_result = self._assess_escalation_needs(patient_id, alert_check_result)
            
            # Step 4: Escalate if necessary
            escalation_action = None
            if escalation_result.get('escalation_needed', False):
                escalation_action = self._escalate_monitoring(patient_id, escalation_result)
            
            # Compile result
            result = {
                'success': True,
                'patient_id': patient_id,
                'timestamp': datetime.utcnow().isoformat(),
                'current_status': status_result,
                'alert_check': alert_check_result,
                'escalation_assessment': escalation_result,
                'escalation_action': escalation_action
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to check monitoring alerts: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to check monitoring alerts: {str(e)}",
                'patient_id': patient_id
            }
    
    def stop_patient_monitoring(self, patient_id: str, reason: str = "Monitoring completed") -> Dict[str, Any]:
        """Stop monitoring for a patient"""
        try:
            # Step 1: Stop continuous monitoring
            stop_result = self._stop_continuous_monitoring(patient_id)
            
            # Step 2: Clear alert thresholds
            clear_result = self._clear_alert_thresholds(patient_id)
            
            # Step 3: Generate monitoring summary
            summary_result = self._generate_monitoring_summary(patient_id)
            
            # Step 4: Update monitoring status
            status_result = self._update_monitoring_status(patient_id, {}, {'status': 'stopped'})
            
            # Compile result
            result = {
                'success': True,
                'patient_id': patient_id,
                'stop_time': datetime.utcnow().isoformat(),
                'reason': reason,
                'stop_result': stop_result,
                'clear_result': clear_result,
                'summary': summary_result,
                'status_update': status_result
            }
            
            # Log monitoring stop
            log_workflow_event("monitoring", "stopped", f"Stopped monitoring for patient {patient_id}", patient_id, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to stop patient monitoring: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to stop monitoring: {str(e)}",
                'patient_id': patient_id
            }
    
    def _initialize_monitoring(self, patient_id: str, monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize monitoring for a patient"""
        try:
            # Use monitoring agent to initialize
            init_result = self.monitoring_agent.initialize_monitoring(patient_id, monitoring_config)
            
            return {
                'success': init_result.get('success', False),
                'monitoring_session_id': init_result.get('session_id'),
                'initialization_time': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to initialize monitoring: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _setup_monitoring_parameters(self, patient_id: str, monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup monitoring parameters"""
        try:
            # Extract monitoring parameters
            vital_signs_frequency = monitoring_config.get('vital_signs_frequency', 300)  # 5 minutes default
            alert_thresholds = monitoring_config.get('alert_thresholds', {})
            monitoring_type = monitoring_config.get('monitoring_type', 'standard')
            
            # Setup parameters using monitoring agent
            setup_result = self.monitoring_agent.setup_monitoring_parameters(
                patient_id, vital_signs_frequency, alert_thresholds, monitoring_type
            )
            
            return {
                'success': setup_result.get('success', False),
                'vital_signs_frequency': vital_signs_frequency,
                'alert_thresholds': alert_thresholds,
                'monitoring_type': monitoring_type,
                'parameters_set': setup_result.get('parameters_set', [])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to setup monitoring parameters: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _start_continuous_monitoring(self, patient_id: str, monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
        """Start continuous monitoring"""
        try:
            # Start continuous monitoring using monitoring agent
            continuous_result = self.monitoring_agent.start_continuous_monitoring(patient_id, monitoring_config)
            
            return {
                'success': continuous_result.get('success', False),
                'monitoring_active': continuous_result.get('monitoring_active', False),
                'next_check_time': continuous_result.get('next_check_time'),
                'monitoring_interval': monitoring_config.get('vital_signs_frequency', 300)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start continuous monitoring: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _setup_alert_thresholds(self, patient_id: str, monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup alert thresholds"""
        try:
            alert_thresholds = monitoring_config.get('alert_thresholds', {})
            
            # Setup thresholds using monitoring agent
            threshold_result = self.monitoring_agent.setup_alert_thresholds(patient_id, alert_thresholds)
            
            return {
                'success': threshold_result.get('success', False),
                'thresholds_set': list(alert_thresholds.keys()),
                'total_thresholds': len(alert_thresholds)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to setup alert thresholds: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_vital_signs(self, vital_signs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate vital signs data"""
        try:
            # Use validation tools to validate vital signs
            validation_tool = self.tools.get('validation', {})
            if hasattr(validation_tool, 'validate_vital_signs'):
                validation_result = validation_tool.validate_vital_signs(vital_signs)
            else:
                # Basic validation
                validation_result = {
                    'is_valid': True,
                    'errors': [],
                    'warnings': []
                }
                
                # Check for required fields
                required_fields = ['patient_id']
                for field in required_fields:
                    if field not in vital_signs:
                        validation_result['errors'].append(f"Missing required field: {field}")
                        validation_result['is_valid'] = False
                
                # Check numeric values
                numeric_fields = ['heart_rate', 'systolic_bp', 'diastolic_bp', 'temperature', 'oxygen_saturation']
                for field in numeric_fields:
                    if field in vital_signs and vital_signs[field] is not None:
                        try:
                            float(vital_signs[field])
                        except (ValueError, TypeError):
                            validation_result['errors'].append(f"Invalid {field}: must be numeric")
                            validation_result['is_valid'] = False
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Failed to validate vital signs: {str(e)}")
            return {
                'is_valid': False,
                'errors': [str(e)],
                'warnings': []
            }
    
    def _analyze_vital_signs(self, patient_id: str, vital_signs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze vital signs using monitoring agent"""
        try:
            # Use monitoring agent to analyze vital signs
            analysis_result = self.monitoring_agent.analyze_vital_signs(patient_id, vital_signs)
            
            return {
                'analysis_complete': analysis_result.get('success', False),
                'abnormalities_found': analysis_result.get('abnormalities', []),
                'overall_severity': analysis_result.get('overall_severity', 'normal'),
                'recommendations': analysis_result.get('recommendations', [])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze vital signs: {str(e)}")
            return {
                'analysis_complete': False,
                'error': str(e),
                'abnormalities_found': [],
                'overall_severity': 'unknown'
            }
    
    def _check_abnormalities(self, patient_id: str, vital_signs: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Check for abnormalities in vital signs"""
        try:
            abnormalities = analysis_result.get('abnormalities_found', [])
            
            # Categorize abnormalities by severity
            critical_abnormalities = []
            high_abnormalities = []
            moderate_abnormalities = []
            low_abnormalities = []
            
            for abnormality in abnormalities:
                severity = abnormality.get('severity', 'low')
                if severity == 'critical':
                    critical_abnormalities.append(abnormality)
                elif severity == 'high':
                    high_abnormalities.append(abnormality)
                elif severity == 'moderate':
                    moderate_abnormalities.append(abnormality)
                else:
                    low_abnormalities.append(abnormality)
            
            return {
                'total_abnormalities': len(abnormalities),
                'critical_count': len(critical_abnormalities),
                'high_count': len(high_abnormalities),
                'moderate_count': len(moderate_abnormalities),
                'low_count': len(low_abnormalities),
                'critical_abnormalities': critical_abnormalities,
                'high_abnormalities': high_abnormalities,
                'moderate_abnormalities': moderate_abnormalities,
                'low_abnormalities': low_abnormalities
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check abnormalities: {str(e)}")
            return {
                'total_abnormalities': 0,
                'error': str(e)
            }
    
    def _generate_alerts_if_needed(self, patient_id: str, vital_signs: Dict[str, Any], abnormality_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate alerts if abnormalities are detected"""
        try:
            alerts_generated = []
            
            # Check for critical abnormalities
            critical_abnormalities = abnormality_result.get('critical_abnormalities', [])
            if critical_abnormalities:
                alert_data = {
                    'patient_id': patient_id,
                    'alert_type': 'vital_signs',
                    'severity': 'critical',
                    'title': 'Critical Vital Signs Alert',
                    'message': f'Critical vital signs abnormalities detected: {len(critical_abnormalities)} issues',
                    'source': 'monitoring_workflow'
                }
                
                alert_result = self.monitoring_agent.create_alert(alert_data)
                if alert_result.get('success'):
                    alerts_generated.append({
                        'alert_id': alert_result.get('alert_id'),
                        'severity': 'critical',
                        'type': 'vital_signs'
                    })
            
            # Check for high abnormalities
            high_abnormalities = abnormality_result.get('high_abnormalities', [])
            if high_abnormalities:
                alert_data = {
                    'patient_id': patient_id,
                    'alert_type': 'vital_signs',
                    'severity': 'high',
                    'title': 'High Priority Vital Signs Alert',
                    'message': f'High priority vital signs abnormalities detected: {len(high_abnormalities)} issues',
                    'source': 'monitoring_workflow'
                }
                
                alert_result = self.monitoring_agent.create_alert(alert_data)
                if alert_result.get('success'):
                    alerts_generated.append({
                        'alert_id': alert_result.get('alert_id'),
                        'severity': 'high',
                        'type': 'vital_signs'
                    })
            
            # Log alert generation
            for alert in alerts_generated:
                log_alert_event(alert['type'], alert['severity'], patient_id, 
                              f"Generated {alert['severity']} alert for vital signs abnormalities")
            
            return {
                'alerts_generated': len(alerts_generated),
                'alert_details': alerts_generated,
                'critical_alerts': len([a for a in alerts_generated if a['severity'] == 'critical']),
                'high_alerts': len([a for a in alerts_generated if a['severity'] == 'high'])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate alerts: {str(e)}")
            return {
                'alerts_generated': 0,
                'error': str(e)
            }
    
    def _update_monitoring_status(self, patient_id: str, vital_signs: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Update monitoring status"""
        try:
            # Update monitoring status using monitoring agent
            status_update = {
                'patient_id': patient_id,
                'last_vital_signs_time': datetime.utcnow().isoformat(),
                'abnormalities_count': analysis_result.get('abnormalities_found', []),
                'overall_severity': analysis_result.get('overall_severity', 'normal'),
                'monitoring_active': True
            }
            
            status_result = self.monitoring_agent.update_monitoring_status(patient_id, status_update)
            
            return {
                'success': status_result.get('success', False),
                'status_updated': status_result.get('status_updated', False),
                'last_update': status_update['last_vital_signs_time']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update monitoring status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_monitoring_status(self, patient_id: str) -> Dict[str, Any]:
        """Get current monitoring status"""
        try:
            status_result = self.monitoring_agent.get_monitoring_status(patient_id)
            
            return {
                'monitoring_active': status_result.get('monitoring_active', False),
                'last_vital_signs_time': status_result.get('last_vital_signs_time'),
                'abnormalities_count': status_result.get('abnormalities_count', 0),
                'overall_severity': status_result.get('overall_severity', 'normal')
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get monitoring status: {str(e)}")
            return {
                'monitoring_active': False,
                'error': str(e)
            }
    
    def _check_pending_alerts(self, patient_id: str) -> Dict[str, Any]:
        """Check for pending alerts"""
        try:
            # Get pending alerts using monitoring agent
            alerts_result = self.monitoring_agent.get_pending_alerts(patient_id)
            
            return {
                'pending_alerts': alerts_result.get('alerts', []),
                'alert_count': len(alerts_result.get('alerts', [])),
                'critical_alerts': len([a for a in alerts_result.get('alerts', []) if a.get('severity') == 'critical']),
                'high_alerts': len([a for a in alerts_result.get('alerts', []) if a.get('severity') == 'high'])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check pending alerts: {str(e)}")
            return {
                'pending_alerts': [],
                'alert_count': 0,
                'error': str(e)
            }
    
    def _assess_escalation_needs(self, patient_id: str, alert_check_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess if escalation is needed"""
        try:
            critical_alerts = alert_check_result.get('critical_alerts', 0)
            high_alerts = alert_check_result.get('high_alerts', 0)
            
            # Determine escalation needs
            escalation_needed = False
            escalation_level = 'none'
            
            if critical_alerts > 0:
                escalation_needed = True
                escalation_level = 'emergency'
            elif high_alerts >= 2:
                escalation_needed = True
                escalation_level = 'urgent'
            elif high_alerts == 1:
                escalation_needed = True
                escalation_level = 'attention'
            
            return {
                'escalation_needed': escalation_needed,
                'escalation_level': escalation_level,
                'critical_alerts': critical_alerts,
                'high_alerts': high_alerts,
                'escalation_reason': f"{critical_alerts} critical, {high_alerts} high priority alerts"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to assess escalation needs: {str(e)}")
            return {
                'escalation_needed': False,
                'escalation_level': 'none',
                'error': str(e)
            }
    
    def _escalate_monitoring(self, patient_id: str, escalation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate monitoring based on assessment"""
        try:
            escalation_level = escalation_result.get('escalation_level', 'none')
            
            if escalation_level == 'emergency':
                # Trigger emergency response
                emergency_data = {
                    'patient_id': patient_id,
                    'emergency_type': 'vital_signs_critical',
                    'severity': 'critical',
                    'description': 'Critical vital signs abnormalities detected',
                    'source': 'monitoring_workflow'
                }
                
                escalation_action = self.emergency_agent.assess_emergency(emergency_data)
                
            elif escalation_level == 'urgent':
                # Increase monitoring frequency
                escalation_action = self.monitoring_agent.escalate_monitoring(patient_id, 'urgent')
                
            elif escalation_level == 'attention':
                # Notify medical staff
                escalation_action = self.monitoring_agent.notify_medical_staff(patient_id, 'attention_needed')
                
            else:
                escalation_action = {'success': False, 'message': 'No escalation needed'}
            
            return {
                'escalation_level': escalation_level,
                'escalation_action': escalation_action,
                'escalation_time': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to escalate monitoring: {str(e)}")
            return {
                'escalation_level': 'none',
                'error': str(e)
            }
    
    def _stop_continuous_monitoring(self, patient_id: str) -> Dict[str, Any]:
        """Stop continuous monitoring"""
        try:
            stop_result = self.monitoring_agent.stop_continuous_monitoring(patient_id)
            
            return {
                'success': stop_result.get('success', False),
                'monitoring_stopped': stop_result.get('monitoring_stopped', False),
                'stop_time': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to stop continuous monitoring: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _clear_alert_thresholds(self, patient_id: str) -> Dict[str, Any]:
        """Clear alert thresholds"""
        try:
            clear_result = self.monitoring_agent.clear_alert_thresholds(patient_id)
            
            return {
                'success': clear_result.get('success', False),
                'thresholds_cleared': clear_result.get('thresholds_cleared', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to clear alert thresholds: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_monitoring_summary(self, patient_id: str) -> Dict[str, Any]:
        """Generate monitoring summary"""
        try:
            summary_result = self.monitoring_agent.generate_monitoring_summary(patient_id)
            
            return {
                'success': summary_result.get('success', False),
                'summary_data': summary_result.get('summary', {}),
                'generation_time': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate monitoring summary: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }