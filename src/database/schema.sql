-- Healthcare Management System Database Schema - MySQL Compatible
-- This file contains the MySQL-compatible SQL schema for all healthcare-related tables

-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    mrn VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    emergency_contact JSON,
    insurance_info JSON,
    allergies JSON,
    medications JSON,
    medical_history JSON,
    status ENUM('admitted', 'discharged', 'transferred', 'deceased', 'pending') DEFAULT 'pending',
    admission_date TIMESTAMP NULL,
    discharge_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_patients_mrn (mrn),
    INDEX idx_patients_status (status),
    INDEX idx_patients_name (last_name, first_name)
);

-- Medical records table
CREATE TABLE IF NOT EXISTS medical_records (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    patient_id VARCHAR(36) NOT NULL,
    record_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    doctor_id VARCHAR(50),
    department VARCHAR(100),
    diagnosis_codes JSON,
    medications JSON,
    procedures JSON,
    attachments JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_medical_records_patient (patient_id),
    INDEX idx_medical_records_type (record_type)
);

-- Appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    patient_id VARCHAR(36) NOT NULL,
    doctor_id VARCHAR(50) NOT NULL,
    department VARCHAR(100),
    appointment_type VARCHAR(50),
    scheduled_date TIMESTAMP NOT NULL,
    duration INTEGER,
    status ENUM('scheduled', 'confirmed', 'cancelled', 'completed', 'no_show') DEFAULT 'scheduled',
    notes TEXT,
    room_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_appointments_patient (patient_id),
    INDEX idx_appointments_date (scheduled_date),
    INDEX idx_appointments_status (status),
    INDEX idx_appointments_patient_date (patient_id, scheduled_date)
);

-- Vital signs table
CREATE TABLE IF NOT EXISTS vital_signs (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    patient_id VARCHAR(36) NOT NULL,
    heart_rate FLOAT,
    systolic_bp FLOAT,
    diastolic_bp FLOAT,
    temperature FLOAT,
    oxygen_saturation FLOAT,
    respiratory_rate FLOAT,
    blood_glucose FLOAT,
    pain_level INTEGER,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    device_id VARCHAR(50),
    notes TEXT,
    
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_vital_signs_patient (patient_id),
    INDEX idx_vital_signs_recorded (recorded_at),
    INDEX idx_vital_signs_patient_date (patient_id, recorded_at)
);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    patient_id VARCHAR(36) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    source VARCHAR(100),
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(50),
    acknowledged_at TIMESTAMP NULL,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_alerts_patient (patient_id),
    INDEX idx_alerts_severity (severity),
    INDEX idx_alerts_created (created_at),
    INDEX idx_alerts_patient_severity (patient_id, severity)
);

-- Treatments table
CREATE TABLE IF NOT EXISTS treatments (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    patient_id VARCHAR(36) NOT NULL,
    treatment_type VARCHAR(100) NOT NULL,
    diagnosis TEXT,
    treatment_plan TEXT NOT NULL,
    medications JSON,
    procedures JSON,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NULL,
    status VARCHAR(50) DEFAULT 'active',
    doctor_id VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_treatments_patient (patient_id),
    INDEX idx_treatments_status (status)
);

-- Triage assessments table
CREATE TABLE IF NOT EXISTS triage_assessments (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    patient_id VARCHAR(36) NOT NULL,
    triage_level ENUM('1', '2', '3', '4', '5') NOT NULL,
    chief_complaint TEXT NOT NULL,
    symptoms JSON,
    vital_signs_id VARCHAR(36),
    assessment_notes TEXT,
    assigned_doctor VARCHAR(50),
    wait_time_estimate INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (vital_signs_id) REFERENCES vital_signs(id),
    INDEX idx_triage_patient (patient_id),
    INDEX idx_triage_level (triage_level)
);

-- Emergency responses table
CREATE TABLE IF NOT EXISTS emergency_responses (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    patient_id VARCHAR(36) NOT NULL,
    emergency_type VARCHAR(100) NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    description TEXT NOT NULL,
    response_team JSON,
    response_time INTEGER,
    actions_taken JSON,
    outcome VARCHAR(100),
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_emergency_patient (patient_id),
    INDEX idx_emergency_type (emergency_type)
);

-- Create views for patient summary
CREATE OR REPLACE VIEW patient_summary AS
SELECT 
    p.id,
    p.mrn,
    p.first_name,
    p.last_name,
    p.date_of_birth,
    p.gender,
    p.status,
    p.admission_date,
    COUNT(DISTINCT mr.id) as medical_records_count,
    COUNT(DISTINCT a.id) as appointments_count,
    COUNT(DISTINCT vs.id) as vital_signs_count,
    COUNT(DISTINCT al.id) as active_alerts_count,
    COUNT(DISTINCT t.id) as active_treatments_count
FROM patients p
LEFT JOIN medical_records mr ON p.id = mr.patient_id
LEFT JOIN appointments a ON p.id = a.patient_id
LEFT JOIN vital_signs vs ON p.id = vs.patient_id
LEFT JOIN alerts al ON p.id = al.patient_id AND al.resolved = FALSE
LEFT JOIN treatments t ON p.id = t.patient_id AND t.status = 'active'
GROUP BY p.id, p.mrn, p.first_name, p.last_name, p.date_of_birth, p.gender, p.status, p.admission_date;

-- Create view for critical alerts
CREATE OR REPLACE VIEW critical_alerts AS
SELECT 
    a.id,
    a.patient_id,
    p.first_name,
    p.last_name,
    p.mrn,
    a.alert_type,
    a.severity,
    a.title,
    a.message,
    a.created_at,
    a.acknowledged,
    a.resolved
FROM alerts a
JOIN patients p ON a.patient_id = p.id
WHERE a.severity IN ('high', 'critical') AND a.resolved = FALSE
ORDER BY a.created_at DESC;