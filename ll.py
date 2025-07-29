from faker import Faker
import random
from datetime import datetime, timedelta
from database.connection import get_db_session
from database.models import (
    Patient, MedicalRecord, Appointment, VitalSigns, Alert, Treatment,
    TriageAssessment, EmergencyResponse, AlertSeverity, AppointmentStatus, PatientStatus, TriageLevel
)

fake = Faker()

def random_date(start, end):
    return start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds())),
    )

def insert_fake_data(n_patients=10):
    with get_db_session() as session:
        patients = []
        for _ in range(n_patients):
            patient = Patient(
                mrn=f"MRN{random.randint(1000,9999)}",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                date_of_birth=fake.date_of_birth(),
                gender=random.choice(['Male', 'Female']),
                phone=fake.phone_number(),
                email=fake.email(),
                address=fake.address().replace('\n', ', '),
                emergency_contact={
                    "name": fake.name(),
                    "relationship": random.choice(["Spouse", "Parent", "Sibling", "Friend"]),
                    "phone": fake.phone_number()
                },
                insurance_info={
                    "provider": fake.company(),
                    "policy_number": fake.bothify(text='??#####'),
                    "group_number": fake.bothify(text='GRP###')
                },
                allergies=[fake.word() for _ in range(random.randint(0, 2))],
                medications=[fake.word() for _ in range(random.randint(0, 2))],
                medical_history=[fake.sentence() for _ in range(random.randint(1, 3))],
                status=random.choice([s.value for s in PatientStatus])
            )
            session.add(patient)
            patients.append(patient)
        session.commit()

        # Medical Records, Appointments, Vital Signs, Alerts, Treatments, Triage, Emergency
        for patient in patients:
            # Medical Records
            for _ in range(random.randint(1, 3)):
                record = MedicalRecord(
                    patient_id=patient.id,
                    record_type=random.choice(['diagnosis', 'treatment', 'lab_result']),
                    title=fake.sentence(nb_words=4),
                    content=fake.text(max_nb_chars=200),
                    doctor_id=fake.bothify(text='DR###'),
                    department=fake.word(),
                    diagnosis_codes=[fake.bothify(text='??##.##')],
                    medications=[fake.word()],
                    procedures=[fake.word()]
                )
                session.add(record)

            # Appointments
            for _ in range(random.randint(1, 2)):
                appointment = Appointment(
                    patient_id=patient.id,
                    doctor_id=fake.bothify(text='DR###'),
                    department=fake.word(),
                    appointment_type=random.choice(['consultation', 'follow_up', 'initial']),
                    scheduled_date=random_date(datetime(2023, 1, 1), datetime(2024, 12, 31)),
                    duration=random.choice([20, 30, 45, 60]),
                    status=random.choice([s.value for s in AppointmentStatus]),
                    notes=fake.sentence(),
                    room_number=str(random.randint(100, 500))
                )
                session.add(appointment)

            # Vital Signs
            for _ in range(random.randint(1, 3)):
                vital = VitalSigns(
                    patient_id=patient.id,
                    heart_rate=random.randint(60, 100),
                    systolic_bp=random.randint(110, 150),
                    diastolic_bp=random.randint(70, 100),
                    temperature=round(random.uniform(97.0, 99.5), 1),
                    oxygen_saturation=random.randint(95, 100),
                    respiratory_rate=random.randint(12, 20),
                    blood_glucose=random.randint(80, 140),
                    pain_level=random.randint(0, 5),
                    recorded_at=random_date(datetime(2023, 1, 1), datetime(2024, 12, 31)),
                    device_id=fake.bothify(text='MON###'),
                    notes=fake.sentence()
                )
                session.add(vital)

            # Alerts
            for _ in range(random.randint(1, 2)):
                alert = Alert(
                    patient_id=patient.id,
                    alert_type=random.choice(['vital_signs', 'medication', 'allergy', 'fall']),
                    severity=random.choice([s.value for s in AlertSeverity]),
                    title=fake.sentence(nb_words=3),
                    message=fake.text(max_nb_chars=100),
                    source=random.choice(['monitoring_system', 'manual', 'ai_agent']),
                    acknowledged=random.choice([True, False]),
                    resolved=random.choice([True, False])
                )
                session.add(alert)

            # Treatments
            for _ in range(random.randint(1, 2)):
                treatment = Treatment(
                    patient_id=patient.id,
                    treatment_type=fake.word(),
                    diagnosis=fake.sentence(),
                    treatment_plan=fake.text(max_nb_chars=100),
                    medications=[fake.word()],
                    procedures=[fake.word()],
                    start_date=random_date(datetime(2023, 1, 1), datetime(2024, 12, 31)),
                    status=random.choice(['active', 'completed', 'discontinued']),
                    doctor_id=fake.bothify(text='DR###'),
                    notes=fake.sentence()
                )
                session.add(treatment)

            # Triage Assessments
            triage = TriageAssessment(
                patient_id=patient.id,
                triage_level=random.choice([l for l in TriageLevel]),
                chief_complaint=fake.sentence(),
                symptoms=[fake.word() for _ in range(random.randint(1, 3))],
                assessment_notes=fake.sentence(),
                assigned_doctor=fake.bothify(text='DR###'),
                wait_time_estimate=random.randint(5, 60)
            )
            session.add(triage)

            # Emergency Responses
            emergency = EmergencyResponse(
                patient_id=patient.id,
                emergency_type=random.choice(['Anaphylaxis', 'Chest Pain', 'Seizure', 'Stroke']),
                severity=random.choice([s.value for s in AlertSeverity]),
                description=fake.sentence(),
                response_team=[fake.name() for _ in range(random.randint(2, 4))],
                response_time=random.randint(60, 300),
                actions_taken=[fake.sentence() for _ in range(random.randint(1, 3))],
                outcome=random.choice(['Stabilized', 'Admitted', 'Discharged']),
                resolved_at=random_date(datetime(2023, 1, 1), datetime(2024, 12, 31)),
                created_at=random_date(datetime(2023, 1, 1), datetime(2024, 12, 31))
            )
            session.add(emergency)

        session.commit()
        print(f"Inserted fake data for {n_patients} patients and related records.")

if __name__ == "__main__":
    insert_fake_data(100)