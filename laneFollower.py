#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
from __future__ import division
import cv2
import serial
import socket
import picamera
import picamera.array
import io
import pickle
import math
import numpy as np
import time
import struct


def process_image(img):
	"""
	image pre-processing
	"""
	roi_img = img[ 220 : 450, 0 : img.shape[1] ]  
	gray_img = cv2.cvtColor( roi_img, cv2.COLOR_BGR2GRAY )
	blured_img = cv2.GaussianBlur(gray_img,(5,5),0)
	(thresh, bin_img) = cv2.threshold(blured_img, 200, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
	return bin_img

def costum_HScan(frame, offset): # , first_white_pixel_x , offset):
	'''
	Scans a binary frame horizontally and returns the coordinations of wihte pixels
	Input: numpy.ndarray
	Output: a list of white pixels
	'''

	frame_white_pixels = []
	white_pixels = []

	first_white_pixel_x = - offset
	frame_derivative = np.diff(frame)
	nRows = frame_derivative.shape[0] -1 # in order to start from bottom.. 
	
	for i in xrange(nRows):
		row = nRows-i
		start_pixel = first_white_pixel_x + offset
		# find the position of the edges
		ind_row_derivative = np.nonzero(frame_derivative[row, start_pixel:]) # returns a tuple
		if(len(ind_row_derivative[0])!=0):
			#for p in xrange(len(ind_row_derivative[0])): 
			for p in xrange(2): 
				white_pixels.append([ind_row_derivative[0][p] + start_pixel, row]) #(x,y)
		else: 
			continue
		first_white_pixel_X= white_pixels[0]
		frame_white_pixels.append(white_pixels)
		white_pixels = []
	return frame_white_pixels

def get_first_line(contour_candidates, offset):
	'''
	returns cropped frame pixels to actual frame 
	'''
	first_line = []
	for lines in contour_candidates:
		p = np.add(lines, offset)
		first_line.append(p)
	return first_line

def get_line_specification(contours):

	rotated_rect = cv2.minAreaRect(contours)
	# rect = ((center_x,center_y),(width,height),angle)
	if (rotated_rect[1][0] < rotated_rect[1][1]):
		angle = 90 + rotated_rect[-1]
	else:
		angle = 180 + rotated_rect[-1]

	rotated_rect_list = list(rotated_rect)
	rotated_rect_list[-1] = angle

	return rotated_rect_list

def x_intersection(p1, p2, a, b):
	'''
	 Returns the x of lines intersection
	 input: two points + two angle
	 output: x_coordinate : X = ( (y_2 - b * x_2) - (y_1 - a* x_1) ) // (a - b)
	'''
	# convert all coordinates floating point values to int ???         needs to be checked!!!
	p1 = np.int0(p1)
	p2 = np.int0(p2)
	gradient_a = - math.tan(a*np.pi/180)
	gradient_b = - math.tan(b*np.pi/180)
	intersect = ((p2[1]-gradient_b*p2[0]) - (p1[1]-gradient_a*p1[0]))//(gradient_a-gradient_b)
	return np.int(intersect)

def pidController(actualPoint, setPoint, prevError, Kp):
	'''
	Calculate System Input using a "PID Controller
	'''
	# Error between the desired and actual output
	actualError = setPoint - actualPoint
	# Calculate system input
	pidResult = Kp * actualError
	return pidResult, actualError


s = serial.Serial('/dev/ttyAMA0', 19200) 
print('Serial Connection Is Established!')
'''
dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
dataSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
dataSocket.connect(('192.168.75.96', 7798))
print('Socket Is Binded -> ')
dataFile= dataSocket.makefile('ab')
'''
init_error_val = 0

with picamera.PiCamera() as camera:
	camera.resolution = (640, 480) 
	camera.sensor_mode = 7
	camera.shutter_speed= 10000
	time.sleep(2)
	print('Camera Is ON!')
	stream = io.BytesIO()

	for foo in camera.capture_continuous(stream, 'jpeg', True):
		startTime=time.time()
		#stream.seek(0)
		#-------------------------------------------------
		#live_stream_data = stream.read()
		#stream.truncate()
		#-------------------------------------------------
		imgBgr =  cv2.imdecode(np.fromstring(stream.getvalue(), dtype=np.uint8), 1)
		processed_img = process_image(imgBgr)
		bottom_right_part = processed_img[processed_img.shape[0]//2 : processed_img.shape[0],
										 processed_img.shape[1]//2 : processed_img.shape[1]]
		bottom_left_part = processed_img[processed_img.shape[0]//2 : processed_img.shape[0],
										 0 : processed_img.shape[1]//2 -1]
		right_line_contour_candidates   = costum_HScan(bottom_right_part, -3)
		dashed_line_contour_candidates	= costum_HScan(bottom_left_part, -3)
		if ((len(right_line_contour_candidates)!=0) & (len(dashed_line_contour_candidates)!=0)):
			right_line  = get_first_line(right_line_contour_candidates, ((processed_img.shape[0]//2)-1, (processed_img.shape[1]//2)-1))
			dashed_line = get_first_line(dashed_line_contour_candidates, (0, (processed_img.shape[1]//2)-1))
			# nd.array to 1d.array
			right_line_contours = np.vstack(right_line).squeeze()
			dashed_line_contours = np.vstack(dashed_line).squeeze()
			r_rot_rect = get_line_specification(right_line_contours)
			d_rot_rect = get_line_specification(dashed_line_contours)
			x_intersect = x_intersection(r_rot_rect[0], d_rot_rect[0], r_rot_rect[-1], d_rot_rect[-1] )
			print('\nvanishing point: %s'%x_intersect)
			set_point = 300 #----------------------------------------------------------------
			( PIDoutput, error_val) = pidController(x_intersect, set_point, init_error_val, Kp = 2) 
			init_error_val = error_val
			# Set the Speed of Motors
			initialSpeed = 90
			rWheelSpeed =  initialSpeed + int(PIDoutput)		
			lWheelSpeed =  initialSpeed - int(PIDoutput)
			if(rWheelSpeed<0):
				rWheelSpeed = 0
			elif(lWheelSpeed<0):
				lWheelSpeed = 0

			if(rWheelSpeed>255):
				rWheelSpeed = 255
			elif(lWheelSpeed>255):
				lWheelSpeed = 255
			# just to check the live streaming of images
			lWheelSpeed = 0
			rWheelSpeed = 0

			print('\nright wheel speed: %s'%rWheelSpeed)	
			print('\nleft wheel speed: %s'%lWheelSpeed)
			s.write(struct.pack('>B',rWheelSpeed))
			s.write(struct.pack('>B',lWheelSpeed))
			s.write('\n')
		else: 
			print("\nNo Marking Lines!!!")
			s.write(struct.pack('>B',0))
			s.write(struct.pack('>B',0))
			s.write('\n')
	
		'''	
		dataFile.write(struct.pack('<L', len(live_stream_data)))
		dataFile.flush()
		dataFile.write(live_stream_data)
		dataFile.flush()
		stream.seek(0)
		stream.truncate()
		'''
		print('execution time: %s' %((time.time() - startTime)))




