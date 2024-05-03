import RPi.GPIO as GPIO

from pn532 import PN532_SPI as PN532
from helpers import authenticate_user, register_ntag
from ntag import NTAG

def main():
    try:
        pn532 = PN532(debug=True, reset=20, cs=4)
        pn532.SAM_configuration()
        ntag = NTAG(pn532, debug=True)

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
                        print(ntag_url)
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