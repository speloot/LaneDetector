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
	image_path = '/home/siaesm/Pictures/img_02/img029.jpg'
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


# first scan
right_line_contour_candidates, right_line_found, length_right_line  = costum_HScan(bottom_right_part, -3) #(x,y)
first_broken_line_contour_candidates, first_broken_line_found, length_first_broken_line = costum_HScan(bottom_left_part, -3) #(x,y)

print('length of first broken:%s'%length_first_broken_line)
# In case no broken line is found, do the next scans until that's found

# if the first broken is found, search the second
Y_offset = 5
X_offset = 100

Y_old = processed_image.shape[0]
X_old = processed_image.shape[1]
length_second_broken_line = 0
Y_new = Y_old


while ((length_first_broken_line==0)):
	Y_new =  Y_old - Y_offset
	roi_1 = processed_image[0: Y_new, 0 : processed_image.shape[1]//2 -1 ]

	first_broken_line_contour_candidates, first_broken_line_found, length_first_broken_line = costum_HScan(roi_1, -3)
	if first_broken_line_found:
		print 'first_broken_line_found:%s'%first_broken_line_found
		break
	Y_old = Y_new
	if (Y_new <= 0):
		print('EOF!')
		break
	

if first_broken_line_found:
	# Now find the second broken line
	Y_last = first_broken_line_contour_candidates[-1][-1][1]
	X_last = first_broken_line_contour_candidates[-1][-1][0] 
	while (length_second_broken_line==0):
		Y_new =  Y_last - Y_offset
		X_new = X_last - X_offset
		roi_2 = processed_image[0: Y_new, X_new: processed_image.shape[1]//2 -1 ]
		second_broken_line_contour_candidates, second_broken_line_found, length_second_broken_line = costum_HScan(roi_2, -3) #(x,y)
		if second_broken_line_found:
			break
		Y_last = Y_new

else:
	Y_last = Y_old
	X_last = X_old//4-1
	while (length_second_broken_line==0):
		Y_new =  Y_last - Y_offset
		X_new = X_last - X_offset
		roi_2 = processed_image[0: Y_new, X_new: processed_image.shape[1]//2 -1 ]
		second_broken_line_contour_candidates, second_broken_line_found, length_second_broken_line = costum_HScan(roi_2, -3) #(x,y)
		if second_broken_line_found:
			print('second_broken_line_found: %s'%second_broken_line_found)
			break
		Y_last = Y_new
		if(Y_new <= 0):
			print('EOF!')
		break


#print '\nfirst_broken_line_contour_candidates: %s'%first_broken_line_contour_candidates
#print '\nsecond_broken_line_contour_candidates: %s'%second_broken_line_contour_candidates



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
first_broken_line = filter_get_actual_position(first_broken_line_contour_candidates, (0, 0), right_line=False)
second_broken_line = filter_get_actual_position(second_broken_line_contour_candidates, (first_broken_line_contour_candidates[-1][-1][0] - X_offset, 0), right_line=False)

broken_line = first_broken_line + second_broken_line

# nd.array to 1d.array
right_line_contours = np.vstack(right_line).squeeze()
broken_line_contours = np.vstack(broken_line).squeeze()

print '\nb_line_contours_first: %s'%broken_line_contours[0][1] #164
print '\nb_line_contours_last: %s'%broken_line_contours[-1][1] #68

right_line_cut = []
for r in right_line_contours:
	if ( (r[1]>=broken_line_contours[-1][1]) & (r[1]<broken_line_contours[0][1])):
		right_line_cut.append(r)
print'\nright_line_cut: %s'%right_line_cut

right_line_contours = np.vstack(right_line_cut).squeeze()

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
d_rot_rect, d_unchanged_rotated_rect = get_line_specification(broken_line_contours)

#print'\nright_unchanged_rect%s'%(r_unchanged_rotated_rect,)
#print'\nbroken_unchanged_rect%s'%(d_unchanged_rotated_rect,)

#print'\nright_rotated_rect: %s'%(r_rot_rect,)
#print'\nbroken_rotated_rect: %s'%(d_rot_rect,)


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

#print'\nright line angle: %s'%r_rot_rect[-1]
#print'broken line angle: %s'%d_rot_rect[-1]


x_intersect = x_intersection(r_rot_rect[0], d_rot_rect[0], r_rot_rect[-1], d_rot_rect[-1] )


print 'x_intersect: %s' %x_intersect

#"""
print('executionTime: %s' %((time.time() - startTime)))
#----------Visualizering-------------------------------
for row in first_broken_line:
	for point in row:
		cv2.circle(roi_img, tuple(point), 3,(0, 0, 0))

for row in second_broken_line:
	for point in row:
		cv2.circle(roi_img, tuple(point), 3,(5, 5, 195))
#"""

def draw_rot_rect(image, contours, color):
	box = cv2.boxPoints(tuple(contours))
	box = np.int0(box)
	cv2.drawContours(image, [box], -1, color, 2)


set_point = processed_image.shape[1]//2-1

# in violet : unchanged
draw_rot_rect(roi_img, r_unchanged_rotated_rect, (105, 0, 255))
draw_rot_rect(roi_img, d_unchanged_rotated_rect, (105, 0, 255))

# in green 
#draw_rot_rect(roi_img, r_rot_rect, (0, 155, 0))
#draw_rot_rect(roi_img, d_rot_rect, (0, 155, 0))

cv2.circle(roi_img,(x_intersect, 100), 3,(0,255,0))
cv2.line(roi_img,(set_point, 190), (set_point, 229),(150, 150, 150), 3)

#cv2.line(roi_img,(320, 229), (x_intersect,10),(0, 255, 0), 1)


cv2.putText(roi_img,'Contours',(300,170), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.7,((105, 0, 255)),1)
cv2.putText(roi_img,'1st Broken-line',(280,150), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.7,(0, 0, 0),1)
cv2.putText(roi_img,'2nd Broken-line',(280, 125), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.7,(5, 5, 195),1)
cv2.imshow('image', roi_img)
cv2.waitKey(0)

"""
"""