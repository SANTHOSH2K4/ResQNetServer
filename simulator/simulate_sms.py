import json
import requests
def post_message(phn_no, msg):
    url = "http://192.168.28.83:8000/msg/add_message/"
    payload = json.dumps({"phn_no": phn_no, "message": msg})
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=payload, headers=headers)
    
post_message(6382158828,"SMS Testing through programming confirming the latest built apk working fine")
