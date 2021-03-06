from imutils.video import VideoStream
from imutils.video import FPS
import numpy as np
import argparse
import imutils
import time
import cv2
import os
from openvino.inference_engine import IECore
#from BeamSearch import BeamEntry, BeamState, applyLM, addBeam, ctcBeamSearch
import enchant
import pygame
from gtts import gTTS
import subprocess
import signal
import pvporcupine
import pyaudio
import struct
import sys
#from porcupine_demo_mic import *
#from word_beam_search import WordBeamSearch
#from inference import Inference #for OCR model

#d = enchant.Dict("en_US")

fpsstr = ""
framecount = 0
time1 = 0

def rotated_Rectangle(img, rotatedRect, color, thickness=1, lineType=cv2.LINE_8, shift=0):
    (x, y), (width, height), angle = rotatedRect
 
    pt1_1 = (int(x + width / 2), int(y + height / 2))
    pt2_1 = (int(x + width / 2), int(y - height / 2))
    pt3_1 = (int(x - width / 2), int(y - height / 2))
    pt4_1 = (int(x - width / 2), int(y + height / 2))
 
    t = np.array([[np.cos(angle),   -np.sin(angle), x-x*np.cos(angle)+y*np.sin(angle)],
                    [np.sin(angle), np.cos(angle),  y-x*np.sin(angle)-y*np.cos(angle)],
                    [0,             0,              1]])
 
    tmp_pt1_1 = np.array([[pt1_1[0]], [pt1_1[1]], [1]])
    tmp_pt1_2 = np.dot(t, tmp_pt1_1)
    pt1_2 = (int(tmp_pt1_2[0][0]), int(tmp_pt1_2[1][0]))
 
    tmp_pt2_1 = np.array([[pt2_1[0]], [pt2_1[1]], [1]])
    tmp_pt2_2 = np.dot(t, tmp_pt2_1)
    pt2_2 = (int(tmp_pt2_2[0][0]), int(tmp_pt2_2[1][0]))
 
    tmp_pt3_1 = np.array([[pt3_1[0]], [pt3_1[1]], [1]])
    tmp_pt3_2 = np.dot(t, tmp_pt3_1)
    pt3_2 = (int(tmp_pt3_2[0][0]), int(tmp_pt3_2[1][0]))
 
    tmp_pt4_1 = np.array([[pt4_1[0]], [pt4_1[1]], [1]])
    tmp_pt4_2 = np.dot(t, tmp_pt4_1)
    pt4_2 = (int(tmp_pt4_2[0][0]), int(tmp_pt4_2[1][0]))
 
    points = np.array([pt1_2, pt2_2, pt3_2, pt4_2])

    return points
 

def non_max_suppression(boxes, probs=None, angles=None, overlapThresh=0.3):
    # if there are no boxes, return an empty list
    if len(boxes) == 0:
        return [], []

    # if the bounding boxes are integers, convert them to floats -- this
    # is important since we'll be doing a bunch of divisions
    if boxes.dtype.kind == "i":
        boxes = boxes.astype("float")

    # initialize the list of picked indexes
    pick = []

    # grab the coordinates of the bounding boxes
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    # compute the area of the bounding boxes and grab the indexes to sort
    # (in the case that no probabilities are provided, simply sort on the bottom-left y-coordinate)
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = y2

    # if probabilities are provided, sort on them instead
    if probs is not None:
        idxs = probs

    # sort the indexes
    idxs = np.argsort(idxs)

    # keep looping while some indexes still remain in the indexes list
    while len(idxs) > 0:
        # grab the last index in the indexes list and add the index value to the list of picked indexes
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)

        # find the largest (x, y) coordinates for the start of the bounding box and the smallest (x, y) coordinates for the end of the bounding box
        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])

        # compute the width and height of the bounding box
        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)

        # compute the ratio of overlap
        overlap = (w * h) / area[idxs[:last]]

        # delete all indexes from the index list that have overlap greater than the provided overlap threshold
        idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlapThresh)[0])))

    # return only the bounding boxes that were picked
    return boxes[pick].astype("int"), angles[pick]


