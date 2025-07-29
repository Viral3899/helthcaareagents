-- Sample Data for Healthcare Management System - MySQL Compatible
-- This file contains sample data for testing and development purposes

-- Insert sample patients
INSERT INTO patients (id, mrn, first_name, last_name, date_of_birth, gender, phone, email, address, emergency_contact, insurance_info, allergies, medications, medical_history, status) VALUES
(UUID(), 'MRN001', 'John', 'Smith', '1985-03-15', 'Male', '555-0101', 'john.smith@email.com', '123 Main St, Anytown, USA', 
 JSON_OBJECT('name', 'Jane Smith', 'relationship', 'Spouse', 'phone', '555-0102'),
 JSON_OBJECT('provider', 'Blue Cross', 'policy_number', 'BC123456', 'group_number', 'GRP001'),
 JSON_ARRAY('Penicillin', 'Sulfa drugs'),
 JSON_ARRAY('Lisinopril 10mg daily', 'Metformin 500mg twice daily'),
 JSON_ARRAY('Hypertension', 'Type 2 Diabetes', 'Appendectomy 2010'),
 'admitted'),

(UUID(), 'MRN002', 'Sarah', 'Johnson', '1992-07-22', 'Female', '555-0201', 'sarah.johnson@email.com', '456 Oak Ave, Somewhere, USA',
 JSON_OBJECT('name', 'Mike Johnson', 'relationship', 'Husband', 'phone', '555-0202'),
 JSON_OBJECT('provider', 'Aetna', 'policy_number', 'AE789012', 'group_number', 'GRP002'),
 JSON_ARRAY('Latex', 'Shellfish'),
 JSON_ARRAY('Ibuprofen 400mg as needed', 'Vitamin D 1000IU daily'),
 JSON_ARRAY('Asthma', 'Seasonal allergies'),
 'admitted'),

(UUID(), 'MRN003', 'Michael', 'Brown', '1978-11-08', 'Male', '555-0301', 'michael.brown@email.com', '789 Pine Rd, Elsewhere, USA',
 JSON_OBJECT('name', 'Lisa Brown', 'relationship', 'Wife', 'phone', '555-0302'),
 JSON_OBJECT('provider', 'Cigna', 'policy_number', 'CI345678', 'group_number', 'GRP003'),
 JSON_ARRAY('None known'),
 JSON_ARRAY('Atorvastatin 20mg daily', 'Aspirin 81mg daily'),
 JSON_ARRAY('High cholesterol', 'Heart disease', 'Knee surgery 2015'),
 'pending'),

(UUID(), 'MRN004', 'Emily', 'Davis', '1995-04-30', 'Female', '555-0401', 'emily.davis@email.com', '321 Elm St, Nowhere, USA',
 JSON_OBJECT('name', 'Robert Davis', 'relationship', 'Father', 'phone', '555-0402'),
 JSON_OBJECT('provider', 'UnitedHealth', 'policy_number', 'UH901234', 'group_number', 'GRP004'),
 JSON_ARRAY('Peanuts', 'Tree nuts'),
 JSON_ARRAY('Cetirizine 10mg daily', 'Albuterol inhaler as needed'),
 JSON_ARRAY('Food allergies', 'Eczema'),
 'admitted'),

(UUID(), 'MRN005', 'David', 'Wilson', '1980-12-14', 'Male', '555-0501', 'david.wilson@email.com', '654 Maple Dr, Anywhere, USA',
 JSON_OBJECT('name', 'Jennifer Wilson', 'relationship', 'Sister', 'phone', '555-0502'),
 JSON_OBJECT('provider', 'Humana', 'policy_number', 'HU567890', 'group_number', 'GRP005'),
 JSON_ARRAY('Codeine', 'Morphine'),
 JSON_ARRAY('Omeprazole 20mg daily', 'Tramadol 50mg as needed'),
 JSON_ARRAY('GERD', 'Chronic back pain', 'Gallbladder removal 2018'),
 'discharged');

-- Insert sample medical records
INSERT INTO medical_records (id, patient_id, record_type, title, content, doctor_id, department, diagnosis_codes, medications, procedures) VALUES
(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN001'), 'diagnosis', 'Hypertension Diagnosis', 
 'Patient presents with elevated blood pressure readings over the past 3 months. Systolic consistently above 140 mmHg. Lifestyle modifications recommended along with medication therapy.',
 'DR001', 'Cardiology', JSON_ARRAY('I10'), JSON_ARRAY('Lisinopril 10mg daily'), JSON_ARRAY()),

