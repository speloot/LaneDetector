#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket
import time
import io
import struct
import cStringIO
import Tkinter as tk
from PIL import Image, ImageTk
'''
camClient receives images from camera server
'''
def button_click_exit_mainloop (event):
    event.widget.quit() # this will cause mainloop to unblock.

root = tk.Tk()
root.geometry("640x480")
root.wm_title("pi camera")
root.bind("<Button>", button_click_exit_mainloop)
root.mainloop()

tk_img = ImageTk.PhotoImage(Image.new('RGB', (640, 480)))
panel = tk.Label(root, image=tk_img)
panel.place(x=0,y=0,width=640,height=480)

# connect to the server
client_socket = socket.socket()
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
	print 'Image is received!'
	img = Image.open(frame_stream)
	img.load()
	img.verify()
	tk_img = ImageTk.PhotoImage(img.resize((640, 480),Image.ANTIALIAS))
	panel.configure(image=tk_img)
	root.update()
	print('\nElapsed Time: \n%s\n' %(time.time()-start_time))
