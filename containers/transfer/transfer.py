from common import isCI, secondsTillMidnight
import smartcarclient
import threading
import queue
import logging
import time
import os
import glob
import json
import subprocess

# because we're in a container we can do this :)
RECORDING_PATH = '/recordings/'


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d:LINE %(lineno)d:TID %(thread)d:%(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


def system(s):
    try:
        outp = subprocess.check_output(
            [s], stderr=subprocess.STDOUT, shell=True)
        print(outp)
        return 0
    except subprocess.CalledProcessError as e:
        print(str(e.output))
        print(str(e.cmd))
        print(e)
        return e.returncode


def transfer_all_footage(params, result):
    ping_attempts = 0
    PING_SLEEP = 10
    MAX_PINGS = 3
    HOSTNAME = params.get('hostname', 'nas')
    USERNAME = params.get('username', 'root')
    PASSWORD = params.get('password', 'root')
    PATH = params.get('path', '/recordings')
    METHOD = params.get('method', 'ssh')
    FRAMERATE = params.get('framerate', 10)

    while os.system("ping " + HOSTNAME + " -c 1") != 0 and ping_attempts < MAX_PINGS:
        time.sleep(PING_SLEEP)
        ping_attempts += 1
    if ping_attempts >= MAX_PINGS:
        logging.warning(
            "We did not find the host specified. Keeping the files on the local system.")
    else:
        logging.info("We found the host")
        os.system("iwconfig")
        os.system("ifconfig")
        # first do the ssh key
        if os.system("ssh-keygen -f $HOME/.ssh/id_rsa -t rsa -N ''") != 0:
            logging.error("Something went wrong generating an ssh key")
        else:
            logging.info("We generated an ssh key")
        if os.system('sshpass -p ' + PASSWORD +
                     " ssh-copy-id -o StrictHostKeyChecking=no " + USERNAME + "@" + HOSTNAME) != 0:
            logging.error("Something went wrong with sshpass")
        else:
            logging.info("We authenticated you through ssh")

        logging.info("Going through all h264 files and transfering them")
        videos = glob.glob(RECORDING_PATH + "*.h264")
        for video in videos:
            # loop through every video
            if METHOD == "ssh":
                if os.system("scp -o 'StrictHostKeyChecking=no' -p " + video + " " + USERNAME + "@" + HOSTNAME + ":" + PATH) != 0:
                    logging.error(
                        "Something went wrong with the transfer for " + video + ", keeping file where it is")
                else:
                    logging.info("Copy was successful for " + video + ".")
                    # local_size = os.path.getsize(video)
                    os.remove(video)
                    j = {}
                    j['framerate'] = FRAMERATE
                    vname = video.rsplit('/', 1)[1]
                    if os.system("ssh -o 'StrictHostKeyChecking=no' " + USERNAME + "@" + HOSTNAME + " echo '" + json.dumps(j).replace(
                            '"', '\\"') + " > " + PATH + "/.convert/" + vname.rsplit('.', 1)[0] + '.json' + "'") != 0:
                        logging.info(
                            "We couldn't place the JSON file...note the video might not be converted to mp4 now...")
                    else:
                        logging.info(
                            "Successfully placed JSON file for " + video)
            else:
                logging.error(
                    "The only method supported right now is ssh. nfs might come in a later version...")
        # end for
        logging.info(
            "Finished processing all recordings. If all went well, there should be no files left")
    result.Pass()


def start_conversion(params, result):
    HOSTNAME = params.get('hostname', 'nas')
    USERNAME = params.get('username', 'root')
    PATH = params.get('path', '/recordings')
    DEVELOP = params.get('develop', False)
    # Let's kick off the job on the host to start converting
    if os.system("ssh -o 'StrictHostKeyChecking=no' " + USERNAME + "@" + HOSTNAME + ' nohup bash -c "' + PATH + '/../convert.sh >> ' + PATH + '/../convert.log 2>&1 &"') != 0:
        logging.info("Could not kick off the h264->mp4 job on the backend")
    else:
        logging.info("Successfully kicked off the job")
        logging.debug("Checking for develop mode:")
        if DEVELOP:
            s = secondsTillMidnight()
            logging.info(
                "DEVELOP is on - sleeping until midnight ({} seconds from now)".format(s))
            time.sleep(s)
            logging.info("Done sleeping for DEVELOP mode! Continuing...")
    result.Pass()

#MAIN#


# Use the library
sc = smartcarclient.Client()

# Register ourselves and what we provide to the environment
sc.registerContainer()

sc.registerAction("transfer_all_footage", transfer_all_footage)
sc.registerAction("start_conversion", start_conversion)

# Keep the main thread alive
while True:
    time.sleep(10)
