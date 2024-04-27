import requests

def register_ntag(token, _serial_number, _type, _use):
    url = 'https://digidex.app/api/ntags/'
    headers = {'Authorization': f'Bearer {token}'}
    payload = {
        'serial_number': _serial_number,
        'type': _type,
        'use': _use
    }
    try:
        response = requests.post(url, headers=headers, json=payload, verify=True)
        if response.status_code == 201:
            ntag_url = response.json().get('absolute_url')
            print(f"NTAG: {_serial_number} registered successfully.")
            return ntag_url
        else:
            print("Failed to register NTAG.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with NTAG API: {e}")
        return None
