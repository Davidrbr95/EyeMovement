import math
import numpy as np
import cv2
import processing

class DataPoint(object):
	def __init__(self, vidname, tmili, x, y):
		self.__vidname = vidname
		self.__tmili = tmili
		self.__x = x
		self.__y = y
	def getCoordinates(self):
		return self.__x, self.__y
	def setCoordinates(self, x, y):
		self.__x, self.__y = x, y
	def getTMili(self):
		return self.__tmili
	def setTMili(self, tmili):
		self.__tmili = tmili
	def setVidName(self, name):
		self.__vidname = name


def make_dpoint(vidname, tmili, x, y):
    dpoint = DataPoint("", 0, 0, 0)
    return dpoint

def binarySearch(data, val):
	val = val * 1000
	lo, hi = 0, len(data) - 1
	best_ind = lo
	while lo <= hi:
	    mid = lo + (hi - lo) / 2
	    if data[mid].getTMili() < val:
	        lo = mid + 1
	    elif data[mid].getTMili() > val:
	        hi = mid - 1
	    else:
	        best_ind = mid
	        break
	    # check if data[mid] is closer to val than data[best_ind] 
	    if abs(data[mid].getTMili() - val) < abs(data[best_ind].getTMili() - val):
	        best_ind = mid
	return best_ind

def createVideoData(textFile): 
	videoData = list(list()) #Makes one list per video of the list of data points
	set_up = True;
	for i in range(33): # Skip top line of text file because no data is contained there.
		textFile.next()
	points = list()
	for line in textFile:
		dp = make_dpoint('', 0, 0, 0)
		dataline = line.split()
		# cvt = dataline[3] #current video title
		# dp.setVidName(cvt)
		if set_up:
			tnot = float(dataline[0])
			set_up = False
		# if pvt != cvt:
		# 	videoData.append(points)
		# 	points = list()
		# 	tnot = float(dataline[0])
		dp.setTMili(float(dataline[0])-tnot)
		# print dp.getTMili()
		# if dataline[11] == '2':
		# 	if dataline[16] == 'Blink' or dataline[16] == 'Saccade':
		# 		dp.setCoordinates(float(dataline[21]), float(dataline[22]))
		# 	if dataline[16]=='Visual':
		# 		dp.setCoordinates(float(dataline[22]), float(dataline[23]))
		# else:
		# 	if dataline[14]=='Saccade':
		# 		dp.setCoordinates(float(dataline[19]), float(dataline[20]))
		# 	else:
		# 		dp.setCoordinates(float(dataline[20]), float(dataline[21]))
		dp.setCoordinates(float(dataline[3]), float(dataline[4]))
		# pvt = cvt
		points.append(dp)

	videoData.append(points)

	vid = videoData[0] # Gets only the first part of the data
	return vid

def drawCircle(frame_box, videoData, ignore):
	# alpha = 10
	# delayFactor = 6 - int(frameCount/((1.0/fps)*1000.0) /  alpha) #delay factor
	idx_sub = binarySearch(videoData, frame_box.frame_count)
	point = idx_sub
	if point > len(videoData) - 1:
		point = len(videoData) - 1
	x, y = videoData[point].getCoordinates()

	tpoint = videoData[point].getTMili()
	# print str(frameCount)+'           '+str(lowt)+'             ' +str(tpoint)+ '            ' +str(hight)
	if x == None or y == None:
		return x, y, True
	if math.isnan(float(x)) or math.isnan(float(y)):
		return x, y, ignore
	else:
		cv2.circle(frame_box.img_main, (int(x), int(y)), 5, (255, 0, 0), 10)
	return x, y, ignore
