import RPi.GPIO as GPIO
import pn532.pn532 as nfc
from pn532 import PN532_SPI


BLOCK_NUMBER = 6
BLOCK_DATA = bytes([0x00, 0x01, 0x02, 0x03])

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
                    pn532.ntag2xx_write_block(BLOCK_NUMBER, BLOCK_DATA)
                    if pn532.ntag2xx_read_block(BLOCK_NUMBER) == BLOCK_DATA:
                        print('write block %d successfully' % BLOCK_NUMBER)
                except nfc.PN532Error as e:
                    print(e.errmsg)
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
