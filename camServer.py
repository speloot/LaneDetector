
import socket
import io
import picamera
import struct
import time
from PIL import Image
'''
cam server sends images fron picamera to a client
'''

# create a socket object
server_socket = socket.socket()
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('', 7798))
server_socket.listen(0)

client_socket, addr = server_socket.accept()

dataFile = client_socket.makefile('ab')


with picamera.PiCamera() as camera:
	camera.resolution = (640, 480) 
	camera.sensor_mode = 7
	camera.shutter_speed= 10000
	time.sleep(2)
	cam_stream = io.BytesIO()

	for foo in camera.capture_continuous(cam_stream, 'jpeg', True):
		startTime = time.time()
		cam_stream.seek(0)
		frame = cam_stream.read()
		cam_stream.seek(0)
		cam_stream.truncate()
		dataFile.write(struct.pack('<L', len(frame)))
		dataFile.flush()

		dataFile.write(frame)
		dataFile.flush()
		print'Image Is Sent!'
		print('\nElapsed Time: \n%s\n' %(time.time()-startTime))



