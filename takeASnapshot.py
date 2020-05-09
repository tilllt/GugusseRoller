#!/usr/bin/python
################################################################################
# Gugusse.py
# 
#
# By: Denis-Carl Robidoux
# Gugusse Roller main file.
#
################################################################################
from time import sleep, time
import RPi.GPIO as GPIO
import threading
import json
from ACamera import ACamera
from fractions import Fraction
import os
import cv2
GPIO.setmode(GPIO.BCM) 


colors={
   "red":[GPIO.HIGH, GPIO.LOW, GPIO.LOW],
   "green":[GPIO.LOW, GPIO.HIGH, GPIO.LOW],
   "blue":[GPIO.LOW, GPIO.LOW, GPIO.HIGH],
   "white":[GPIO.HIGH, GPIO.HIGH, GPIO.HIGH],
   "black":[GPIO.LOW, GPIO.LOW, GPIO.LOW],
   "off":[GPIO.LOW, GPIO.LOW, GPIO.LOW]
}

      
class Gugusse():
    def __init__(self):
        GPIO.setup(6,GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(12,GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(13,GPIO.OUT, initial=GPIO.HIGH)
        self.cam=ACamera()
        self.cam.init_camera()

    def setLight(self, color):
       c=colors[color]
       GPIO.output(6,c[0])
       GPIO.output(12,c[1])
       GPIO.output(13,c[2])
        
    def grabAPicComponent(self, fn, fncomplete):
        #try:
        #   self.cam.capture(fn)
        #except exception as e:
        #   self.feeder.disable()
        #   self.filmdrive.disable()
        #   self.pickup.disable()
        #   print("Failure to capture image: {}".format(e))
        #   self.cam.close()
        #   raise Exception("Stop")
        #os.rename(fn,fncomplete)
        pass

    
    def grabAPic(self):
        red=self.cam.colorCycle(None, "red")
        green=self.cam.colorCycle(None, "green")
        blue=self.cam.colorCycle(None, "blue")        
        self.cam.light.setLight("white")
        image=cv2.merge([blue, green, red])
        cv2.imwrite("/dev/shm/combined.tif",image)
           
           

        
import sys
capture=Gugusse()
capture.grabAPic()


