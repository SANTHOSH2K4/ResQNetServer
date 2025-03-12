import requests
from constants import api
# Define API URL
API_URL = f"http://{api}/api/volunteer_request/"

# Replace with actual volunteer_id
volunteer_id = 5  # Example volunteer ID

# Request payload
payload = {
    "volunteer_id": volunteer_id,
    "group_id": 14,
    "group_admin_id": 2,
    "phone": "9876543210",
    "address": "123 Volunteer Street, City"
}

# Make API request
response = requests.post(API_URL, json=payload)

# Print response
if response.status_code == 201:
    print("Volunteer request created successfully:", response.json())
else:
    print("Error:", response.status_code, response.json())
