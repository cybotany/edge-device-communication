import requests
from decouple import config

def post_to_web_server(ip_address, unique_id):
    # Post to web server
    url = config('URL')

    # Get JWT
    token_response = requests.post(f'{url}api/token/', data={
        'username': config('USERNAME'),
        'password': config('PASSWORD'),
    })

    if token_response.status_code != 200:
        print("Failed to obtain JWT.")
        return

    token = token_response.json().get('access')
    
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.post(f'{url}identify_cea/', headers=headers, data={
        'ip_address': ip_address,
        'identifier': unique_id,
    })

    if response.status_code == 200:
        print("Raspberry Pi successfully registered.")
    else:
        print("Failed to register Raspberry Pi.")
        print(response.status_code)