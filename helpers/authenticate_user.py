import requests
import sys
import os

def authenticate_user(auth_url):
    username = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')
    auth_url = os.getenv('AUTH_URL')
    try:
        response = requests.post(auth_url, data={'username': username, 'password': password})
        if response.status_code == 200:
            return response.json().get('access')
        else:
            sys.exit("Authentication failed, exiting program.")
    except requests.exceptions.RequestException as e:
        sys.exit(f"Error during authentication request, exiting program.")
