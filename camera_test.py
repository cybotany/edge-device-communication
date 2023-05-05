import time
from picamera2 import Picamera2

# Initialize the camera
camera = Picamera2()

# Capture the image
camera.start_and_capture_file('test_image.jpg')

# Close the camera
camera.close()

