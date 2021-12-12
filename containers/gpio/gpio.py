from karmen import Karmen
import threading
import queue
import logging
import time
import os
import signal
from common import isCI

# runtime check if we should mock GPIO
if isCI():
    import mockgpio as GPIO
else:
    import RPi.GPIO as GPIO

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)d:LINE %(lineno)d:TID %(thread)d:%(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
# Does an action based on the message we get. The calls needed are made by the container coder

GREEN_LED = 5  # PIN 29 turn on green light on feather latchable relay board
# PIN 31 used to unlatch the power relay (on feather board)
UNLATCH = 6
#                The relay was latched with 12v power from 'key'
KEY_OFF = 13  # PIN 33 used to see if the key is off
KEY_ON = 19  # PIN 35 used to see if the key is on


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
        GPIO.output(UNLATCH, True)
        # we shouldn't get here unless the unlatch is broken
        time.sleep(5)
        logging.error("We tried to shut off the car but it didn't work!!!")
    else:
        # The key isn't off? let the logs know
        logging.error("Not shutting off the car because the key isn't off?")
    if result != None:
        result.Pass()


# Double check the key actually went off


def is_off():
    return bool(GPIO.input(KEY_OFF)) and not bool(GPIO.input(KEY_ON))


##print pins##


def print_pins():
    try:
        logging.info("##############################")
        logging.info(f"KEY_OFF (PIN 33)={str(GPIO.input(KEY_OFF))}")
        logging.info(f"KEY_ON (PIN 35)={str(GPIO.input(KEY_ON))}")
        logging.info("##############################")
    except Exception as e:
        logging.error(e)


def pretend_key_off(signalNumer, frame):
    logging.info("Pretending the key went off")
    k.runEventAsync("key_off")


def poll_key_state():
    was_off = False
    while True:
        is_off_value = is_off()
        logging.info(f"Polling key state. is_off()={is_off_value}. was_off={was_off}")
        # Say the key is now off if it's off now but wasn't before
        if is_off_value and not was_off:
            k.runEventAsync("key_off")
            was_off = is_off_value
        # Say the key is now on if it's on now but wasn't before
        if not is_off_value and was_off:
            k.runEventAsync("key_on")
            was_off = is_off_value
        # Sleep in between checks
        time.sleep(5)


def gpio_setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(True)
    # Set up output pins
    GPIO.setup(GREEN_LED, GPIO.OUT)
    GPIO.setup(UNLATCH, GPIO.OUT)
    # Set up input pins
    # Used to check if ignition is on
    GPIO.setup(KEY_OFF, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # Used to check if ignition is onclear
    GPIO.setup(KEY_ON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # Start a polling thread that will say if the key is on or off on a state change
    threading.Thread(target=poll_key_state).start()


###MAIN###
logging.info("Starting the karmen client")
# Use the library to abstract the difficulty
k = Karmen(hostname="karmen")
k.addAction(power_off, "power_off")
k.register()

# For debugging, a USR1 signal simulates a keyOff (software-wise)
signal.signal(signal.SIGUSR1, pretend_key_off)

# Set up the GPIO pins if we're not in CI
gpio_setup()

# If this code is running, the key must be on, so we'll force a key_on event
# Change if your pi doesn't start with the car.
while True:
    result = k.runEvent("key_on")
    if result.result.code == k.Pass():
        logging.info("Initial key_on was successful")
        break
    else:
        logging.error(
            "Error occurred when turning the key on. Trying again in a few seconds..."
        )
        time.sleep(5)

# Sit here after key_on is done

while True:
    signal.pause()
