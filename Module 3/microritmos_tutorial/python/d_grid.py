#!/bin/usr/python3
# -*- coding: utf-8 -*-


"""
| i n t e r s p e c i f i c s TUB seminar | autumn 2021 |
| tutorial 4: micro-rhythms |

install:
pip install numpy
pip install oscpy
pip install opencv-python

steps:
    a. adquire images from camera
    b. preprocess image
    c. find light sources
   >d. measure in a grid
    e. patterns
    f. selftraining

"""

# import modules
import cv2
import numpy as np

# dimensions
w = 640                   # screen
h = 480   
camw = 640                # camera 
camh = 480   

binThreshold = 200



def create_blank(w, h, rgb_color=(0, 0, 0)):
    """ create new image(numpy array) filled with certain color in rgb """
    image = np.zeros((h, w), np.uint8)
    color = tuple(reversed(rgb_color))
    image[:] = 0
    return image

def binarize_keypoints (binSize, w, kpList):
    """ divide w en bins de tamaño binsize
        pone cada keypoint en los bins correspondientes
        devuelve una lista de bins activos    
    """
    nBin = int (w / binSize)
    a = np.zeros(nBin, int)
    for kp in kpList:
        cBin = int(kp[0] / binSize)
        a[cBin] = 1
    return a


# create window}
canvas = create_blank(w, h, rgb_color=(0,0,0))
window_name = ": TUTORIAL4 : micro-rhythms :"
cv2.namedWindow(window_name)
cv2.moveWindow(window_name, 0, 0)

# camera is a capture object connected to device 1
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_AUTOFOCUS, 0) 

# create a detector
pp=cv2.SimpleBlobDetector_Params()
pp.minThreshold=208
pp.maxThreshold=255
pp.filterByArea=True
pp.minArea=200
pp.maxArea=10000
pp.filterByColor=True
pp.blobColor=255
pp.filterByCircularity=False
pp.filterByConvexity=False
pp.filterByInertia=False
blob_finder = cv2.SimpleBlobDetector_create(pp)


# repeat   
while(True):
    # get a frame  
    _r, img = cam.read()

    # adjust brightness and contrast
    frame = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    contrast =1.90
    brightness = -250
    frame[:,:,2] = np.clip(contrast * frame[:,:,2] + brightness, 0, 255)
    img = cv2.cvtColor(frame, cv2.COLOR_HSV2BGR)

    # blur + threshold
    gImg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bImg = cv2.medianBlur(gImg, 21)
    #tImg = cv2.threshold(bImg, binThreshold, 255, cv2.THRESH_TRUNC)

    # find the sources
    keyPoints = blob_finder.detect(bImg)
    kp_coo = [k.pt for k in keyPoints]	
    #print (kp_coo)
    print ("{} objects found".format(len(kp_coo)))

    # locate in the grid
    kp_bin = binarize_keypoints(20, 640, kp_coo) 
    print (kp_bin)

    # show the image
    canvas[0:h, 0:w] = bImg
    cv2.imshow(window_name, canvas)   # << .................

    # press q for quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# release cam and exit
cam.release()
cv2.destroyAllWindows()
print ("[._.] terminated.")      


#tImg = cv2.threshold(bImg, binThreshold, 255, cv2.THRESH_BINARY);
#tImg = cv2.threshold(bImg, binThreshold, 255, cv2.THRESH_BINARY_INV);
#tImg = cv2.threshold(bImg, binThreshold, 255, cv2.THRESH_TRUNC);
#tImg = cv2.threshold(bImg, binThreshold, 255, cv2.THRESH_TOZERO);
#tImg = cv2.threshold(bImg, binThreshold, 255, cv2.THRESH_TOZERO_INV);
