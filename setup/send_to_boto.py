from dotenv import load_dotenv
import boto3
import os

def upload_to_s3(filename, path):
    # Load .env file
    load_dotenv()

    my_bucket = os.environ.get('S3_BUCKET')
    s3 = boto3.resource('s3')

    # Upload a new file
    data = open(filename, 'rb')
    s3.Bucket(my_bucket).put_object(Key=path, Body=data)