def decode_predictions(scores, geometry1, geometry2):
    
    # grab the number of rows and columns from the scores volume, then
    # initialize our set of bounding box rectangles and corresponding
    # confidence scores
    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []
    angles = []

    # loop over the number of rows
    for y in range(0, numRows):
        # extract the scores (probabilities), followed by the
        # geometrical data used to derive potential bounding box
        # coordinates that surround text
        scoresData = scores[0, 0, y]
        xData0 = geometry1[0, 0, y]
        xData1 = geometry1[0, 1, y]
        xData2 = geometry1[0, 2, y]
        xData3 = geometry1[0, 3, y]
        anglesData = geometry2[0, 0, y]
        
        # loop over the number of columns
        for x in range(0, numCols):
            # if our score does not have sufficient probability,
            # ignore it
            if scoresData[x] < args["min_confidence"]:
                continue

            # compute the offset factor as our resulting feature
            # maps will be 4x smaller than the input image
            (offsetX, offsetY) = (x * 4.0, y * 4.0)

            # extract the rotation angle for the prediction and
            # then compute the sin and cosine
            angle = anglesData[x]
            cos = np.cos(angle)
            sin = np.sin(angle)

            # use the geometry volume to derive the width and height
            # of the bounding box
            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]

            # compute both the starting and ending (x, y)-coordinates
            # for the text prediction bounding box
            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)

            # add the bounding box coordinates and probability score
            # to our respective lists
            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])
            angles.append(angle)

	# return a tuple of the bounding boxes and associated confidences
    return (rects, confidences, angles)

#preprocess OCR input
def preprocess_input(image):
        '''
        Before feeding the data into the model for inference,
        you might have to preprocess it. This function is where you can do that.
        '''
        
        #make sure the image shape is not 0 before preprocessing
        if image.shape[0] == 0 or image.shape[1] == 0 or image.shape[2] == 0:
            pass
        #log.info("Preprocessing input...")
        #n, c, h, w = input_shape
        
        else:
            n, c, h, w = input_shape
            grayimg = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            img = cv2.resize(grayimg, (w, h))
            #img = img.transpose((2,0,1))
            img = img.reshape((n, c, h, w))
        
            return img

#predict info for OCR
def predict(image):
        '''
            This method is meant for running predictions on the input image.
        '''
        #log.info("Inference...")
        #print(image.shape)
        input_image = preprocess_input(image)

        input_dict = {input_blob_rec: input_image}

        outputs = exec_net_rec.infer(input_dict) #this is (TXBXC)
        #need to evaluate and return decoded text

        #outputs = ctc_decoder(res['shadow/LSTMLayers/transpose_time_major'])
        #outputs = exec_net_rec.requests[0].output_blobs[output_blob_rec]
        #print(outputs['shadow/LSTMLayers/transpose_time_major'].shape)

        return outputs
    
#decoder and output processing for OCR
def greedy_decoder(data):
	# index for largest probability each row
    return [np.argmax(s) for s in data]
    
