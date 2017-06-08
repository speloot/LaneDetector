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

#print('a row of a binarized frame: %s'% bottom_right_part[0])
# Find the righ line candidate


def efficient_HScan(frame, offset): # , first_white_pixel_x , offset):
	'''
	Scans a binary frame horizontally and returns the coordinations of wihte pixels
	Input: numpy.ndarray
	Output: a list of white pixels

	'''
	print 'image shape: %s' %(frame.shape,)
	frame_white_pixels = []
	white_pixels = []
	assigned_FWP = False
	frame_derivative = np.diff(frame)
	nRows = frame_derivative.shape[0]-1 # in order to start from bottom.. remove -1?
	
	for i in xrange(nRows):
		row = nRows-i
		if not assigned_FWP:
			# find the position of the edges
			ind_row_derivative = np.nonzero(frame_derivative[row]) # returns a tuple
			if(len(ind_row_derivative)!=0):
				for p in xrange(len(ind_row_derivative)): #len(ind_row_derivative[0]  # two first lines
					white_pixels.append((ind_row_derivative[0][p], row)) #(x,y)
			else:
				continue
			first_white_pixel_x = white_pixels[0][0]  # neglect the +1 position for now..
			assigned_FWP = True
		else:
			start_pixel = first_white_pixel_x + offset
			ind_row_derivative = np.nonzero(frame_derivative[row][start_pixel:])
			if(len(ind_row_derivative)!=0):
				for p in xrange(len(ind_row_derivative)):
					white_pixels.append((ind_row_derivative[0][p]+start_pixel, row))
			else:
				continue
			first_white_pixel_x = white_pixels[0][0]  # neglrct the +1 position for now..
			assigned_FWP = True
		frame_white_pixels.append(white_pixels)
		white_pixels = []
	return frame_white_pixels

def efficient_VScan(frame, offset): 
	'''
	Scans a binary frame vertically and returns the coordinations of wihte pixels
	Input: numpy.ndarray
	Output: a list of white pixels

	'''
	
	frame_white_pixels = []
	white_pixels = []
	assigned_FWP = False
	# find derivative of entire frame
	frame_derivative = np.diff(frame)

	nCols = frame_derivative.shape[1]
	for i in xrange(0,nCols):
		if not assigned_FWP:
			# find the position of the edges
			column = frame_derivative[:,i]
			reversed_column = column[::-1]
			# the index of white pixel before reversion 
			reverse_ind = np.nonzero(reversed_column)
			ind_col_derivative = np.absolute(reverse_ind - len(column))
			if (len(ind_col_derivative)!=0):
				for p in xrange(len(ind_col_derivative)): #len(ind_row_derivative[0]  # two first lines
					white_pixels.append((i, ind_col_derivative[0][p])) #(x,y)
			else:
				continue		
			first_white_pixel_y = white_pixels[0][1]  
			assigned_FWP = True
		else:
			start_pixel = first_white_pixel_y + offset  #negative offset
			reversed_column = frame_derivative[start_pixel:,i] # needs optimiziation..
			ind_col_derivative = np.nonzero(reversed_column)
			if (len(ind_col_derivative)!=0):
				for p in xrange(len(ind_col_derivative)): #len(ind_row_derivative[0]  # two first lines
					white_pixels.append((i, ind_col_derivative[0][p]+start_pixel))
			else:
				continue		
			first_white_pixel_y = white_pixels[0][1]  # neglrct the +1 position for now..
			assigned_FWP = True
		frame_white_pixels.append(white_pixels)
		white_pixels = []
	return frame_white_pixels

right_line_contour_candidate = efficient_HScan(bottom_right_part, -3)
left_line_contour_candidate = efficient_VScan(top_left_part, -3)

for rows in wpixel:
	for points in rows:
		cv2.circle(bottom_right_part, points,2,(155,155,155))
print('executionTime: %s' %(time.time() - startTime))
cv2.imshow('image',top_left_part)
cv2.waitKey(0)

"""

"""
