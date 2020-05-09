#!/usr/bin/python
################################################################################
# Gugusse.py
# 
#
# By: Denis-Carl Robidoux
# Gugusse Roller main file.
#
################################################################################
from TrinamicSilentMotor import TrinamicSilentMotor
from time import sleep, time
import RPi.GPIO as GPIO
import threading
import json
from ACamera import ACamera
from fractions import Fraction
import os
GPIO.setmode(GPIO.BCM) 

class MotorThread (threading.Thread):
   def __init__(self, motor):
      threading.Thread.__init__(self)
      self.motor=motor
   def run(self):
      self.motor.move()

colors={
   "red":[GPIO.HIGH, GPIO.LOW, GPIO.LOW],
   "green":[GPIO.LOW, GPIO.HIGH, GPIO.LOW],
   "blue":[GPIO.LOW, GPIO.LOW, GPIO.HIGH],
   "white":[GPIO.HIGH, GPIO.HIGH, GPIO.HIGH],
   "black":[GPIO.LOW, GPIO.LOW, GPIO.LOW],
   "off":[GPIO.LOW, GPIO.LOW, GPIO.LOW]
}

      
class Gugusse():
    def __init__(self, cfg, start_frame):
        GPIO.setup(6,GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(12,GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(13,GPIO.OUT, initial=GPIO.HIGH)
        for item in cfg:
           if isinstance(cfg[item], dict):
              cfg[item]["name"]=item
        self.filmdrive=TrinamicSilentMotor(cfg["filmdrive"], trace=True)
        self.feeder=TrinamicSilentMotor(cfg["feeder"],autoSpeed=True)
        self.pickup=TrinamicSilentMotor(cfg["pickup"],autoSpeed=True)
        self.framecount=start_frame
        try:
            os.mkdir("/dev/shm/complete")
        except Exception:
            print("Ho well... directory already exists, who cares?");
        self.feeder.enable()
        self.filmdrive.enable()
        self.pickup.enable()
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

    def grabASimpleSequential(self):
        fn="/dev/shm/%05d.jpg"%self.framecount
        fncomplete="/dev/shm/complete/%05d.jpg"%self.framecount
        self.grabAPicComponent(fn, fncomplete)
        self.framecount+= 1

    
    def grabAPic(self):
        save_path="/dev/shm/inprogress"
        final_path="/dev/shm/complete"
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        if not os.path.exists(final_path):
            os.makedirs(final_path)
        
        fn="{}/{:05}.tif".format(save_path,self.framecount)
        fncomplete="{}/{:05}.tif".format(final_path,self.framecount)
        image=self.cam.captureImage(fn)
        os.rename(fn,fncomplete)
        self.framecount+= 1
        return image
           
    def frameAdvance(self):
        m1=MotorThread(self.filmdrive)
        m2=MotorThread(self.feeder)
        m3=MotorThread(self.pickup)
        m2.start()
        m3.start()
        m3.join()
        m2.join()
        m1.start()
        m1.join()
        #self.cam.gcApplySettings()
        if m1.motor.fault or m2.motor.fault or m3.motor.fault:
           self.feeder.disable()
           self.filmdrive.disable()
           self.pickup.disable()
           raise Exception("Motor Fault!")
        sleep(0.25)
        return self.grabAPic()
           

        
import sys
try:
   print("Loading film config")
   h=open(sys.argv[1])
   filmcfg=json.load(h)
   h.close()
   print("Loading hardware config")
   h=open("hardwarecfg.json")
   cfg=json.load(h)
   print("merging the 2")
   for device in filmcfg:
      print("merging {}".format(device))
      cfg[device].update(filmcfg[device])
   print("Reading the other 2 parameters")
   firstNum=int(sys.argv[2])
   feederDirection=sys.argv[3]
except Exception as e:
   print (e.message)
   print ("\nUSAGE: {} <film format json file> <initial file number> <cw|ccw>\n".format(sys.argv[0]))
   sys.exit(0)
if feederDirection == "cw":
   cfg["feeder"]["invert"]=not cfg["feeder"]["invert"]
capture=Gugusse(cfg, firstNum)

while True:
    capture.frameAdvance()
    sleep(0.05)
