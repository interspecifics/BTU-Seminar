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
   >a. adquire images from camera
    b. preprocess image
    c. find light sources
    d. measure in a grid
    e. patterns
    f. selftraining

"""

# import modules
import cv2

# camera is a capture object connected to device 0
cam = cv2.VideoCapture(0)

# repeat   
while(True):
    # get a frame  
    _r, frame = cam.read()
    # show
    cv2.imshow('frame', frame)      
    # press q for quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# release cam and exit
cam.release()
cv2.destroyAllWindows()