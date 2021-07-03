import karmen
import threading
import queue
import logging
import time
import os
import datetime
import socket
from common import isCI

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d:LINE %(lineno)d:TID %(thread)d:%(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


def execute(params, result):

    # hopefully we get the docker network we're on and we want to talk to the host
    hostname_array = socket.gethostbyname(socket.gethostname()).split('.')
    hostname_array[3] = '1'
    hostname = '.'.join(hostname_array)

    command = params['command']
    username = params['username']
    password = params['password']

    logging.info(f"About to execute {command} on {hostname} as {username}")
    if os.system(f"sshpass -p {password} ssh -o 'StrictHostKeyChecking=no' {username}@{hostname} {command}") == 0:
        result.Pass()
    else:
        result.Fail()

###MAIN###


# Use the library to abstract the difficulty
k = karmen.Client()

# Register ourselves and what we provide to the environment
k.registerContainer()

k.registerAction("execute", execute)

while True:
    time.sleep(10)
