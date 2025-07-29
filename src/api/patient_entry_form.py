from flask import Blueprint, render_template_string, request, redirect, url_for, flash
from database.connection import get_db_session
from database.models import Patient
import json

patient_form_bp = Blueprint('patient_form', __name__)

PATIENT_FORM_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>New Patient Entry</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f4f6fb; }
    .container { max-width: 600px; margin: 40px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 8px #ccc; padding: 30px; }
    h2 { text-align: center; color: #4f8cff; }
    label { display: block; margin-top: 18px; font-weight: bold; }
    input, select, textarea { width: 100%; padding: 10px; margin-top: 6px; border-radius: 6px; border: 1px solid #ccc; }
    .row { display: flex; gap: 10px; }
    .row > div { flex: 1; }
    button { margin-top: 24px; width: 100%; padding: 12px; background: #4f8cff; color: #fff; border: none; border-radius: 6px; font-size: 1.1em; cursor: pointer; }
    button:hover { background: #375fa0; }
    .success { color: green; margin-top: 20px; text-align: center; }
    .error { color: red; margin-top: 20px; text-align: center; }
  </style>
</head>
<body>
  <div class="container">
    <h2>New Patient Entry</h2>
    {% if message %}
      <div class="{{ 'success' if success else 'error' }}">{{ message }}</div>
    {% endif %}
    <form method="post" autocomplete="off">
      <div class="row">
        <div>
          <label>First Name</label>
          <input type="text" name="first_name" required>
        </div>
        <div>
          <label>Last Name</label>
          <input type="text" name="last_name" required>
        </div>
      </div>
      <label>Date of Birth</label>
      <input type="date" name="date_of_birth" required>
      <label>Gender</label>
      <select name="gender" required>
        <option value="">Select...</option>
        <option>Male</option>
        <option>Female</option>
        <option>Other</option>
      </select>
      <label>Phone</label>
      <input type="text" name="phone" required>
      <label>Email</label>
      <input type="email" name="email" required>
      <label>Address</label>
      <textarea name="address" required></textarea>
      <h3>Emergency Contact</h3>
      <div class="row">
        <div>
          <label>Name</label>
          <input type="text" name="emergency_contact_name" required>
        </div>
        <div>
          <label>Relationship</label>
          <input type="text" name="emergency_contact_relationship" required>
        </div>
        <div>
          <label>Phone</label>
          <input type="text" name="emergency_contact_phone" required>
        </div>
      </div>
      <h3>Insurance Info</h3>
      <div class="row">
        <div>
          <label>Provider</label>
          <input type="text" name="insurance_provider" required>
        </div>
        <div>
          <label>Policy #</label>
          <input type="text" name="insurance_policy_number" required>
        </div>
        <div>
          <label>Group #</label>
          <input type="text" name="insurance_group_number" required>
        </div>
      </div>
      <label>Allergies (comma separated)</label>
      <input type="text" name="allergies">
      <label>Medications (comma separated)</label>
      <input type="text" name="medications">
      <label>Medical History (comma separated)</label>
      <input type="text" name="medical_history">
      <label>Status</label>
      <select name="status" required>
        <option value="">Select...</option>
        <option>admitted</option>
        <option>discharged</option>
        <option>pending</option>
      </select>
      <button type="submit">Submit Patient</button>
    </form>
  </div>
</body>
</html>
'''

@patient_form_bp.route('/patient-entry', methods=['GET', 'POST'])
def patient_entry():
    message = None
    success = False
    if request.method == 'POST':
        try:
            data = request.form
            with get_db_session() as session:
                patient = Patient(
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    date_of_birth=data['date_of_birth'],
                    gender=data['gender'],
                    phone=data['phone'],
                    email=data['email'],
                    address=data['address'],
                    emergency_contact=json.dumps({
                        'name': data['emergency_contact_name'],
                        'relationship': data['emergency_contact_relationship'],
                        'phone': data['emergency_contact_phone']
                    }),
                    insurance_info=json.dumps({
                        'provider': data['insurance_provider'],
                        'policy_number': data['insurance_policy_number'],
                        'group_number': data['insurance_group_number']
                    }),
                    allergies=json.dumps([s.strip() for s in data.get('allergies', '').split(',') if s.strip()]),
                    medications=json.dumps([s.strip() for s in data.get('medications', '').split(',') if s.strip()]),
                    medical_history=json.dumps([s.strip() for s in data.get('medical_history', '').split(',') if s.strip()]),
                    status=data['status']
                )
                session.add(patient)
                session.commit()
            message = 'Patient added successfully!'
            success = True
        except Exception as e:
            message = f'Error: {e}'
            success = False
    return render_template_string(PATIENT_FORM_HTML, message=message, success=success) 