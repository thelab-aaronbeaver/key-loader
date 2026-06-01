import socket
import subprocess

UDP_IP = "0.0.0.0"  # Listen on all available interfaces
UDP_PORT = 5005  # Choose a port number

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

while True:
    data, addr = sock.recvfrom(1024)  # Buffer size is 1024 bytes
    message = data.decode()

    if message == "START":
        subprocess.call(['osascript', '-e', 'tell application "System Events" to tell application process "LightBurn" to keystroke return'])