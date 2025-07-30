"""
Patient Entry Form API Module

This module provides API endpoints for patient registration and form handling.
"""

from flask import Blueprint, request, render_template_string, jsonify
from sqlalchemy.orm import Session
from typing import Optional
from database.connection import get_db_session
from database.models import Patient
from tools.database_tools import generate_unique_mrn
import json
import uuid
from datetime import datetime

# Create blueprint
patient_form_bp = Blueprint('patient_form', __name__)

def generate_mrn():
    """Generate a unique Medical Record Number"""
    return generate_unique_mrn()

# HTML template for patient entry form
PATIENT_FORM_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>New Patient Entry</title>
  <style>
    body { 
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      margin: 0;
      padding: 20px;
      min-height: 100vh;
    }
    .container { 
      max-width: 800px; 
      margin: 0 auto; 
      background: #fff; 
      border-radius: 15px; 
      box-shadow: 0 10px 30px rgba(0,0,0,0.2); 
      padding: 40px; 
    }
    h2 { 
      text-align: center; 
      color: #4f8cff; 
      margin-bottom: 30px;
      font-size: 2.2em;
    }
    label { 
      display: block; 
      margin-top: 20px; 
      font-weight: 600;
      color: #333;
    }
    input, select, textarea { 
      width: 100%; 
      padding: 12px; 
      margin-top: 8px; 
      border-radius: 8px; 
      border: 2px solid #e1e5e9; 
      font-size: 16px;
      transition: border-color 0.3s ease;
    }
    input:focus, select:focus, textarea:focus {
      outline: none;
      border-color: #4f8cff;
      box-shadow: 0 0 0 3px rgba(79, 140, 255, 0.1);
    }
    .row { 
      display: flex; 
      gap: 15px; 
      margin-bottom: 10px;
    }
    .row > div { 
      flex: 1; 
    }
    .required { 
      color: #e74c3c; 
    }
    .btn { 
      background: linear-gradient(45deg, #4f8cff, #6c5ce7); 
      color: white; 
      padding: 15px 30px; 
      border: none; 
      border-radius: 8px; 
      font-size: 16px; 
      font-weight: 600; 
      cursor: pointer; 
      margin-top: 20px; 
      width: 100%;
      transition: transform 0.2s ease;
    }
    .btn:hover { 
      transform: translateY(-2px); 
      box-shadow: 0 5px 15px rgba(79, 140, 255, 0.3);
    }
    .success { 
      background: #d4edda; 
      color: #155724; 
      padding: 15px; 
      border-radius: 8px; 
      margin-bottom: 20px; 
    }
    .error { 
      background: #f8d7da; 
      color: #721c24; 
      padding: 15px; 
      border-radius: 8px; 
      margin-bottom: 20px; 
    }
    .form-section {
      background: #f8f9fa;
      padding: 20px;
      border-radius: 10px;
      margin-bottom: 20px;
    }
    .section-title {
      color: #4f8cff;
      font-size: 1.2em;
      margin-bottom: 15px;
      border-bottom: 2px solid #4f8cff;
      padding-bottom: 5px;
    }
  </style>
</head>
<body>
  <div class="container">
    <h2>🏥 New Patient Registration</h2>
    
    {% if message %}
    <div class="{{ 'success' if success else 'error' }}">
      {{ message }}
    </div>
    {% endif %}
    
    <form method="POST" action="/patient-entry/">
      <div class="form-section">
        <div class="section-title">📋 Basic Information</div>
        
        <div class="row">
          <div>
            <label for="mrn">Medical Record Number <span class="required">*</span></label>
            <input type="text" id="mrn" name="mrn" value="{{ mrn }}" required readonly>
          </div>
        </div>
        
        <div class="row">
          <div>
            <label for="first_name">First Name <span class="required">*</span></label>
            <input type="text" id="first_name" name="first_name" value="{{ first_name }}" required>
          </div>
          <div>
            <label for="last_name">Last Name <span class="required">*</span></label>
            <input type="text" id="last_name" name="last_name" value="{{ last_name }}" required>
          </div>
        </div>
        
        <div class="row">
          <div>
            <label for="date_of_birth">Date of Birth <span class="required">*</span></label>
            <input type="date" id="date_of_birth" name="date_of_birth" value="{{ date_of_birth }}" required>
          </div>
          <div>
            <label for="gender">Gender <span class="required">*</span></label>
            <select id="gender" name="gender" required>
              <option value="">Select Gender</option>
              <option value="Male" {{ 'selected' if gender == 'Male' }}>Male</option>
              <option value="Female" {{ 'selected' if gender == 'Female' }}>Female</option>
              <option value="Other" {{ 'selected' if gender == 'Other' }}>Other</option>
            </select>
          </div>
        </div>
      </div>
      
      <div class="form-section">
        <div class="section-title">📞 Contact Information</div>
        
        <div class="row">
          <div>
            <label for="phone">Phone Number <span class="required">*</span></label>
            <input type="tel" id="phone" name="phone" value="{{ phone }}" required>
          </div>
          <div>
            <label for="email">Email Address <span class="required">*</span></label>
            <input type="email" id="email" name="email" value="{{ email }}" required>
          </div>
        </div>
        
        <div>
          <label for="address">Address <span class="required">*</span></label>
          <textarea id="address" name="address" rows="3" required>{{ address }}</textarea>
        </div>
      </div>
      
      <div class="form-section">
        <div class="section-title">🚨 Emergency Contact</div>
        
        <div class="row">
          <div>
            <label for="emergency_contact_name">Emergency Contact Name <span class="required">*</span></label>
            <input type="text" id="emergency_contact_name" name="emergency_contact_name" value="{{ emergency_contact_name }}" required>
          </div>
          <div>
            <label for="emergency_contact_relationship">Relationship <span class="required">*</span></label>
            <input type="text" id="emergency_contact_relationship" name="emergency_contact_relationship" value="{{ emergency_contact_relationship }}" required>
          </div>
        </div>
        
        <div>
          <label for="emergency_contact_phone">Emergency Contact Phone <span class="required">*</span></label>
          <input type="tel" id="emergency_contact_phone" name="emergency_contact_phone" value="{{ emergency_contact_phone }}" required>
        </div>
      </div>
      
      <div class="form-section">
        <div class="section-title">🏥 Insurance Information (Optional)</div>
        
        <div class="row">
          <div>
            <label for="insurance_provider">Insurance Provider</label>
            <input type="text" id="insurance_provider" name="insurance_provider" value="{{ insurance_provider }}">
          </div>
          <div>
            <label for="insurance_policy_number">Policy Number</label>
            <input type="text" id="insurance_policy_number" name="insurance_policy_number" value="{{ insurance_policy_number }}">
          </div>
        </div>
      </div>
      
      <button type="submit" class="btn">✅ Register Patient</button>
    </form>
  </div>
</body>
</html>
'''

@patient_form_bp.route('/', methods=['GET'])
def patient_entry_form():
    """Render the patient entry form"""
    mrn = generate_mrn()
    return render_template_string(PATIENT_FORM_HTML, 
                                mrn=mrn,
                                first_name='',
                                last_name='',
                                date_of_birth='',
                                gender='',
                                phone='',
                                email='',
                                address='',
                                emergency_contact_name='',
                                emergency_contact_relationship='',
                                emergency_contact_phone='',
                                insurance_provider='',
                                insurance_policy_number='',
                                message='',
                                success=False)

@patient_form_bp.route('/', methods=['POST'])
def process_patient_entry():
    """Process patient registration form submission"""
    try:
        # Get form data
        mrn = request.form.get('mrn')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        emergency_contact_name = request.form.get('emergency_contact_name')
        emergency_contact_relationship = request.form.get('emergency_contact_relationship')
        emergency_contact_phone = request.form.get('emergency_contact_phone')
        insurance_provider = request.form.get('insurance_provider')
        insurance_policy_number = request.form.get('insurance_policy_number')
        
        # Validate required fields
        required_fields = {
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': date_of_birth,
            'gender': gender,
            'phone': phone,
            'email': email,
            'address': address,
            'emergency_contact_name': emergency_contact_name,
            'emergency_contact_relationship': emergency_contact_relationship,
            'emergency_contact_phone': emergency_contact_phone
        }
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            return render_template_string(PATIENT_FORM_HTML,
                                       mrn=mrn,
                                       first_name=first_name,
                                       last_name=last_name,
                                       date_of_birth=date_of_birth,
                                       gender=gender,
                                       phone=phone,
                                       email=email,
                                       address=address,
                                       emergency_contact_name=emergency_contact_name,
                                       emergency_contact_relationship=emergency_contact_relationship,
                                       emergency_contact_phone=emergency_contact_phone,
                                       insurance_provider=insurance_provider,
                                       insurance_policy_number=insurance_policy_number,
                                       message=f"Missing required fields: {', '.join(missing_fields)}",
                                       success=False)
        
        # Validate email format
        if '@' not in email or '.' not in email:
            return render_template_string(PATIENT_FORM_HTML,
                                       mrn=mrn,
                                       first_name=first_name,
                                       last_name=last_name,
                                       date_of_birth=date_of_birth,
                                       gender=gender,
                                       phone=phone,
                                       email=email,
                                       address=address,
                                       emergency_contact_name=emergency_contact_name,
                                       emergency_contact_relationship=emergency_contact_relationship,
                                       emergency_contact_phone=emergency_contact_phone,
                                       insurance_provider=insurance_provider,
                                       insurance_policy_number=insurance_policy_number,
                                       message="Invalid email format",
                                       success=False)
        
        # Validate gender
        if gender not in ['Male', 'Female', 'Other']:
            return render_template_string(PATIENT_FORM_HTML,
                                       mrn=mrn,
                                       first_name=first_name,
                                       last_name=last_name,
                                       date_of_birth=date_of_birth,
                                       gender=gender,
                                       phone=phone,
                                       email=email,
                                       address=address,
                                       emergency_contact_name=emergency_contact_name,
                                       emergency_contact_relationship=emergency_contact_relationship,
                                       emergency_contact_phone=emergency_contact_phone,
                                       insurance_provider=insurance_provider,
                                       insurance_policy_number=insurance_policy_number,
                                       message="Invalid gender selection",
                                       success=False)
        
        # Save to database
        with get_db_session() as session:
            # Check if patient already exists
            existing_patient = session.query(Patient).filter(
                (Patient.mrn == mrn) | (Patient.email == email)
            ).first()
            
            if existing_patient:
                return render_template_string(PATIENT_FORM_HTML,
                                           mrn=mrn,
                                           first_name=first_name,
                                           last_name=last_name,
                                           date_of_birth=date_of_birth,
                                           gender=gender,
                                           phone=phone,
                                           email=email,
                                           address=address,
                                           emergency_contact_name=emergency_contact_name,
                                           emergency_contact_relationship=emergency_contact_relationship,
                                           emergency_contact_phone=emergency_contact_phone,
                                           insurance_provider=insurance_provider,
                                           insurance_policy_number=insurance_policy_number,
                                           message="Patient with this MRN or email already exists",
                                           success=False)
            
            # Create new patient
            patient = Patient(
                mrn=mrn,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d').date(),
                gender=gender,
                phone=phone,
                email=email,
                address=address,
                emergency_contact_name=emergency_contact_name,
                emergency_contact_relationship=emergency_contact_relationship,
                emergency_contact_phone=emergency_contact_phone,
                insurance_provider=insurance_provider,
                insurance_policy_number=insurance_policy_number,
                created_at=datetime.utcnow()
            )
            
            session.add(patient)
            session.commit()
            
            return render_template_string(PATIENT_FORM_HTML,
                                       mrn=generate_mrn(),
                                       first_name='',
                                       last_name='',
                                       date_of_birth='',
                                       gender='',
                                       phone='',
                                       email='',
                                       address='',
                                       emergency_contact_name='',
                                       emergency_contact_relationship='',
                                       emergency_contact_phone='',
                                       insurance_provider='',
                                       insurance_policy_number='',
                                       message=f"Patient {first_name} {last_name} registered successfully with MRN: {mrn}",
                                       success=True)
    
    except Exception as e:
        return render_template_string(PATIENT_FORM_HTML,
                                   mrn=mrn,
                                   first_name=first_name,
                                   last_name=last_name,
                                   date_of_birth=date_of_birth,
                                   gender=gender,
                                   phone=phone,
                                   email=email,
                                   address=address,
                                   emergency_contact_name=emergency_contact_name,
                                   emergency_contact_relationship=emergency_contact_relationship,
                                   emergency_contact_phone=emergency_contact_phone,
                                   insurance_provider=insurance_provider,
                                   insurance_policy_number=insurance_policy_number,
                                   message=f"Error registering patient: {str(e)}",
                                   success=False)

@patient_form_bp.route('/api/patients')
def get_patients_api():
    """API endpoint to get patients list"""
    try:
        search = request.args.get('search')
        limit = min(int(request.args.get('limit', 50)), 100)
        
        with get_db_session() as session:
            query = session.query(Patient)
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    (Patient.first_name.ilike(search_term)) |
                    (Patient.last_name.ilike(search_term)) |
                    (Patient.mrn.ilike(search_term)) |
                    (Patient.email.ilike(search_term))
                )
            
            patients = query.limit(limit).all()
            
            patients_data = []
            for patient in patients:
                patients_data.append({
                    "id": patient.id,
                    "mrn": patient.mrn,
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                    "gender": patient.gender,
                    "phone": patient.phone,
                    "email": patient.email,
                    "address": patient.address,
                    "emergency_contact_name": patient.emergency_contact_name,
                    "emergency_contact_relationship": patient.emergency_contact_relationship,
                    "emergency_contact_phone": patient.emergency_contact_phone,
                    "insurance_provider": patient.insurance_provider,
                    "insurance_policy_number": patient.insurance_policy_number,
                    "created_at": patient.created_at.isoformat() if patient.created_at else None
                })
            
            return jsonify({
                "success": True,
                "patients": patients_data,
                "total_count": len(patients_data)
            })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to retrieve patients: {str(e)}"
        }), 500 