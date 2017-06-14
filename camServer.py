
import socket
import io
import picamera
import sys
import struct
import time

'''
cam server sends images fron picamera to a client
'''

# create a socket object
server_socket = socket.socket()
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', port))
server_socket.listen(0)
dataSocket.connect(('192.168.75.96', 7798))

dataFile= server_socket.makefile('ab')

client_socket, addr = server_socket.accept()

with picamera.PiCamera() as camera:
	camera.resolution = (640, 480) 
	camera.sensor_mode = 7
	camera.shutter_speed= 10000
	time.sleep(2)
	stream = io.BytesIO()

	for foo in camera.capture_continuous(stream, 'jpeg', True):
		stream.seek(0)
        frame = stream.read()
        stream.seek(0)
		stream.truncate()
		
		dataFile.write(struct.pack('<L', len(frame)))
		dataFile.flush()

		dataFile.write(frame)
		dataFile.flush()
		



