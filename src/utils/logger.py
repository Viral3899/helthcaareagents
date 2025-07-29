"""
Logger Utility

This module provides centralized logging functionality for the healthcare management system.
"""

import logging
import logging.handlers
import os
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Configure logging
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    else:
        # Default log file
        default_log_file = logs_dir / f"healthcare_system_{datetime.now(UTC).strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            default_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name"""
    return logging.getLogger(name)

def log_agent_event(agent_name: str, event_type: str, message: str, extra_data: Optional[Dict[str, Any]] = None) -> None:
    """Log agent events with structured data"""
    logger = get_logger("agent_events")
    
    log_data = {
        'agent_name': agent_name,
        'event_type': event_type,
        'message': message,
        'timestamp': datetime.now(UTC).isoformat(),
        'extra_data': extra_data or {}
    }
    
    logger.info(f"Agent Event: {json.dumps(log_data)}")

def log_patient_event(patient_id: str, event_type: str, message: str, extra_data: Optional[Dict[str, Any]] = None) -> None:
    """Log patient-related events"""
    logger = get_logger("patient_events")
    
    log_data = {
        'patient_id': patient_id,
        'event_type': event_type,
        'message': message,
        'timestamp': datetime.now(UTC).isoformat(),
        'extra_data': extra_data or {}
    }
    
    logger.info(f"Patient Event: {json.dumps(log_data)}")

def log_system_event(event_type: str, message: str, severity: str = "INFO", extra_data: Optional[Dict[str, Any]] = None) -> None:
    """Log system events"""
    logger = get_logger("system_events")
    
    log_data = {
        'event_type': event_type,
        'message': message,
        'severity': severity,
        'timestamp': datetime.now(UTC).isoformat(),
        'extra_data': extra_data or {}
    }
    
    if severity.upper() == "ERROR":
        logger.error(f"System Event: {json.dumps(log_data)}")
    elif severity.upper() == "WARNING":
        logger.warning(f"System Event: {json.dumps(log_data)}")
    else:
        logger.info(f"System Event: {json.dumps(log_data)}")

def log_security_event(event_type: str, message: str, user_id: Optional[str] = None, ip_address: Optional[str] = None, extra_data: Optional[Dict[str, Any]] = None) -> None:
    """Log security-related events"""
    logger = get_logger("security_events")
    
    log_data = {
        'event_type': event_type,
        'message': message,
        'user_id': user_id,
        'ip_address': ip_address,
        'timestamp': datetime.now(UTC).isoformat(),
        'extra_data': extra_data or {}
    }
    
    logger.warning(f"Security Event: {json.dumps(log_data)}")

def log_performance_event(operation: str, duration: float, success: bool, extra_data: Optional[Dict[str, Any]] = None) -> None:
    """Log performance metrics"""
    logger = get_logger("performance_events")
    
    log_data = {
        'operation': operation,
        'duration_seconds': duration,
        'success': success,
        'timestamp': datetime.now(UTC).isoformat(),
        'extra_data': extra_data or {}
    }
    
    logger.info(f"Performance Event: {json.dumps(log_data)}")

def log_database_event(operation: str, table: str, record_id: Optional[str] = None, success: bool = True, extra_data: Optional[Dict[str, Any]] = None) -> None:
    """Log database operations"""
    logger = get_logger("database_events")
    
    log_data = {
        'operation': operation,
        'table': table,
        'record_id': record_id,
        'success': success,
        'timestamp': datetime.now(UTC).isoformat(),
        'extra_data': extra_data or {}
    }
    
    if success:
        logger.info(f"Database Event: {json.dumps(log_data)}")
    else:
        logger.error(f"Database Event: {json.dumps(log_data)}")

def log_api_event(endpoint: str, method: str, status_code: int, duration: float, user_id: Optional[str] = None, extra_data: Optional[Dict[str, Any]] = None) -> None:
    """Log API requests and responses"""
    logger = get_logger("api_events")
    
    log_data = {
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'duration_seconds': duration,
        'user_id': user_id,
        'timestamp': datetime.now(UTC).isoformat(),
        'extra_data': extra_data or {}
    }
    
    if status_code >= 400:
        logger.warning(f"API Event: {json.dumps(log_data)}")
    else:
        logger.info(f"API Event: {json.dumps(log_data)}")

def log_error(error: Exception, context: Optional[str] = None, extra_data: Optional[Dict[str, Any]] = None) -> None:
    """Log errors with context"""
    logger = get_logger("errors")
    
    log_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context,
        'timestamp': datetime.now(UTC).isoformat(),
        'extra_data': extra_data or {}
    }
    
    logger.error(f"Error: {json.dumps(log_data)}", exc_info=True)

