import requests
from constants import api  # Ensure that constants.API is defined as '192.168.84.105:8000'

def approve_volunteer(volunteer_id, group_id):
    url = f"http://{api}/api/approve_volunteer/"
    payload = {
        "volunteer_id": volunteer_id,
        "group_id": group_id
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an error for non-200 responses
        print("Volunteer approved successfully!")
        print("Response:", response.json())
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("An unexpected error occurred:", err)

if __name__ == "__main__":
    approve_volunteer(5, 1)
