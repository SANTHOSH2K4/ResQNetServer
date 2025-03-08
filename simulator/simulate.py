import requests

# URL for your registration endpoint
registration_url = "http://192.168.236.83:8000/admin-registration/"

# Data fields to be sent (non-file fields)
data = {
    "mobile_number": "9363393614",
    "email": "sandy@example.com",
    "address": "123 Admin Street",
    "reason_for_admin_request": "I need admin access.",
    "past_experience": "5 years in administrative roles.",
    "affiliation": "Tech Company",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_relationship": "Sister",
    "emergency_contact_number": "0987654321",
    "emergency_contact_address": "456 Another St, City",
    
    # New fields
    "job": "System Administrator",
    "gender": "Male"
}

# Files to be sent. Make sure to provide the correct file paths.
files = {
    "identity_document1": open("iddoc1.pdf", "rb"),
    "identity_document2": open("iddoc2.pdf", "rb"),
    "identity_document3": open("iddoc3.pdf", "rb"),
    "live_selfie_capture": open("miphoto.jpg", "rb"),
    "signature_upload": open("misign.jpg", "rb"),
    "disaster_management_training_certificate": open("vdoc1.pdf", "rb"),
    "authorization_letter": open("vdoc2.pdf", "rb"),
}

# Send the POST request
response = requests.post(registration_url, data=data, files=files)

# Close the opened files
for f in files.values():
    f.close()

print("Status Code:", response.status_code)
try:
    print("Response JSON:", response.json())
except Exception as e:
    print("Response Text:", response.text)
