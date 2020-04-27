import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM) 
colors={
   "red":[GPIO.HIGH, GPIO.LOW, GPIO.LOW],
   "green":[GPIO.LOW, GPIO.HIGH, GPIO.LOW],
   "blue":[GPIO.LOW, GPIO.LOW, GPIO.HIGH],
   "white":[GPIO.HIGH, GPIO.HIGH, GPIO.HIGH],
   "black":[GPIO.LOW, GPIO.LOW, GPIO.LOW],
   "off":[GPIO.LOW, GPIO.LOW, GPIO.LOW]
}

class Backlight():
    def __init__(self):
        GPIO.setup(6,GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(12,GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(13,GPIO.OUT, initial=GPIO.HIGH)
        self.setLight("white")
        
    def setLight(self, color):
        c=colors[color]
        GPIO.output(6,c[0])
        GPIO.output(12,c[1])
        GPIO.output(13,c[2])
    
