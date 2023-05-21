from decouple import config
import requests
import json

url = 'http://10.0.0.218:8080/api/token/'

credentials = {
    'username': config('USERNAME'),
    'password': config('PASSWORD'),
}

response = requests.post(url, data=credentials)

print(response.json())