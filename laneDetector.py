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
bottom_right_part = processed_img[processed_img.shape[0]//2 : processed_img.shape[0], processed_img.shape[1]//2 : processed_img.shape[1]]
bottom_left_part = processed_img[processed_img.shape[0]//2 : processed_img.shape[0], 0 : processed_img.shape[1]//2 -1]
top_right_part = processed_img[0 : processed_img.shape[0]//2-1, processed_img.shape[1]//2 : processed_img.shape[1]]
top_left_part = processed_img[0 : processed_img.shape[0]//2-1, 0 : processed_img.shape[1]//2 -1]

print('a row of a binarized frame: %s'% bottom_right_part[0])
# Find the righ line candidate

def HScan(frame): # , first_white_pixel_x , offset):
	'''
	Scans a row of a binary image and returns the coordinations of wihte pixels
	Input: a binary list 
	Output: a list of white pixels
			nonZeroCoordinates: column number of transition from black to white and vice versa, i.e. edges!
			binarizedRow: almost tha same as row but begining and end of the white pixels
			are turned to 1
	'''
	row_derivative = np.diff(frame[0])
	print row_derivative
	ind_row_derivative = np.nonzero(row_derivative)
	
	return ind_row_derivative












d = HScan(bottom_right_part)
print d[0]
print('executionTime: %s' %(time.time() - startTime))
cv2.imshow('image', top_right_part)
cv2.waitKey(0)