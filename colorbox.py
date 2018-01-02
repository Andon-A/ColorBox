#! /usr/bin/python
v = "0.1.1"

print("Andon's ColorBox V%s, Beginning") % v

from blinkt import set_pixel, show, clear
from Adafruit_IO import Client
from colorsys import rgb_to_hsv, hsv_to_rgb
from datetime import datetime
import RPi.GPIO as GPIO
import time
import ConfigParser

#Pull info from config file.
cfg = ConfigParser.ConfigParser()
cfg.read("config.cfg")
ID = cfg.getint("Config", "id")
feed = cfg.get("Config","feed")
brightness = cfg.getfloat("Config", "brightness")


#Set up Adafruit IO
aio = Client(cfg.get("Config","key"))
aio.receive(feed) #This will cause the program to abort if key is bad.

#Set up the buttons
GPIO.setmode(GPIO.BCM)
GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def getPixels(id):
	#Gets pixels this device controls.
	#Device 0 controls pixels 0 and 1, D1 controls 2 and 3, D2 controls 4 and 5, and D3 controls 6 and 7
	#Thus, the pixels are ID * 2, and ID * 2 + 1
	p1 = id * 2 #First pixel
	p2 = p1 + 1 #Second pixel
	return (p1, p2)

def getColors():
	#Pulls color information from the interwebs
	c = aio.receive(feed)
	c = str(c.value)
	c = c.strip("[]")
	c = c.split(", ")
	for i, v in enumerate(c):
		c[i] = float(v)
	return c

def rgb255(r, g, b):
	#Converts float 0-1 RGB values to int 0-255 RGB values
	r = int(r * 255)
	g = int(g * 255)
	b = int(b * 255)
	return (r, g, b)

def rgbFloat(r, g, b):
	r = float(r / 255.0)
	g = float(g / 255.0)
	b = float(b / 255.0)
	return (r, g, b)

def changeColor(c, up=True):
	#Adjusts the color value for this device
	if up:
		c[ID] += 0.05
		if c[ID] > 1.0:
			c[ID] = 0.0
	else:
		c[ID] -= 0.05
		if c[ID] < 0.0:
			c[ID] = 1.0
	c255 = hsv_to_rgb(c[ID], 1, brightness)
	c255 = rgb255(c255[0], c255[1], c255[2])
	px = getPixels(ID)
	set_pixel(px[0], c255[0], c255[1], c255[2])
	set_pixel(px[1], c255[0], c255[1], c255[2])
	show()
	return c

def dispAllColors(c):
	#Displays all colors from all devices
	for i, p in enumerate(c):
		rgb = hsv_to_rgb(p, 1, brightness)
		rgb = rgb255(rgb[0], rgb[1], rgb[2])
		px = getPixels(i)
		set_pixel(px[0], rgb[0], rgb[1], rgb[2])
		set_pixel(px[1], rgb[0], rgb[1], rgb[2])
	show()
	return

def getButtons():
	#Returns button states
	b1 = GPIO.input(9)
	b2 = GPIO.input(11)
	return (b1, b2)

def getOffset():
	#Offset in seconds for sending color updates.
	#Makes sure we don't conflict with other devices.
	ost = ID * 15
	return ost

colors = getColors()
newcol = []
t = datetime.now()
ot = datetime.now()
down = False
up = False

dispAllColors(colors)


def runLoop(hour=0):
	global ot
	global colors
	global newcol
	global t
	global down
	global up
	print ("Andon's ColorBox version %s starting.") % v
	#Runs a loop. When the hour changes to the designated one, the loop terminates.
	while True:
		#Main Loop. Checks buttons, retrieves and sets pixels.
		#Update the time. Put Old Time as the current time, then update current time.
		ot = t
		t = datetime.now()
		disp = False #If we need to display new colors
		#If the second is an interval of 5, update colors.
		if (t.second % 15 == 0) and not down:
			newcol = getColors()
			down = True
			#print(newcol[ID])
			#print(colors[ID])
			if newcol[ID] != colors[ID]:
				#AIO's color is out of date.
				newcol[ID] = colors[ID]
				up = True
			if newcol != colors:
				#One of the other devices has changed.
				print("New Colors Detected")
				disp = True
			colors = newcol
		elif t.second % 15 == 1:
			#Reset download cue.
				down = False
		#Now that we have colors updated - If ours is out of date, send an update.
		#Timed bits. Once a minute, we send an update.
		if up and (t.second == getOffset()):
			#We're in a new second, and the second corresponds to our update offset.
			print("Sending color information")
			aio.send(feed, colors)
			up = False #We've sent it, don't send it again.
		#Now we check if we want to change our own color, via buttons.
		b = getButtons()
		if not b[0] and b[1]:
			#Button 1 is pressed. Button 2 is not.
			print("Changing color up")
			colors = changeColor(colors)
			disp = True
		elif not b[1] and b[0]:
			#Button 2 is pressed, Button 1 is not.
			print("Changing color down")
			colors = changeColor(colors, False)
			disp = True
		#Now display colors if they have changed.
		if disp:
			#print("Updating Color Display")
			dispAllColors(colors)
		#Check to see if we need to kill the loop.
		if t.hour == hour:
			#We have the right hour. We run this multiple times per second, so we check if we're at Minute 0, Second 0.
			if t.minute == 0 and t.second == 0:
			#We are! Kill the loop.
				break
		#There! Now we're done. Take a short break.
		time.sleep(0.1) #This will make it run 10 times per second.