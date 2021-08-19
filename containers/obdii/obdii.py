#!/usr/bin/python3
import obd
from karmen.karmen import Karmen
import logging
import threading
import time
import glob
import os


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d:LINE %(lineno)d:TID %(thread)d:%(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

list_of_files = glob.glob('/dev/pts/*')
latest_file = max(list_of_files, key=os.path.getctime)
logging.info(f"Selected {latest_file} as the most likely pts for OBDII")
connection = obd.OBD(latest_file)
stop_thread = False


def collect_obdii_data(params):
    global connection
    global stop_thread
    fields = [obd.commands.SPEED, obd.commands.RPM, obd.commands.THROTTLE_POS]
    # What will be sent over pub
    params = {}
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
                    val = float(response.value.to("mph").magnitude)
                    params['speed'] = str(val)
                elif field == obd.commands.RPM:
                    val = float(response.value.magnitude)
                    params['rpm'] = str(val)
                elif field == obd.commands.THROTTLE_POS:
                    val = float(response.value.magnitude)
                    params['throttle'] = str(val)
                else:
                    # Fallthrough doesn't set a param
                    val = float(response.value.magnitude)
                output += "{}".format(val)
                # if it's the last field don't put a comma
                if field != fields[-1]:
                    output += ','
            output += '\n'
            # only call file write once per collection
            f.write(output)
            # publish the data
            result = k.runEvent("pub", parameters=params)
            if result.result.code != 200:
                logging.error(result.result.message)
        time.sleep(1)


def start_obdii(params, result):
    obd_thread = threading.Thread(target=collect_obdii_data, args=(params,))
    obd_thread.start()
    result.code = 200


def stop_obdii(params, result):
    global stop_thread
    stop_thread = True
    result.code = 200


def p(params, result):
    logging.info("In obdii.p, here's what I got:")
    logging.info(params)
    result.code = 200


## Main ##
logging.info("Starting the karmen client")
k = Karmen(hostname="karmen")

# Actions obdii can perform
k.addAction(start_obdii, "start_obdii")
k.addAction(stop_obdii, "stop_obdii")

# Temporary action
k.addAction(p, "print")

k.register()

while True:
    time.sleep(10)
