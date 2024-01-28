import os
import requests
import RPi.GPIO as GPIO
from pn532 import PN532_SPI
from ntag import NTAG213

username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

if __name__ == '__main__':
    try:
        pn532 = PN532_SPI(debug=True, reset=20, cs=4)
        pn532.SAM_configuration()

        ntag213 = NTAG213(pn532, debug=True)
        print('Waiting for an NFC card...')

        # JWT token authentication endpoint
        auth_url = 'https://digidex.app/api/token/' if not ntag213.debug else 'http://10.0.0.218:8080/api/token/'

        auth_response = requests.post(auth_url, data={'username': username, 'password': password})
        if auth_response.status_code == 200:
            token = auth_response.json().get('access')
            print("Authentication successful, JWT access token obtained.")
        else:
            print("Failed to authenticate:", auth_response.text)
            token = None

        uid_list = []
        last_uid = None

        while True:
            serial_number = pn532.list_passive_target(timeout=0.5)
            if serial_number is None:
                continue
            if serial_number != last_uid:
                last_uid = serial_number
                uid_str = ':'.join(['{:02X}'.format(i) for i in serial_number])
                if uid_str not in uid_list:
                    uid_list.append(uid_str)
                    print('Found new card. Extracted UID:', uid_str)

                    if ntag213.debug:
                        api_url = f'http://10.0.0.218:8080/api/create-link/{uid_str}/'
                    else:
                        api_url = f'https://digidex.app/api/create-link/{uid_str}/'

                    if token:
                        headers = {'Authorization': f'Bearer {token}'}
                        try:
                            response = requests.post(api_url, headers=headers, data={'serial_number': uid_str}, verify=False)
                            if response.status_code == 201:
                                print('Link created successfully in Django app.')
                                link_url = response.json().get('link_url')

                                if ntag213.debug:
                                    stripped_url = link_url.replace('http://', '')
                                else:
                                    stripped_url = link_url.replace('https://', '')

                                # Use the stripped_url as the payload for the NDEF record
                                record = ntag213.create_ndef_record(tnf=0x01, record_type='U', payload=stripped_url)               
                                ntag213.write_ndef_message(record)
                                ntag_data = ntag213.dump(start_block=0, end_block=25)
                            else:
                                print('Failed to create link in Django app:', response.text)
                        except requests.exceptions.RequestException as e:
                            print('Error communicating with Django app:', e)
                    else:
                        print("No authentication token available.")
                else:
                    print('Found duplicate card. Extracted UID:', uid_str)
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
