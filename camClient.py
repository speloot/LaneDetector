#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
import cv2
import serial
import socket
#import picamera
#import picamera.array
import io
#import pickle
import math
import numpy as np
import time
import struct
import Tkinter as tk
from PIL import Image, ImageTk

def button_click_exit_mainloop (event):
    event.widget.quit() # this will cause mainloop to unblock.

def get_image(src_img):
	"""
	image pre-processing
	"""
	#image_path = '/home/siaesm/Pictures/img_02/img034.jpg'
	#src_img = cv2.imread(image_path)
	roi_img = src_img[ 400 : 450, src_img.shape[1]//2: src_img.shape[1] ]  	#	needs to be adjusted! (Y, X)
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
		
	return frame_white_pixels #(x,y)

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
	# rect = ((center_x,center_y),(width,height),angle)
	rotated_rect = cv2.minAreaRect(contours)
	# rotated_rect = ((center_x,center_y),(width,height),angle)
	angle = 90 + rotated_rect[-1]

	return rotated_rect, angle

def pidController(actualPoint, setPoint, Kp):
	'''
	Calculate System Input using a "PID Controller
	'''
	# Error between the desired and actual output
	actualError = setPoint - actualPoint
	# Calculate system input
	pidResult = Kp * actualError
	return pidResult, actualError

def draw_rot_rect(image, contours, color, thickness):
	box = cv2.boxPoints(tuple(contours))
	box = np.int0(box)
	cv2.drawContours(image, [box], -1, color, thickness)

img_size = (320, 30)
root = tk.Tk()
root.geometry("320x30")
root.wm_title("pi camera")
root.bind("<Button>", button_click_exit_mainloop)
root.mainloop()
print 'Released!'
tk_img = ImageTk.PhotoImage(Image.new('RGB', img_size))
panel = tk.Label(root, image=tk_img)
panel.place(x=0,y=0,width=img_size[0],height=img_size[1])

# connect to the server
client_socket = socket.socket()
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
client_socket.connect(('192.168.75.13', 7798))
data_file = client_socket.makefile()
frame_stream = io.BytesIO()



while True:

	start_time = time.time()
	frame_len = struct.unpack('<L', data_file.read(struct.calcsize('<L')))[0]
	
	if not frame_len:
		print'No Image'

	frame_stream.seek(0)
	frame_stream.write(data_file.read(frame_len))
	frame_stream.seek(0)
	print 'Image is received!'
	imgBgr =  cv2.imdecode(np.fromstring(frame_stream.getvalue(), dtype=np.uint8), 1)

	
	processed_image = get_image(imgBgr)
	
	right_line_contour_candidates = costum_HScan(processed_image, -3) #(x,y)
	right_line  = filter_get_actual_position(right_line_contour_candidates, (0, 0)) #processed_image.shape[1]//2
	# nd.array to 1d.array
	right_line_contours = np.vstack(right_line).squeeze()
	r_rot_rect, Angle = get_line_specification(right_line_contours)
	print('\nAngle: %s'%Angle)
	print('\nx: %s'%r_rot_rect[0][1])







	draw_rot_rect(processed_image, r_rot_rect, (105, 0, 255), 2)
	img = Image.fromarray(processed_image)
	tk_img = ImageTk.PhotoImage(img.resize((320, 30),Image.ANTIALIAS))
	panel.configure(image=tk_img)
	root.update()
	print('\nElapsed Time: \n%s\n' %(time.time()-start_time))
