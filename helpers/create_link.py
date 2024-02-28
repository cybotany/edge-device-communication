import requests
import logging

def create_link(api_url, token, uid_str, ntag_type, ntag_use):
    try:
        headers = {'Authorization': f'Bearer {token}'}
        payload = {
            'serial_number': uid_str,
            'type': ntag_type,
            'use': ntag_use
        }
        response = requests.post(api_url, headers=headers, json=payload, verify=True) 
        if response.status_code == 201:
            logging.info('Link created successfully in Django app.')
            print('Link created successfully in Django app.')
            return response.json().get('ntag_url')
        else:
            logging.error(f'Failed to create link in Django app: {response.text}')
            print(f'Failed to create link in Django app: {response.text}')
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f'Error communicating with Django app: {e}')
        print(f'Error communicating with Django app: {e}')
        return None