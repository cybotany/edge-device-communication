from picamera2 import Picamera2

def capture_image(filename):
    # Initialize camera
    camera = Picamera2()
    camera.start_and_capture_file(filename)