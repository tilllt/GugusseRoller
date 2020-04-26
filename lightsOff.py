#!/usr/bin/python

import RPi.GPIO as GPIO
from time import sleep

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM) 

GPIO.setup(6,GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(12,GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(13,GPIO.OUT, initial=GPIO.LOW)


