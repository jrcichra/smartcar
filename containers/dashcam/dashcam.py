import smartcarsocket
import threading
import queue
import logging
import time
import os
import datetime

FRAMERATE = 10           # Framerate used
HRES = 1280  # Horizontal pixels
VRES = 720  # Vertical pixels


def isCI():
    return os.uname()[4] != 'armv7l'


camera = None
##get_new_filename##


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


if not isCI():
    # Do all the camera setup, this will probably come from a config file at some point...
    import picamera
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
    camera.rotation = 0
    camera.preview.alpha = 128
    current_filename = get_new_filename()


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d:LINE %(lineno)d:TID %(thread)d:%(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
# Does an action based on the message we get. The calls needed are made by the container coder


def sendResponse(msg, sc):
    # Craft a response with the actionResponse object
    response = sc.newActionResponse(msg['data']['name'])
    response.setEventID(msg['event_id'])
    response.setMessage("OK")
    response.setStatus(0)
    sc.sendall(response)


def start_preview(msg, sc):
    if not isCI():
        try:
            global camera
            camera.start_preview()
        except Exception as e:
            logging.error(e)
    else:
        logging.info("We're in CI, we would have started the preview")
    sendResponse(msg, sc)


def stop_preview(msg, sc):
    if not isCI():
        try:
            global camera
            camera.stop_preview()
        except Exception as e:
            logging.error(e)
    else:
        logging.info("We're in CI, we would have stopped the preview")
    sendResponse(msg, sc)


def start_recording(msg, sc):
    if not isCI():
        try:
            global camera
            camera.start_recording(get_new_filename(), sps_timing=True)
        except Exception as e:
            logging.error(e)
    else:
        logging.info("We're in CI, we would have started recording")
    sendResponse(msg, sc)


def stop_recording(msg, sc):
    if not isCI():
        try:
            global camera
            camera.stop_recording()
        except Exception as e:
            logging.error(e)
    else:
        logging.info("We're in CI, we would have stopped recording")
    sendResponse(msg, sc)

# Ideally we could get this into the library and not put it on the user? Not sure


def getActions(sc, temp):
    while True:
        msg = sc.getQueue().get()
        if msg['type'] == "trigger-action":
            # Trigger the action
            if msg['data']['name'] == 'start_recording':
                a = threading.Thread(target=start_recording, args=(msg, sc))
                a.start()
            elif msg['data']['name'] == 'stop_recording':
                a = threading.Thread(target=stop_recording, args=(msg, sc))
                a.start()
            elif msg['data']['name'] == 'start_preview':
                a = threading.Thread(target=start_preview, args=(msg, sc))
                a.start()
            elif msg['data']['name'] == 'stop_preview':
                a = threading.Thread(target=stop_preview, args=(msg, sc))
                a.start()
            else:
                logging.error("I don't recognize this action:")
                logging.error(msg)
        else:
            logging.warning(
                "Got a packet response that wasn't what we expected, the library should handle this:")
            logging.info(msg)

#MAIN#


# Use the library to abstract the difficulty
sc = smartcarsocket.smartcarsocket()

# Register ourselves and what we provide to the environment
sc.registerContainer()

sc.registerEvent("started_recording")
sc.registerEvent("stopped_recording")

sc.registerEvent("started_preview")
sc.registerEvent("stopped_preview")

sc.registerAction("start_recording")
sc.registerAction("stop_recording")

sc.registerAction("start_preview")
sc.registerAction("stop_preview")

# Handle incoming action requests
t = threading.Thread(target=getActions, args=(sc, True))
t.start()

# Do what you need to do here to emit events. In this case the dashcam is reactive
# So we'll just have the main thread block for the endless getActions...
t.join()
