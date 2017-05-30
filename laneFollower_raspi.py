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
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def processImage(image, nRow):
	'''
    Binarizes a row of the image
    Arguments: an image in form of arra

    '''

	roi = image[ nRow : nRow+1, 0 : image.shape[1] ] 

	gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
	(thresh, bw) = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
	processedRow = bw
	return processedRow

def getWhitePixelCoordinates(row):
	'''
	Scans a row of a binary image and returns the coordinations of wihte pixels
	Input: a binary list 
	Output: a list of white pixels
			nonZeroCoordinates: column number of transition from black to white and vice versa, i.e. edges!
			binarizedRow: almost tha same as row but begining and end of the white pixels
			are turned to 1
	'''
	
	nCol = row.shape[1]
	nonZeroCoordinates = []
	beginingPixel = []
	endPixel = []
	#binarizedRow = []
	# Scan a row of a binary image 
	for j in range(nCol-1):
		# Check where transition from 0 to 1 or vice versa occurs!
		val = int(row[0][j+1]) - int(row[0][j])
		if (val > 0):
			nonZeroCoordinates.append((j))
			#binarizedRow.append(1)
		elif (val < 0):
			nonZeroCoordinates.append((j))
			#binarizedRow.append(1)
		#else: binarizedRow.append(0)

	return nonZeroCoordinates

def getLocalCoordinates(row, points):

    '''
    Transforms points to local coordinate system.
    This assumes camera is mounted at 25 degrees to the vertical, but angle can
    be modified by cam_mount_angle.
    Input: normalized(row: the row number, column: whitePixelCoordinates)
    Output: a list of tuples: points: coordinates of white pixels in cm from camera origin

    '''
    camAngle = 70.0 #78 # 74.6 	# in degrees
    pi = 3.14159265
    h = 20 				# cm

    cam_mount_angle = camAngle * pi/180
    cam_x_fov = 62.2*pi/180
    cam_y_fov = 48.8*pi/180
    xPositions = []
    yPositions = []
    localPoints = []

    for p in points:
    
        phi_x = ((p/640)-0.5)*cam_x_fov
        phi_y = -((row/480)-0.5)*cam_y_fov
        theta_y = cam_mount_angle + phi_y
        theta_x = phi_x
        y = math.tan(theta_y) * h
        r = math.sqrt(y**2+h**2)
        x = r * math.tan(theta_x)
    	localPoints.append((x,y))

    return localPoints

def getMarkingPoints(whitePoints):

	'''
	Measures the gap between detected white pixels in a row of an image, check if they meet the criteria
	Input: a tuple: points: coordinates of white pixels in cm from camera origin
	Output:  a list of possible marking points
	'''
	markings = []
	minLineWidth = 1.5
	maxLineWidth = 3.2
	nWhitePoints = len(whitePoints)

	for m in range(0,nWhitePoints):
		if( m != nWhitePoints-1):
			width = whitePoints[m+1][0] - whitePoints[m][0]
			if ( (width < maxLineWidth) & (width > minLineWidth) ):
				markings.append(whitePoints[m])
				markings.append(whitePoints[m+1])
					
	return markings 

def isInSameCluster(currentPoint, nextPoint):

	margin = 5
	rangeResult = False
	rightOffset = currentPoint + margin
	leftOffset = currentPoint - margin
	if ((nextPoint <= rightOffset) & (nextPoint >= leftOffset)):
		rangeResult = True

	return rangeResult

def isConcatable(currentPoint, nextPoint):
	'''
	checks if the points in a cluster are concatable

	Input: two successive points (x1,y1),(x2, y2) 
	Output: boolean True or False 
	'''
	margin = 0.155
	rangeResult = False
	rightOffset = currentPoint[1] + margin
	leftOffset = currentPoint[1] - margin
	if ((nextPoint[1] <= rightOffset) & (nextPoint[1] >= leftOffset)):
		rangeResult = True

	return rangeResult

def pidController(actualPoint, setPoint, prevError, Kd, Kp,):
	'''
	Calculate System Input using a "PID Controller"

	'''
	# Error between the desired and actual output
	actualError = setPoint - actualPoint

	# Derivation Input
	derivativeState = 1/Kd * (actualError - prevError )

	# Calculate system input
	pidResult = Kp * (actualError + derivativeState)

	
	return pidResult, actualError


s = serial.Serial('/dev/ttyAMA0', 19200) 
dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
dataSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
dataSocket.connect(('192.168.75.96', 7798))

dataFile= dataSocket.makefile('ab')

u0 = 0
e0 = 0																	
pi = 3.14159265



