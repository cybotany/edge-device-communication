import boto3
from dotenv import load_dotenv
import os
import time
from picamera2 import Picamera2


# Load .env file
load_dotenv()

my_bucket = os.environ.get('S3_BUCKET')
s3 = boto3.resource('s3')

# Upload a new file
data = open('test.jpg', 'rb')
s3.Bucket(my_bucket).put_object(Key='test.jpg', Body=data)

# Initialize camera
camera = Picamera2()
interval = 500