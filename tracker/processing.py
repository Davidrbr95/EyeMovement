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

head = True;
class Reference_Template:
    ref_dsts = []
    image = None
    def __init__(self, dsts, number):
        self.ref_dsts = dsts
        self.image = number
    def appendDST(self, dst):
        self.ref_dsts.append(dst)
    def setImage(self, number):
        self.image = number

class Frame_Info:
    img_main = None
    img_out = None
    img_blackout = None
    img_original = None
    frame_index = 0
    frame_count = 0
    video_fps = 0
    eye_x = 0
    eye_y = 0
    ref_templates = []
    dst_bol = False
    fres_image = None

    def __init__(self, main, frame_index, fps):
        self.img_main = main
        self.frame_index = frame_index
        self.frame_count = frame_index*1000.0/fps
        self.video_fps = fps
        self.img_blackout = main.copy()
        self.ref_templates = None
        self.eye_x = 0
        self.eye_y = 0
        height, width = main.shape[:2]
        self.img_original = cv2.resize(main.copy(),(200, 200), interpolation = cv2.INTER_CUBIC)
        self.fres_image = None

    def addXY(self, x, y):
        self.eye_x = x
        self.eye_y = y

    def addTemplate(self, template):
        self.ref_templates.append(template)

    def setOutImage(self, out):
        self.img_out = out

    def updateBlackout(self, blackout):
        self.img_blackout = blackout

    def addDST(self, dst, number):
        self.dst_bol = True
        self.ref_template[number].appendDST(dst)
    


def getFrame(queue, startFrame, endFrame, videoFile, fps, img, data, ref_names):
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
        if frame_box.fres_image == None:
            object_viewed = 'None'
        else:
            # print 'I AM DOING TAKING OBJECT NAME'
            print ref_names
            print frame_box.fres_image
            object_viewed = ref_names[1]
        frame_box_variables = [frame_box.frame_index, frame_box.frame_count, frame_box.eye_x, frame_box.eye_y, object_viewed]
        text_file = open("images/Output.txt", "a")
        text_file.write('{:5} {:>16} {:>20f} {:>16f} {:>16s}'.format(frame_box_variables[0], frame_box_variables[1], frame_box_variables[2], frame_box_variables[3], frame_box_variables[4]))
        text_file.write('\n')
        text_file.close()
        # for i in range(len(frame_box_variables)):
            # output_variables += str(frame_box_variables[i])
            # output_variables += '           '
        # print output_variables
        # text_file.write(output_variables)
        if corr_flag:
            frame_box_template = frame_box
        if ret:
            try:
                queue.put([frameNo, f])
            except:
                queue.append([frameNo, f])
        first_flag = False
    cap.release()

def singleProcess(processCount, fileLength, videoFile, fps, img, data, ref_names):
    frameQueue = []
    bunches = createArrays(1, fileLength, fps)
    getFrame(frameQueue, 0, fileLength - 1, videoFile, fps, img, data, ref_names)
    results = []
    for i in range(bunches[0][0], bunches[0][1] - 1):
        results.append(frameQueue[i])
    return results, False, None, None

def multiProcess(processCount, fileLength, videoFile, fps, img, data, ref_names):
    qList = []
    for i in range(processCount):
    	qList.append(mp.JoinableQueue())
    bunches = createArrays(processCount, fileLength, fps)
    getFrames = []
    for i in range(processCount):
        getFrames.append(mp.Process(target=getFrame, args=(qList[i], bunches[i][0], bunches[i][1], videoFile, fps, img, data, ref_names)))
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