import smartcarsocket
import threading
import queue
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d:LINE %(lineno)d:TID %(thread)d:%(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
# Does an action based on the message we get. The calls needed are made by the container coder


def preformAction(msg):
    pass


# Ideally we could get this into the library and not put it on the user? Not sure
def getMessages(in_queue, temp):
    while True:
        msg = in_queue.get()
        if msg['type'] == "trigger-action":
            # Trigger the action
            logging.debug("We got a trigger-action to do " +
                          msg['data']['name'])
            t = threading.Thread(target=preformAction, args=(msg))
            t.start()
        else:
            logging.info("Got a packet response:")
            logging.info(msg)

#MAIN#


# Use the library to abstract the difficulty
sc = smartcarsocket.smartcarsocket()

# Register ourselves and what we provide to the environment
sc.registerContainer()
sc.registerEvent("started_recording")
sc.registerAction("start_recording")

t = threading.Thread(target=getMessages, args=(sc.getQueue(), True))
t.start()
