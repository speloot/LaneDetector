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
	image_path = '/home/siaesm/Pictures/img_02/img019.jpg'
	src_img = cv2.imread(image_path)
	roi_img = src_img[ 220 : 450, 0 : src_img.shape[1] ]  	#	needs to be adjusted! (Y, X)
	gray_img = cv2.cvtColor( roi_img, cv2.COLOR_BGR2GRAY )
	blured_img = cv2.GaussianBlur(gray_img,(9, 9),0)			# may get excluded!
	#edges_img = cv2.Canny(blured_img, 30, 160)
	(thresh, binarized_img) = cv2.threshold(blured_img, 200, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
	processed_img = binarized_img
	return roi_img, processed_img

startTime = time.time()
roi_img, processed_image = get_image()
print'Processed Image Shape: %s'%(processed_image.shape,)

# devide the frame into 4 separate sub-frame 	#(260, 640)
#top_right_part = processed_image[0 : processed_image.shape[0]//2-1, processed_image.shape[1]//2 : processed_image.shape[1]]
#top_left_part = processed_image[0 : processed_image.shape[0]//2-1, 0 : processed_image.shape[1]//2 -1]

def costum_HScan(ROI, offset): # , first_white_pixel_x , offset):
	'''
	Scans a binary frame horizontally and returns the coordinations of wihte pixels
	Input: numpy.ndarray
	Output: a list of white pixels
	'''

	frame_white_pixels = []
	white_pixels = []

	first_white_pixel_x = - offset
	frame_derivative = np.diff(ROI)
	nRows = ROI.shape[0] -1 # in order to start from bottom.. 
	
	for i in xrange(nRows):
		row = nRows-i
		start_pixel = first_white_pixel_x + offset
		# find the position of the edges
		ind_row_derivative = np.nonzero(frame_derivative[row, start_pixel:]) # returns a tuple of x coordinates
		length_ind = len(ind_row_derivative[0])
		if(length_ind!=0):
			for p in xrange(len(ind_row_derivative[0])): 
				white_pixels.append([ind_row_derivative[0][p] + start_pixel, row]) #(x,y)
		else: 
			white_pixels.append([])
			continue
		first_white_pixel_x= white_pixels[0][0]
		frame_white_pixels.append(white_pixels)
		white_pixels = []
	return frame_white_pixels #(x,y)

bottom_left_part =  processed_image[0 : processed_image.shape[0] , 0 : processed_image.shape[1]//2 -1] #(Y, X)
bottom_right_part = processed_image[0 : processed_image.shape[0] , processed_image.shape[1]//2: processed_image.shape[1]]

right_line_contour_candidates   = costum_HScan(bottom_right_part, -3) #(x,y)
#dashed_line_contour_candidates	= costum_HScan(bottom_left_part, -3) #(x,y)



#print '\ndashed_line_contour_candidates: %s'%dashed_line_contour_candidates
def filter_get_actual_position(contour_candidates, offset):
	'''
	returns cropped frame pixels to actual frame 
	'''
	act_line = []
	line_point_list = []
	for lines in contour_candidates:
		if (lines!=[]):
			for p in xrange(2):
				line_point = np.add(lines[p], offset)
				line_point_list.append(line_point)
			act_line.append(line_point_list)
			line_point_list = []

	return act_line

right_line  = filter_get_actual_position(right_line_contour_candidates, (processed_image.shape[1]//2, 0))

#dashed_line = filter_get_actual_position(dashed_line_contour_candidates, (0, 0))


# nd.array to 1d.array
right_line_contours = np.vstack(right_line).squeeze()
#dashed_line_contours = np.vstack(dashed_line).squeeze()


def get_line_specification(contours):

	rotated_rect = cv2.minAreaRect(contours)
	# rect = ((center_x,center_y),(width,height),angle)
	unchanged_rotated_rect = rotated_rect
	#Compare w-h
	if (rotated_rect[1][0] < rotated_rect[1][1]):
		angle = 90 + rotated_rect[-1]
	else:
		angle = 180 + rotated_rect[-1]

	rotated_rect_list = list(rotated_rect)
	rotated_rect_list[-1] = angle

	return rotated_rect_list, unchanged_rotated_rect

r_rot_rect, r_unchanged_rotated_rect = get_line_specification(right_line_contours)
#d_rot_rect, d_unchanged_rotated_rect = get_line_specification(dashed_line_contours)


#print('r_unchanged %s' %(r_unchanged_rotated_rect,))
"""
print'\nright line box: %s' %(r_rot_rect,)
print'\ndashed line box: %s'%(d_rot_rect,)

print '\nright line angle: %s'%(r_rot_rect[-1])
print '\ndashed line angle: %s'%(d_rot_rect[-1])

print'\nright line center: %s' %(r_rot_rect[0],)
print'\ndashed line center: %s' %(d_rot_rect[0],)
"""
#------------------------------------------------------

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

#"""
#x_intersect = x_intersection(r_rot_rect[0], d_rot_rect[0], r_rot_rect[-1], d_rot_rect[-1] )

print('executionTime: %s' %((time.time() - startTime)))
#print 'x_intersect: %s' %x_intersect


#----------Visualizering-------------------------------

def draw_rot_rect(image, contours, color):
	box = cv2.boxPoints(tuple(contours))
	box = np.int0(box)
	#print box
	cv2.drawContours(image, [box], -1, color, 2)


set_point = 319

draw_rot_rect(roi_img, r_unchanged_rotated_rect, (0,0,255))
#draw_rot_rect(roi_img, r_rot_rect, (0,255,255))
#draw_rot_rect(roi_img, d_unchanged_rotated_rect, (0, 255, 255))
#cv2.circle(roi_img,(x_intersect, 195), 3,(0,255,0))
cv2.line(roi_img,(set_point, 200), (set_point, 229),(255,255,255), 1)

#cv2.line(roi_img,(320, 229), (x_intersect,10),(0, 255, 0), 1)


cv2.imshow('image', roi_img)
cv2.waitKey(0)

"""

def costum_HScan_reversed(ROI, offset): 
	'''
	Scans a binary ROI vertically and returns the coordinations of wihte pixels
	Input: numpy.ndarray
	Output: a list of white pixels
	'''
	#print 'image shape: %s' %(ROI.shape,)
	ctr = 0
	frame_white_pixels = []
	white_pixels = []
	first_white_pixel_x = - offset
	# find derivative of entire ROI
	frame_derivative = np.diff(ROI, axis = 0)
	nRows = ROI.shape[0] -1 # in order to start from bottom.. 
	for r in xrange(nRows)
			
			start_pixel = first_white_pixel_x + offset   #negative offset
			column = frame_derivative[start_pixel:,i] # needs optimiziation..
			reversed_column = column[::-1]
			reverse_ind = np.nonzero(reversed_column)
			ind_col_derivative = np.subtract((np.repeat(len(column)-1, len(reverse_ind))),reverse_ind)
			#print 'ind_col_derivative: %s'%ind_col_derivative
			if (len(ind_col_derivative[0])!=0):
				for p in xrange(len(ind_col_derivative[0])): #len(ind_row_derivative[0]  # two first lines
					white_pixels.append((i, ind_col_derivative[0][p]+start_pixel))
			else:
				ctr+=1
				continue		
			#print 'whitepixels: %s'%white_pixels
			first_white_pixel_y = white_pixels[-1][1]
			frame_white_pixels.append(white_pixels)
			white_pixels = []
		
	return frame_white_pixels

"""