def log_audit_trail(user_id: str, action: str, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Log audit trail events"""
    logger = get_logger("audit_trail")
    
    log_data = {
        'user_id': user_id,
        'action': action,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'timestamp': datetime.now(UTC).isoformat(),
        'details': details or {}
    }
    
    logger.info(f"Audit Trail: {json.dumps(log_data)}")

def log_health_check(component: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Log health check results"""
    logger = get_logger("health_checks")
    
    log_data = {
        'component': component,
        'status': status,
        'timestamp': datetime.now(UTC).isoformat(),
        'details': details or {}
    }
    
    if status.lower() == "healthy":
        logger.info(f"Health Check: {json.dumps(log_data)}")
    else:
        logger.warning(f"Health Check: {json.dumps(log_data)}")

def log_notification(notification_type: str, recipient: str, success: bool, details: Optional[Dict[str, Any]] = None) -> None:
    """Log notification events"""
    logger = get_logger("notifications")
    
    log_data = {
        'notification_type': notification_type,
        'recipient': recipient,
        'success': success,
        'timestamp': datetime.now(UTC).isoformat(),
        'details': details or {}
    }
    
    if success:
        logger.info(f"Notification: {json.dumps(log_data)}")
    else:
        logger.warning(f"Notification: {json.dumps(log_data)}")

def log_workflow_event(workflow_name: str, step: str, status: str, patient_id: Optional[str] = None, extra_data: Optional[Dict[str, Any]] = None) -> None:
    """Log workflow events"""
    logger = get_logger("workflow_events")
    
    log_data = {
        'workflow_name': workflow_name,
        'step': step,
        'status': status,
        'patient_id': patient_id,
        'timestamp': datetime.now(UTC).isoformat(),
        'extra_data': extra_data or {}
    }
    
    if status.lower() == "completed":
        logger.info(f"Workflow Event: {json.dumps(log_data)}")
    elif status.lower() == "failed":
        logger.error(f"Workflow Event: {json.dumps(log_data)}")
    else:
        logger.info(f"Workflow Event: {json.dumps(log_data)}")

def log_alert_event(alert_type: str, severity: str, patient_id: str, message: str, extra_data: Optional[Dict[str, Any]] = None) -> None:
    """Log alert events"""
    logger = get_logger("alert_events")
    
    log_data = {
        'alert_type': alert_type,
        'severity': severity,
        'patient_id': patient_id,
        'message': message,
        'timestamp': datetime.now(UTC).isoformat(),
        'extra_data': extra_data or {}
    }
    
    if severity.lower() in ["critical", "high"]:
        logger.warning(f"Alert Event: {json.dumps(log_data)}")
    else:
        logger.info(f"Alert Event: {json.dumps(log_data)}")

def log_data_validation(data_type: str, validation_result: Dict[str, Any], extra_data: Optional[Dict[str, Any]] = None) -> None:
    """Log data validation results"""
    logger = get_logger("data_validation")
    
    log_data = {
        'data_type': data_type,
        'validation_result': validation_result,
        'timestamp': datetime.now(UTC).isoformat(),
        'extra_data': extra_data or {}
    }
    
    if validation_result.get('is_valid', True):
        logger.info(f"Data Validation: {json.dumps(log_data)}")
    else:
        logger.warning(f"Data Validation: {json.dumps(log_data)}")

def log_tool_usage(tool_name: str, input_data: Dict[str, Any], output_data: Dict[str, Any], duration: float, success: bool) -> None:
    """Log tool usage events"""
    logger = get_logger("tool_usage")
    
    log_data = {
        'tool_name': tool_name,
        'input_data': input_data,
        'output_data': output_data,
        'duration_seconds': duration,
        'success': success,
        'timestamp': datetime.now(UTC).isoformat()
    }
    
    if success:
        logger.info(f"Tool Usage: {json.dumps(log_data)}")
    else:
        logger.warning(f"Tool Usage: {json.dumps(log_data)}")

def log_chatbot_event(session_id: str, event_type: str, message: str, level: str = "INFO"):
    """Log chatbot-specific events"""
    logger = logging.getLogger('chatbot')
    
    log_entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "event_type": event_type,
        "message": message,
        "level": level
    }
    
    if level == "ERROR":
        logger.error(f"Chatbot Event: {json.dumps(log_entry)}")
    elif level == "WARNING":
        logger.warning(f"Chatbot Event: {json.dumps(log_entry)}")
    else:
        logger.info(f"Chatbot Event: {json.dumps(log_entry)}")
    
    # Also write to chatbot-specific log file
    try:
        with open('logs/chatbot.log', 'a') as f:
            f.write(f"{json.dumps(log_entry)}\n")
    except Exception as e:
        logger.error(f"Failed to write to chatbot log: {str(e)}")

# Initialize logging when module is imported
setup_logging()
