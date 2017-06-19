#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

from __future__ import division
import cv2
import os
import math
import numpy as np
import time
import struct
import matplotlib
import matplotlib.pyplot as plt

def get_image():
	"""
	image pre-processing
	"""
	image_path = '/home/siaesm/Pictures/img_02/img034.jpg'
	src_img = cv2.imread(image_path)
	roi_img = src_img[ 400 : 450, 0 : src_img.shape[1] ]  	#	needs to be adjusted! (Y, X)
	gray_img = cv2.cvtColor( roi_img, cv2.COLOR_BGR2GRAY )
	blured_img = cv2.GaussianBlur(gray_img,(9, 9),0)			# may get excluded!
	#edges_img = cv2.Canny(blured_img, 30, 160)
	(thresh, binarized_img) = cv2.threshold(blured_img, 200, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
	processed_img = binarized_img
	return roi_img, processed_img

startTime = time.time()
roi_img, processed_image = get_image()
bottom_right_part = processed_image[0 : processed_image.shape[0] , processed_image.shape[1]//2: processed_image.shape[1]]
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

right_line_contour_candidates, right_line_found, length_right_line  = costum_HScan(bottom_right_part, -3) #(x,y)

def filter_get_actual_position(contour_candidates, offset, right_line=True):
	'''
	returns cropped frame pixels to actual frame 
	offset :(x, y)
	'''
	act_line = []
	line_point_list = []
	for lines in contour_candidates:
		if right_line:
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
		else:
			if (len(lines)>=2):
				for p in xrange(-2, 0):
					line_point = np.add(lines[p], offset)
					line_point_list.append(line_point)
			else:
				for p in xrange(len(lines)):
					line_point = np.add(lines[p], offset)
					line_point_list.append(line_point)

			act_line.append(line_point_list)
			line_point_list = []


	return act_line
right_line  = filter_get_actual_position(right_line_contour_candidates, (processed_image.shape[1]//2, 0), right_line=True)
# nd.array to 1d.array
right_line_contours = np.vstack(right_line).squeeze()

def get_line_specification(contours):

	rotated_rect = cv2.minAreaRect(contours)
	# rect = ((center_x,center_y),(width,height),angle)
	unchanged_rotated_rect = rotated_rect
	angle = 90 + rotated_rect[-1]
	#rotated_rect_list = list(rotated_rect)
	#print(rotated_rect[-1])
	#rotated_rect_list[-1] = angle

	return angle

right_line_angle = get_line_specification(right_line_contours)
print('\nAngle: %s'%right_line_angle)
print('executionTime: %s' %((time.time() - startTime)))

