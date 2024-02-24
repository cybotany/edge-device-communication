import os
import RPi.GPIO as GPIO
from helpers import authenticate_user, create_link, process_ntag_url
from pn532 import PN532_SPI as PN532
from ntag import NTAG
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    log_file = os.getenv('LOG_FILE_PATH')

    # Rotate log after reaching 10MB, keep 3 backup log files
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=3)
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

def main():
    setup_logging()

    username = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')
    env_debug = os.getenv('DEBUG')

    if env_debug:
        auth_url = os.getenv('DEV_AUTH_URL')
        api_url_base = os.getenv('DEV_API_URL_BASE')
    else:
        auth_url = os.getenv('PROD_AUTH_URL')
        api_url_base = os.getenv('PROD_API_URL_BASE')

    pn532 = PN532(debug=env_debug, reset=20, cs=4)
    pn532.SAM_configuration()
    ntag = NTAG(pn532, debug=env_debug)

    token = authenticate_user(auth_url, username, password)
    uid_list = []
    last_uid = None
    message1 = 'Waiting for an NFC card...'
    logging.info(message1)
    print(message1)

    try:
        while True:
            serial_number = pn532.list_passive_target(timeout=0.5)
            if serial_number and serial_number != last_uid:
                last_uid = serial_number
                uid_str = ':'.join(['{:02X}'.format(i) for i in serial_number])
                if uid_str not in uid_list:
                    uid_list.append(uid_str)
                    message2 = f'Found new card. Extracted UID: {uid_str}'
                    logging.info(message2)
                    print(message2)

                    api_url = f'{api_url_base}{uid_str}/'
                    ntag_url = create_link(api_url, token, uid_str)
                    
                    if ntag_url:
                        stripped_url = process_ntag_url(ntag, ntag_url)
                        record = ntag.create_ndef_record(tnf=0x01, record_type='U', payload=stripped_url)
                        ntag.write_ndef_message(record)
                    else:
                        message3 = "Failed to process NFC URL."
                        logging.info(message3)
                        print(message3)
                else:
                    message4 = f'Found duplicate card. Extracted UID: {uid_str}'
                    logging.info(message4)
                    print(message4)
    except Exception as e:
        logging.error(e)
        print(e)
    finally:
        GPIO.cleanup()

if __name__ == '__main__':
    main()