(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN001'), 'treatment', 'Diabetes Management Plan',
 'Type 2 diabetes management with Metformin therapy. Blood glucose monitoring recommended. Dietary consultation scheduled.',
 'DR002', 'Endocrinology', JSON_ARRAY('E11.9'), JSON_ARRAY('Metformin 500mg twice daily'), JSON_ARRAY()),

(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN002'), 'diagnosis', 'Asthma Assessment',
 'Patient reports wheezing and shortness of breath. Spirometry shows mild obstruction. Asthma diagnosis confirmed.',
 'DR003', 'Pulmonology', JSON_ARRAY('J45.909'), JSON_ARRAY('Albuterol inhaler as needed'), JSON_ARRAY()),

(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN003'), 'lab_result', 'Cholesterol Panel Results',
 'Total cholesterol: 240 mg/dL, LDL: 160 mg/dL, HDL: 45 mg/dL, Triglycerides: 200 mg/dL. Statin therapy recommended.',
 'DR001', 'Cardiology', JSON_ARRAY('E78.5'), JSON_ARRAY('Atorvastatin 20mg daily'), JSON_ARRAY()),

(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN004'), 'diagnosis', 'Food Allergy Assessment',
 'Patient reports severe allergic reactions to peanuts and tree nuts. Epinephrine auto-injector prescribed.',
 'DR004', 'Allergy', JSON_ARRAY('Z91.010'), JSON_ARRAY('Epinephrine auto-injector', 'Cetirizine 10mg daily'), JSON_ARRAY());

