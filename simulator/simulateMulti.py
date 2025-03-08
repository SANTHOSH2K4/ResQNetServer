import requests

# URL for your registration endpoint
registration_url = "http://192.168.10.56:8000/admin-registration/"

# List of user details to insert
users = [
    {
        "name": "Ravi Kumar",
        "mobile_number": "9363393611",
        "email": "ravi.kumar@example.com",
        "job": "District Collector",
        "gender": "Male",
        "dob": "1980-04-10",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "pincode": "600001",
        "emergency_contact_alternate_number": "9876543210",
    },
    {
        "name": "Arun Sharma",
        "mobile_number": "9363393612",
        "email": "arun.sharma@example.com",
        "job": "NGO Founder - Disaster Relief",
        "gender": "Male",
        "dob": "1975-06-15",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400001",
        "emergency_contact_alternate_number": "9876543220",
    },
    {
        "name": "Vikram Singh",
        "mobile_number": "9363393613",
        "email": "vikram.singh@example.com",
        "job": "National Disaster Response Force (NDRF) Officer",
        "gender": "Male",
        "dob": "1983-08-20",
        "city": "Delhi",
        "state": "Delhi",
        "pincode": "110001",
        "emergency_contact_alternate_number": "9876543230",
    },
    {
        "name": "Manoj Reddy",
        "mobile_number": "9363393614",
        "email": "manoj.reddy@example.com",
        "job": "Fire and Emergency Services Director",
        "gender": "Male",
        "dob": "1987-12-05",
        "city": "Hyderabad",
        "state": "Telangana",
        "pincode": "500001",
        "emergency_contact_alternate_number": "9876543240",
    },
    {
        "name": "Sandeep Verma",
        "mobile_number": "9363393615",
        "email": "sandeep.verma@example.com",
        "job": "Red Cross Disaster Response Coordinator",
        "gender": "Male",
        "dob": "1982-03-25",
        "city": "Kolkata",
        "state": "West Bengal",
        "pincode": "700001",
        "emergency_contact_alternate_number": "9876543250",
    },
]

# Static data fields
base_data = {
    "address": "123 Admin Street",
    "reason_for_admin_request": "I need admin access for disaster relief coordination.",
    "past_experience": "10+ years in disaster response and administration.",
    "affiliation": "Government / NGO",
    "emergency_contact_name": "Amit Kumar",
    "emergency_contact_relationship": "Brother",
    "emergency_contact_number": "9876543200",
    "emergency_contact_address": "456 Another St, City",
}

# File paths
file_paths = {
    "identity_document1": "iddoc1.pdf",
    "identity_document2": "iddoc2.pdf",
    "identity_document3": "iddoc3.pdf",
    "live_selfie_capture": "miphoto.jpg",
    "signature_upload": "misign.jpg",
}

# Loop to insert new records
for user in users:
    data = {**base_data, **user}  # Merge user-specific and base data
    
    # Open files with proper renaming
    files = {}
    for key, path in file_paths.items():
        ext = path.split('.')[-1]
        renamed_file = f"{user['mobile_number']}_{key}.{ext}"  # e.g., 9363393611_identity_document1.pdf
        files[key] = (renamed_file, open(path, "rb"))

    try:
        # Send the POST request
        response = requests.post(registration_url, data=data, files=files)
        print(f"Inserted {user['email']} - Status Code: {response.status_code}")

        # Print response
        try:
            print("Response JSON:", response.json())
        except Exception:
            print("Response Text:", response.text)
    
    finally:
        # Close all opened files
        for f in files.values():
            f[1].close()
