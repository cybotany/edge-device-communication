import os
import requests

def register_ntag(token, uid):
    api_url = os.getenv('API_URL')
    headers = {'Authorization': f'Bearer {token}'}
    payload = {
        'serial_number': uid
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, verify=True)
        if response.status_code == 201:
            ntag_url = response.json().get('absolute_url')
            print(f"NTAG: {uid} registered successfully.")
            return ntag_url
        else:
            print("Failed to register NTAG.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with NTAG API: {e}")
        return None
