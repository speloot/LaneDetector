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

def get_image(src_img):
	"""
	image pre-processing
	"""
	#image_path = '/home/siaesm/Pictures/img_02/img034.jpg'
	#src_img = cv2.imread(image_path)
	roi_img = src_img[ 400 : 450, 0 : src_img.shape[1] ]  	#	needs to be adjusted! (Y, X)
	gray_img = cv2.cvtColor( roi_img, cv2.COLOR_BGR2GRAY )
	blured_img = cv2.GaussianBlur(gray_img,(9, 9),0)			# may get excluded!
	#edges_img = cv2.Canny(blured_img, 30, 160)
	(thresh, binarized_img) = cv2.threshold(blured_img, 200, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
	processed_img = binarized_img
	return processed_img

def costum_HScan(regionOfInterest, x_offset): # , first_white_pixel_x , offset):
	'''
	Scans the regionOfInterest[Y, X] and returns the coordinations of wihte pixels (x, y) and the length of 'em
	Input: numpy.ndarray
	Output: a list of white pixels
	'''
	white_pixel_found = False
	frame_white_pixels = []
	white_pixels = []
	first_white_pixel_x = - x_offset
	frame_derivative = np.diff(regionOfInterest)
	nRows = regionOfInterest.shape[0] -1 # in order to start from bottom.. 
	length = 0
	for i in xrange(nRows):

		row = nRows-i
		start_pixel = first_white_pixel_x + x_offset
		# find the position of the edges
		ind_row_derivative = np.nonzero(frame_derivative[row, start_pixel:]) # returns a tuple of x coordinates
		length_ind = len(ind_row_derivative[0])
		if(length_ind!=0):
			white_pixel_found = True
			length +=1
			for p in xrange(len(ind_row_derivative[0])): 
				white_pixels.append([ind_row_derivative[0][p] + start_pixel, row]) #(x,y)	
		else: 
			#print('No White Pixels..')
			break
		first_white_pixel_x= white_pixels[0][0]
		frame_white_pixels.append(white_pixels)
		white_pixels = []
		
	return frame_white_pixels, white_pixel_found, length #(x,y)

def filter_get_actual_position(contour_candidates, offset):
	'''
	returns cropped frame pixels to actual frame 
	offset :(x, y)
	'''
	act_line = []
	line_point_list = []
	for lines in contour_candidates:
		
		if (len(lines)>=2):
			for p in xrange(2):
				line_point = np.add(lines[p], offset)
				line_point_list.append(line_point)
		else:
			for p in xrange(len(lines)):
				line_point = np.add(lines[p], offset)
				line_point_list.append(line_point)

		act_line.append(line_point_list)
		line_point_list = []

	return act_line

def get_line_specification(contours):

	rotated_rect = cv2.minAreaRect(contours)
	# rotated_rect = ((center_x,center_y),(width,height),angle)
	angle = 90 + rotated_rect[-1]

	return angle, rotated_rect[0][1]

def pidController(actualPoint, setPoint, Kp):
	'''
	Calculate System Input using a "PID Controller
	'''
	# Error between the desired and actual output
	actualError = setPoint - actualPoint
	# Calculate system input
	pidResult = Kp * actualError
	return pidResult, actualError


s = serial.Serial('/dev/ttyAMA0', 115200) 
print('Serial Connection Is Established!')
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
		
		imgBgr =  cv2.imdecode(np.fromstring(stream.getvalue(), dtype=np.uint8), 1)
		print 'image taken'
		processed_image = get_image(imgBgr)
		bottom_right_part = processed_image[0 : processed_image.shape[0] , processed_image.shape[1]//3: processed_image.shape[1]]
		right_line_contour_candidates, right_line_found, length_right_line  = costum_HScan(bottom_right_part, -3) #(x,y)
		right_line  = filter_get_actual_position(right_line_contour_candidates, (processed_image.shape[1]//2, 0))
		# nd.array to 1d.array
		right_line_contours = np.vstack(right_line).squeeze()
		right_line_angle, right_line_x = get_line_specification(right_line_contours)
		print('\nAngle: %s'%right_line_angle)
		print('\nx: %s'%right_line_x)
		set_point_A = 66.5#----------------------------------------------------------------
		set_point_X = 25.0
		( PID_A, error_val_A) = pidController(right_line_angle, set_point_A, Kp = 10) 
		( PID_X, error_val_X) = pidController(right_line_x, set_point_X, Kp = 30) 
		#init_error_val = error_val
		# Set the Speed of Motors
		initialSpeed = 70
		rWheelSpeed =  initialSpeed + int(PID_X)		
		lWheelSpeed =  initialSpeed - int(PID_X)
		if(rWheelSpeed<0):
			rWheelSpeed = 0
		elif(lWheelSpeed<0):
			lWheelSpeed = 0

		if(rWheelSpeed>255):
			rWheelSpeed = 255
		elif(lWheelSpeed>255):
			lWheelSpeed = 255
		print('\nright wheel speed: %s'%rWheelSpeed)	
		print('\nleft wheel speed: %s'%lWheelSpeed)
		# just to check the live streaming of images
		#lWheelSpeed = 0
		#rWheelSpeed = 0

		#print('\nright wheel speed: %s'%rWheelSpeed)	
		#print('\nleft wheel speed: %s'%lWheelSpeed)
		s.write(struct.pack('>b',rWheelSpeed))
		s.write(struct.pack('>b',lWheelSpeed))
		s.write('\n')

	
		print('\nexecutionTime: %s' %((time.time() - startTime)))
		#time.sleep(2)
		stream.seek(0)
