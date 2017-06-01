#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

from __future__ import division
import cv2
import serial
import socket
#import picamera
#import picamera.array
import io
import pickle
import math
import numpy as np
import time
import struct
import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt

def processImage(image, nRow):
	'''
    Binarizes a row of the image
    Arguments: an image in form of an array
    '''
	roi = image[ nRow : nRow+1, 0 : image.shape[1] ] 
	gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
	#blured = cv2.GaussianBlur(gray, (15, 15), 0)
	(thresh, bw) = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
	processedRow = bw
	return processedRow
def HScan(row):
	'''
	Scans a row of a binary image and returns the coordinations of wihte pixels
	Input: a binary list 
	Output: a list of white pixels
			nonZeroCoordinates: column number of transition from black to white and vice versa, i.e. edges!
			binarizedRow: almost tha same as row but begining and end of the white pixels
			are turned to 1
	'''
	#print row
	nCol = row.shape[1]
	nonZeroCoordinates = []
	# Scan a row of a binary image 
	for j in range(nCol-1):
		# Check where transition from 0 to 1 or vice versa occurs!
		val = int(row[0][j+1]) - int(row[0][j])
		if (val > 0):
			nonZeroCoordinates.append((j))
		elif (val < 0):
			nonZeroCoordinates.append((j))

	return nonZeroCoordinates
def isInSameCluster(currentPoint, nextPoint):

	margin = 2
	rangeResult = False
	rightOffset = currentPoint + margin
	leftOffset = currentPoint - margin
	if ((nextPoint <= rightOffset) & (nextPoint >= leftOffset)):
		rangeResult = True

	return rangeResult
def VScan(H_Input):
	"""
		Clustering (Vertical scan) of found horizontal white pixels
		input: list of found white pixels
		output : list of clustered white pixels
	"""

	clusters = []

	for HscanLine in H_Input:
		for point in HscanLine:
			assigned = False
			for cluster in clusters:
				if (isInSameCluster(point[0],cluster[-1][0])):
					cluster.append(point)
					assigned = True
			if not assigned:
				clusters.append([point])
	return clusters
def getLocalCoordinates(pointLists):

    '''
    Transforms points to local coordinate system.
    This assumes camera is mounted at 25 degrees to the vertical, but angle can
    be modified by cam_mount_angle.
    Input: normalized(row: the row number, column: whitePixelCoordinates)
    Output: a list of tuples: points: coordinates of white pixels in cm from camera origin

    '''
    camAngle = 70.0 #78 # 74.6 	# in degrees
    pi = 3.14159265
    h = 18 				# cm

    cam_mount_angle = camAngle * pi/180
    cam_x_fov = 62.2*pi/180
    cam_y_fov = 48.8*pi/180
    xPositions = []
    yPositions = []
    localPoints = []
    localPoint = []
    for pointList in pointLists:
    	for p in pointList:
	        phi_x = ((p[0]/640)-0.5)*cam_x_fov
	        phi_y = -((p[1]/480)-0.5)*cam_y_fov
	        theta_y = cam_mount_angle + phi_y
	        theta_x = phi_x
	        y = math.tan(theta_y) * h
	        r = math.sqrt(y**2+h**2)
	        x = r * math.tan(theta_x)
	    	localPoint.append((x,y))
	localPoints.append(localPoint)

    return localPoints


imagePath = '/home/siaesm/Pictures/img_02/img031.jpg'
imgBgr = cv2.imread(imagePath)
#cv2.imshow('image', imgBgr)
#cv2.waitKey(0)
startTime=time.time()
	
				
nScanLines = 300	#number of scan lines
stepSize = 1	 					#distance between scan lines!?
beginingRow = imgBgr.shape[0] - 1  	# start from the second row!?



H_White_Pixels_Lists = []
for i in range(0,nScanLines):
		nRow = beginingRow - i * stepSize
		# binarize a row of an image
		processedRow = processImage(imgBgr, nRow)
		# extract white pixels
		whitePixelsCoordinates = HScan(processedRow)
		newList = zip(whitePixelsCoordinates, ([nRow]*len(whitePixelsCoordinates)))
		H_White_Pixels_Lists.append(newList)
		#print('\nHScan resualt: \n%s\n' %H_White_Pixels_Lists)
		# represent the location of white pixels in vehicle coordinate system
		#mappedPoints = getLocalCoordinates(nRow, whitePixelsCoordinates)
		# whitePixelsCoordinates need to be checked if they actually are marking lines(or their mapped values)
		#markingPoint = getMarkingPoints(mappedPoints)



VH = VScan(H_White_Pixels_Lists)
localCoordinate_whitePixels = getLocalCoordinates(VH)

#print('\nVHScan resualt: \n%s\n' %VH)
#print('\nLocal Coords: \n%s\n' %localCoordinate_whitePixels)




plt.subplot(121)
for cluster in localCoordinate_whitePixels:
	for point in cluster:
		plt.scatter(point[0], point[1], s=5, facecolor='0.1', lw = 0)

plt.show(block=False)
print('\nelapsed Time: \n%s\n' %(time.time()-startTime))

for cluster in VH:
	for point in cluster:
		cv2.circle(imgBgr, point, 2, (0, 0, 200))

cv2.imshow('image', imgBgr)
cv2.waitKey(0)

		

