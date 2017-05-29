import socket
import time
import pickle
import io
import struct
#import matplotlib
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

#-------------------SOCKET------------------------------------------
plotterSock = socket.socket() # socket.AF_INET, socket.SOCK_STREAM
plotterSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
plotterSock.bind(('', 7798))
plotterSock.listen(1)
(conn, addr) = plotterSock.accept()
dataFile = conn.makefile('ab')

#---------------------PLOT----------------------------------------------
#fig, ax = plt.subplots()
x_data, y_data = [], []
#plt.grid(True)
fig = plt.figure()
#fig.canvas.mpl_connect('close_event', quit)
ax = fig.add_subplot(111, axisbg='k')
plt.ion()

ax.set_xlim(-50, 50)
ax.set_ylim(20, 70)

prev_frame, current_frame = [], []
terms = True
ax.scatter([],[] )
plt.show()	
while terms:		
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
	if not data:
		print('No data!')
		continue
	
	current_frame = data
	

	for points in current_frame:
		for point in points:
			x_data.append(point[0])
			y_data.append(point[1])
			#print point[0]
	#plt.hold(False)
	ax.scatter(x_data, y_data, color='w')
	ax.set_xlim(-50, 50)
	ax.set_ylim(20, 70)
	
	fig.canvas.draw()
	x_data, y_data = [], []
	#plt.hold(False)
	ax.scatter(x_data, y_data, color='w')
	print('elapsedTime: %s'%(time.time()-t))


