#!/usr/bin/env python

import os
from datetime import datetime
import boto3
import bme680
from dotenv import load_dotenv
from picamera2 import Picamera2


def capture_image(filename):
    # Initialize camera
    camera = Picamera2()
    camera.start_and_capture_file(filename)


def get_environmental_data():
    # Initialize BME680 sensor
    try:
        sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    except (RuntimeError, IOError):
        sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

    # These oversampling settings can be tweaked to
    # change the balance between accuracy and noise in
    # the data.

    sensor.set_humidity_oversample(bme680.OS_2X)
    sensor.set_pressure_oversample(bme680.OS_4X)
    sensor.set_temperature_oversample(bme680.OS_8X)
    sensor.set_filter(bme680.FILTER_SIZE_3)
    sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

    sensor.set_gas_heater_temperature(320)
    sensor.set_gas_heater_duration(150)
    sensor.select_gas_heater_profile(0)

    # Up to 10 heater profiles can be configured, each
    # with their own temperature and duration.
    # sensor.set_gas_heater_profile(200, 150, nb_profile=1)
    # sensor.select_gas_heater_profile(1)

    output = '{0:.2f} C,{1:.2f} hPa,{2:.2f} %RH'.format(
        sensor.data.temperature,
        sensor.data.pressure,
        sensor.data.humidity)

    if sensor.data.heat_stable:
        print('{0},{1} Ohms'.format(
            output,
            sensor.data.gas_resistance))
    else:
        print(output)


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
    get_environmental_data()


main()