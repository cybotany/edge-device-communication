import RPi.GPIO as GPIO
from pn532 import PN532_SPI

if __name__ == '__main__':
    try:
        pn532 = PN532_SPI(debug=False, reset=20, cs=4)
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
                try:
                    block0 = pn532.ntag2xx_read_block(0)
                    uid = block0[:7]
                    uid_hex = [hex(i) for i in uid]

                    if uid_hex not in uid_list:
                        uid_list.append(uid_hex)
                        print('Found new card. Extracted UID:', uid_hex)

                    else:
                        print('Found duplicate card. Extracted UID:', uid_hex)
                except Exception as e:
                    print("Error reading tag:", e)
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
