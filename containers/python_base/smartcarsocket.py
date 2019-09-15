###
# jrcichra 2019
# Object for communicating with the rpi-smartcar system
# Abstracts away the protocol and JSON communication, just deal with the object instead!
###
import socket
import logging
import json
import time
import queue
import threading

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d:%(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

class actionResponse:
    def __init__(self, name):
        self.response = {
        'type': "trigger-action-response",
        'timestamp': time.time(),
        'data': {
            'name': name,
            'message': "unknown",
            'status': -1
            }
        }
    def setMessage(self,msg):
        self.response['data']['message'] = msg
    def setStatus(self,s):
        self.response['data']['status'] = s
    def setEventID(self,eid):
        self.response['event_id'] = eid
    def getDict(self):
        return self.response
class connector:

    def __init__(self, s):
        self.s = s
        self.lock = threading.Lock()            #keeping the send thread safe

    def receive_packet(self, s):
        message = b""  # create an empty binary message buffer
        flag = False  # determines if we found the end or not
        err = False
        while not flag:  # while we haven't found that end \n, depicting the end of an object...
            r = s.recv(1024)  # copy over x bytes into our buffer
            if(b"\n" in r):  # if that buffer has the \n
                flag = True  # set the flag that we found the end
            elif(not r):  # socket dropped on us
                flag = True
                err = True
            message += r  # append it onto our message
        return message, err  # return this byte array, with the \n on the end, in byte form

    def packetize(self, s):
        # encode the string into a byte array and append on the newline character
        return (s + '\n').encode()

    # converts a byte array into a string, removing the ending newline

    def depacketize(self, b):
        # remove that last \n and decode the string back to it's original form
        return b.decode()[:-1]

    def connect(self, host, port):
        try:
            self.s.connect((host, port))
            return 0
        except Exception as e:
            logging.error(e)
            return 1

    def sendall(self, data):
        
        if isinstance(data, dict):
            logging.debug(
                "In sendall(), found a dictionary, converting to JSON before packetizing...")
            with self.lock:
                # Best one liner ever - send a packetsized version of the data after it's been converted
                self.s.sendall(self.packetize(json.dumps(data)))
        elif isinstance(data, str):
            logging.debug(
                "In sendall(), found a string, making sure it's valid JSON before packetizing...")
            try:
                json.loads(data)
            except Exception as e:
                logging.error(
                    "In sendall(), string was not valid JSON. Cannot send this.")
                exit(1)
            with self.lock:
                self.s.sendall(self.packetize(data))
        elif isinstance(data,actionResponse):
            logging.debug(
                "In sendall(), found an actionResponse, converting the dict inside into JSON before packetizing...")
            self.s.sendall(self.packetize(json.dumps(data.getDict())))
        else:
            logging.error(
                "In sendall(), this is not a string or dict/json type, I don't know how to send this...")
            exit(-1)

    def recv(self):
        return json.loads(self.depacketize(self.receive_packet(self.s)[0]))

    def gethostname(self):
        return socket.gethostname()

    def getSocket(self):
        return self.s

class smartcarsocket:
    def __init__(self):
        # Use my connector object to avoid any python low level stuff in this object (keep it straightforward)
        self.s = connector(socket.socket())
        self.user_queue = queue.Queue()         # So the client can have a thread that handles different actions
                                                # with our library
        self.connect()                          # This needs to happen so the thread has a connection, need to investigate how we can wait...
        self.queue_thread = threading.Thread(target=self.handleIncoming)
        self.queue_thread.start()
        self.internal_queue = queue.Queue()      # For blocking on registering stuff, checking the internal JSON for problems
                                                # The user doesn't need to know / care about our internal JSON messaging
        self.responses = [
            "register-container-response",
            "register-event-response",
            "register-action-response",
            "trigger-action-response",
            "trigger-action",
            "emit-event-response"]

    # internal socket functions

    def connect(self, host="controller", port=8080):
        logging.debug("I am connecting to the socket with host= " + host + " and port= " + str(port))
        self.s.connect(host, port)

    def sendall(self, data):
        self.s.sendall(data)

    def send(self, data):
        self.sendall(data)

    def recv(self):
        return self.s.recv()

    # user functions

    def registerContainer(self, name=""):
        if name is None or name == "":
            # default to the container name
            name = self.s.gethostname()
        register_container = {
            'type': "register-container",
            'timestamp': time.time(),
            'data': {
                'container': {
                    'container_id': name
                }
            }
        }
        self.s.sendall(register_container)
        # wait for a response
        response = self.internal_queue.get()
        try:
            if response['type'] == "register-container-response":
                if response['data']['status'] != 0:
                    logging.error("Something went wrong with register-container-response:")
                    logging.error(response['data']['message'])
                else:
                    logging.debug("Got a good register-container-response, all is good :)")
        except Exception as e:
            logging.error(e)
    def registerEvent(self, name):
        if name is None or name == "":
            logging.error("Cannot register an event with an empty name")
            exit(-1)
        else:
            register_event = {
                'type': "register-event",
                'timestamp': time.time(),
                'container_id': self.s.gethostname(),
                'data': {
                    'name': name
                }
            }
            self.s.sendall(register_event)
            # wait for a response
            response = self.internal_queue.get()
            try:
                if response['type'] == "register-event-response":
                    if response['data']['status'] != 0:
                        logging.error("Something went wrong with register-event-response:")
                        logging.error(response['data']['message'])
                    else:
                        logging.debug("Got a good register-event-response, all is good :)")
            except Exception as e:
                logging.error(e)
    def registerAction(self, name):
        if name is None or name == "":
            logging.error("Cannot register an action with an empty name")
            exit(-1)
        else:
            register_action = {
                'type': "register-action",
                'timestamp': time.time(),
                'container_id': self.s.gethostname(),
                'data': {
                    'name': name
                }
            }
            self.s.sendall(register_action)
            # wait for a response
            response = self.internal_queue.get()
            try:
                if response['type'] == "register-action-response":
                    if response['data']['status'] != 0:
                        logging.error("Something went wrong with register-action-response:")
                        logging.error(response['data']['message'])
                    else:
                        logging.debug("Got a good register-action-response, all is good :)")
            except Exception as e:
                logging.error(e)
    def emitEvent(self, name):
        if name is None or name == "":
            logging.error("Cannot emit an event with an empty name")
            exit(-1)
        else:
            emit_event = {
                'type': "emit-event",
                'timestamp': time.time(),
                'container_id': self.s.gethostname(),
                'data': {
                        'name': name
                }
            }
            self.s.sendall(emit_event)
            # wait for a response
            response = self.internal_queue.get()
            try:
                if response['type'] == "emit-event-response":
                    if response['data']['status'] != 0:
                        logging.error("Something went wrong with emit-event-response:")
                        logging.error(response['data']['message'])
                    else:
                        logging.debug("Got a good emit-event-response, all is good :)")
            except Exception as e:
                logging.error(e)
    def handleIncoming(self):
        # This is run in a dedicated thread that will just listen on the socket,
        # listen for incoming things and translate it into the user queue
        done = False
        while not done:
            # This should be blocking
            obj = self.s.recv()
            logging.debug("handleIncoming got something:")
            logging.debug(obj)
            # obj is a json object of the internal protocol
            # look at it and determine what we should expose to the user / handle internally
            try:
                obj_type = obj['type']
                if obj_type == "trigger-action":
                    logging.debug("This is a trigger-action, we want to pass this along to the user queue")
                    self.user_queue.put(obj)
                else:
                    found = False
                    for r in self.responses:
                    
                        if r == obj_type:
                            found = True
                            # Pass the result through the internal queue, they can handle it for now
                            # Nothing that goes in this queue should be unexpected
                            self.internal_queue.put(obj)
                    if not found:
                        logging.error("The server sent a response we are not aware of...")
            except Exception as e:
                logging.error("Something went wrong when putting things in queues and doing key stuff")
                logging.error(e)

    def sendActionResponse(self,name, event_id,status,message):
        # Tells the controller you finished the action you were assigned
        # needs to be done... or the event won't end / go to the next action
        action_response = {
            "type": "trigger-action-response",
            "timestamp": "epochhere",
            "event_id": event_id,
            "data": {
                "name": name,
                "status": status,
                "message": message
            }
        }
        self.s.sendall(action_response)

    def newActionResponse(self,name):
        return actionResponse(name)

    def getQueue(self):
        # Showing the user a Queue object that has the name of the event.
        # They'll need to have a thread listen for this, I'm not dealing with async/await now...
        return self.user_queue
