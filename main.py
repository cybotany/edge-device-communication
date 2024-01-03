import requests
import RPi.GPIO as GPIO
from pn532 import PN532_SPI
from ntag import NTAG213

if __name__ == '__main__':
    try:
        pn532 = PN532_SPI(debug=True, reset=20, cs=4)
        pn532.SAM_configuration()

        ntag213 = NTAG213(pn532, debug=True)
        print('Waiting for an NFC card...')
        uid_list = []
        last_uid = None

        while True:
            uid = pn532.list_passive_target(timeout=0.5)
            if uid is None:
                continue
            if uid != last_uid:
                last_uid = uid
                uid_str = ':'.join(['{:02X}'.format(i) for i in uid])
                if uid_str not in uid_list:
                    uid_list.append(uid_str)
                    print('Found new card. Extracted UID:', uid_str)
                    # Send UID to Django API
                    #api_url = f'http://10.0.0.218:8080/api/create/link/{uid_str}/'
                    #try:
                    #    response = requests.post(api_url, data={'uid': uid_str})
                    #    if response.status_code == 201:
                    #        print('Link created successfully in Django app.')
                    #    else:
                    #        print('Failed to create link in Django app:', response.text)
                    #except requests.exceptions.RequestException as e:
                    #    print('Error communicating with Django app:', e)  
                    try:
                        ndef_url = f'10.0.0.218:8080/link/{uid_str}'
                        record = ntag213.create_ndef_record(tnf=0x01, record_type='U', payload=ndef_url)               
                        ntag213.write_ndef_message(record)
                        ntag_data = ntag213.dump(start_block=0, end_block=20)
                    except Exception as e:
                        print(e)               
                else:
                    print('Found duplicate card. Extracted UID:', uid_str)
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
