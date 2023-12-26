import requests
import RPi.GPIO as GPIO
import pn532.pn532 as nfc
from pn532 import PN532_SPI

API_URL = 'http://10.0.0.218:8080/api/create/link/'

if __name__ == '__main__':
    try:
        pn532 = PN532_SPI(debug=True, reset=20, cs=4)
        pn532.SAM_configuration()
        print('Waiting for an NFC card...')
        uid_list = []
        last_uid = None

        while True:
            uid = pn532.list_passive_target(timeout=0.5)
            if uid is None:
                continue
            if uid != last_uid:
                # Convert UID to string format
                uid_str = ':'.join(['{:02X}'.format(i) for i in uid])
                if uid_str not in uid_list:
                    uid_list.append(uid_str)
                    print('Found new card. Extracted UID:', uid_str)
                    # Send UID to Django API
                    try:
                        response = requests.post(API_URL, data={'uid': uid_str})
                        if response.status_code == 201:
                            print('Link created successfully in Django app.')
                        else:
                            print('Failed to create link in Django app:', response.text)
                    except requests.exceptions.RequestException as e:
                        print('Error communicating with Django app:', e)                 
                else:
                    print('Found duplicate card. Extracted UID:', uid_str)
                
                try:
                    record1 = pn532.create_ndef_record(tnf=0x01, record_type='T', payload='Testing', record_position='only')
                    ndef_message = pn532.combine_ndef_records([record1])                   
                    pn532.write_ndef_message(ndef_message)
                    ntag_data = pn532.ntag2xx_dump(start_block=4, end_block=9)
                except nfc.PN532Error as e:
                    print(e.errmsg)
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
