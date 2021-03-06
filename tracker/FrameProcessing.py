import cv2
import multiprocessing as mp
import math
import numpy as np
import datamani
import drMatches
from drMatches import Position, getXY
from processing import Reference_Template
import time
import polygons_overlapping
import sys
import templatefind
import processing
from skimage.measure import compare_ssim as ssim


'''Creating instance variables'''
MIN_MATCH_COUNT = 20
font = cv2.FONT_HERSHEY_SIMPLEX
s = None
kp_ref, kp2, des_ref, des2 = [], [], [], []
first_run_flag = True
videoData = None
flag = True
poly_arr = []
poly_template = []
object_number = None
template_flag = False


def checkRect(array):
    x1 = array[0][0]
    y1 = array[0][1]
    x2 = array[1][0]
    y2 = array[1][1]
    x3 = array[2][0]
    y3 = array[2][1]
    x4 = array[3][0]
    y4 = array[3][1]

    cx=(x1+x2+x3+x4)/4
    cy=(y1+y2+y3+y4)/4

    dd1=math.sqrt(abs(cx-x1))+math.sqrt(abs(cy-y1))
    dd2=math.sqrt(abs(cx-x2))+math.sqrt(abs(cy-y2))
    dd3=math.sqrt(abs(cx-x3))+math.sqrt(abs(cy-y3))
    dd4=math.sqrt(abs(cx-x4))+math.sqrt(abs(cy-y4))
    a = abs(dd1-dd2)/((dd1+dd2)/2)
    b = abs(dd1-dd3)/((dd1+dd3)/2)
    c = abs(dd1-dd4)/((dd1+dd4)/2)

    if a > 0.2 or b>0.2 or c>0.2:
        return False
    else:
        return True

def startProcess(references, frame_box):
    global s, pos, first_run_flag, poly_arr, poly_template, flag, template_flag
    # Initiate SIFT detector
    # find the keypoints and descriptors with SIFT
    s=np.zeros((4,4))
    #print s.dtype
    pos = Position(0,0,0,0)
    flag = True

    first_run_flag = True

    for i, reference_1 in enumerate(references):
        new_template = Reference_Template([], i)
        frame_box.addTemplate(new_template)
        # if first_run_flag == False:
        #     frame_box.img_main = img3
        poly_arr, poly_template = [], []
        object_nmbr = i
        cmatch = 0
        template_flag = False
        referenceMatch(reference_1)
        while True:
            cmatch +=1
            good_matches= featureMatch(reference_1, frame_box)
            matchesMask, ignore, dst, break_flag = drawBorders(good_matches, i, reference_1, frame_box, object_nmbr)
            if break_flag or cmatch>20:
                # print "break"
                break
            x, y = getXY(frame_box, videoData)
            placeText(ignore, i, dst, x, y, frame_box)
    x, y = drawCircleAndMatches(ignore, good_matches, reference_1, frame_box)
    frame_box.addXY(x, y)
    cv2.putText(frame_box.img_main,str(frame_box.frame_index),(30,250), font, 1,(255,255,255),2,cv2.LINE_AA)
    if flag:
        cv2.putText(frame_box.img_main,'Gazing at none of the object',(250,30), font, 1,(255,255,255),2,cv2.LINE_AA)
    else:
        cv2.putText(frame_box.img_main,'Gazing at the '+str(object_number)+' object',(250,30), font, 1,(255,255,255),2,cv2.LINE_AA)
    first_run_flag = False

def referenceMatch(reference_1):  #Find the keypoints and des of the reference image only once in the process
    global kp_ref, des_ref
    sift = cv2.xfeatures2d.SIFT_create()
    kp_ref, des_ref = sift.detectAndCompute(reference_1,None)

def featureMatch(reference_1, frame_box):
    global kp_ref, kp2, des_ref
    sift = cv2.xfeatures2d.SIFT_create()

    kp2, des2 = sift.detectAndCompute(frame_box.img_blackout,None)

    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks = 50)

    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des_ref, des2, k=2)
    good = []
    for m,n in matches:
        if m.distance < 0.7*n.distance:
            good.append(m)
    return good

