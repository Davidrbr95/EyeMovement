import cv2
import multiprocessing as mp
import math
import numpy as np
import datamani
import drMatches
from drMatches import Position
import time
import processing
from processing import multiProcess, singleProcess
import sortout
def writeFrames(result, success):
    for frame in result:
        if len(frame) == 0:
            print 'Well it looks like there is an empty image. '+'Frame: '+str(i)
        success.write(frame[1])

if __name__ == '__main__':
    ######## Initialize Constants ########
    i = 0
    img = [cv2.imread('images/ragu.png', 0), cv2.imread('images/frosted_flakes.png',0)] ## Reads in comparison images
    videoData = datamani.createVideoData(open('images/mady.txt', 'r')) ## Reads in data file
    file = "images/madison_30sec.mp4"
    capture_temp = cv2.VideoCapture(file)
    fileLen = int((capture_temp).get(cv2.CAP_PROP_FRAME_COUNT))  # opencv3
    fps = capture_temp.get(cv2.CAP_PROP_FPS) ##fps
    ret,temp=capture_temp.read(); ## Reads the first frame
    capture_temp.release()
    height, width = temp.shape[:2]
    capSize = (width,height) ## this is the size of my source video
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v') ## starts ouput file
    success = cv2.VideoWriter('images/output.mp4',fourcc,fps,capSize)
    processCount = 4
    ref_names = ['Ragu', 'Frosted Flakes']
    text_file = open("images/Output.txt", "w")
    text_file.write('Frame Number      Time Stamp       Gaze-X           Gaze-Y         Object Observed')
    text_file.write('\n')
    text_file.close()
    text_file = open("images/Output.txt", "a")
    results, multi_flag, getFrames, qList = multiProcess(processCount, fileLen, file, fps, img, videoData, ref_names)
    text_file.close()
    sortout.sortOutput("images/Output.txt")
    if multi_flag:
        for result in results:
            writeFrames(result, success)
    else:
        writeFrames(results, success)
    if multi_flag:
        processing.terminate(getFrames, qList)
    success.release()
    capture_temp.release()
    print 'I am DONE'


