import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
    DATABASE_PORT = os.getenv('DATABASE_PORT', '5432')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'healthcare_db')
    DATABASE_USER = os.getenv('DATABASE_USER', 'postgres')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'password')
    
    # LLM Configuration
    GROQ_API_KEY = os.getenv('GROQ_API_KEY',)
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768')
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.1'))
    LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '2048'))
    
    # API Configuration
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '5000'))
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Healthcare System Configuration
    TRIAGE_LEVELS = {
        1: {'name': 'Immediate', 'wait_time': 0, 'color': 'red'},
        2: {'name': 'Emergent', 'wait_time': 15, 'color': 'orange'},
        3: {'name': 'Urgent', 'wait_time': 30, 'color': 'yellow'},
        4: {'name': 'Less Urgent', 'wait_time': 60, 'color': 'green'},
        5: {'name': 'Non-urgent', 'wait_time': 120, 'color': 'blue'}
    }
    
    # Monitoring Thresholds
    VITAL_SIGNS_THRESHOLDS = {
        'heart_rate': {'min': 60, 'max': 100},
        'systolic_bp': {'min': 90, 'max': 140},
        'diastolic_bp': {'min': 60, 'max': 90},
        'temperature': {'min': 97.0, 'max': 99.5},
        'oxygen_saturation': {'min': 95.0, 'max': 100.0},
        'respiratory_rate': {'min': 12, 'max': 20}
    }
    
    # Emergency Alert Configuration
    EMERGENCY_ALERT_TYPES = [
        'Cardiac', 'Respiratory', 'Neurological', 'Temperature',
        'Blood Pressure', 'Medication', 'Fall', 'Other'
    ]
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/healthcare_system.log')
    
    @property
    def database_url(self):
        return f"mysql+pymysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"