def drawBorders(good, ref_number, reference_1, frame_box, object_nmbr):
    global template_flag, poly_template
    ignore = False
    break_flag = False

    if len(good)>MIN_MATCH_COUNT:
        print "Enough Mathces"
        src_pts = np.float32([ kp_ref[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
        dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC,5.0)
        if mask == None:
            break_flag = True
            return None, None, None, break_flag
        matchesMask = mask.ravel().tolist()
        h,w = reference_1.shape
        pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
        dst = cv2.perspectiveTransform(pts,M)
        if len(dst) == 0:
            break_flag = True
            return None, None, None, break_flag
        if dst.size ==0:
            print "Size is the best method"
            break_flag = True
            return None, None, None, break_flag
        poly_currentarr = []
        for i in range(len(dst)):
            sub_dst = dst[i]
            sub2_dst = sub_dst[0]
            x1 = sub2_dst[0]
            y1 = sub2_dst[1]
            arr = [x1, y1]
            poly_currentarr.append(arr)
        poly_currentarr.append(poly_currentarr[0])
        current_rec = checkRect(poly_currentarr)
        # print template_flag
        if current_rec and not template_flag:
            poly_temporary = []
            xb = poly_currentarr[0][0]
            yb = poly_currentarr[0][1]
            for i in range(len(poly_currentarr)):
                arr = [poly_currentarr[i][0]-xb, poly_currentarr[i][1]-yb]
                poly_temporary.append(arr)
            poly_template = poly_temporary
            template_flag = True
            print "I am skipping long method"

        if not template_flag:
            print "I am doing long method"
            poly_template = templatefind.t_Start(reference_1, frame_box.img_main)
            template_flag = True
        ######## Checking to see if the current mask is a rectangle
        poly_current = np.asarray(poly_currentarr)
        if len(poly_arr)>0:
            for p in poly_arr:
                if polygons_overlapping.pair_overlapping(p, poly_current) ==2 or not current_rec:
                    xnot=dst[0][0][0]
                    ynot = dst[0][0][1]
                    t2_a = []
                    for i in range(len(poly_template)):
                        # print "Im here"
                        t2_b = []
                        t_a =np.int32([poly_template[i][0]+xnot, poly_template[i][1]+ynot])
                        t2_b.append(t_a)
                        t2_a.append(t2_b)
                    t3_a = np.int32(t2_a)
                    dst = t3_a
        if len(poly_arr)==0 and not current_rec:
            xnot=dst[0][0][0]
            ynot = dst[0][0][1]
            t2_a = []
            for i in range(len(poly_template)):
                t2_b = []
                t_a =np.int32([poly_template[i][0]+xnot, poly_template[i][1]+ynot])
                t2_b.append(t_a)
                t2_a.append(t2_b)
            t3_a = np.int32(t2_a)
            dst = t3_a
        poly_arr.append(poly_current)

        try: 
            frame_box.ref_templates[ref_number].appendDST(dst)
            frame_box.img_main = cv2.polylines(frame_box.img_main,[np.int32(dst)],True, (0, 255, 0),3, cv2.LINE_AA)
            frame_box.img_blackout = cv2.fillPoly(frame_box.img_blackout,[np.int32(dst)],(0,0,0))
        except:
            print 'EXCEPT BREAK'
            break_flag = True
            return None, None, None, break_flag
    else:
        # print "Not enough matches are found - %d/%d" % (len(good),MIN_MATCH_COUNT)
        matchesMask = None
        ignore = True
        dst = None
        break_flag = True
    return matchesMask, ignore, dst, break_flag

def drawCircleAndMatches(ignore, good, reference_1, frame_box):
    global pos, first_run_flag
    x, y = 0, 0
    if first_run_flag == True:
        x, y, ignore= datamani.drawCircle(frame_box, videoData, ignore)
    # frame_box.img_main= drMatches.drawMatches(reference_1,kp1,frame_box.img_main,kp2,good, pos)
    # img3, pos = drMatches.drawMatches(img1,kp1,img2,kp2,good, pos) ## line must not execute
    return x, y

def placeText(ignore, i, dst, x, y, frame_box):
    global s, flag, object_number
    if not ignore:
        s[i][0]=dst[0][0][0];
        s[i][1]=dst[3][0][0];
        s[i][2]=dst[0][0][1];
        s[i][3]=dst[2][0][1];
        # frame_box.addS(s)
        if x>s[i][0] and x<s[i][1] and y>s[i][2] and y<s[i][3]:
            if i == 0:
            frame_box.fres_image = i
            object_number = i+1
            flag = False

def mse(imageA, imageB):
    # the 'Mean Squared Error' between the two images is the
    # sum of the squared difference between the two images;
    # NOTE: the two images must have the same dimension
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1])
    
    # return the MSE, the lower the error, the more "similar"
    # the two images are
    return err

def compare_images(imageA, imageB):
    # compute the mean squared error and structural similarity
    # index for the images
    m = mse(imageA, imageB)
    print m
    s = ssim(imageA, imageB)
    print s
    return mse, s

def drawTemplate(frame_box, frame_box_template):
    ignore = False
    x, y, ignore= datamani.drawCircle(frame_box, videoData, ignore)
    frame_box.addXY(x, y)
    ## Need to get all the dst for the previous frame_box
    ix = 0;
    flag_write = True
    for i, i_dst in enumerate(frame_box_template.dsts):
        print 'DSTS: '+ str(i)+' DSTS_LENGTH: '+str(len(frame_box_template.dsts))
        frame_box.img_main = cv2.polylines(frame_box.img_main,[np.int32(i_dst)],True, (0, 255, 0),3, cv2.LINE_AA)
        if x>i_dst[0][0][0] and x<i_dst[3][0][0] and y>i_dst[0][0][1] and y<i_dst[2][0][1]:
            frame_box.fres_image = i
            flag_write = False
            if i == 0:
                print 'I AM TRUE FOR REFERENCE IMAGE RAGU'
            ix = i
    cv2.putText(frame_box.img_main,str(frame_box.frame_index),(30,250), font, 1,(255,255,255),2,cv2.LINE_AA)
    if flag_write:
        cv2.putText(frame_box.img_main,'Gazing at none of the object',(250,30), font, 1,(255,255,255),2,cv2.LINE_AA)
    else:
        cv2.putText(frame_box.img_main,'Gazing at the '+str(ix)+' object',(250,30), font, 1,(255,255,255),2,cv2.LINE_AA)

def checkCorrelation(frame_box_current, frame_box_template):
    current_gray = cv2.cvtColor(frame_box_current.img_original, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(frame_box_template.img_original, cv2.COLOR_BGR2GRAY)
    mse, si = compare_images(current_gray,template_gray)
    corr_flag = False
    if si<0.3:
        print 'recalculate'
        corr_flag = True
    else:
        print 'un-changed'
    return corr_flag

def processImage(frame_box, references, data, frame_box_template, first_flag):
    global videoData
    videoData = data
    #prescreening
    corr_flag = True
    if not first_flag:
        corr_flag = checkCorrelation(frame_box, frame_box_template)
    if corr_flag:
        startProcess(references, frame_box)
        # Need to set template = frame_box
    else:
        drawTemplate(frame_box, frame_box_template)
    return frame_box.img_main, corr_flag