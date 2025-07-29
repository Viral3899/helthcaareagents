import json

def ask(question, validator=None, allow_empty=False):
    while True:
        answer = input(f"🤖 {question}\n👤 ")
        if not answer and not allow_empty:
            print("Please enter a value.")
            continue
        if validator:
            try:
                answer = validator(answer)
            except Exception as e:
                print(f"Invalid input: {e}")
                continue
        return answer

def comma_list(answer):
    if answer.strip().lower() == 'none':
        return []
    return [item.strip() for item in answer.split(',') if item.strip()]

def main():
    print("Welcome to the Patient Entry Chat!\nLet's add a new patient. Please answer the following questions:")

    patient = {}
    patient['first_name'] = ask("What is the patient's first name?")
    patient['last_name'] = ask("What is the patient's last name?")
    patient['date_of_birth'] = ask("What is the patient's date of birth? (YYYY-MM-DD)")
    patient['gender'] = ask("What is the patient's gender? (Male/Female/Other)")
    patient['phone'] = ask("What is the patient's phone number?")
    patient['email'] = ask("What is the patient's email address?")
    patient['address'] = ask("What is the patient's address?")
    # Emergency contact
    print("\nLet's add emergency contact details.")
    patient['emergency_contact'] = {
        'name': ask("Emergency contact name?"),
        'relationship': ask("Relationship to patient?"),
        'phone': ask("Emergency contact phone number?")
    }
    # Insurance info
    print("\nNow, insurance information.")
    patient['insurance_info'] = {
        'provider': ask("Insurance provider?"),
        'policy_number': ask("Insurance policy number?"),
        'group_number': ask("Insurance group number?")
    }
    # Allergies, Medications, Medical History
    patient['allergies'] = ask("List any allergies (comma separated, or 'none'):", comma_list)
    patient['medications'] = ask("List current medications (comma separated, or 'none'):", comma_list)
    patient['medical_history'] = ask("List medical history items (comma separated, or 'none'):", comma_list)
    patient['status'] = ask("What is the patient's status? (admitted/discharged/pending)")

    print("\n✅ Patient entry complete! Here is the summary:\n")
    print(json.dumps(patient, indent=2))

    # Optionally, save to file or send to API/database here
    # with open('new_patient.json', 'w') as f:
    #     json.dump(patient, f, indent=2)

if __name__ == "__main__":
    main() 