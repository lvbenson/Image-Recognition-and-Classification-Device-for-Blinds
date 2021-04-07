import pygame
from gtts import gTTS
import os

with open("/home/pi/build/open_model_zoo/demos/python_demos/object_detection_demo_py/det_labels.txt", 'r') as reader:
    result = reader.read()
                
if pygame.mixer.music.get_busy() == False:

    name = str(result)+'.mp3'
    if not os.path.isfile(name):
        tts = gTTS(text=str(result), lang='en')

        tts.save(name)

    #pygame.init()

    pygame.mixer.music.load(str(name))
    pygame.mixer.music.play()


