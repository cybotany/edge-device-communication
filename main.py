import RPi.GPIO as GPIO
from pn532 import *

def unique_uid(uid, uid_list):
    """ Check if UID is unique in the list """
    return not any(uid == existing_uid for existing_uid in uid_list)

if __name__ == '__main__':
    try:
        pn532 = PN532_SPI(debug=False, reset=20, cs=4)

        ic, ver, rev, support = pn532.get_firmware_version()
        print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))

        # Configure PN532 to communicate with MiFare cards
        pn532.SAM_configuration()

        print('Waiting for RFID/NFC card...')
        uid_list = []
        while True:
            # Check if a card is available to read
            uid = pn532.read_passive_target(timeout=0.5)
            print('.', end="")
            # Try again if no card is available.
            if uid is None:
                continue
            if unique_uid(uid, uid_list):
                uid_list.append(uid)
                print('Found new card with UID:', [hex(i) for i in uid])
            else:
                print('Duplicate card detected. UID:', [hex(i) for i in uid])
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
