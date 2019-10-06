import smartcarsocket
import threading
import queue
import logging
import time
import os

def isCI():
    return os.uname()[4] != 'armv7l'

if not isCI():
    import RPi.GPIO as GPIO

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d:LINE %(lineno)d:TID %(thread)d:%(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
# Does an action based on the message we get. The calls needed are made by the container coder

GREEN_LED = 5           # PIN 29 turn on green light on feather latchable relay board
UNLATCH = 6             # PIN 31 used to unlatch the power relay (on feather board)
                         #                The relay was latched with 12v power from 'key'
KEY_OFF = 13             # PIN 33 used to see if the key is off
KEY_ON = 19              # PIN 35 used to see if the key is on



def sendResponse(msg, sc):
    # Craft a response with the actionResponse object
    response = sc.newActionResponse(msg['data']['name'])
    response.setEventID(msg['event_id'])
    response.setMessage("OK")
    response.setStatus(0)
    sc.sendall(response)

def power_off(msg, sc):
    # For now, I'm going to have it so the power_off function only works when the key is actually off
    # if we run this code and find that the car is actually back on, we'll emit a key_on
    if is_off():
        # Okay, the key is off, we want to pull the relay
        # first, sync the filesystem
        os.system("sync")
        # sleep a little
        time.sleep(3)
        # unlatch
        if not isCI():
            GPIO.output(UNLATCH,True)
            # we shouldn't get here unless the unlatch is broken
            time.sleep(5)
            logging.error("We tried to shut off the car but it didn't work!!!")
        else:
            logging.info("This is where the car would be shut down, but we're in a CI environment")
    else:
        # The key isn't off? let the logs know
        logging.error("Not shutting off the car because the key isn't off?")
    # no matter what, send a response
    sendResponse(msg,sc)


# Ideally we could get this into the library and not put it on the user? Not sure
def getActions(sc, temp):
    while True:
        msg = sc.getQueue().get()
        if msg['type'] == "trigger-action":
            # Trigger the action
            logging.debug("We got a trigger-action to do " +
                          msg['data']['name'])
            if msg['data']['name'] == 'power_off':
                a = threading.Thread(target=power_off, args=(msg, sc))
                a.start()
            else:
                logging.warning("Got a trigger-action that I don't understand: printing for debugging:")
                logging.warning(msg)
        else:
            logging.warning(
                "Got a packet response that wasn't what we expected, the library should handle this:")
            logging.info(msg)

# Double check the key actually went off
def is_off():
  return GPIO.input(KEY_OFF) and not GPIO.input(KEY_ON)

##print pins##
def print_pins():
  global KEY_OFF
  global KEY_ON
  
  logging.info("##############################")
  logging.info("KEY_OFF (PIN 33)="+str(GPIO.input(KEY_OFF)))
  logging.info("KEY_ON (PIN 35)="+str(GPIO.input(KEY_ON)))
  logging.info("##############################")

def key_went_off(self):
    logging.info("We got a change in key state...")
    time.sleep(2)
    print_pins()

    if is_off():
        logging.info("Yes, the key did in fact go off.")
        # We emit the event
        sc.emitEvent("key_off")
    else:
        #In some situations, we might want to send "key_on" here. Not doing this yet
        logging.info("False alarm, or the owner turned the key back on within the timeout.")

def gpio_setup():
    if not isCI():
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
        # Set up output pins
        GPIO.setup(GREEN_LED, GPIO.OUT)
        GPIO.setup(UNLATCH, GPIO.OUT)
        # Set up input pins
        GPIO.setup(KEY_OFF, GPIO.IN,pull_up_down=GPIO.PUD_UP)  #Used to check if ignition is on
        #event handling for when KEY_OFF is triggered
        GPIO.add_event_detect(KEY_OFF, GPIO.RISING, callback=key_went_off, bouncetime=500)
        GPIO.setup(KEY_ON,  GPIO.IN,pull_up_down=GPIO.PUD_UP)  #Used to check if ignition is onclear
    else:
        logging.info("We're in the CI, no GPIO setup. Sleeping for 10 seconds, and then pretending the key went off.")
        time.sleep(10)
        key_went_off(None)


#MAIN#

# Use the library to abstract the difficulty
sc = smartcarsocket.smartcarsocket()

# Register ourselves and what we provide to the environment
sc.registerContainer()

sc.registerContainer()
sc.registerEvent("key_on")
sc.registerEvent("key_off")
sc.registerAction("power_off")

# Handle incoming action requests
t = threading.Thread(target=getActions, args=(sc, True))
t.start()

# If this code is running, the key must be on, so we'll force a key_on event
# Change if your pi doesn't start with the car.
sc.emitEvent("key_on")

# Set up the GPIO pins if we're not in travis
gpio_setup()


t.join()
