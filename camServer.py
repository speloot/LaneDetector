
import socket
import io
import picamera
import struct
import time
import serial
from PIL import Image
import threading
import pickle
from cStringIO import StringIO
import base64
'''
cam server:
			1-sends images fron picamera to a client
			2-receives commands from cam server
			3-send commands to the Arduino

'''

# create a socket object
server_socket = socket.socket()
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('', 7798))
server_socket.listen(0)



# create serial connection to Arduino
#s = serial.Serial('/dev/ttyAMA0', 19200) 
#print('Serial Connection Is Established!')

# Set camera parameters
camera = picamera.PiCamera()
camera.resolution = (640, 480) 
camera.sensor_mode = 7
camera.shutter_speed= 10000
camera.framerate=40
# Thread..
image_lock = threading.Lock()
# pickle
src = StringIO()
p = pickle.Pickler(src)
# Image to String

frame = b'asdf'
timing = False


def time_op(start, name):
	tt = time.time() - start
	if timing:
		print('Time taken for %s: %s'%(name, tt))
	return time.time()

def camera_thread():
	global frame
	global frame_str
	cam_stream = io.BytesIO()

	for foo in camera.capture_continuous(cam_stream, 'jpeg', True, quality=15, thumbnail=None):
		
		cam_stream.seek(0)
		frame = cam_stream.read()
		frame_str = base64.b64encode(frame)
		cam_stream.seek(0)
		cam_stream.truncate()
		#if no clients are connected, just chill and wait to save power.
		while(threading.active_count() < 3):
			time.sleep(0.2)

def network_thread(server_socket):
	global frame
	global frame_str

	client_connection = server_socket.makefile('rwb')
	try:
		while True:
			command = client_connection.read(1)
			if command != b'':
				#t = time_op(t, 'recv command')
				if command ==b'p':
				# 	t= time.time()
				# #	t=time_op(t, 'capture')
				# 	client_connection.write(struct.pack('<L', len(frame)))
				# #	t = time_op(t, 'send header')
				# 	# Rewind the stream and send the image data over the wire
				# 	client_connection.write(frame)
				# 	client_connection.flush()
				
				client_connection.write(struct.pack('<L', len(frame_str)))
				client_connection.write(frame_str)
				client_connection.flush()

				#	t = time_op(t, 'send data')
			else:
				raise Exception('Stream broken!')
	except:
			print('Error: %s'%sys.exc_info()[0])
			print('Error: %s'%sys.exc_info()[1])
			print('Error: %s'%sys.exc_info()[2])
			client_connection.close()
			server_socket.close()


threading.Thread(target=camera_thread, daemon=True).start()

while True:
	connection, addr = server_socket.accept()
   
	threading.Thread(target=network_thread, args=[connection]).start()
	print(connection)



