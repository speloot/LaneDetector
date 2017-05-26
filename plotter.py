import socket
import time
import pickle
import io
import struct
#import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation

def animate(frame):
	for eachList in frame:
		for point in eachList:
			#print(point)
			plt.scatter(point[0], point[1], s = 50, marker= '.', color='0.1')  #, animated= 'True'

plotterSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
plotterSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
plotterSock.bind(('', 7798))
plotterSock.listen(1)

(conn, addr) = plotterSock.accept()

dataFile = conn.makefile('ab')



fig = plt.figure()
ax = fig.add_subplot(1,1,1)

xlistofzeros = [0] * 40
ylistofzeros = [0] * 40
#print (len(ylistofzeros))
#ax.plot(range(-20,20,1), ylistofzeros, color='k', lw = 3 )
#ax.plot(xlistofzeros, range(0,40,1), color = 'k', lw = 3 )
#fig.ion()  # set plot to animated
#plt.axis('equal')
# make scatter


prev_frame = []
current_frame = []

while True:		
	t = time.time()	

	numberLength = struct.calcsize('<L')  

	#print('numberLength: %s'% numberLength)

	packedLength = dataFile.read(numberLength)

	#print('packedLength: %s'% packedLength)

	length = struct.unpack('<L', packedLength)[0]  # 400

	#print('length: %s'%length)

	binardata = dataFile.read(length)

	#print('data Length: %s'% dataLength)
	
	data = pickle.loads(binardata)

	#print ('data: %s' %data)

	print('elapsedTime: %s'%(time.time()-t))
	

	if not data:
		print('No data!')
		continue


	current_frame = data
	print(len(current_frame))

	#if (prev_frame!=[]):
	#	animate(prev_frame)

	if (current_frame != []):
		animate(current_frame)
		
	
	
	#prev_frame = current_frame
	#current_frame = []
	#data = []
	print('ok')
	plt.show(block = False)

	
		

	



