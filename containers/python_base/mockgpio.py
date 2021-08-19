# write a GPIO mock class
# import logging

# logging.basicConfig(level=logging.DEBUG,
#                     format='%(asctime)s.%(msecs)d:LINE %(lineno)d:TID %(thread)d:%(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


BCM = True
OUT = None
IN = None
PUD_UP = None
PUD_DOWN = None

GREEN_LED = 5
UNLATCH = 6
KEY_OFF = 13
KEY_ON = 19
pins = {
    UNLATCH: True,
    GREEN_LED: False,
    KEY_ON: True,
    KEY_OFF: False,
}


def output(pin, value):
    # value must be a boolean
    if isinstance(value, bool):
        pins[pin] = value
    else:
        raise TypeError("value must be a boolean")


def input(pin):
    if pin in pins:
        return pins[pin]
    else:
        # default pin value is False
        return False


def setmode(mode):
    pass


def cleanup():
    pass


def setup(pin=None, mode=None, pull_up_down=None):
    pass


def setwarnings(value):
    pass
