import smartcarsocket
import threading
import queue
import logging
import time
import os


def isCI():
    return os.uname()[4] != 'armv7l'


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


def transfer_all_footage(msg, sc):
    pass


def kick_off_conversion(msg, sc):
    pass

# Ideally we could get this into the library and not put it on the user? Not sure


def getActions(sc, temp):
    while True:
        msg = sc.getQueue().get()
        if msg['type'] == "trigger-action":
            # Trigger the action
            logging.debug("We got a trigger-action to do " +
                          msg['data']['name'])
            if msg['data']['name'] == 'transfer_all_footage':
                a = threading.Thread(
                    target=transfer_all_footage, args=(msg, sc))
                a.start()
            elif msg['data']['name'] == 'kick_off_conversion':
                a = threading.Thread(
                    target=kick_off_conversion, args=(msg, sc))
                a.start()
            else:
                logging.warning(
                    "Got a trigger-action that I don't understand: printing for debugging:")
                logging.warning(msg)
        else:
            logging.warning(
                "Got a packet response that wasn't what we expected, the library should handle this:")
            logging.info(msg)

#MAIN#


# Use the library to abstract the difficulty
sc = smartcarsocket.smartcarsocket()

# Register ourselves and what we provide to the environment
sc.registerContainer()

sc.registerAction("transfer_all_footage")
sc.registerAction("kick_off_conversion")

# Handle incoming action requests
t = threading.Thread(target=getActions, args=(sc, True))
t.start()

t.join()
