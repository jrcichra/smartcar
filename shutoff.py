#!/usr/bin/python3

import os
import time
import RPi.GPIO as GPIO

# PIN 31 used to unlatch the power relay (on feather board)
UNLATCH = 6

GPIO.setmode(GPIO.BCM)
GPIO.setup(UNLATCH, GPIO.OUT)


def power_off():
    print("Shutting down the system in a few seconds...")
    # first, sync the filesystem (output before sync so things are more likely to be saved)
    os.system("sync")
    # sleep a little
    time.sleep(3)
    # unlatch
    GPIO.output(UNLATCH, True)


power_off()
