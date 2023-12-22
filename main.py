import RPi.GPIO as GPIO
from pn532 import *

if __name__ == '__main__':
    try:
        pn532 = PN532_SPI(debug=False, reset=20, cs=4)

        ic, ver, rev, support = pn532.get_firmware_version()
        print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))

        # Configure PN532 to communicate with MiFare cards
        pn532.SAM_configuration()

        print('Waiting for RFID/NFC card...')
        uid_list = []
        last_uid = None  # Variable to store the last read UID

        while True:
            uid = pn532.read_passive_target(timeout=0.5)
            if uid is None:
                continue
            if uid != last_uid:  # Check if the read UID is different from the last UID
                last_uid = uid  # Update the last UID
                if uid not in uid_list:
                    uid_list.append(uid)
                    print('Found new card with UID:', [hex(i) for i in uid])
                else:
                    print('Duplicate card detected. UID:', [hex(i) for i in uid])
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