-- Insert sample appointments
INSERT INTO appointments (id, patient_id, doctor_id, department, appointment_type, scheduled_date, duration, status, notes, room_number) VALUES
(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN001'), 'DR001', 'Cardiology', 'follow_up', '2024-01-15 10:00:00', 30, 'confirmed', 'Blood pressure check and medication review', '101'),
(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN002'), 'DR003', 'Pulmonology', 'consultation', '2024-01-16 14:30:00', 45, 'scheduled', 'Asthma management review', '205'),
(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN003'), 'DR001', 'Cardiology', 'initial', '2024-01-17 09:00:00', 60, 'scheduled', 'New patient consultation for heart disease', '101'),
(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN004'), 'DR004', 'Allergy', 'follow_up', '2024-01-18 11:15:00', 30, 'confirmed', 'Allergy testing results review', '310'),
(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN005'), 'DR005', 'General Medicine', 'discharge', '2024-01-19 15:00:00', 20, 'scheduled', 'Discharge planning and follow-up instructions', '105');

-- Insert sample vital signs
INSERT INTO vital_signs (id, patient_id, heart_rate, systolic_bp, diastolic_bp, temperature, oxygen_saturation, respiratory_rate, blood_glucose, pain_level, device_id, notes) VALUES
(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN001'), 72, 145, 95, 98.6, 98, 16, 120, 2, 'MON001', 'Blood pressure elevated'),
(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN001'), 75, 142, 92, 98.4, 97, 15, 118, 1, 'MON001', 'Slight improvement'),
(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN002'), 68, 118, 78, 98.8, 96, 18, 95, 3, 'MON002', 'Mild wheezing noted'),
(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN002'), 70, 120, 80, 98.6, 97, 17, 92, 2, 'MON002', 'Respiratory status stable'),
(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN004'), 65, 110, 70, 98.2, 99, 14, 88, 0, 'MON004', 'All vital signs normal');

-- Insert sample alerts
INSERT INTO alerts (id, patient_id, alert_type, severity, title, message, source, acknowledged, resolved) VALUES
(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN001'), 'vital_signs', 'medium', 'Elevated Blood Pressure', 
 'Patient MRN001 has systolic BP of 145 mmHg, above normal range. Consider medication adjustment.', 'monitoring_system', FALSE, FALSE),

(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN002'), 'respiratory', 'low', 'Mild Respiratory Distress',
 'Patient MRN002 showing mild wheezing. Oxygen saturation at 96%. Continue monitoring.', 'monitoring_system', TRUE, FALSE),

(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN004'), 'allergy', 'high', 'Allergy Alert',
 'Patient MRN004 has severe peanut and tree nut allergies. Ensure no exposure to allergens.', 'manual', FALSE, FALSE),

(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN001'), 'medication', 'medium', 'Medication Due',
 'Patient MRN001 due for Metformin dose. Last dose was 8 hours ago.', 'medication_system', FALSE, FALSE);

-- Insert sample treatments
INSERT INTO treatments (id, patient_id, treatment_type, diagnosis, treatment_plan, medications, procedures, start_date, status, doctor_id, notes) VALUES
(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN001'), 'Hypertension Management', 'Essential Hypertension',
 'Lifestyle modifications including low-sodium diet, regular exercise, and medication therapy with Lisinopril.',
 JSON_ARRAY('Lisinopril 10mg daily', 'Low-sodium diet', 'Regular exercise'), JSON_ARRAY(), '2024-01-01 00:00:00', 'active', 'DR001', 'Patient responding well to treatment'),

(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN001'), 'Diabetes Management', 'Type 2 Diabetes',
 'Blood glucose monitoring, dietary management, and Metformin therapy.',
 JSON_ARRAY('Metformin 500mg twice daily', 'Blood glucose monitoring', 'Diabetic diet'), JSON_ARRAY(), '2024-01-01 00:00:00', 'active', 'DR002', 'Blood glucose levels improving'),

(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN002'), 'Asthma Management', 'Mild Persistent Asthma',
 'Inhaled bronchodilator therapy and trigger avoidance education.',
 JSON_ARRAY('Albuterol inhaler as needed', 'Trigger avoidance', 'Peak flow monitoring'), JSON_ARRAY(), '2024-01-05 00:00:00', 'active', 'DR003', 'Asthma well controlled'),

(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN004'), 'Allergy Management', 'Food Allergies',
 'Strict allergen avoidance, emergency action plan, and epinephrine auto-injector training.',
 JSON_ARRAY('Epinephrine auto-injector', 'Allergen avoidance', 'Emergency action plan'), JSON_ARRAY(), '2024-01-10 00:00:00', 'active', 'DR004', 'Patient and family educated on allergen avoidance');

-- Insert sample triage assessments
INSERT INTO triage_assessments (id, patient_id, triage_level, chief_complaint, symptoms, assessment_notes, assigned_doctor, wait_time_estimate) VALUES
(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN001'), '3', 'Chest pain and elevated blood pressure',
 JSON_ARRAY('Chest discomfort', 'Shortness of breath', 'Elevated BP'),
 'Patient reports chest pain for 2 hours. Blood pressure elevated at 145/95. ECG ordered.',
 'DR001', 30),

(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN002'), '4', 'Wheezing and difficulty breathing',
 JSON_ARRAY('Wheezing', 'Shortness of breath', 'Chest tightness'),
 'Patient with known asthma experiencing mild exacerbation. Oxygen saturation 96%.',
 'DR003', 45),

(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN004'), '2', 'Severe allergic reaction',
 JSON_ARRAY('Facial swelling', 'Difficulty breathing', 'Hives'),
 'Patient reports exposure to peanuts. Epinephrine administered. Monitoring required.',
 'DR004', 15);

-- Insert sample emergency responses
INSERT INTO emergency_responses (id, patient_id, emergency_type, severity, description, response_team, response_time, actions_taken, outcome) VALUES
(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN004'), 'Anaphylaxis', 'critical', 
 'Patient experienced severe allergic reaction after accidental peanut exposure.',
 JSON_ARRAY('Dr. Smith', 'Nurse Johnson', 'Respiratory Therapist Brown'), 120,
 JSON_ARRAY('Epinephrine administration', 'Oxygen therapy', 'IV fluids', 'Antihistamines'),
 'Stabilized and admitted for observation'),

(UUID(), (SELECT id FROM patients WHERE mrn = 'MRN001'), 'Chest Pain', 'high',
 'Patient presented with chest pain and elevated blood pressure.',
 JSON_ARRAY('Dr. Wilson', 'Nurse Davis', 'Cardiac Tech Miller'), 180,
 JSON_ARRAY('ECG', 'Blood work', 'Chest X-ray', 'Nitroglycerin'),
 'Ruled out MI, admitted for observation');