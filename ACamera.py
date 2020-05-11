#!/usr/bin/python

import sys
import os
import time
import cv2
import tty
import termios
import threading
import numpy as np
import signal
import json
from ImageConvert import *
import arducam_config_parser
import ArducamSDK
import Backlight


defaultCameraValues={
        "gain":0x65,
        "gainsRGBG":[0x21,0x24,0x24,0x20],
        "exposures":{
            "red"  :0x1C,
            "green":0x1A,
            "blue" :0x18,
            "white":0x18
        },
        "RGBbacklightPins":[6,12,13],
        "factoryFileSettings": "factoryConfigs/MT9J001_MONO_8b_3664x2748_4fps.cfg"
    }

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

#global cfg,running,Width,Heigth,save_flag,color_mode,handles,totalFrames,save_raw
#running = True
#save_flag = True
#save_raw = False
#cfg = {}
#handles = []
#totalFrames = []

class ACamera():
    def __init__(self):
        self.fn="ACamera_settings.json"
        self.running=True
        self.save_raw=False
        self.totalFrame=0
        self.light=Backlight.Backlight()
        self.glitches=0
        cv2.namedWindow("Gugusse",1)
        

    def init_camera(self):        
        try:
            h=open(self.fn,"r")
            content=h.read()
            h.close()
            self.camValues=json.loads(content)
        except Exception:
            print("Could not open {} or it is corrupted".format(self.fn))
            print("Do you want to create/overwrite the file with default values? (y/n)")
            ch=getch()
            if ch == 'y':
                h=open(self.fn,"w")
                json.dump(defaultCameraValues,h)
                h.close()
                print("file created, please restart application")
            else:
                print("aborted")
            sys.exit(0)
        
    
        devices_num,index,serials = ArducamSDK.Py_ArduCam_scan()
        assert devices_num == 1, "We expected 1 camera but we found {}".format(devices_num)
        print("Found {} device".format(devices_num))
        datas = serials[0]
        serial = "%c%c%c%c-%c%c%c%c-%c%c%c%c"%(datas[0],datas[1],datas[2],datas[3],
                                            datas[4],datas[5],datas[6],datas[7],
                                            datas[8],datas[9],datas[10],datas[11])
        time.sleep(2)
        self.camera_init_Factory_Settings()
        if self.handle != None:
            ret_val = ArducamSDK.Py_ArduCam_setMode(self.handle,ArducamSDK.EXTERNAL_TRIGGER_MODE)
            if(ret_val == ArducamSDK.USB_BOARD_FW_VERSION_NOT_SUPPORT_ERROR):
                print("USB_BOARD_FW_VERSION_NOT_SUPPORT_ERROR")
                sys.exit(0)
        else:
            print("No handle???")
            sys.exit(0)
        self.activateCameraValues()
        self.colorCycle("red", "red")
        
    def justSetTheColorSpecificGlobalGain(self, color):
        ArducamSDK.Py_ArduCam_writeSensorReg(self.handle,0x3012,self.camValues["exposures"][color])
        
    def activateCameraValues(self, color="white"):
        ArducamSDK.Py_ArduCam_writeSensorReg(self.handle,0x0204,self.camValues["gain"])
        ArducamSDK.Py_ArduCam_writeSensorReg(self.handle,0x3012,self.camValues["exposures"][color])
        ArducamSDK.Py_ArduCam_writeSensorReg(self.handle,0x0206,self.camValues["gainsRGBG"][0])
        ArducamSDK.Py_ArduCam_writeSensorReg(self.handle,0x0208,self.camValues["gainsRGBG"][1])
        ArducamSDK.Py_ArduCam_writeSensorReg(self.handle,0x020a,self.camValues["gainsRGBG"][2])
        ArducamSDK.Py_ArduCam_writeSensorReg(self.handle,0x020c,self.camValues["gainsRGBG"][3])

    def configBoard(self, config):
        ArducamSDK.Py_ArduCam_setboardConfig(
            self.handle,
            config.params[0],
            config.params[1],
            config.params[2],
            config.params[3],
            config.params[4:config.params_length]
        )

    def camera_init_Factory_Settings(self):
        #global Width,Height,color_mode,save_raw
        #load config file

        #cv2.namedWindow("Gugusse",1)
        config = arducam_config_parser.LoadConfigFile(self.camValues["factoryFileSettings"])
        camera_parameter = config.camera_param.getdict()
        self.Width = camera_parameter["WIDTH"]
        self.Height = camera_parameter["HEIGHT"]
        BitWidth = camera_parameter["BIT_WIDTH"]
        ByteLength = 1
        if BitWidth > 8 and BitWidth <= 16:
            ByteLength = 2
            self.save_raw = True
        FmtMode = camera_parameter["FORMAT"][0]
        self.color_mode = camera_parameter["FORMAT"][1]
        I2CMode = camera_parameter["I2C_MODE"]
        I2cAddr = camera_parameter["I2C_ADDR"]
        TransLvl = camera_parameter["TRANS_LVL"]        
        cfg = {"u32CameraType":0x00,
                "u32Width":self.Width,"u32Height":self.Height,
                "usbType":0,
                "u8PixelBytes":ByteLength,
                "u16Vid":0,
                "u32Size":0,
                "u8PixelBits":BitWidth,
                "u32I2cAddr":I2cAddr,
                "emI2cMode":I2CMode,
                "emImageFmtMode":FmtMode,
                "u32TransLvl":TransLvl
        }
        print(json.dumps(cfg,indent=4))
        # ArducamSDK.
        ret,self.handle,rtn_cfg = ArducamSDK.Py_ArduCam_open(cfg,0)
        #ret,handle,rtn_cfg = ArducamSDK.Py_ArduCam_autoopen(cfg)
        if ret == 0:
            #ArducamSDK.Py_ArduCam_writeReg_8_8(handle,0x46,3,0x00)
            usb_version = rtn_cfg['usbType']
            #print("USB VERSION:",usb_version)
            configs = config.configs
            configs_length = config.configs_length
            for i in range(configs_length):
                type = configs[i].type
                if ((type >> 16) & 0xFF) != 0 and ((type >> 16) & 0xFF) != usb_version:
                    continue
                if type & 0xFFFF == arducam_config_parser.CONFIG_TYPE_REG:
                    ArducamSDK.Py_ArduCam_writeSensorReg(self.handle, configs[i].params[0], configs[i].params[1])
                elif type & 0xFFFF == arducam_config_parser.CONFIG_TYPE_DELAY:
                    time.sleep(float(configs[i].params[0])/1000)
                elif type & 0xFFFF == arducam_config_parser.CONFIG_TYPE_VRCMD:
                    self.configBoard(configs[i])

            rtn_val,datas = ArducamSDK.Py_ArduCam_readUserData(self.handle,0x400-16, 16)
            print("Serial: %c%c%c%c-%c%c%c%c-%c%c%c%c"%(datas[0],datas[1],datas[2],datas[3],
                                                        datas[4],datas[5],datas[6],datas[7],
                                                        datas[8],datas[9],datas[10],datas[11]))

        else:
            print("open fail,ret_val = ",ret)
            sys.exit(0)

    def getSingleFrame(self):
        print("Take picture.")
        display_time = time.time()
        rtn_val= None
        retries=5
        while retries > 0:
            rtn_val,data,rtn_cfg = ArducamSDK.Py_ArduCam_getSingleFrame(self.handle)
            if rtn_val == 0:
                break
            self.glitches+= 1
            retries -= 1
            time.sleep(0.1)
            ArducamSDK.Py_ArduCam_softTrigger(self.handle)
            while ArducamSDK.Py_ArduCam_isFrameReady(self.handle)!=1:
                time.sleep(0.001)
        if rtn_val != 0:
            print("Take picture fail,ret_val = ",rtn_val)
            sys.exit(0)
        datasize = rtn_cfg['u32Size']
        if datasize == 0:
            print("data length zero!")
            return

        image = convert_image(data,rtn_cfg,self.color_mode)

        return image    
    def colorCycle(self, nextColor, currentColor):
        self.light.setLight(currentColor)
        #clean out any rogue trigger
        if ArducamSDK.Py_ArduCam_isFrameReady(self.handle)==1:
            self.getSingleFrame()
        self.justSetTheColorSpecificGlobalGain(nextColor)
        ArducamSDK.Py_ArduCam_softTrigger(self.handle)
        while ArducamSDK.Py_ArduCam_isFrameReady(self.handle)!=1:
            time.sleep(0.001)
        image=self.getSingleFrame()
        return image
    def captureImage(self, fn="/dev/shm/compose.tif"):
        #self.colorCycle("red", "red")
        retries=5
        while True:
            red=self.colorCycle("green", "red")
            green=self.colorCycle("blue", "green")
            blue=self.colorCycle("red", "blue")
            if self.glitches==0:
                break
            else:
                print("Glitch detected, retrying")
                self.glitches=0
                retries-= 1
                if retries==0:                    
                    sys.exit(0)
        self.light.setLight("white")
        image=cv2.merge([blue, green, red])
        cv2.imwrite(fn, image)
        image = cv2.resize(image,(1024,768),interpolation = cv2.INTER_LINEAR)

        cv2.imshow("Gugusse",image)
        cv2.waitKey(20)
        return image

            

if __name__ == "__main__":
    cam=ACamera()
    cam.init_camera()
    
    print("Finished initing handle")
    count=0
    cam.captureImage()
