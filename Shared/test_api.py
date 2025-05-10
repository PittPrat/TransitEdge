import requests
import json

# API endpoint
url = "http://127.0.0.1:5000/predict_speed"

# Data to send
data = {
    "time": 9,
    "location_id": 101
}

# Make the POST request
response = requests.post(url, json=data)

# Print the response
print("Status Code:", response.status_code)
print("Response:", response.json()) 