import cv2
import socket
import io
import picamera
import struct
import time
import serial
import numpy as np
'''
right line follower platform

'''

def crop_bin_image(src_img):
	"""
	image pre-processing
	"""
	roi_img = src_img[ 400 : 450, src_img.shape[1]//2: src_img.shape[1] ]  	
	gray_img = cv2.cvtColor( roi_img, cv2.COLOR_BGR2GRAY )
	blured_img = cv2.GaussianBlur(gray_img,(9, 9),0)
	(thresh, processed_img) = cv2.threshold(blured_img, 200, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
	return processed_img
def costum_HScan(regionOfInterest, x_offset): 
	'''
	Scans the regionOfInterest[Y, X] and returns the coordinations of wihte pixels (x, y) and the length of 'em
	Input: numpy.ndarray, x_offset determines the start point in x axies
	Output: a list of white pixels
	'''
	frame_white_pixels = []
	white_pixels = []
	first_white_pixel_x = - x_offset
	frame_derivative = np.diff(regionOfInterest)
	nRows = regionOfInterest.shape[0] -1 # in order to start from bottom.. 
	for i in xrange(nRows):
		row = nRows-i
		start_pixel = first_white_pixel_x + x_offset
		# find the position of the edges
		ind_row_derivative = np.nonzero(frame_derivative[row, start_pixel:]) # returns a tuple of x coordinates
		length_ind = len(ind_row_derivative[0])
		if(length_ind!=0):
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
	checks the first two found points + returns cropped frame pixels to actual frame + offset
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
	angle = 90 + rotated_rect[-1]
	return rotated_rect, angle


s = serial.Serial('/dev/ttyAMA0', 115200) 
print('Serial OK!')

try:

	with picamera.PiCamera() as camera:
		camera.resolution = (640, 480) 
		camera.sensor_mode = 7
		camera.shutter_speed= 10000
		time.sleep(2)
		print('Camera ON!')
		stream = io.BytesIO()
		for foo in camera.capture_continuous(stream, 'jpeg', True):
			start_time=time.time()
			
			imgBgr =  cv2.imdecode(np.fromstring(stream.getvalue(), dtype=np.uint8), 1)
			print 'image taken'
			processed_image = crop_bin_image(imgBgr)
			right_line_contour_candidates = costum_HScan(processed_image, -3) #(x,y)
			right_line  = filter_get_actual_position(right_line_contour_candidates, (0, 0)) #processed_image.shape[1]//2
			# nd.array to 1d.array
			right_line_contours = np.vstack(right_line).squeeze()
			r_rot_rect, Angle = get_line_specification(right_line_contours)
			pos = r_rot_rect[0][0]
			print('\nAngle: %s'%Angle)
			print('\nActual X: %s'%pos)
			s.write('%d\n'%(int(pos)))#(msg)
			print('\nElapsed Time: \n%s\n' %(time.time()-start_time))
			stream.seek(0)
except:
	KeyboardInterrupt




