import json
import requests

# Set the URL based on your configuration
url = "http://172.20.110.32:8000/api/create_group/"

# Prepare the payload; the API will look up the admin based on this phone number.
payload = {
    "group_name": "Test Group Simulation for Dindigul not Chennai guy",
    "city": "Dindigul",
    "phone": "+919363393614"  # This phone is associated with admin id 2
}

headers = {"Content-Type": "application/json"}

response = requests.post(url, data=json.dumps(payload), headers=headers)

print("Status Code:", response.status_code)
try:
    print("Response JSON:", response.json())
except Exception as e:
    print("Error parsing JSON response:", e)
