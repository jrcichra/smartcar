import smartcarsocket
import threading
import queue
import logging
import time
import os
if os.uname()[4] == 'armv7l':
    import picamera

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d:LINE %(lineno)d:TID %(thread)d:%(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
# Does an action based on the message we get. The calls needed are made by the container coder


def performAction(msg, sc):
    logging.debug("I got an action:")
    logging.debug(msg)
    # Act like we have some work to do for this
    time.sleep(5)
    # Craft a response with the actionResponse object
    response = sc.newActionResponse(msg['data']['name'])
    response.setEventID(msg['event_id'])
    response.setMessage("OK")
    response.setStatus(0)
    sc.sendall(response)


# Ideally we could get this into the library and not put it on the user? Not sure
def getActions(sc, temp):
    while True:
        msg = sc.getQueue().get()
        if msg['type'] == "trigger-action":
            # Trigger the action
            logging.debug("We got a trigger-action to do " +
                          msg['data']['name'])
            a = threading.Thread(target=performAction, args=(msg, sc))
            a.start()
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