def preprocess_output(outputs):
    #print(len(outputs['shadow/LSTMLayers/transpose_time_major']))
    result = ctc_decoder(outputs['shadow/LSTMLayers/transpose_time_major'])
    
    #mat = outputs['shadow/LSTMLayers/transpose_time_major']
    #classes = "0123456789abcdefghijklmnopqrstuvwxyz#"
    
    #try beamsearch
    #kPadSymbol = '#'
    
    #text = ctcBeamSearch(mat, classes, None)
    
    if result:
        #if d.check(str(text)) == True:
        #    cv2.putText(orig, text, (startX, startY - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        #    print(text)
        cv2.putText(orig, result, (startX, startY - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        print(result)
        
        #tts_start = time.time()
        
        
        if result and pygame.mixer.music.get_busy() == False:
                # and pygame.mixer.music.get_busy() == False
            name = str(result)+'.mp3'
                #pygame.mixer.init()
            if not os.path.isfile(name):
                tts = gTTS(text=str(result), lang='en')
                tts.save(name)
            pygame.mixer.music.load(name)
            pygame.mixer.music.play()
            
            
            #tts_stop = time.time()
            #print('TTS TIME:', tts_stop-tts_start)
                

def ctc_decoder(data):
    
        symbols = "0123456789abcdefghijklmnopqrstuvwxyz#"
        result = ""
        prev_pad = False
        num_classes = len(symbols)
        for i in range(data.shape[0]):
            symbol = symbols[np.argmax(data[i])]
            if symbol != symbols[-1]:
                if len(result) == 0 or prev_pad or (len(result) > 0 and symbol != result[-1]):
                    prev_pad = False
                    result = result + symbol
            else:
                prev_pad = True
        return result    
    
    
    
    

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-east", "--east", type=str, default="/home/pi/Downloads/frozen_east_text_detection.xml", help="path to input EAST text detector")

ap.add_argument("-rec", "--rec", type=str, default="/home/pi/Downloads/text-recognition-0012.xml", help="path to input text recognition model")

ap.add_argument("-v", "--video", type=str, default="/dev/video0", help="path to optinal input video file")
ap.add_argument("-c", "--min-confidence", type=float, default=0.7, help="minimum probability required to inspect a region")
ap.add_argument("-w", "--width", type=int, default=256,	help="resized image width (should be multiple of 32)")
ap.add_argument("-e", "--height", type=int, default=256, help="resized image height (should be multiple of 32)")
ap.add_argument("-cw", "--camera_width", type=int, default=640, help='USB Camera resolution (width). (Default=640)')
ap.add_argument("-ch", "--camera_height", type=int, default=480, help='USB Camera resolution (height). (Default=480)')
ap.add_argument('--device', type=str, default='MYRIAD', help='Specify the target device to infer on; CPU, GPU, FPGA or MYRIAD is acceptable. \
                                                           Sample will look for a suitable plugin for device specified (CPU by default)')
#initiate pygame for TTS
pygame.mixer.init()

#Wake word script initialization.



#handle = pvporcupine.create(keywords=['computer', 'terminator'])

args = vars(ap.parse_args())

# initialize the original frame dimensions, new frame dimensions,
# and ratio between the dimensions
(W, H) = (None, None)
(newW, newH) = (args["width"], args["height"])
(rW, rH) = (None, None)

mean = np.array([123.68, 116.779, 103.939][::-1], dtype="float16")

# define the two output layer names for the EAST detector model that
# we are interested -- the first is the output probabilities and the
# second can be used to derive the bounding box coordinates of text

# load the pre-trained EAST text detector
print("[INFO] loading EAST text detector...")
model_xml = args["east"]
model_bin = os.path.splitext(model_xml)[0] + ".bin"

ie = IECore()


net = ie.read_network(model_xml, model_bin)

input_info = net.input_info
input_blob = next(iter(input_info))


exec_net = ie.load_network(network=net, device_name=args["device"])

print("INFO: loading OCR model....")
model_rec_xml = args["rec"]
model_rec_bin = os.path.splitext(model_rec_xml)[0] + ".bin"
#reads network from .xml and .bin formats


net_rec= ie.read_network(model_rec_xml, model_rec_bin)



exec_net_rec = ie.load_network(network=net_rec, device_name=args["device"]) #loaded network



input_blob_rec = next(iter(net_rec.input_info)) #input name
input_shape = net_rec.input_info[input_blob_rec].input_data.shape #input shape
output_blob_rec = next(iter(net_rec.outputs)) #output name
output_shape = net_rec.outputs[output_blob_rec].shape #output shape

#WAKEUP KEY INITIALIZED


# if a video path was not supplied, grab the reference to the web cam
if not args.get("video", False):
    print("[INFO] starting video stream...")
    vs = VideoStream(src=0).start()
    time.sleep(1.0)

    # otherwise, grab a reference to the video file
else:
    vs = cv2.VideoCapture(args["video"])

    # start the FPS throughput estimator
fps = FPS().start()

    # loop over frames from the video stream

#initialize the thing

#recognize = os.system("python3 rhino_demo_mic.py --context_path /home/pi/Downloads/Starting_Now_en_raspberry-pi_2021-04-23-utc_v1_6_0.rhn")
#print('RETURNING',recognize)

#recognize = subprocess.Popen(['python3','porcupine_demo_mic.py','--keywords','computer'])
#recognize = os.system("python3 porcupine_demo_mic.py --keywords computer")
#if recognize is not None:
#if recognize == 'BeginInference':
#    signal.SIGINT
    
    #trigger second step wake up word
    #ocr = os.system("python3 porcupine_demo_mic.py --keywords terminator")
    #if ocr is not None:
    #recognize.terminate()

    
#while True:
    
    #ocr = os.system("python3 rhino_demo_mic.py --context_path /home/pi/Downloads/Starting_Now_en_raspberry-pi_2021-04-23-utc_v1_6_0.rhn")
porcupine = None
pa = None
audio_stream = None

try:
    porcupine = pvporcupine.create(keywords=["computer"])

    pa = pyaudio.PyAudio()

    audio_stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length)
    
    print('LISTENING FOR READ WORD')

    while True:
        
        pcm = audio_stream.read(porcupine.frame_length)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

        keyword_index = porcupine.process(pcm)
        
        
        if keyword_index >= 0:
            
            print("reading.....")

            t1 = time.perf_counter()
            count = 0
            while count < 10:

            # grab the current frame, then handle if we are using a
            # VideoStream or VideoCapture object
            
            #detection_time_start = time.time()
            
            
                frame = vs.read()
                frame = frame[1] if args.get("video", False) else frame

                # check to see if we have reached the end of the stream
                if frame is None:
                    break

                # resize the frame, maintaining the aspect ratio
                frame = imutils.resize(frame, width=args["camera_width"])
                orig = frame.copy()

                # if our frame dimensions are None, we still need to compute the
                # ratio of old frame dimensions to new frame dimensions
                if W is None or H is None:
                    (H, W) = frame.shape[:2]
                    rW = W / float(newW)
                    rH = H / float(newH)

                # resize the frame, this time ignoring aspect ratio
                frame = cv2.resize(frame, (newW, newH))

                # construct a blob from the frame and then perform a forward pass
                # of the model to obtain the two output layer sets
                frame = frame.astype(np.float32)
                frame -= mean
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.expand_dims(frame, axis=0)
                frame = np.transpose(frame, [0, 3, 1, 2])
                predictions = exec_net.infer(inputs={input_blob: frame})
                scores = predictions['feature_fusion/Conv_7/Sigmoid']
                geometry1 = predictions['feature_fusion/mul_6']
                geometry2 = predictions['feature_fusion/sub/Fused_Add_']

                # decode the predictions, then  apply non-maxima suppression to
                # suppress weak, overlapping bounding boxes
                (rects, confidences, angles) = decode_predictions(scores, geometry1, geometry2)
                boxes, angles = non_max_suppression(np.array(rects), probs=confidences, angles=np.array(angles))

                # loop over the bounding boxes
                for ((startX, startY, endX, endY), angle) in zip(boxes, angles):
                    # scale the bounding box coordinates based on the respective ratios
                    startX = int(startX * rW)
                    startY = int(startY * rH)
                    endX = int(endX * rW)
                    endY = int(endY * rH)

                    # draw the bounding box on the frame
                    width   = abs(endX - startX)
                    height  = abs(endY - startY)
                    centerX = int(startX + width / 2)
                    centerY = int(startY + height / 2)

                    rotatedRect = ((centerX, centerY), ((endX - startX), (endY - startY)), -angle)
                    points = rotated_Rectangle(orig, rotatedRect, color=(0, 255, 0), thickness=2)
                    cv2.polylines(orig, [points], isClosed=True, color=(0, 255, 0), thickness=2, lineType=cv2.LINE_8, shift=0)
                    cv2.putText(orig, fpsstr, (args["camera_width"]-170,15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (38,0,255), 1, cv2.LINE_AA)
                    
                    #detection_time_stop = time.time()
                    #print('DETECTION TIME:', detection_time_stop - detection_time_start)
                    
                    ###################################################################################################
                    #OCR
                    ###################################################################################################
                    
                    #get ROI image
                    roi = orig[startY:endY, startX:endX]
                    
                    #ocr = os.system("python3 porcupine_demo_mic.py --keywords computer")
                    #    if ocr is not None:
                    #ocr = os.system("python3 porcupine_demo_mic.py --keywords terminator")
                    
                    #if ocr is not None:
                    #preprocess and prepares output
                    #only do OCR if theres text detected?????
                    
                        #ocr.terminate()
                    outputs = predict(roi)
                    
                    preprocess_output(outputs)
                    
                count += 1
                    
                
                cv2.imshow("Text Detection", orig)
                if cv2.waitKey(1)&0xFF == ord('q'):
                    signal.SIGINT
                    break
                print(count)
                
                
                
               
                
                
                fps.update()
                """
                # FPS calculation 
                framecount += 1
                if framecount >= 10:
                    fpsstr = "(Playback) {:.1f} FPS".format(time1/10)
                    framecount = 0
                    time1 = 0
                t2 = time.perf_counter()
                elapsedTime = t2-t1
                time1 += 1/elapsedTime
                """


except KeyboardInterrupt:
    print('stopping...')
    

finally:
    if porcupine is not None:
        porcupine.delete()

    if audio_stream is not None:
        audio_stream.close()

    if pa is not None:
        pa.terminate()
        
        #quit()
            
            

# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# if we are using a webcam, release the pointer
if not args.get("video", False):
    vs.stop()

# otherwise, release the file pointer
else:
    vs.release()

# close all windows
cv2.destroyAllWindows()


test = os.listdir("/home/pi")
for item in test:
    if item.endswith(".mp3"):
        os.remove(item)


#if __name__ == '__main__':
#    sys.exit(0)