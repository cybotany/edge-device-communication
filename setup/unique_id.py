import os

def get_unique_id():
    # Get the unique identifier of the Raspberry Pi
    unique_id = 1#os.popen('cat /sys/class/net/wlan0/address').read()
    return unique_id