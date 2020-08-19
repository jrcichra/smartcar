import karmen
import threading
import queue
import logging
import time
import os
import signal
from common import isCI

if not isCI():
    import RPi.GPIO as GPIO

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d:LINE %(lineno)d:TID %(thread)d:%(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
# Does an action based on the message we get. The calls needed are made by the container coder

GREEN_LED = 5           # PIN 29 turn on green light on feather latchable relay board
# PIN 31 used to unlatch the power relay (on feather board)
UNLATCH = 6
#                The relay was latched with 12v power from 'key'
KEY_OFF = 13             # PIN 33 used to see if the key is off
KEY_ON = 19              # PIN 35 used to see if the key is on


def power_off(params, result):
    # For now, I'm going to have it so the power_off function only works when the key is actually off
    # if we run this code and find that the car is actually back on, we'll emit a key_on
    if is_off():
        # Okay, the key is off, we want to pull the relay
        logging.info("Shutting down the system in a few seconds...")
        # first, sync the filesystem (output before sync so things are more likely to be saved)
        os.system("sync")
        # sleep a little
        time.sleep(3)
        # unlatch
        if not isCI():
            GPIO.output(UNLATCH, True)
            # we shouldn't get here unless the unlatch is broken
            time.sleep(5)
            logging.error("We tried to shut off the car but it didn't work!!!")
        else:
            logging.info(
                "This is where the car would be shut down, but we're in a CI environment")
    else:
        # The key isn't off? let the logs know
        logging.error("Not shutting off the car because the key isn't off?")
    if result != None:
        result.Pass()

# Double check the key actually went off


def is_off():
    if not isCI():
        return GPIO.input(KEY_OFF) and not GPIO.input(KEY_ON)
    else:
        return True

##print pins##


def print_pins():
    if not isCI():
        try:
            logging.info("##############################")
            logging.info("KEY_OFF (PIN 33)="+str(GPIO.input(KEY_OFF)))
            logging.info("KEY_ON (PIN 35)="+str(GPIO.input(KEY_ON)))
            logging.info("##############################")
        except Exception as e:
            logging.error(e)


def pretend_key_off(signalNumer, frame):
    logging.info("Pretending the key went off")
    k.emitEvent("key_off")


def poll_key_state():
    # Start the previous state assuming the key was on
    was_off = False
    while True:
        # Say the key is now off if it's off now but wasn't before
        if is_off() and not was_off:
            k.emitEvent("key_off")
            was_off = not was_off
        # Say the key is now on if it's on now but wasn't before
        if not is_off() and was_off:
            k.emitEvent("key_on")
            was_off = not was_off
        # Sleep in between checks
        time.sleep(5)


def gpio_setup():
    if not isCI():
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
        # Set up output pins
        GPIO.setup(GREEN_LED, GPIO.OUT)
        GPIO.setup(UNLATCH, GPIO.OUT)
        # Set up input pins
        # Used to check if ignition is on
        GPIO.setup(KEY_OFF, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Used to check if ignition is onclear
        GPIO.setup(KEY_ON,  GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Start a polling thread that will say if the key is on or off on a state change
        t = threading.Thread(target=poll_key_state)
        t.start()
    else:
        logging.info(
            "We're in the CI, no GPIO setup. Sleeping for 10 seconds, and then pretending the key went off.")
        time.sleep(10)
        k.emitEvent("key_off")


###MAIN###
logging.info("Starting the karmen client")
# Use the library to abstract the difficulty
k = karmen.Client()

# Register ourselves and what we provide to the environment
k.registerContainer()

k.registerEvent("key_on")
k.registerEvent("key_off")
k.registerAction("power_off", power_off)

# For debugging, a USR1 signal simulates a keyOff (software-wise)
signal.signal(signal.SIGUSR1, pretend_key_off)

# If this code is running, the key must be on, so we'll force a key_on event
# Change if your pi doesn't start with the car.
k.emitEvent("key_on")

# Set up the GPIO pins if we're not in CI
gpio_setup()

while True:
    signal.pause()
# os._exit(0)