with picamera.PiCamera() as camera:
	camera.resolution = (640, 480) 
	camera.sensor_mode = 7
	camera.shutter_speed= 10000
	time.sleep(2)
	stream = io.BytesIO()
	#with picamera.array.PiRGBArray(camera) as stream:
	

	for foo in camera.capture_continuous(stream, 'jpeg', True):
		startTime=time.time()
		stream.seek(0)
		imgBgr =  cv2.imdecode(np.fromstring(stream.getvalue(), dtype=np.uint8), 1)
		#cv2.imwrite('image.png', imgBgr)
		nScanLines = 20 					#number of scan lines
		stepSize = 	 3					#distance between scan lines!?
		beginingRow = imgBgr.shape[0] - 50  	# start from the second row!?

		markingPoints = []
		clusters = []
		
		for i in range(0,nScanLines):

			nRow = beginingRow - i * stepSize
			# binarize a row of an image
			processedRow = processImage(imgBgr, nRow)
			# extract white pixels
			whitePixelsCoordinates = getWhitePixelCoordinates(processedRow)
			#whitePixels.append(whitePixelsCoordinates)
			# represent the location of white pixels in vehicle coordinate system
			mappedPoints = getLocalCoordinates(nRow, whitePixelsCoordinates)
			# whitePixelsCoordinates need to be checked if they actually are marking lines(or their mapped values)
			markingPoint = getMarkingPoints(mappedPoints)
			markingPoints.append((markingPoint))
			
			# clustering: pick a marking line of current row, compare it to the other elements of previous and next ones
			for point in markingPoint:
				assigned = False
				for cluster in clusters:
					if (isInSameCluster(point[0],cluster[-1][0])):
						cluster.append(point)
						assigned = True
				if not assigned:
					clusters.append([point])
		print('len clusters: %s'%len(clusters))
		
		if (clusters != []):

			sortedClusters = []
			for cluster in clusters:
				if (len(cluster) >= 0.7*nScanLines):
					sortedClusters.append(cluster)
					
			if (len(sortedClusters)!=0):

				lanes = sorted(sortedClusters, key=lambda cluster:cluster ) #cluster[0][0]
				clusters = []
				dataString = pickle.dumps(lanes)

				dataFile.write(struct.pack('<L', len(dataString)))
				dataFile.flush()
				dataFile.write(dataString)
				dataFile.flush()
				
				degree = 1
				coeffs = []
				x, y = [], []
				coefficients = []
				if (lanes):
					for point in lanes[-1]:
						x.append(point[0])
						y.append(point[1])
					coeffs = np.polyfit(y, x, degree)
					x = []
					y = []
					coefficients.append(coeffs.tolist())

				slope1 = coefficients[0][0]
				print('slope: %s'%slope1)

				angle = math.atan(slope1)	# in radians [0, pi]
				print('angle= %d' %(angle*(180/3.1415)))
				( PIDoutput, e0) = pidController(angle, 0.0, e0, Kd = 1, Kp=90) 
				# Set the Speed of Motors
				initialSpeed = 80

				rWheelSpeed =  initialSpeed + int(PIDoutput)		
				lWheelSpeed =  initialSpeed - int(PIDoutput)

				print('right wheel speed: %s'%rWheelSpeed)	
				print('left wheel speed: %s'%lWheelSpeed)
				if(rWheelSpeed<0):
					rWheelSpeed = 0
				elif(lWheelSpeed<0):
					lWheelSpeed = 0

				if(rWheelSpeed>255):
					rWheelSpeed = 255
				elif(lWheelSpeed>255):
					lWheelSpeed = 255

				#lWheelSpeed = 0
				#rWheelSpeed = 0

				s.write(struct.pack('>B',rWheelSpeed))
				s.write(struct.pack('>B',lWheelSpeed))
				s.write('\n')	

			else:
				print("No Marking Point's Found!")
				s.write(struct.pack('>B',0))
				s.write(struct.pack('>B',0))
				s.write('\n')
		else:
			print("No Marking Point's Found!")
			s.write(struct.pack('>B',0))
			s.write(struct.pack('>B',0))
			s.write('\n')	
		


		stream.seek(0)
		stream.truncate()
		
		dt_all = time.time() - startTime
		print('executionTime: %s' %(dt_all))	
		


					





"""

			# classify solid and broken lines
			brokenLinesCluster = []
			solidLinesCluster = []

			brokenClusters = []
			solidClusters = []

			for cluster in sortedClusters:
				for point in range(0, len(cluster)-1):
					if not (isConcatable(cluster[point], cluster[point +1])):
						#print(cluster[point])
						brokenLinesCluster.append(cluster[point])
					else:
						solidLinesCluster.append(cluster[point])
						
				brokenClusters.append(brokenLinesCluster)
				solidClusters.append(solidLinesCluster)
				brokenLinesCluster = []
				solidLinesCluster = []
# Find the fitting line for the "last" broken line and "one last" solid line
			#brokenLine = brokenClusters[-1]
			#solidLine = solidClusters[-2]
			determinantClusters = []
			#determinantClusters.append(brokenClusters[-1])
			determinantClusters.append(solidClusters[0])
			#print(determinantClusters)
"""

