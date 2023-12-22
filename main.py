import RPi.GPIO as GPIO
from pn532 import *

def extract_uid(pages):
    """ Extract the 7-byte UID from the first 9 bytes of memory. """
    # UID is the first 7 bytes of the combined pages
    return pages[:7]

if __name__ == '__main__':
    try:
        pn532 = PN532_SPI(debug=False, reset=20, cs=4)

        ic, ver, rev, support = pn532.get_firmware_version()
        print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))

        # Configure PN532 to communicate with MiFare cards
        pn532.SAM_configuration()

        print('Waiting for RFID/NFC card...')
        uid_list = []
        last_uid = None

        while True:
            uid = pn532.read_passive_target(timeout=0.5)
            if uid is None:
                continue
            if uid != last_uid:
                last_uid = uid
                try:
                    # Read the first 3 blocks (9 bytes)
                    page0 = pn532.ntag2xx_read_block(0)
                    page1 = pn532.ntag2xx_read_block(1)
                    page2 = pn532.ntag2xx_read_block(2)
                    combined_pages = page0 + page1 + page2[:1]  # First 9 bytes

                    extracted_uid = extract_uid(combined_pages)
                    uid_hex = [hex(i) for i in extracted_uid]

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
