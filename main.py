import os
import sys
import requests
import uuid
import RPi.GPIO as GPIO

from pn532 import PN532_SPI as PN532
from ntag import NTAG

def authenticate_user():
    email = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')
    auth_url = os.getenv('AUTH_URL')
    try:
        response = requests.post(auth_url, data={'email': email, 'password': password})
        if response.status_code == 200:
            return response.json().get('access')
        else:
            sys.exit("Authentication failed, exiting program.")
    except requests.exceptions.RequestException as e:
        sys.exit(f"Error during authentication request, exiting program. Error was: {e}")

def register_ntag(token, uid):
    api_url = os.getenv('API_URL')
    headers = {'Authorization': f'Bearer {token}'}
    payload = {'uid': uid}
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, verify=True)
        if response.status_code == 201 or response.status_code == 200:
            uuid = response.json().get('uuid')
            return uuid
        else:
            print(f"Failed to register or update NTAG. Status code: {response.status_code}, Error: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with NTAG API: {e}")
        return None

def main():
    try:
        pn532 = PN532(debug=True, reset=20, cs=4)
        pn532.SAM_configuration()
        ntag = NTAG(pn532, debug=False)

        token = authenticate_user()
        uid_list = []
        last_uid = None
        print('Waiting for an NFC card...')
        while True:
            uid = pn532.list_passive_target(timeout=0.5)
            if uid and uid != last_uid:
                last_uid = uid
                uid = ''.join(['{:02X}'.format(i) for i in uid])
                if uid not in uid_list:
                    uid_list.append(uid)
                    print(f'Found new card. Extracted UID: {uid}')
                    
                    ntag_uuid = register_ntag(token, uid)
                    if ntag_uuid:
                        ntag_uuid = uuid.UUID(ntag_uuid)
                        ntag_pwd = ntag_uuid.hex[:8]
                        # ntag.set_password(ntag_pwd)
                        success = ntag.write_ndef()
                        if success:
                            print(f'Wrote NDEF message to NTAG. Password: {ntag_pwd}')
                        else:
                            print('Failed to write NDEF message to NTAG.')
                else:
                    print(f'Found duplicate card. Extracted UID: {uid}')
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()

if __name__ == '__main__':
    main()
