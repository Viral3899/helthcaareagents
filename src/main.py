#!/usr/bin/env python3
"""
Healthcare Management System - Main Application Entry Point

This module serves as the main entry point for the healthcare management system,
initializing all components and starting the Flask API server.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any
import time

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
        'medical': DrugInteractionTool(),
        'notification': CreateAlertTool(),
        'validation': ValidationTools()
    }

def initialize_agents(tools: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize all agents with their required tools"""
    return {
        'chatbot': ChatbotAgent(tools),
        'emergency': EmergencyAgent(tools),
        'triage': TriageAgent(tools),
        'monitoring': MonitoringAgent(tools),
        'treatment': TreatmentAgent(tools),
        'medical_records': MedicalRecordsAgent(tools),
        'scheduling': SchedulingAgent(tools)
    }

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "agents": list(app.config.get('AGENTS', {}).keys()),
        "tools": list(app.config.get('TOOLS', {}).keys())
    }

@app.route('/')
def index():
    """Root endpoint with navigation"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Healthcare Management System</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .endpoint a { color: #007bff; text-decoration: none; }
            .endpoint a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 Healthcare Management System</h1>
            <p>Welcome to the multi-agent healthcare management system.</p>
            
            <h2>Available Endpoints:</h2>
            <div class="endpoint">
                <a href="/chatbot">🤖 Chatbot Interface</a>
                <p>AI-powered conversational interface for patient interactions</p>
            </div>
            <div class="endpoint">
                <a href="/patient-entry">📝 Patient Registration</a>
                <p>Patient registration and medical history entry</p>
            </div>
            <div class="endpoint">
                <a href="/api/docs">📚 API Documentation</a>
                <p>Interactive API documentation</p>
            </div>
            <div class="endpoint">
                <a href="/health">💚 Health Check</a>
                <p>System health and status information</p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/chatbot')
def chatbot_ui():
    """Chatbot UI endpoint"""
    return send_from_directory(app.static_folder, 'chatbot.html')

def main():
    """Main entry point for the application"""
    app = create_app()
    
    # Run the application
    host = config.API_HOST
    port = config.API_PORT
    debug = True
    
    print(f"Starting Healthcare Management System on {host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Health check: http://{host}:{port}/health")
    print(f"Chatbot: http://{host}:{port}/chatbot")
    print(f"Patient Entry: http://{host}:{port}/patient-entry")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )

if __name__ == "__main__":
    main()

