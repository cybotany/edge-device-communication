#!/usr/bin/env python
import os
from datetime import datetime
from environment_sensor import get_environmental_data
from camera import capture_image


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

    path = os.path.join(root_dir, folder, filename)
    get_environmental_data()
    #capture_image(filename)
    #return path

main()
