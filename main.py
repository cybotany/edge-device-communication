_NTAG_CMD_READ = 0x30
import os
import RPi.GPIO as GPIO
from helpers import authenticate_user, create_link, process_nfc_url
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

    auth_url = os.getenv('AUTH_URL')
    api_url_base = os.getenv('API_URL_BASE')
    env_debug = os.getenv('ENV_DEBUG')

    pn532 = PN532(debug=env_debug, reset=20, cs=4)
    pn532.SAM_configuration()

    token = authenticate_user(auth_url, username, password)
    uid_list = []
    last_uid = None
    logging.info('Waiting for an NFC card...')

    try:
        while True:
            uid = pn532.list_passive_target(timeout=0.5)
            if uid and uid != last_uid:
                last_uid = uid
                uid_str = ':'.join(['{:02X}'.format(i) for i in uid])
                if uid_str not in uid_list:
                    uid_list.append(uid_str)
                    logging.info(f'Found new NTAG. Extracted UID: {uid_str}')

                    # Create a new NTAG instance for the new UID
                    ntag = NTAG(pn532)
                    ntag.fill_memory()

                    # Extract the URL from the NTAG

                    api_url = f'{api_url_base}{uid_str}/'
                    create_link(api_url, token, uid_str)

                else:
                    logging.info(f'Found duplicate NTAG. Extracted UID: {uid_str}')
    except Exception as e:
        logging.error(e)
    finally:
        GPIO.cleanup()

    def read_block(self, block_number):
        """
        Read a block of data from the card.
        """
        response = self.pn532._call_function(params=[0x01, _NTAG_CMD_READ, block_number & 0xFF],
                                             response_length=17)
        if response is None:
            print(f'Communication error while reading block {block_number}.')
            return None
        elif response[0] != 0x00:
            print(f'Error reading block {block_number}: {response[0]}')
            return None
        return response[1:][:4]
if __name__ == '__main__':
    main()