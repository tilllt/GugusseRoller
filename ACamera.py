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


defaultCameraValues=
    {
        "gainsRGBG":[0x1E,0x1D,0x1C,0x1B],
        "apertureRGB":[0x21,0x1E,0x1B]
        "apertureW":0x18,
        "pinsRGB":[6,12,13],
        "factoryFileSettings": "MT9J001_MONO_8b_3664x2748_4fps.cfg"
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



#global cfg,handle,running,Width,Heigth,save_flag,color_mode,save_raw,zoom,quadra,aperture
    
class ACamera():
    def __init__(self):

        self.running = True
        self.save_flag = False
        self.save_raw = False
        self.zoom=0
        self.color_mode=None
        self.cfg = {}
        self.handle = {}
        self.Width=0
        self.Height=0

    def configBoard(self, config):
        ArducamSDK.Py_ArduCam_setboardConfig(
            self.handle,
            config.params[0], 
            config.params[1],
            config.params[2],
            config.params[3], 
            config.params[4:config.params_length]
        )


    def camera_initFromFile(self,fileName):
        #load config file
        # config = json.load(open(fialeName,"r"))
        config = arducam_config_parser.LoadConfigFile(fileName)
        camera_parameter = config.camera_param.getdict()
        print("{}\r".format(camera_parameter))
    
        self.width = camera_parameter["WIDTH"]
        self.height = camera_parameter["HEIGHT"]

        BitWidth = camera_parameter["BIT_WIDTH"]
        ByteLength = 1
        if BitWidth > 8 and BitWidth <= 16:
            ByteLength = 2
            save_raw = True
        FmtMode = camera_parameter["FORMAT"][0]
        color_mode = camera_parameter["FORMAT"][1]
        print("color mode",color_mode)

        I2CMode = camera_parameter["I2C_MODE"]
        I2cAddr = camera_parameter["I2C_ADDR"]
        TransLvl = camera_parameter["TRANS_LVL"]
        self.cfg = {
            "u32CameraType":0x00,
            "u32Width":self.width,"u32Height":self.height,
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

        #ret,handle,rtn_cfg = ArducamSDK.Py_ArduCam_open(cfg,0)
        ret,self.handle,rtn_cfg = ArducamSDK.Py_ArduCam_autoopen(self.cfg)
        if ret == 0:
       
            #ArducamSDK.Py_ArduCam_writeReg_8_8(handle,0x46,3,0x00)
            usb_version = rtn_cfg['usbType']
            configs = config.configs
            configs_length = config.configs_length
            for i in range(configs_length):
                type = configs[i].type
    
                if ((type >> 16) & 0xFF) != 0 and ((type >> 16) & 0xFF) != usb_version:
                    continue
                if type & 0xFFFF == arducam_config_parser.CONFIG_TYPE_REG:
                    print("About to writeSensorReg({:04X}, {:04X})\r".format(configs[i].params[0], configs[i].params[1]))
                    ArducamSDK.Py_ArduCam_writeSensorReg(self.handle, configs[i].params[0], configs[i].params[1])
                elif type & 0xFFFF == arducam_config_parser.CONFIG_TYPE_DELAY:
                    time.sleep(float(configs[i].params[0])/1000)
                elif type & 0xFFFF == arducam_config_parser.CONFIG_TYPE_VRCMD:
                    self.configBoard(configs[i])

            rtn_val,datas = ArducamSDK.Py_ArduCam_readUserData(self.handle,0x400-16, 16)
            print("Serial: %c%c%c%c-%c%c%c%c-%c%c%c%c\r"%(datas[0],datas[1],datas[2],datas[3],
                                                    datas[4],datas[5],datas[6],datas[7],
                                                    datas[8],datas[9],datas[10],datas[11]))

            return True
        else:
            print("open fail,rtn_val = \r",ret)
            return False

       
def captureImage_thread():
    global handle,running

    rtn_val = ArducamSDK.Py_ArduCam_beginCaptureImage(handle)
    if rtn_val != 0:
        print("Error beginning capture, rtn_val = \r",rtn_val)
        running = False
        return
    else:
        print("Capture began, rtn_val = \r",rtn_val)
    
    while running:
        #print "capture"
        rtn_val = ArducamSDK.Py_ArduCam_captureImage(handle)
        if rtn_val > 255:
            print("Error capture image, rtn_val = \r",rtn_val)
            if rtn_val == ArducamSDK.USB_CAMERA_USB_TASK_ERROR:
                break
        time.sleep(0.005)
        
    running = False
    ArducamSDK.Py_ArduCam_endCaptureImage(handle)

def readImage_thread():
    global handle,running,Width,Height,save_flag,cfg,color_mode,save_raw,zoom
    #global COLOR_BayerGB2BGR,COLOR_BayerRG2BGR,COLOR_BayerGR2BGR,COLOR_BayerBG2BGR
    count = 0
    totalFrame = 0
    time0 = time.time()
    time1 = time.time()
    data = {}
    cv2.namedWindow("ArduCam Demo",1)
    if not os.path.exists("images"):
        os.makedirs("images")
    while running: 
        display_time = time.time()
        if ArducamSDK.Py_ArduCam_availableImage(handle) > 0:		
            rtn_val,data,rtn_cfg = ArducamSDK.Py_ArduCam_readImage(handle)
            datasize = rtn_cfg['u32Size']
            if rtn_val != 0 or datasize == 0:
                ArducamSDK.Py_ArduCam_del(handle)
                print("read data fail!\r")
                continue

            image = convert_image(data,rtn_cfg,color_mode)
        
            time1 = time.time()
            if time1 - time0 >= 1:
                #print("%s %d %s\n"%("fps:",count,"/s"))
                count = 0
                time0 = time1
            count += 1
            if save_flag:
                fn="images/%05d.jpg"%totalFrame
                print("saving {}\r".format(fn))
                cv2.imwrite(fn,image)
                if save_raw:
                    with open("images/%05d.raw"%totalFrame, 'wb') as f:
                        f.write(data)
                totalFrame += 1
                save_flag=False
            if zoom > 5:
                zoom=0
            elif zoom == 5:
                image=image[int(self.height/2-20):int(self.height/2+20),int(self.width/2-20):int(self.width/2+20)]
            elif zoom != 0:
                startx=int(self.width*zoom/10)
                starty=int(self.height*zoom/10)
                endx=int(self.width-startx)
                endy=int(self.height-starty)
                #print("\r")
                #print("zooming [{}:{},{}:{}]\r".format(starty,endy,startx,endx))
                image=image[starty:endy,startx:endx]
            image = cv2.resize(image,(1024,768),interpolation = cv2.INTER_NEAREST)
            cv2.imshow("ArduCam Demo",image)
            cv2.waitKey(10)
            ArducamSDK.Py_ArduCam_del(handle)
            #print("------------------------display time:",(time.time() - display_time))
        else:
            time.sleep(0.001)
        
def showHelp():
    print(" usage: sudo python ArduCam_Py_Demo.py <path/config-file-name>	\
        \n\n example: sudo python ArduCam_Py_Demo.py ../../../python_config/AR0134_960p_Color.json	\
        \n\n While the program is running, you can press the following buttons in the terminal:	\
        \n\n 's' + Enter:Save the image to the images folder.	\
        \n\n 'c' + Enter:Stop saving images.	\
        \n\n 'q' + Enter:Stop running the program.	\
        \n\n")

def sigint_handler(signum, frame):
    global running,handle
    running = False
    exit()

signal.signal(signal.SIGINT, sigint_handler)
#signal.signal(signal.SIGHUP, sigint_handler)
signal.signal(signal.SIGTERM, sigint_handler)

if __name__ == "__main__":

    
    config_file_name = "8bits.cfg"
    

    if camera_initFromFile(config_file_name):
        ArducamSDK.Py_ArduCam_setMode(handle,ArducamSDK.CONTINUOUS_MODE)
        ct = threading.Thread(target=captureImage_thread)
        rt = threading.Thread(target=readImage_thread)
        ct.start()
        rt.start()
        
        while running:
            input_kb = getch()
            if input_kb == 'z' or input_kb == 'Z':
                zoom+= 1
            elif input_kb == 'q' or input_kb == 'Q':
                running = False
            elif input_kb == 's' or input_kb == 'S':
                save_flag = True
            elif input_kb == 'c' or input_kb == 'C':
                save_flag = False
            elif input_kb == '-' or input_kb == '+':
                if input_kb == '-' and aperture > 0:
                    aperture -= 1
                elif input_kb == '+' and aperture < 0xff:
                    aperture += 1
                else:
                    continue
                print("new aperture: {:02X}".format(aperture))
                ArducamSDK.Py_ArduCam_writeSensorReg(handle,0x3012,aperture)
                
                        
            elif input_kb > '0' and input_kb < '9':
                val=int(input_kb)
                idx=val-5
                if val < 5:
                    idx=val-1
                    if quadra[idx] == 0x0:
                        quadra[idx]=0xff
                    else:
                        quadra[idx]-= 1
                else:
                    if quadra[idx] == 0xff:
                        quadra[idx]=0x0
                    else:
                        quadra[idx]+= 1
                ArducamSDK.Py_ArduCam_writeSensorReg(handle,0x0206,quadra[0])
                ArducamSDK.Py_ArduCam_writeSensorReg(handle,0x0208,quadra[1])
                ArducamSDK.Py_ArduCam_writeSensorReg(handle,0x020a,quadra[2])
                ArducamSDK.Py_ArduCam_writeSensorReg(handle,0x020c,quadra[3])
                print("\rNew quadra:({:02X},{:02X},{:02X},{:02X})\n\r".format(quadra[0],quadra[1],quadra[2],quadra[3]))

        ct.join()
        rt.join()
        #pause
        #ArducamSDK.Py_ArduCam_writeReg_8_8(handle,0x46,3,0x40)
        rtn_val = ArducamSDK.Py_ArduCam_close(handle)
        if rtn_val == 0:
            print("device close success!\r")
        else:
            print("device close fail!\r")

        #os.system("pause")
