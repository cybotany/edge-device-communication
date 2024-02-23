import os
import logging
from logging.handlers import RotatingFileHandler
import RPi.GPIO as GPIO

from nfc.communication import PN532_SPI as PN532
from nfc.helpers import authenticate_user, create_link
from nfc.tags import NTAG

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

    auth_url = os.getenv('AUTH_URL')
    api_url_base = os.getenv('API_URL_BASE')
    env_debug = os.getenv('ENV_DEBUG')

    pn532 = PN532(debug=env_debug, reset=20, cs=4)
    pn532.SAM_configuration()

    token = authenticate_user(auth_url, username, password)
    ntags = []
    last_uid = None
    logging.info('PN532 NFC reader initialized.')

    try:
        while True:
            uid = pn532.list_passive_target(timeout=0.5)
            if uid and uid != last_uid:
                last_uid = uid
                clean_uid = ':'.join(['{:02X}'.format(i) for i in uid])
                if clean_uid not in ntags:
                    ntags.append(clean_uid)
                    logging.info(f'Found new NTAG: {clean_uid}')

                    # Create a new NTAG instance for the new UID
                    ntag = NTAG(pn532, clean_uid)
                    ntags.append(ntag)

                    api_url = f'{api_url_base}{clean_uid}/'
                    create_link(api_url, token, clean_uid)

                else:
                    logging.info(f'Found duplicate NTAG: {clean_uid}')
    except Exception as e:
        logging.error(e)
    finally:
        GPIO.cleanup()

if __name__ == '__main__':
    main()