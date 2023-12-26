import RPi.GPIO as GPIO
from pn532 import PN532_SPI

def extract_uid(pages):
    """
    Extract the 7-byte UID from the first 9 bytes of memory.
    """
    return pages[:7]

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
                    page0 = pn532.ntag2xx_read_block(0)
                    page1 = pn532.ntag2xx_read_block(1)
                    page2 = pn532.ntag2xx_read_block(2)
                    combined_pages = page0 + page1 + page2[:1]

                    extracted_uid = extract_uid(combined_pages)
                    uid_hex = [hex(i) for i in extracted_uid]

                    if uid_hex not in uid_list:
                        uid_list.append(uid_hex)
                        print('Found new card. Extracted UID:', uid_hex)

                        for i in range(135):
                            try:
                                print(i, ':', ' '.join(['%02X' % x
                                    for x in pn532.ntag2xx_read_block(i)]))
                            except Exception as e:
                                print(e)
                                break
                    else:
                        print('Found duplicate card. Extracted UID:', uid_hex)
                except Exception as e:
                    print("Error reading tag:", e)
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
