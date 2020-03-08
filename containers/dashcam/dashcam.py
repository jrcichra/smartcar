import karmen
import threading
import queue
import logging
import time
import os
import datetime
from common import isCI

if not isCI():
    import picamera
##get_new_filename##
camera = None


def getserial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo', 'r')
        for line in f:
            if line[0:6] == 'Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"

    return cpuserial


def get_new_filename():
    return "travel__" + datetime.datetime.now().strftime("%Y--%m--%d__%H--%M--%S") + "__" + str(getserial()) + ".h264"


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d:LINE %(lineno)d:TID %(thread)d:%(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


def start_preview(params, result):
    if not isCI():
        logging.info("Starting the preview...")
        try:
            global camera
            camera.start_preview()
            # The preview alpha has to be set after the preview is already active
            camera.preview.alpha = 128
        except Exception as e:
            logging.error(e)
    else:
        logging.info("We're in CI, but we would have started the preview")
    result.Pass()


def stop_preview(params, result):
    if not isCI():
        logging.info("Stopping the preview...")
        try:
            global camera
            camera.stop_preview()
        except Exception as e:
            logging.error(e)
    else:
        logging.info("We're in CI, we would have stopped the preview")
    result.Pass()


def start_recording(params, result):
    logging.info("params for start_recording are: {}".format(params))
    HRES = int(params.get('hres', 1280))
    VRES = int(params.get('vres', 720))
    ROT = int(params.get('rot', 0))
    FRAMERATE = int(params.get('framerate', 10))
    if not isCI():
        logging.info("Starting the recording...")
        # try:
        global camera
        # Do all the camera setup
        camera = picamera.PiCamera()  # the camera object
        camera.resolution = (HRES, VRES)
        # annotations
        camera.annotate_foreground = picamera.Color('white')
        camera.annotate_background = picamera.Color('black')
        camera.annotate_frame_num = True
        camera.annotate_text_size = 48
        camera.annotate_text = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        # set the framerate
        camera.framerate = FRAMERATE
        # set the rotation
        camera.rotation = ROT
        camera.start_recording(
            '/recordings/' + get_new_filename(), sps_timing=True)
        # spawn a thread that handles updating the time/frame counter
        t = threading.Thread(target=update_annotations)
        t.start()
        # except Exception as e:
        # logging.error(e)
    else:
        logging.info(
            "We're in CI, we would have started recording. Instead creating a fake big file")
        f = open('/recordings/' + get_new_filename(), "wb")
        f.seek(1073741824-1)
        f.write(b"\0")
        f.close()
    result.Pass()


def stop_recording(params, result):
    if not isCI():
        logging.info("Stopping the recording...")
        try:
            global camera
            camera.stop_recording()
        except Exception as e:
            logging.error(e)
    else:
        logging.info("We're in CI, we would have stopped recording")
    result.Pass()


def update_annotations():
    global camera
    while True:
        camera.annotate_text = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        time.sleep(.2)


###MAIN###

# Use the library to abstract the difficulty
k = karmen.Client()

# Register ourselves and what we provide to the environment
k.registerContainer()

k.registerAction("start_recording", start_recording)
k.registerAction("stop_recording", stop_recording)

k.registerAction("start_preview", start_preview)
k.registerAction("stop_preview", stop_preview)

while True:
    time.sleep(10)
