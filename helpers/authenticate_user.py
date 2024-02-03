import requests
import logging
import sys

def authenticate_user(auth_url, username, password):
    try:
        response = requests.post(auth_url, data={'username': username, 'password': password})
        if response.status_code == 200:
            logging.info("Authentication successful, JWT access token obtained.")
            return response.json().get('access')
        else:
            logging.error(f"Failed to authenticate: {response.text}")
            sys.exit("Authentication failed, exiting program.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during authentication: {e}")
        sys.exit(f"Error during authentication request, exiting program.")
