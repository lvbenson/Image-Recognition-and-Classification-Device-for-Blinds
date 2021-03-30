#another wake word initiates text detection to "read" a word allowed

#a final wake word "stops" text detection, returns to object detection


#import config 
import object_detection_comb 
#import text_detection_comb 

import cv2 
import argparse 
import os
import signal
import sys
import struct
import pyaudio
import pvporcupine

def main():
    begin_object = os.system("python3 /home/pi/build/open_model_zoo/demos/python_demos/object_detection_demo_py/object_detection_comb.py -m /home/pi/Downloads/mobilenet-ssd.xml -at ssd -i /dev/video0 -d MYRIAD --labels /home/pi/build/open_model_zoo/demos/python_demos/object_detection_demo_py/voclabels.txt")
  
            

if __name__=='__main__':
    main()
