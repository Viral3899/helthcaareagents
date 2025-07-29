"""
Monitoring Agent

This agent handles continuous patient monitoring, vital signs analysis,
and automated alert generation for abnormal conditions.
"""

from typing import Dict, List, Any, Optional
from langchain_core.tools import BaseTool
from agents.base_agent import BaseHealthcareAgent
from utils.logger import log_agent_event
from database.models import VitalSigns, Alert, AlertSeverity
from database.connection import get_db_session
from datetime import datetime, timedelta
import json

class MonitoringAgent(BaseHealthcareAgent):
    """AI agent for patient monitoring and alerting"""
    def __init__(self, tools: Dict[str, Any]):
        system_prompt = """You are a Monitoring Agent responsible for continuously monitoring patient vital signs and health status.

Your responsibilities include:
1. Analyzing real-time vital signs data
2. Detecting abnormal or critical values
3. Generating alerts for medical staff
4. Recommending interventions or escalations
5. Ensuring patient safety and rapid response

Always act promptly and escalate critical situations."""
        monitoring_tools = [
            tools.get('database', None),
            tools.get('medical', None),
            tools.get('notification', None),
            tools.get('validation', None)
        ]
        monitoring_tools = [tool for tool in monitoring_tools if tool is not None]
        super().__init__("MonitoringAgent", system_prompt, monitoring_tools)
        self.logger = log_agent_event
    
    def analyze_vital_signs(self, vital_signs_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze vital signs and generate alerts if needed"""
        try:
            # Prepare analysis input
            analysis_input = self._prepare_analysis_input(vital_signs_data)
            
            # Execute vital signs analysis
            result = self.execute(analysis_input)
            
            if result['success']:
                # Parse analysis results
                analysis_result = self._parse_analysis_result(result['result'])
                
                # Create alerts if abnormalities detected
                alerts_created = []
                if analysis_result.get('abnormalities'):
                    alerts_created = self._create_alerts(vital_signs_data, analysis_result)
                
                # Log monitoring event
                self.logger("MonitoringAgent", "vital_signs_analyzed", 
                           f"Vital signs analyzed for patient {vital_signs_data.get('patient_id', 'unknown')}, {len(alerts_created)} alerts created")
                
                return {
                    'success': True,
                    'analysis': analysis_result,
                    'alerts_created': alerts_created,
                    'assessment': result['result']
                }
            else:
                self.logger("MonitoringAgent", "analysis_failed", 
                           f"Vital signs analysis failed: {result.get('error', 'Unknown error')}")
                return result
                
        except Exception as e:
            self.logger("MonitoringAgent", "analysis_error", f"Vital signs analysis error: {str(e)}")
            return {
                'success': False,
                'error': f"Vital signs analysis failed: {str(e)}"
            }
    
    def _prepare_analysis_input(self, vital_signs_data: Dict[str, Any]) -> str:
        """Prepare input for vital signs analysis"""
        input_parts = []
        
        # Patient information
        if 'patient_id' in vital_signs_data:
            input_parts.append(f"Patient ID: {vital_signs_data['patient_id']}")
        
        if 'age' in vital_signs_data:
            input_parts.append(f"Age: {vital_signs_data['age']}")
        
        if 'gender' in vital_signs_data:
            input_parts.append(f"Gender: {vital_signs_data['gender']}")
        
        # Vital signs
        vitals = vital_signs_data.get('vital_signs', {})
        if vitals:
            vitals_str = []
            for vital, value in vitals.items():
                if value is not None:
                    vitals_str.append(f"{vital}: {value}")
            if vitals_str:
                input_parts.append(f"Current Vital Signs: {', '.join(vitals_str)}")
        
        # Previous vital signs for trend analysis
        if 'previous_vitals' in vital_signs_data:
            prev_vitals = vital_signs_data['previous_vitals']
            if isinstance(prev_vitals, list) and len(prev_vitals) > 0:
                input_parts.append(f"Previous Vital Signs (last 3 readings): {json.dumps(prev_vitals[:3])}")
        
        # Medical history
        if 'medical_history' in vital_signs_data:
            history = vital_signs_data['medical_history']
            if isinstance(history, list):
                history_str = ", ".join(history)
            else:
                history_str = str(history)
            input_parts.append(f"Medical History: {history_str}")
        
        # Current medications
        if 'medications' in vital_signs_data:
            meds = vital_signs_data['medications']
            if isinstance(meds, list):
                meds_str = ", ".join(meds)
            else:
                meds_str = str(meds)
            input_parts.append(f"Current Medications: {meds_str}")
        
        # Allergies
        if 'allergies' in vital_signs_data:
            allergies = vital_signs_data['allergies']
            if isinstance(allergies, list):
                allergies_str = ", ".join(allergies)
            else:
                allergies_str = str(allergies)
            input_parts.append(f"Allergies: {allergies_str}")
        
        # Additional context
        if 'additional_context' in vital_signs_data:
            input_parts.append(f"Additional Context: {vital_signs_data['additional_context']}")
        
        # Create analysis prompt
        analysis_prompt = f"""
Please analyze these patient vital signs for abnormalities and trends:

{chr(10).join(input_parts)}

Based on the above information, please:
1. Assess if any vital signs are outside normal ranges
2. Identify any concerning trends or patterns
3. Determine alert severity for any abnormalities
4. Recommend monitoring frequency adjustments
5. Suggest any immediate actions needed
6. Provide overall health status assessment

Format your response as:
OVERALL_STATUS: [normal/abnormal/concerning]
ABNORMALITIES: [list any abnormal vital signs with values and severity]
TRENDS: [any concerning trends or patterns]
ALERT_SEVERITY: [critical/high/medium/low/none]
RECOMMENDED_ACTIONS: [immediate actions needed]
MONITORING_FREQUENCY: [suggested monitoring frequency]
ASSESSMENT: [brief health status assessment]
"""
        
        return analysis_prompt
    
    def _parse_analysis_result(self, result: str) -> Dict[str, Any]:
        """Parse analysis result from agent output"""
        try:
            analysis = {
                'overall_status': 'normal',
                'abnormalities': [],
                'trends': [],
                'alert_severity': 'none',
                'recommended_actions': [],
                'monitoring_frequency': 'standard',
                'assessment': ''
            }
            
            lines = result.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('OVERALL_STATUS:'):
                    status = line.split(':', 1)[1].strip().lower()
                    analysis['overall_status'] = status
                elif line.startswith('ABNORMALITIES:'):
                    current_section = 'abnormalities'
                elif line.startswith('TRENDS:'):
                    current_section = 'trends'
                elif line.startswith('ALERT_SEVERITY:'):
                    severity = line.split(':', 1)[1].strip().lower()
                    analysis['alert_severity'] = severity
                elif line.startswith('RECOMMENDED_ACTIONS:'):
                    current_section = 'recommended_actions'
                elif line.startswith('MONITORING_FREQUENCY:'):
                    frequency = line.split(':', 1)[1].strip()
                    analysis['monitoring_frequency'] = frequency
                elif line.startswith('ASSESSMENT:'):
                    assessment = line.split(':', 1)[1].strip()
                    analysis['assessment'] = assessment
                elif line and current_section and line.startswith('-'):
                    item = line[1:].strip()
                    if current_section in analysis:
                        analysis[current_section].append(item)
            
            return analysis
            
        except Exception as e:
            self.logger("MonitoringAgent", "parse_error", f"Failed to parse analysis result: {str(e)}")
            return {
                'overall_status': 'normal',
                'abnormalities': [],
                'trends': [],
                'alert_severity': 'none',
                'recommended_actions': [],
                'monitoring_frequency': 'standard',
                'assessment': 'Analysis completed successfully'
            }
    
    def _create_alerts(self, vital_signs_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create alerts based on analysis results"""
        alerts_created = []
        
        try:
            with get_db_session() as session:
                # Map severity string to enum
                severity_map = {
                    'critical': AlertSeverity.CRITICAL,
                    'high': AlertSeverity.HIGH,
                    'medium': AlertSeverity.MEDIUM,
                    'low': AlertSeverity.LOW
                }
                
                severity = severity_map.get(analysis_result['alert_severity'], AlertSeverity.MEDIUM)
                
                if analysis_result['abnormalities']:
                    # Create alert for abnormalities
                    alert = Alert(
                        patient_id=vital_signs_data['patient_id'],
                        alert_type='vital_signs',
                        severity=severity,
                        title='Abnormal Vital Signs Detected',
                        message=f"Monitoring system detected: {', '.join(analysis_result['abnormalities'])}",
                        source='monitoring_agent'
                    )
                    
                    session.add(alert)
                    session.commit()
                    session.refresh(alert)
                    
                    alerts_created.append({
                        'id': str(alert.id),
                        'type': 'vital_signs',
                        'severity': severity.value,
                        'message': alert.message
                    })
                
                if analysis_result['trends']:
                    # Create alert for concerning trends
                    trend_alert = Alert(
                        patient_id=vital_signs_data['patient_id'],
                        alert_type='trend_analysis',
                        severity=AlertSeverity.MEDIUM,
                        title='Concerning Health Trends Detected',
                        message=f"Trend analysis shows: {', '.join(analysis_result['trends'])}",
                        source='monitoring_agent'
                    )
                    
                    session.add(trend_alert)
                    session.commit()
                    session.refresh(trend_alert)
                    
                    alerts_created.append({
                        'id': str(trend_alert.id),
                        'type': 'trend_analysis',
                        'severity': 'medium',
                        'message': trend_alert.message
                    })
                
        except Exception as e:
            self.logger("MonitoringAgent", "alert_error", f"Failed to create alerts: {str(e)}")
        
        return alerts_created
    
    def get_monitoring_statistics(self, patient_id: Optional[str] = None) -> Dict[str, Any]:
        """Get monitoring statistics"""
        try:
            with get_db_session() as session:
                # Base query
                vital_signs_query = session.query(VitalSigns)
                alerts_query = session.query(Alert)
                
                if patient_id:
                    vital_signs_query = vital_signs_query.filter(VitalSigns.patient_id == patient_id)
                    alerts_query = alerts_query.filter(Alert.patient_id == patient_id)
                
                # Get vital signs statistics
                total_vital_signs = vital_signs_query.count()
                
                # Get recent vital signs (last 24 hours)
                yesterday = datetime.utcnow() - timedelta(days=1)
                recent_vital_signs = vital_signs_query.filter(
                    VitalSigns.recorded_at >= yesterday
                ).count()
                
                # Get alerts statistics
                total_alerts = alerts_query.count()
                active_alerts = alerts_query.filter(Alert.resolved == False).count()
                
                # Get alerts by severity
                severity_counts = {}
                for severity in AlertSeverity:
                    count = alerts_query.filter(Alert.severity == severity).count()
                    severity_counts[severity.value] = count
                
                # Get recent alerts (last 24 hours)
                recent_alerts = alerts_query.filter(
                    Alert.created_at >= yesterday
                ).count()
                
                return {
                    'success': True,
                    'statistics': {
                        'total_vital_signs': total_vital_signs,
                        'recent_vital_signs_24h': recent_vital_signs,
                        'total_alerts': total_alerts,
                        'active_alerts': active_alerts,
                        'recent_alerts_24h': recent_alerts,
                        'alerts_by_severity': severity_counts
                    }
                }
                
        except Exception as e:
            self.logger("MonitoringAgent", "stats_error", f"Failed to get monitoring statistics: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to get monitoring statistics: {str(e)}"
            }
    
    def get_patient_vital_trends(self, patient_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get patient vital signs trends over time"""
        try:
            with get_db_session() as session:
                # Get vital signs for the specified time period
                start_time = datetime.utcnow() - timedelta(hours=hours)
                
                vital_signs = session.query(VitalSigns).filter(
                    VitalSigns.patient_id == patient_id,
                    VitalSigns.recorded_at >= start_time
                ).order_by(VitalSigns.recorded_at).all()
                
                # Organize data by vital sign type
                trends = {
                    'heart_rate': [],
                    'systolic_bp': [],
                    'diastolic_bp': [],
                    'temperature': [],
                    'oxygen_saturation': [],
                    'respiratory_rate': [],
                    'blood_glucose': []
                }
                
                for vs in vital_signs:
                    if vs.heart_rate is not None:
                        trends['heart_rate'].append({
                            'value': vs.heart_rate,
                            'timestamp': vs.recorded_at.isoformat()
                        })
                    if vs.systolic_bp is not None:
                        trends['systolic_bp'].append({
                            'value': vs.systolic_bp,
                            'timestamp': vs.recorded_at.isoformat()
                        })
                    if vs.diastolic_bp is not None:
                        trends['diastolic_bp'].append({
                            'value': vs.diastolic_bp,
                            'timestamp': vs.recorded_at.isoformat()
                        })
                    if vs.temperature is not None:
                        trends['temperature'].append({
                            'value': vs.temperature,
                            'timestamp': vs.recorded_at.isoformat()
                        })
                    if vs.oxygen_saturation is not None:
                        trends['oxygen_saturation'].append({
                            'value': vs.oxygen_saturation,
                            'timestamp': vs.recorded_at.isoformat()
                        })
                    if vs.respiratory_rate is not None:
                        trends['respiratory_rate'].append({
                            'value': vs.respiratory_rate,
                            'timestamp': vs.recorded_at.isoformat()
                        })
                    if vs.blood_glucose is not None:
                        trends['blood_glucose'].append({
                            'value': vs.blood_glucose,
                            'timestamp': vs.recorded_at.isoformat()
                        })
                
                return {
                    'success': True,
                    'patient_id': patient_id,
                    'time_period_hours': hours,
                    'trends': trends,
                    'total_readings': len(vital_signs)
                }
                
        except Exception as e:
            self.logger("MonitoringAgent", "trends_error", f"Failed to get vital trends: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to get vital trends: {str(e)}"
            }
