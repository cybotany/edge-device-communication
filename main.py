import os
import RPi.GPIO as GPIO
from helpers import authenticate_user, create_link, process_nfc_url
from pn532 import PN532_SPI
from ntag import NTAG213
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    log_file = os.getenv('LOG_FILE_PATH', '/path/to/your/logfile.log')

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
    auth_url = os.getenv('AUTH_URL', 'https://digidex.app/api/token/')
    api_url_base = os.getenv('API_URL_BASE', 'https://digidex.app/api/create-link/')

    pn532 = PN532_SPI(debug=False, reset=20, cs=4)
    pn532.SAM_configuration()
    ntag213 = NTAG213(pn532, debug=False)

    token = authenticate_user(auth_url, username, password)
    uid_list = []
    last_uid = None
    logging.info('Waiting for an NFC card...')

    try:
        while True:
            serial_number = pn532.list_passive_target(timeout=0.5)
            if serial_number and serial_number != last_uid:
                last_uid = serial_number
                uid_str = ':'.join(['{:02X}'.format(i) for i in serial_number])
                if uid_str not in uid_list:
                    uid_list.append(uid_str)
                    logging.info(f'Found new card. Extracted UID: {uid_str}')

                    api_url = f'{api_url_base}{uid_str}/'
                    if token:
                        nfc_url = create_link(api_url, token, uid_str)
                        if nfc_url:
                            stripped_url = process_nfc_url(ntag213, nfc_url)
                            record = ntag213.create_ndef_record(tnf=0x01, record_type='U', payload=stripped_url)
                            ntag213.write_ndef_message(record)
                        else:
                            logging.error("Failed to process NFC URL.")
                    else:
                        logging.error("No authentication token available.")
                else:
                    logging.info(f'Found duplicate card. Extracted UID: {uid_str}')
    except Exception as e:
        logging.error(e)
    finally:
        GPIO.cleanup()

if __name__ == '__main__':
    main()