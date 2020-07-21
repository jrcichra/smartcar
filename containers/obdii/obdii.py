#!/usr/bin/python3
import obd
import karmen
import logging
from common import isCI
import threading
import time
import glob
import os


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d:LINE %(lineno)d:TID %(thread)d:%(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

list_of_files = glob.glob('/dev/pts/*')
latest_file = max(list_of_files, key=os.path.getctime)
logging.info("Selected {} as the most likely pts for OBDII".format(latest_file))
connection = obd.OBD(latest_file)
stop_thread = False


def collect_obdii_data(params):
    global connection
    global stop_thread
    fields = [obd.commands.SPEED, obd.commands.RPM, obd.commands.THROTTLE_POS]
    while not stop_thread:
        with open("/obdii/obdii.log", "a") as f:
            output = ""
            # first field is always an epoch
            epoch = int(time.time())
            output += "{},".format(epoch)
            for field in fields:
                cmd = field
                response = connection.query(cmd)
                # Conversion checks
                if field == obd.commands.SPEED:
                    # convert to mph
                    val = response.value.to("mph").magnitude
                else:
                    # keep as is
                    val = str(response.value.magnitude)
                output += "{}".format(val)
                # if it's the last field don't put a comma
                if field != fields[-1]:
                    output += ','
            output += '\n'
            # only call file write once
            f.write(output)
        time.sleep(1)


def start_obdii(params, result):
    obd_thread = threading.Thread(target=collect_obdii_data, args=(params,))
    obd_thread.start()
    result.Pass()


def stop_obdii(params, result):
    global stop_thread
    stop_thread = True
    result.Pass()


## Main ##
logging.info("Starting the karmen client")
# Use the library to abstract the difficulty
k = karmen.Client()

# Register ourselves and what we provide to the environment
k.registerContainer()

k.registerAction("start_obdii", start_obdii)
k.registerAction("stop_obdii", stop_obdii)

while True:
    time.sleep(10)
