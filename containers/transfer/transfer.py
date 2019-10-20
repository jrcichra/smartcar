import smartcarsocket
import threading
import queue
import logging
import time
import os
import yaml
import glob
import json
import subprocess

# because we're in a container we can do this :)
RECORDING_PATH = '/recordings/'


def isCI():
    return os.uname()[4] != 'armv7l'


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d:LINE %(lineno)d:TID %(thread)d:%(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
# Does an action based on the message we get. The calls needed are made by the container coder


def sendResponse(msg, sc):
    # Craft a response with the actionResponse object
    response = sc.newActionResponse(msg['data']['name'])
    response.setEventID(msg['event_id'])
    response.setMessage("OK")
    response.setStatus(0)
    sc.sendall(response)


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


def transfer_all_footage(msg, sc):
    ping_attempts = 0
    PING_SLEEP = 10
    MAX_PINGS = 3
    while os.system("ping " + HOSTNAME + " -c 1") != 0 and ping_attempts < MAX_PINGS:
        time.sleep(PING_SLEEP)
        ping_attempts += 1
    if ping_attempts >= MAX_PINGS:
        logging.warn(
            "We did not find the host specified. Keeping the files on the local system.")
    else:
        logging.info("We found the host")

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
                    local_size = os.path.getsize(video)
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
    sendResponse(msg, sc)


def kick_off_conversion(msg, sc):
    # Let's kick off the job on the host to start converting
    if os.system("ssh -o 'StrictHostKeyChecking=no' " + USERNAME + "@" + HOSTNAME + ' nohup bash -c "' + PATH + '/../convert.sh >> ' + PATH + '/../convert.log 2>&1 &"') != 0:
        logging.info("Could not kick off the h264->mp4 job on the backend")
    else:
        logging.info("Successfully kicked off the job")
    sendResponse(msg, sc)

# Ideally we could get this into the library and not put it on the user? Not sure


def getActions(sc, temp):
    while True:
        msg = sc.getQueue().get()
        if msg['type'] == "trigger-action":
            # Trigger the action
            logging.debug("We got a trigger-action to do " +
                          msg['data']['name'])
            if msg['data']['name'] == 'transfer_all_footage':
                a = threading.Thread(
                    target=transfer_all_footage, args=(msg, sc))
                a.start()
            elif msg['data']['name'] == 'kick_off_conversion':
                a = threading.Thread(
                    target=kick_off_conversion, args=(msg, sc))
                a.start()
            else:
                logging.warning(
                    "Got a trigger-action that I don't understand: printing for debugging:")
                logging.warning(msg)
        else:
            logging.warning(
                "Got a packet response that wasn't what we expected, the library should handle this:")
            logging.info(msg)

#MAIN#


# Parse our settings
with open('/settings.yml', 'r') as f:
    y = yaml.safe_load(f)
    try:
        settings = y['transfer']
    except Exception as e:
        logging.warn("No settings found for the transfer container")

try:
    HOSTNAME = settings['hostname']
except KeyError as e:
    HOSTNAME = ""
    logging.warn("Did not find a hostname in the settings, ignoring transfers")

try:
    USERNAME = settings['username']
except KeyError as e:
    USERNAME = ""
    logging.warn(
        "Did not find a username in the settings, ignoring transfers " +
        "(we're in a container, I don't know your username outside this)")
try:
    PASSWORD = settings['password']
except KeyError as e:
    PASSWORD = ""
    logging.warn(
        "Did not find a password in the settings, if you haven't set up ssh keys somehow, things might not work")

try:
    METHOD = settings['method']
except KeyError as e:
    METHOD = "ssh"
    logging.warn("Did not find a method in the settings, defaulting to ssh")

try:
    PATH = settings['path']
except KeyError as e:
    PATH = ""
    logging.warn("Did not find a path in the settings, ignoring transfers")
try:
    FRAMERATE = y['dashcam']['fps']
except KeyError as e:
    FRAMERATE = 10
    logging.warn(
        "Transfer needs to know the framerate of the dashcam, didn't find one, defaulting to " + FRAMERATE)

# Use the library to abstract the difficulty
sc = smartcarsocket.smartcarsocket()

# Register ourselves and what we provide to the environment
sc.registerContainer()

sc.registerAction("transfer_all_footage")
sc.registerAction("kick_off_conversion")

# Handle incoming action requests
t = threading.Thread(target=getActions, args=(sc, True))
t.start()

t.join()
