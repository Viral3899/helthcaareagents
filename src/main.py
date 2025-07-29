#!/usr/bin/env python3
"""
Healthcare Management System - Main Application Entry Point

This module serves as the main entry point for the healthcare management system,
initializing all components and starting the API server.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, send_from_directory, jsonify
from config.settings import Config
from database.connection import init_database
from api.routes import api_bp
from api.chatbot_routes import chatbot_bp
from api.patient_entry_form import patient_form_bp
from api.middleware import setup_middleware
from utils.logger import setup_logging
from agents.triage_agent import TriageAgent
from agents.emergency_agent import EmergencyAgent
from agents.monitoring_agent import MonitoringAgent
from agents.treatment_agent import TreatmentAgent
from agents.medical_records_agent import MedicalRecordsAgent
from agents.scheduling_agent import SchedulingAgent
from agents.chatbot_agent import ChatbotAgent

from tools.database_tools import PatientSearchTool, GetPatientRecordTool, RecordVitalSignsTool, GetTriageQueueTool, CheckDrugInteractionsTool
from tools.medical_tools import DrugInteractionTool, MedicalCodeLookupTool, SymptomAnalysisTool, VitalSignsAnalysisTool
from tools.notification_tools import CreateAlertTool, SendMessageTool, EmergencyNotificationTool, PatientNotificationTool, StaffNotificationTool
from tools.validation_tools import ValidationTools

# Global application instance
app = Flask(__name__)
config = Config()

def create_app():
    """Create and configure the Flask application"""
    
    # Configure Flask app
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    
    # Setup logging
    setup_logging(config.LOG_LEVEL, config.LOG_FILE)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        init_database()
        logger.info("Database connection established successfully")
        
        # Initialize tools
        logger.info("Initializing tools...")
        tools = initialize_tools()
        logger.info("Tools initialized successfully")
        
        # Initialize agents
        logger.info("Initializing agents...")
        agents = initialize_agents(tools)
        logger.info("Agents initialized successfully")
        
        # Setup API routes
        logger.info("Setting up API routes...")
        app.register_blueprint(api_bp, url_prefix='/api')
        app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
        app.register_blueprint(patient_form_bp)  # /patient-entry
        
        # Setup static files
        app.static_folder = 'static'
        app.static_url_path = '/static'
        
        # Setup middleware
        setup_middleware(app)
        
        # Store agents and tools in app context
        app.config['AGENTS'] = agents
        app.config['TOOLS'] = tools
        
        logger.info("Application initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise
    
    return app

def initialize_tools():
    """Initialize all tools"""
    return {
        'database': PatientSearchTool(),
        'medical_drug_interaction': DrugInteractionTool(),
        'medical_code_lookup': MedicalCodeLookupTool(),
        'medical_symptom_analysis': SymptomAnalysisTool(),
        'medical_vital_signs_analysis': VitalSignsAnalysisTool(),
        'notification_create_alert': CreateAlertTool(),
        'notification_send_message': SendMessageTool(),
        'notification_emergency': EmergencyNotificationTool(),
        'notification_patient': PatientNotificationTool(),
        'notification_staff': StaffNotificationTool(),
        'validation': ValidationTools()
    }

def initialize_agents(tools: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize all AI agents"""
    agents = {}
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize specialized agents
        agents['triage'] = TriageAgent(tools)
        agents['emergency'] = EmergencyAgent(tools)
        agents['monitoring'] = MonitoringAgent(tools)
        agents['treatment'] = TreatmentAgent(tools)
        agents['medical_records'] = MedicalRecordsAgent(tools)
        agents['scheduling'] = SchedulingAgent(tools)
        agents['chatbot'] = ChatbotAgent(tools)
        
        logger.info(f"Initialized {len(agents)} agents successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize agents: {str(e)}")
        raise
    
    return agents

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'Healthcare Management System',
        'version': '1.0.0'
    }

@app.route('/')
def index():
    return '''
    <h2>Healthcare Management System</h2>
    <ul>
      <li><a href="/patient-entry">Patient Entry Form (UI)</a></li>
      <li><a href="/static/patient_entry_form.html">Patient Entry Form (AJAX)</a></li>
      <li><a href="/static/patient_entry_chat.html">Patient Entry Chat (UI)</a></li>
      <li><a href="/chatbot">Chatbot UI</a></li>
      <li><a href="/api/docs">API Documentation</a></li>
      <li><a href="/api/patients">View Patients (API)</a></li>
    </ul>
    '''

# Optionally, serve chatbot.html at /chatbot
@app.route('/chatbot')
def chatbot_ui():
    return send_from_directory(app.static_folder, 'chatbot.html')

def main():
    """Main application entry point"""
    try:
        # Create application
        app = create_app()
        
        # Get configuration
        host = config.API_HOST
        port = config.API_PORT
        debug = os.getenv('FLASK_ENV') == 'development'
        
        # Start the application
        print(f"Starting Healthcare Management System on {host}:{port}")
        print(f"Debug mode: {debug}")
        print(f"Health check: http://{host}:{port}/health")
        print(f"API documentation: http://{host}:{port}/api/docs")
        
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\nShutting down Healthcare Management System...")
        sys.exit(0)
    except Exception as e:
        print(f"Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
