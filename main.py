import RPi.GPIO as GPIO
import pn532.pn532 as nfc
from pn532 import PN532_SPI


BLOCK_NUMBER = 6
BLOCK_DATA = bytes([0x01, 0x02, 0x03, 0x04])

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
                last_uid = uid
                uid_hex = [hex(i) for i in uid]
                if uid_hex not in uid_list:
                    uid_list.append(uid_hex)
                    print('Found new card. Extracted UID:', uid_hex)                        
                else:
                    print('Found duplicate card. Extracted UID:', uid_hex)
                
                try:
                    record1 = pn532.create_ndef_record(tnf=0x01, record_type='U', payload='https://www.google.com')
                    record2 = pn532.create_ndef_record(tnf=0x01, record_type='U', payload='https://www.microsoft.com')
                    record3 = pn532.create_ndef_record(tnf=0x01, record_type='U', payload='https://www.yahoo.com')
                    ndef_message = pn532.combine_ndef_records([record1, record2, record3])
                    pn532.write_ndef_message(ndef_message)
                except nfc.PN532Error as e:
                    print(e.errmsg)
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
