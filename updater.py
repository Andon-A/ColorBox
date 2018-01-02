#!/usr/bin/python
v = "0.1.0"

print ("Andon's Colorbox Updater version %s") % v

import urllib
import urllib2
import ConfigParser
import os
import time

cfg = ConfigParser.ConfigParser()
cfg.read("config.cfg")
remloc = cfg.get("Remote","location")
files = []
reboot = False


def getVersion(filename, local=True):
	#Version numbers are on the second line of the prepared files.
	#They are a variable such as v = "0.1.0"
	#They are all formatted as a string, to work with this function.
	#They will all have three version numbers, in the following order:
	#Major release, Minor Release, Bugfixing release.
	#As with most version numbers, they do not necessarily influence each other.
	#IE, Version 0.1.10 follows version 0.1.9, instead of 0.2.0 following 0.1.9
	#If local is true, we use the local file. Obviously.
	#If local is false, we use the same file located in the remote directory.
	lfile = "local"
	if not local:
		lfile = "remote"
	print("Getting version number of %s file %s") % (lfile, filename)
	ver = 0
	if local:
		f = open(filename, "r")
	else:
		f = urllib2.urlopen(remloc + "/" + filename)
	f.readline() #Read the first line. We don't need it.
	ver = f.readline()
	f.close()
	v1 = ver.find('"')
	v2 = ver[v1+1:].find('"') + v1
	ver = ver[v1+1:v2+1]
	ver = ver.split(".")
	for i, v in enumerate(ver):
		ver[i] = int(v)
	ver.append(local)
	return ver

def downloadFile(filename, overwrite=False, reload = True):
	#Downloads a file. By default, it won't overwrite a file.
	#Returns "True" if a file is downloaded.
	#False if the file exists and overwrite is false.
	#Can be downloaded under a new name.
	#By default, if the file is a python file (*.py) and is loaded, we will reload it.
	print("Attempting download of " + filename)
	if overwrite:
		print("Overwriting is enabled")
	if os.path.isfile(filename) and not overwrite:
		print("File exists. Try again with overwrite enabled.")
		return False
	else:
		urllib.urlretrieve(remloc + "/" + filename, filename)
		print(filename + " downloaded and saved.")
		if filename[-3:] == ".py":
			#We have a python file. Check if we have it loaded.
			if filename[:-3] in dir():
				reload(filename[:-3])
				print(filename + " reloaded.")
		return True

def getFileList():
	#The file list doesn't have a version number. It's just a list of files that should be checked.
	#And, more importantly, it sets the order to check them in.
	downloadFile("filelist.txt", True)
	f = open("filelist.txt", "r")
	for line in f:
		files.append(line.strip("\r\n"))
	print("File list populated.")
	return True

def checkAllFiles(update=True):
	#Checks all files in the file list.
	#If the file doesn't exist locally, download it.
	#If it does exist, make sure it's the latest version.
	print("Checking files for update")
	ufiles = []
	for file in files:
		vL = False
		if os.path.isfile(file):
			vL = getVersion(file)
			vR = getVersion(file, False)
		if not vL: 
			ufiles.append(file)
		else:
			#If major number is lower than remote, update.
			#If major number is the same but minor is lower, update.
			#If minor number is the same but bugfix is lower, update.
			#Otherwise, don't worry.
			if vL[0] < vR[0]:
				ufiles.append(file)
			elif vL[1] < vR[1]:
				ufiles.append(file)
			elif vL[2] < vR[2]:
				ufiles.append(file)
	for file in ufiles:
		print(file + " is outdated and needs updating")
		if update:
			downloadFile(file, True)
			print(file + " has been updated.")
			if file == "updater.py":
				print("Main file updated. System will reboot.")
				reboot = True
	if update:
		print ("All files are now up to date")
		return True
	else:
		return ufiles

def restartPi():
	#Restarts the entire Pi.
	print("SYSTEM IS REBOOTING IN 10 SECONDS")
	for i in range(10):
		time.sleep(1)
		i2 = 9 - i
		if i2 > 0:
			print("SYSTEM IS REBOOTING IN %i SECONDS") % i2
	print("SYSTEM IS REBOOTING.")
	os.system("sudo reboot")

#Now the meat of the program.
#Update the files, then run the main program.

#Run the updater once before loading any other files.
getFileList()
checkAllFiles()
if reboot:
	restartPi()
import colorbox

while True:
	print ("Getting File list.")
	getFileList()
	checkAllFiles()
	if reboot:
		break
	colorbox.runLoop() #This loop will, by default, restart at midnight.

#If we get to this point, we'll want the pi to restart and re-run everything.		
restartPi()