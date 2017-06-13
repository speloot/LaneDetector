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
	image_path = '/home/siaesm/Pictures/img_02/img003.jpg'
	src_img = cv2.imread(image_path)
	roi_img = src_img[ 220 : 480, 0 : src_img.shape[1] ]  	#	needs to be adjusted!
	gray_img = cv2.cvtColor( roi_img, cv2.COLOR_BGR2GRAY )
	blured_img = cv2.GaussianBlur(gray_img,(5,5),0)			# may get excluded!
	#edges_img = cv2.Canny(blured_img, 30, 160)
	(thresh, binarized_img) = cv2.threshold(blured_img, 200, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
	processed_img = binarized_img
	return processed_img

startTime=time.time()
processed_img = get_image()

# devide the frame into 4 separate sub-frame 	#(260, 640)
top_right_part = processed_img[0 : processed_img.shape[0]//2-1, processed_img.shape[1]//2 : processed_img.shape[1]]
top_left_part = processed_img[0 : processed_img.shape[0]//2-1, 0 : processed_img.shape[1]//2 -1]
bottom_left_part = processed_img[processed_img.shape[0]//2 : processed_img.shape[0], 0 : processed_img.shape[1]//2 -1]
bottom_right_part = processed_img[processed_img.shape[0]//2 : processed_img.shape[0], processed_img.shape[1]//2 : processed_img.shape[1]]

def efficient_VScan(frame, offset): 
	'''
	Scans a binary frame vertically and returns the coordinations of wihte pixels
	Input: numpy.ndarray
	Output: a list of white pixels
	'''
	#print 'image shape: %s' %(frame.shape,)
	ctr = 0
	frame_white_pixels = []
	white_pixels = []
	first_white_pixel_y = - offset
	# find derivative of entire frame
	frame_derivative = np.diff(frame, axis = 0)
	nCols = frame_derivative.shape[1]-1

	for i in xrange(nCols):
		if ctr<=2:
			start_pixel = first_white_pixel_y + offset  #negative offset
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
		else:
			break
	return frame_white_pixels

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

# in order to extract features of rectangles like rotation , there might be no need to re-form the image as whole!?

right_line_contour_candidates   = costum_HScan(bottom_right_part, -3)
dashed_line_contour_candidates	= costum_HScan(bottom_left_part, -3)

def get_first_line(contour_candidates, offset):
	first_line = []
	for lines in contour_candidates:
		p = np.add(lines, offset)
		first_line.append(p)
	return first_line

right_line  = get_first_line(right_line_contour_candidates, (319, 129))
dashed_line = get_first_line(dashed_line_contour_candidates, (0,129))

right_line_contours = np.vstack(right_line).squeeze()
dashed_line_contours = np.vstack(dashed_line).squeeze()
# rect = ((center_x,center_y),(width,height),angle)
r_rot_rect = cv2.minAreaRect(right_line_contours)
d_rot_rect = cv2.minAreaRect(dashed_line_contours)

print('executionTime: %s' %((time.time() - startTime)))

print'\nright line box: %s' %(r_rot_rect,)
print'\ndashed line box: %s'%(d_rot_rect,)

print '\nright line angle: %s'%(r_rot_rect[-1])
print '\ndashed line angle: %s'%(d_rot_rect[-1])

print'\nright line center: %s' %(r_rot_rect[0],)
print'\ndashed line center: %s' %(d_rot_rect[0],)

#------------------------------------------------------
"""
def x_intersection(p1, a, p2, b):
	'''
	 Returns the x of lines intersection
	 input: two points + two angle
	 output: x_coordinate : X = ( (y_2 - b * x_2) - (y_1 - a* x_1) ) // (a - b)
	'''
	# convert all coordinates floating point values to int ???         needs to be checked!!!
	p1 = np.int0(p1)
	p2 = np.int0(p2)
	gradient_a = math.tan(-a)
	print 'grad_a: %s'%gradient_a
	gradient_b = math.tan(180 + b)
	print 'grad_b: %s'%gradient_b


	intersect = ((p2[1]-gradient_b*p2[0]) - (p1[1]-gradient_a*p1[0]))//(a-b)
	#intersect -= p2[0]
	return np.int(intersect)


x_intersect = x_intersection(r_rot_rect[0], r_rot_rect[-1], d_rot_rect[0], d_rot_rect[-1] )

print('executionTime: %s' %((time.time() - startTime)))
print 'x_intersect: %s' %x_intersect
"""


#----------Visualizering-------------------------------

def draw_rot_rect(image, contours):
	box = cv2.boxPoints(contours)
	box = np.int0(box)
	cv2.drawContours(image, [box], -1,(0,0,255),2)

roi_img = cv2.cvtColor( processed_img, cv2.COLOR_GRAY2BGR)
draw_rot_rect(roi_img, r_rot_rect)
draw_rot_rect(roi_img, d_rot_rect)

#cv2.circle(roi_img,(x_intersect, 10), 3,(0,255,0))

"""
for l in right_line:
	for p in l:
		cv2.circle(roi_img,tuple(p), 2,(0,255,0))
for l in dashed_line:
	for p in l:
		cv2.circle(roi_img,tuple(p), 2,(0,255,0))
"""		

cv2.imshow('image', roi_img)
cv2.waitKey(0)

"""
#-----------Regression-------------------------------
def line_fit(x_candidates, y_candidates):
	
	(gradient, y_intercept) = np.polyfit(x_candidates, y_candidates, 1)
	return gradient, y_intercept

right_line = line_fit(x_right_line, y_right_line)
dashed_line = line_fit(x_dashed_line, y_dashed_line)

def x_intersection(line_1, line_2):
	'''
	 Returns the x of lines intersection
	 input: gradient and y-intercept of two lines (np.ndarray)
	 output: x_coordinate in   
	'''
	return (line_2[1]-line_1[1])//(line_1[0]-line_2[0])



#----------classify lines------------------------------
if ( (r_line[0]<0) & (d_line[0]>0) ):
	print ok
	x_vanishing_point = x_intersection(r_line, d_line)

	print x_vanishing_point


"""
"""
for rows in right_line_contour_candidate:
	for points in rows:
		p = np.add(points,(319, 129))
		cv2.circle(roi_img, tuple(p), 2, (0,0,255))

for rows in dashed_line_contour_candidate:
	for points in rows:
		p = np.add(points,(0, 129))
		cv2.circle(roi_img, tuple(p),2,(0,255,0))

for rows in left_line_contour_candidate:
	for points in rows:
		cv2.circle(roi_img, points,2,(255,0,0))



roi_img = cv2.cvtColor( processed_img, cv2.COLOR_GRAY2BGR)
cv2.circle(roi_img, (x_right_line, y_right_line), 2, (0,0,255))

"""

