import os
from datetime import datetime, timezone
import boto3
from dotenv import load_dotenv
from picamera2 import Picamera2
from sense_hat import SenseHat


def capture_image(filename):
    # Initialize camera
    camera = Picamera2()
    camera.start_and_capture_file(filename)


def get_environmental_data():
    # Initialize SenseHat
    sense = SenseHat()

    # Get environmental data
    temp_c = sense.get_temperature()
    humidity = sense.get_humidity()
    pressure = sense.get_pressure()

    # Convert temperature to Fahrenheit and round all values to 2 decimal places
    temp_c = round(temp_c, 2)
    temp_f = round(temp_c * 9/5 + 32, 2)
    humidity = round(humidity, 2)
    pressure = round(pressure, 2)

    return temp_c, temp_f, humidity, pressure



def upload_to_s3(filename, path):
    # Load .env file
    load_dotenv()

    my_bucket = os.environ.get('S3_BUCKET')
    s3 = boto3.resource('s3')

    # Upload a new file
    data = open(filename, 'rb')
    s3.Bucket(my_bucket).put_object(Key=path, Body=data)


def main():

    # Create root directory
    user = 'test'
    device = 'cea01'
    root_dir = f'{user}/{device}'

    # Get for folder and filename
    now = datetime.now()

    year = now.year
    month = now.month
    day = now.day
    folder = f'{year}/{month}/{day}'

    hour = now.hour
    minute = now.minute
    second = now.second
    filename = f'image-{hour}-{minute}-{second}.jpg'
    
    capture_image(filename)
    path = os.path.join(root_dir, folder, filename)

    upload_to_s3(filename, path)
    temp_c, temp_f, humidity, pressure = get_environmental_data()
    print(f'Temperature: {temp_c} C')
    print(f'Temperature: {temp_f} F')
    print(f'Humidity: {humidity} %')
    print(f'Pressure: {pressure} mbar')

main()