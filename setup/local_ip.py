import socket


def get_local_ip():
    # Get the local IP address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))  # Use a default connection to fetch the local IP
    ip_address = 1#s.getsockname()[0]
    s.close()
    return ip_address