import os
import sys
import requests

import RPi.GPIO as GPIO

from pn532 import PN532_SPI as PN532
from ntag import NTAG

def authenticate_user():
    username = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')
    auth_url = os.getenv('AUTH_URL')
    try:
        response = requests.post(auth_url, data={'username': username, 'password': password})
        if response.status_code == 200:
            return response.json().get('access')
        else:
            sys.exit("Authentication failed, exiting program.")
    except requests.exceptions.RequestException as e:
        sys.exit(f"Error during authentication request, exiting program. Error was: {e}")

def register_ntag(token, uid):
    api_url = os.getenv('API_URL')
    headers = {'Authorization': f'Bearer {token}'}
    payload = {'serial_number': uid}
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, verify=True)
        if response.status_code == 201:
            ntag_url = response.json().get('ntag_url')
            print(f"NTAG: {uid} registered successfully.")
            print(f"NTAG URL: {ntag_url}")
            return ntag_url
        elif response.status_code == 200:
            ntag_url = response.json().get('ntag_url')
            print(f"NTAG: {uid} registered successfully.")
            print(f"NTAG URL: {ntag_url}")
            return ntag_url
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
        #ntag = NTAG(pn532, debug=True)

        token = authenticate_user()
        uid_list = []
        last_uid = None
        print('Waiting for an NFC card...')
        while True:
            serial_number = pn532.list_passive_target(timeout=0.5)
            if serial_number and serial_number != last_uid:
                last_uid = serial_number
                uid = ':'.join(['{:02X}'.format(i) for i in serial_number])
                if uid not in uid_list:
                    uid_list.append(uid)
                    print(f'Found new card. Extracted UID: {uid}')
                    ntag_url = register_ntag(token, uid)
                    if ntag_url:
                        print("NTAG URL routed on backend.")
                    #    record = ntag.create_ndef_record(tnf=0x01, record_type='U', payload=ntag_url)
                    #    ntag.write_ndef_message(record)
                else:
                    print(f'Found duplicate card. Extracted UID: {uid}')
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()

if __name__ == '__main__':
    main()