from imutils.object_detection import non_max_suppression
from imutils import paths
import numpy as np
import argparse
import imutils
import cv2

import configparser
import time
import sys
import grequests
import json

from picamera.array import PiRGBArray
from picamera import PiCamera

from peopletracker import PeopleTracker
from tripline import Tripline

from PiVideoStream import PiVideoStream

import threading
from bottle import run, post, request, response, get, route


# frame dimension (calculated below in go)
_frame_width = 0
_frame_height = 0

# how many frames processed
_frame = 0

_total_in = 0
_total_out = 0

@route('/',method = 'GET')
def result():
	global _total_in
	global _total_out
	return json.dumps({'in': _total_in, 'out': _total_out})


def inside(r, q):
    rx, ry, rw, rh = r
    qx, qy, qw, qh = q
    return rx > qx and ry > qy and rx + rw < qx + qw and ry + rh < qy + qh


def process(frame):
    #frame = crop_and_resize(frame)

    frame = handle_the_people(frame)
    frame = render_hud(frame)

    #cv2.imshow('Camerafeed', frame)

# all the data that overlays the video
def render_hud(frame):

    global _total_in
    global _total_out

    cv2.putText(frame, 'in: %d ' % _total_in, (10, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    cv2.putText(frame, 'out: %d' % _total_out, (10, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    return frame

def handle_the_people(frame):

    (rects, weight) = hog.detectMultiScale(frame, winStride=(4, 4), padding=(2, 2), scale=1.4)

    people = finder.people(rects)

    # draw triplines
    for line in lines:
        for person in people:
            if line.handle_collision(person) == 1:
                new_collision(person)

        frame = line.draw(frame)

    for person in people:
        frame = person.draw(frame)
        person.colliding = False

    return frame

def new_collision(person):
    global _total_in
    global _total_out

    print(person.meta['line-0'])
    if person.meta['line-0'] == 'In':
    	_total_in = _total_in + 1
    if person.meta['line-0'] == 'Out':
    	_total_out = _total_out + 1


def crop_and_resize(frame):
    #frame = frame[0:240,0:320]
    frame = imutils.resize(frame, width=320)
    return frame                                                                                                                             


if __name__ == '__main__':
    #Web Service
    server_thread = threading.Thread(target=run, kwargs=dict(host='localhost', port=8080))
    server_thread.start()

    people_options = {'life':20,'max_distance':50,'charge':8}
    endpoint = None


    # setup lines
    lines = []
  
    #Tripline
    key = 'line2'
    start = eval('(120,30)')
    end = eval('(200, 240)')
    buffer = '10'
    direction_1 = 'In'
    direction_2 = 'Out'
    line = Tripline(point_1=start, point_2=end, buffer_size=buffer, direction_1=direction_1, direction_2=direction_2)
    lines.append(line)

    lines = lines


    #People tracking
    finder = PeopleTracker(people_options=people_options)
    #For Webcam
    #camera = cv2.VideoCapture(0)
    #camera.set(3, 320)
    #camera.set(4, 240)
    
    #For Pi Camera
    camera = PiCamera()
    camera.resolution = (320,240)
    camera.framerate = 20
    rawCapture = PiRGBArray(camera, size=(320,240))
    time.sleep(1)

    # setup detectors
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    #For Webcam
    #while camera.isOpened():
         #_,frame = camera.read()
         #if frame.any():
             #process(frame)
         #else:
             #print('error')

         #if cv2.waitKey(1) & 0xFF == ord('q'):
             #break
    #For Pi Camera
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        image = frame.array
        process(image)
        cv2.imshow('Camerafeed', image)
        #clear the stream in preparation for the next frame
        rawCapture.truncate(0)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    #For threading
    #vs = PiVideoStream().start()
    #time.sleep(2)
    #while True:
        #frame = vs.read()
        #frame = imutils.resize(frame, width=400)
        #process(frame)
        

    cv2.destroyAllWindows()
    #vs.stop()
