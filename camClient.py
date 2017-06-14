#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket
import time
import io
import struct
from PIL import Image, ImageTk
import Tkinter as tk
'''
camClient receives images from camera server
'''

picSize = (640,480)
root = tk.Tk()
root.geometry('%dx%d+%d+%d' %(640,480,100,100))


tkpi = ImageTk.PhotoImage(Image.new('RGB', picSize))

label_image = tk.Label(root, image=tkpi)
label_image.pack()
root.mainloop()

client_socket = socket.socket()
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


# connect to the server
client_socket.connect(('192.168.75.13', 7798))
data_file = client_socket.makefile()
frame_stream = io.BytesIO()


while True:

	start_time = time.time()
	frame_len = struct.unpack('<L', data_file.read(struct.calcsize('<L')))[0]
	
	if not frame_len:
		print'No Image'

	frame_stream.seek(0)
	frame_stream.write(data_file.read(frame_len))
	frame_stream.seek(0)
	img = Image.open(frame_stream)
	
	
	img.load()
	img.verify()

	img_tk = ImageTk.PhotoImage(image=img)
	label_image.img_tk = img_tk
	label_image.configure(image=img_tk)
	
	
