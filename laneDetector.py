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
	roi_img = src_img[ 240 : 450, 0 : src_img.shape[1] ]  	#	needs to be adjusted! (Y, X)
	gray_img = cv2.cvtColor( roi_img, cv2.COLOR_BGR2GRAY )
	blured_img = cv2.GaussianBlur(gray_img,(9, 9),0)			# may get excluded!
	#edges_img = cv2.Canny(blured_img, 30, 160)
	(thresh, binarized_img) = cv2.threshold(blured_img, 200, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
	processed_img = binarized_img
	return roi_img, processed_img

startTime = time.time()
roi_img, processed_image = get_image()
#print'Processed Image Shape: %s'%(processed_image.shape,)

# devide the frame into 4 separate sub-frame 	#(260, 640)
#top_right_part = processed_image[0 : processed_image.shape[0]//2-1, processed_image.shape[1]//2 : processed_image.shape[1]]
#top_left_part = processed_image[0 : processed_image.shape[0]//2-1, 0 : processed_image.shape[1]//2 -1]
bottom_left_part =  processed_image[0 : processed_image.shape[0] , 0 : processed_image.shape[1]//2 -1] #(Y, X)
bottom_right_part = processed_image[0 : processed_image.shape[0] , processed_image.shape[1]//2: processed_image.shape[1]]

def costum_HScan(ROI, offset): # , first_white_pixel_x , offset):
	'''
	Scans a binary frame horizontally and returns the coordinations of wihte pixels
	Input: numpy.ndarray
	Output: a list of white pixels
	'''
	white_pixel_found = False
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
			white_pixel_found = True
			for p in xrange(len(ind_row_derivative[0])): 
				white_pixels.append([ind_row_derivative[0][p] + start_pixel, row]) #(x,y)	
		else: 
			print('No White Pixels..')
			break
		first_white_pixel_x= white_pixels[0][0]
		frame_white_pixels.append(white_pixels)
		white_pixels = []
		
	return frame_white_pixels, white_pixel_found #(x,y)


# first scan
right_line_contour_candidates, right_line_found  = costum_HScan(bottom_right_part, -3) #(x,y)
first_dashed_line_contour_candidates, first_broken_line_found = costum_HScan(bottom_left_part, -3) #(x,y)
print('length of first broken scan:%s'%len(first_dashed_line_contour_candidates))
# In case no broken line is found, do the next scans until that's found
Y_offset = 10
Y_old = processed_image.shape[0]
# Find the first broken line
while (len(first_dashed_line_contour_candidates)==0):
	Y_new =  Y_old - Y_offset
	roi_1 = processed_image[0: Y_new, 0 : processed_image.shape[1]//2 -1 ]

	first_dashed_line_contour_candidates, first_broken_line_found = costum_HScan(roi_1, -3)
	if first_broken_line_found:
		break
	Y_old = Y_new
print 'first_broken_line_found:%s'%first_broken_line_found
print '\nfirst_dashed_line_contour_candidates: %s'%first_dashed_line_contour_candidates

# Now find the second broken line
second_dashed_line_contour_candidates = []
broken_line_offset = 10
if first_broken_line_found:
	Y_old_2 = first_dashed_line_contour_candidates[-1][-1][1]
	while (len(second_dashed_line_contour_candidates)==0):
		Y_new_2 =  Y_old_2 - Y_offset
		roi_2 = processed_image[0: Y_new_2, 0 : processed_image.shape[1]//2 -1 ]
		second_dashed_line_contour_candidates, second_broken_line_found = costum_HScan(roi_2, -3) #(x,y)
		if second_broken_line_found:
			break
		Y_old_2 = Y_new_2
print 'second_broken_line_found:%s'%second_broken_line_found
print '\nsecond_dashed_line_contour_candidates: %s'%second_dashed_line_contour_candidates
			
dashed_line_contour_candidates = first_dashed_line_contour_candidates + second_dashed_line_contour_candidates
#print 'dashed_line: %s'%dashed_line_contour_candidates

for row in second_dashed_line_contour_candidates:
	for point in row:
		cv2.circle(roi_img, tuple(point), 3,(0,255,0))

for row in first_dashed_line_contour_candidates:
	for point in row:
		cv2.circle(roi_img, tuple(point), 7,(0,0, 150))






















def filter_get_actual_position(contour_candidates, offset):
	'''
	returns cropped frame pixels to actual frame 
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

right_line  = filter_get_actual_position(right_line_contour_candidates, (processed_image.shape[1]//2, 0))
dashed_line = filter_get_actual_position(dashed_line_contour_candidates, (0, 0))

# nd.array to 1d.array
right_line_contours = np.vstack(right_line).squeeze()
dashed_line_contours = np.vstack(dashed_line).squeeze()


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
d_rot_rect, d_unchanged_rotated_rect = get_line_specification(dashed_line_contours)

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

#print'right line angle: %s'%r_rot_rect[-1]
#print'dashed line angle: %s'%d_rot_rect[-1]
x_intersect = x_intersection(r_rot_rect[0], d_rot_rect[0], r_rot_rect[-1], d_rot_rect[-1] )
"""
# check if x_intersects falls in the range
if (x_intersect > processed_image.shape[1]):
	x_intersect = processed_image.shape[1] - (x_intersect%processed_image.shape[1])
"""
print('executionTime: %s' %((time.time() - startTime)))
print 'x_intersect: %s' %x_intersect



#----------Visualizering-------------------------------

def draw_rot_rect(image, contours, color):
	box = cv2.boxPoints(tuple(contours))
	box = np.int0(box)
	#print box
	cv2.drawContours(image, [box], -1, color, 2)


set_point = processed_image.shape[1]//2-1

# in red : unchanged
draw_rot_rect(roi_img, r_unchanged_rotated_rect, (0, 0, 255))
draw_rot_rect(roi_img, d_unchanged_rotated_rect, (0, 0, 255))

# in green 
draw_rot_rect(roi_img, r_rot_rect, (0, 155, 0))
draw_rot_rect(roi_img, d_rot_rect, (0, 155, 0))

cv2.circle(roi_img,(x_intersect, 100), 3,(0,255,0))
cv2.line(roi_img,(set_point, 200), (set_point, 229),(255,255,255), 1)

#cv2.line(roi_img,(320, 229), (x_intersect,10),(0, 255, 0), 1)


cv2.imshow('image', roi_img)
cv2.waitKey(0)

"""
"""