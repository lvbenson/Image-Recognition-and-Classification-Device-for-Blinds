#another wake word initiates text detection to "read" a word allowed

#a final wake word "stops" text detection, returns to object detection


#import object_detection_comb 
#import text_detection_comb 
import multiprocessing
import time

import cv2 
import argparse 
import os
import signal
import sys
import struct
import pyaudio
import pvporcupine
from pynput.keyboard import Key, Controller


#thread: block object detection


#not sure I need this one. I can use the wakeword as the blocker. 
"""
def detection(event):
    print("Waiting to start detection."
    event.wait() #blocks event until set() creates internal flag
    event.is_set() #True if internal flag is true. 
"""

def switch_to_object(event):
    
    event.wait() #waits until wake word occurs
    
    #if command is not None: #if wake word for either switching process occurs
    event.is_set()
    
    os.system("python3 /home/pi/build/open_model_zoo/demos/python_demos/object_detection_demo_py/object_detection_NEW.py -m /home/pi/Downloads/mobilenet-ssd.xml -at ssd -i /dev/video0 -d MYRIAD --labels /home/pi/build/open_model_zoo/demos/python_demos/object_detection_demo_py/voclabels.txt")


def switch_to_text(event):
    
    event.wait() #waits until wake word occurs
    
    #if command is not None: #if wake word for either switching process occurs
    event.is_set()
    
    os.system("python3 /home/pi/build/open_model_zoo/demos/python_demos/object_detection_demo_py/text_detection_comb.py")

    
    
    



def wakeword(event):
    
    #starting with object detection
    detection = 'object'

    porcupine = None
    pa = None
    audio_stream = None

    try:
        porcupine = pvporcupine.create(keywords=["blueberry"])

        pa = pyaudio.PyAudio()

        audio_stream = pa.open(
                    rate=porcupine.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=porcupine.frame_length)

        while True:
            
            #print("new wakeword loop")
            
            #detection = 'object'
    
            #start = time.time()

            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)
            
            
            if keyword_index >= 0:
                
                #stop = time.time()
                #t = stop-start 


                if detection == 'object':
                    #check if other process is happening. If so, terminate it before beginning new process.
                    try:
                        wait3
                    except NameError:
                        
                        detection = 'text'
                        
                        print("not yet")
                        #switch to object detection
                        wait2 = multiprocessing.Process(name='object',target=switch_to_object,args=(event,))
                        wait2.start()
                        event.set()
                        
                        continue
                        
                    else:
                        
                        print("currently text detection. NEED TO TERMINATE TEXT DETECTION")
                        detection = 'text'
                        #print(detection)
                        
                        print("terminating text detection")
                        #signal.SIGINT
                        wait3.terminate()
                        signal.SIGINT
                        #Controller().press('q')
                        #Controller().release('q')
                        
                        
                        wait2 = multiprocessing.Process(name="object",target=switch_to_object,args=(event,))
                        wait2.start()
                        event.set()
                                        
                        continue
            
                if detection == 'text':
                    
                    print("SWITCHING TO TEXT DETECTION")
                    
                    detection = 'object'
                    
                    #terminate object detection process
                    wait2.terminate()
                    Controller().press('q')
                    Controller().release('q')
                    
                    
                    
                    wait3 = multiprocessing.Process(name="text",target=switch_to_text,args=(event,))
                 

                    wait3.start()
                    event.set()
                    
                    
                    
                    continue
                    
        
    except KeyboardInterrupt:
        print('stopping...')


if __name__ == '__main__':
    
    detection_event = multiprocessing.Event() #initiate wakeword event
    
    command = wakeword(detection_event)
    
    end_now = 0
    
    
    
    #detection_event = multiprocessing.Event()

    #FLAG for wakeword subprocess
    #wait1 = multiprocessing.Process(name='block switch',target=wakeword,args=(command_event,))

    #wait1.start()
    #command_event.set()
    





    

    #unblocks detection from occuring. 
    #wait2 = multiprocessing.Process(name='non-block',target=switch,args=(event,command,t))

    #wait2.start()

    #event.set()


"""
def detection(system): #runs text detection or object detection according to wake word
    if system == 0:
        begin_object = os.system("python3 /home/pi/build/open_model_zoo/demos/python_demos/object_detection_demo_py/object_detection_comb.py -m /home/pi/Downloads/mobilenet-ssd.xml -at ssd -i /dev/video0 -d MYRIAD --labels /home/pi/build/open_model_zoo/demos/python_demos/object_detection_demo_py/voclabels.txt")

    else:
        begin_text = os.system("python3 /home/pi/build/open_model_zoo/demos/python_demos/object_detection_demo_py/text_detection_comb.py
"""