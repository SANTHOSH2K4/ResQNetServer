import requests
import time

BASE_URL = "http://192.168.28.83:8000"  # Replace with your backend URL
admin_id = 22  # Using admin id 22 for testing

# --- 1. Create a New AdminGroup ---
group_data = {
    "group_name": "Test Group 1",
    "admin": admin_id,
    "allowed_volunteers": []  # Optional: empty list
}
print("Creating AdminGroup...")
group_create_url = f"{BASE_URL}/admin-group-create/"
group_create_response = requests.post(group_create_url, json=group_data)
print("Status Code:", group_create_response.status_code)
try:
    group_create_json = group_create_response.json()
    print("Response:", group_create_json)
except Exception as e:
    print("Error decoding JSON:", e)
    group_create_json = {}

if group_create_response.status_code != 201:
    print("AdminGroup creation failed. Exiting.")
    exit(1)

group_id = group_create_json.get("id")
time.sleep(2)  # Delay for 2 seconds

# --- 2. Update the AdminGroup ---
group_update_data = {"group_name": "Test Group 1 - Updated"}
print("\nUpdating AdminGroup...")
group_update_url = f"{BASE_URL}/admin-group-update/{group_id}/update/"
group_update_response = requests.post(group_update_url, json=group_update_data)
print("Status Code:", group_update_response.status_code)
try:
    print("Response:", group_update_response.json())
except Exception as e:
    print("Error decoding JSON:", e)
time.sleep(2)

# --- 3. Create a New TodoTitle (Task) ---
todo_data = {"title": "Evacuation Plan", "created_by": admin_id}
print("\nCreating TodoTitle...")
todo_create_url = f"{BASE_URL}/todo-titles/"
todo_create_response = requests.post(todo_create_url, json=todo_data)
print("Status Code:", todo_create_response.status_code)
try:
    todo_create_json = todo_create_response.json()
    print("Response:", todo_create_json)
except Exception as e:
    print("Error decoding JSON:", e)
    todo_create_json = {}

if todo_create_response.status_code != 201:
    print("TodoTitle creation failed. Exiting.")
    exit(1)

todo_id = todo_create_json.get("id")
time.sleep(2)

# --- 4. Update the TodoTitle ---
todo_update_data = {"title": "Evacuation Plan - Updated"}
print("\nUpdating TodoTitle...")
todo_update_url = f"{BASE_URL}/todo-titles/{todo_id}/update/"
todo_update_response = requests.post(todo_update_url, json=todo_update_data)
print("Status Code:", todo_update_response.status_code)
try:
    print("Response:", todo_update_response.json())
except Exception as e:
    print("Error decoding JSON:", e)
time.sleep(2)

# --- 5. Create a New SubTask ---
subtask_data = {
    "todo_title": todo_id,   # Parent TodoTitle ID
    "description": "Assess available shelter spaces",
    "completed": False,
    "completion_approved": False,
    "assigned_volunteer": None  # Optional field; can be omitted or set to null
}
print("\nCreating SubTask...")
subtask_create_url = f"{BASE_URL}/subtasks/"
subtask_create_response = requests.post(subtask_create_url, json=subtask_data)
print("Status Code:", subtask_create_response.status_code)
try:
    subtask_create_json = subtask_create_response.json()
    print("Response:", subtask_create_json)
except Exception as e:
    print("Error decoding JSON:", e)
if subtask_create_response.status_code != 201:
    print("SubTask creation failed. Exiting.")
    exit(1)

subtask_id = subtask_create_json.get("id")
time.sleep(2)

# --- 6. Update the SubTask ---
subtask_update_data = {
    "description": "Assess available shelter spaces - Updated",
    "completed": True,
    "completion_approved": True
}
print("\nUpdating SubTask...")
subtask_update_url = f"{BASE_URL}/subtasks/{subtask_id}/update/"
subtask_update_response = requests.post(subtask_update_url, json=subtask_update_data)
print("Status Code:", subtask_update_response.status_code)
try:
    print("Response:", subtask_update_response.json())
except Exception as e:
    print("Error decoding JSON:", e)
