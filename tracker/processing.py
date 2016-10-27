import cv2
import multiprocessing as mp
import math
import numpy as np
import datamani
import drMatches
from drMatches import Position
import FrameProcessing
from FrameProcessing import processImage
import time

class Frame_Info:
    img_main = None
    img_out = None
    img_blackout = None
    img_original = None
    template = []
    frame_index = 0
    frame_count = 0
    video_fps = 0
    eye_x = 0
    eye_y = 0
    dsts = None
    dst_bol = False

    def __init__(self, main, frame_index, fps):
        self.img_main = main
        self.frame_index = frame_index
        self.frame_count = frame_index*1000.0/fps
        self.video_fps = fps
        self.img_blackout = main.copy()
        self.img_original = main.copy()
        self.dsts = list()
        self.eye_x = 0;
        self.eye_y = 0;

    def addXY(self, x, y):
        self.eye_x = x
        self.eye_y = y

    def addTemplate(self, template):
        self.template = template

    def setOutImage(self, out):
        self.img_out = out

    def updateBlackout(self, blackout):
        self.img_blackout = blackout

    def addDST(self, dst):
        dst_bol = True
        self.dsts.append(dst)
    


def getFrame(queue, startFrame, endFrame, videoFile, fps, img, data, text_file):
    cap = cv2.VideoCapture(videoFile)  # crashes here
    frame_box_template = None
    first_flag = True
    for frame in range(startFrame, endFrame):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame)  # opencv3
        print 'Current frame: '+ str(frame)         
        frameNo = int(cap.get(cv2.CAP_PROP_POS_FRAMES))  # opencv3
        ret, f = cap.read()
        frame_box = Frame_Info(f, frame, fps)
        f, corr_flag = processImage(frame_box, img, data, frame_box_template, first_flag)
        frame_box_variables = [frame_box.frame_index, frame_box.frame_count, frame_box.eye_x, frame_box.eye_y]
        output_variables = ['', '', '', '']
        for i in range(len(frame_box_variables)):
            output_variables += str(frame_box_variables[i])
            while output_variables[i] < 17:
                output_variables[i] += ' '
        for var in output_variables:
            text_file.write(var)
        text_file.write('\n')
        if corr_flag:
            frame_box_template = frame_box
        if ret:
            try:
                queue.put([frameNo, f])
            except:
                queue.append([frameNo, f])
        first_flag = False
    cap.release()

def singleProcess(processCount, fileLength, videoFile, fps, img, data, text_file):
    frameQueue = []
    bunches = createArrays(1, fileLength, fps)
    getFrame(frameQueue, 0, fileLength - 1, videoFile, fps, img, data, text_file)
    results = []
    for i in range(bunches[0][0], bunches[0][1] - 1):
        results.append(frameQueue[i])
    return results, False, None, None

def multiProcess(processCount, fileLength, videoFile, fps, img, data):
    qList = []
    for i in range(processCount):
    	qList.append(mp.JoinableQueue())
    bunches = createArrays(processCount, fileLength, fps)
    getFrames = []
    for i in range(processCount):
        getFrames.append(mp.Process(target=getFrame, args=(qList[i], bunches[i][0], bunches[i][1], videoFile, fps, img, data)))
    for process in getFrames:
        process.start()
    results = []
    for i in range(len(qList)):
        results.append([qList[i].get() for p in range(bunches[i][0], bunches[i][1])])
    return results, True, getFrames, qList

def divideFrames(processCount, fileLength):
    bunches = []
    ratio = int(fileLength/processCount)
    for startFrame in range(0, fileLength, ratio):
        endFrame = startFrame + ratio
        if fileLength-startFrame< 2*ratio:
            endFrame = fileLength
            bunches.append((startFrame, endFrame-10))
            break
        bunches.append((startFrame, endFrame))
    return bunches

def createArrays(processCount, fileLength, fps):
    bunches = divideFrames(processCount, fileLength)
    return bunches

def terminate(processes, queues):
    for process in processes:
        process.terminate()
        process.join()

    for queue in queues:
        queue.close()