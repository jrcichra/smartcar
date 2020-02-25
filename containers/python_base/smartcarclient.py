###
# jrcichra 2020 - made for controllerv2
###

import enum
import json
import logging
import os
import queue
import socket
import sys
import threading
import time

REGISTERCONTAINER = "register-container"
REGISTERCONTAINERRESPONSE = "register-container-response"
REGISTEREVENT = "register-event"
REGISTEREVENTRESPONSE = "register-event-response"
REGISTERACTION = "register-action"
REGISTERACTIONRESPONSE = "register-action-response"
EMITEVENT = "emit-event"
EMITEVENTRESPONSE = "emit-event-response"
TRIGGERACTION = "trigger-action"
TRIGGERACTIONRESPONSE = "trigger-action-response"
DISPATCHEDEVENT = "dispatched-event"
OK = 200
ERROR = 503
ONLINE = "online"
OFFLINE = "offline"


# TODO: RAISING ERRORS IN THIS PYTHON LIBRARY

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d:%(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class CallbackThread(threading.Thread):
    # https://gist.github.com/amirasaran/e91c7253c03518b8f7b7955df0e954bb
    def __init__(self, callback=None, callback_args=None, *args, **kwargs):
        target = kwargs.pop('target')
        super(CallbackThread, self).__init__(
            target=self.target_with_callback, *args, **kwargs)
        self.callback = callback
        self.method = target
        self.callback_args = callback_args

    def target_with_callback(self, p, r):
        self.method(p, r)
        if self.callback is not None:
            self.callback(*self.callback_args)


class Message:

    def __init__(self):
        pass

    def setType(self, t):
        self.type = t

    def getType(self):
        return self.type

    def setTimestamp(self, timestamp):
        self.timestamp = timestamp

    def getTimestamp(self):
        return self.timestamp

    def setContainerName(self, cn):
        self.container_name = cn

    def getContainerName(self):
        return self.container_name

    def setName(self, name):
        self.name = name

    def getName(self):
        return self.name

    def setResponseCode(self, rc):
        self.response_code = rc

    def getReponseCode(self):
        return self.response_code

    def setProperties(self, p):
        self.properties = p

    def getProperties(self):
        return self.properties

    def setID(self, idee):
        self.id = idee

    def getID(self):
        return self.id

    def makeRegisterContainer(self, container_name):
        self.name = container_name
        self.timestamp = int(time.time())
        self.response_code = OK
        self.properties = None
        self.type = REGISTERCONTAINER
        self.container_name = container_name
        self.id = None

    def makeRegisterEvent(self, container_name, event_name):
        self.name = event_name
        self.timestamp = int(time.time())
        self.response_code = OK
        self.properties = None
        self.type = REGISTEREVENT
        self.container_name = container_name
        self.id = None

    def makeRegisterAction(self, container_name, action_name):
        self.name = action_name
        self.timestamp = int(time.time())
        self.response_code = OK
        self.properties = None
        self.type = REGISTERACTION
        self.container_name = container_name
        self.id = None

    def makeEmitEvent(self, container_name, event_name, properties):
        self.name = event_name
        self.timestamp = int(time.time())
        self.response_code = OK
        self.properties = properties
        self.type = EMITEVENT
        self.container_name = container_name
        self.id = None

    def makeActionResponse(self, container_name, action_name, rc):
        self.name = action_name
        self.timestamp = int(time.time())
        self.response_code = rc
        self.properties = None
        self.type = TRIGGERACTIONRESPONSE
        self.container_name = container_name
        self.id = None

    def toJSONStr(self):
        # Go common message
        # type Message struct {
        # 	Type          string      `json:"type"`           //Type of message being sent
        # 	Timestamp     int64       `json:"timestamp"`      //What time this message was created
        # 	ContainerName string      `json:"container_name"` //Container Name we want to address
        # 	Name          string      `json:"name"`           //Name of the event/action/container based on type
        # 	ResponseCode  int         `json:"response_code"`  //Response code (might be nil based on type)
        # 	Properties    interface{} `json:"properties"`     //Properties attached to the event
        #   ID            string      `json:"id"`             //Message IDs for the clients to keep track of their messages (passed thru)
        # }
        j = {
            "type": self.type,
            "timestamp": self.timestamp,
            "container_name": self.container_name,
            "name": self.name,
            "response_code": self.response_code,
            "properties": self.properties,
            "id": self.id
        }
        return json.dumps(j)


class Result:
    # Result of a user's action
    def __init__(self):
        self.PASS = True
        self.FAIL = False
        self.status = self.PASS

    def Pass(self):
        self.status = self.PASS

    def Fail(self):
        self.status = self.FAIL

    def getResult(self):
        return self.status


class Client:
    # Client used by python code wanting to inserface with the controller
    def __init__(self, host="controller", port=8080):
        self.host = host
        self.port = port
        self.socket = socket.socket()
        self.hostname = socket.gethostname()
        self.inboundQueues = {
            REGISTERCONTAINERRESPONSE: queue.Queue(),
            REGISTEREVENTRESPONSE: queue.Queue(),
            REGISTERACTIONRESPONSE: queue.Queue(),
            # TRIGGERACTION: queue.Queue(),
            EMITEVENTRESPONSE: queue.Queue(),
            DISPATCHEDEVENT: queue.Queue(),
        }
        self.outboundQueue = queue.Queue()
        self.actions = {}       # Map of action:function for each event we support
        self.eventQueues = {}   # Map of event:queue of bools
        self.eventThreads = {}  # Map of event:thread
        self.connect()

    def send(self, string):
        self.outboundQueue.put(string)

    def handleEvent(self, message):
        my_id = message['id']
        # wait for this event to end
        response = self.eventQueues[my_id].get()
        logging.info("Event {} finished with a return code of {}".format(
            response['name'], response['response_code']))
        # Now remove the queue (to reclaim memory)
        del self.eventQueues[my_id]
        # Also remove my own reference
        del self.eventThreads[my_id]
        # This event thread can die gracefully

    def handleSending(self):
        while True:
            self.socket.sendall(self.outboundQueue.get().encode())

    def sendActionResponse(self, message, r):
        logging.debug(
            "sendActionResponse got an r of {} ".format(r.getResult()))
        # Send a response back
        m = Message()
        if r.getResult():
            m.makeActionResponse(self.hostname, message['name'], OK)
        else:
            m.makeActionResponse(self.hostname, message['name'], ERROR)
        self.send(m.toJSONStr())

    def handleMessages(self):
        while True:
            j = self.receive()  # receive a message (hopefully blocks)
            # if we are to trigger an action, spawn a thread based on the action functions we've been given
            logging.debug("Got a message: {}".format(j))
            if j['type'] == TRIGGERACTION:
                # Make a result object for the user to return a value through
                r = Result()
                self.handleActionThread = CallbackThread(
                    target=self.actions[j['name']], args=(j['properties'], r), callback=self.sendActionResponse, callback_args=(j, r))
                self.handleActionThread.start()
            elif j['type'] == DISPATCHEDEVENT:
                # Event responses should be handled by a new thread based on the event id
                self.eventQueues[j['id']] = queue.Queue()
                self.eventThreads[j['id']] = threading.Thread(
                    target=self.handleEvent, args=(j,))
                self.eventThreads[j['id']].start()
                self.inboundQueues[j['type']].put(j)
            elif j['type'] == EMITEVENTRESPONSE:
                # Tell the event thread that the event is done
                self.eventQueues[j['id']].put(j)
            else:
                self.inboundQueues[j['type']].put(j)

    def connect(self):
        self.socket.connect((self.host, self.port))
        self.handleMessagesThread = threading.Thread(
            target=self.handleMessages)
        self.handleSendingThread = threading.Thread(
            target=self.handleSending)
        self.handleMessagesThread.start()
        self.handleSendingThread.start()

    def receive(self):
        message = b""  # create an empty binary message buffer
        flag = False  # determines if we found the end or not
        err = False
        while not flag:  # while we haven't found that end \n, depicting the end of an object...
            r = self.socket.recv(1)  # copy over x bytes into our buffer
            if(b"\n" in r):  # if that buffer has the \n
                flag = True  # set the flag that we found the end
            elif(not r or r == ""):  # socket dropped on us
                flag = True
                err = True
            message += r  # append it onto our message
        if err:
            logging.error(
                "Got an error while receiving a message. Did the connection get severed?")
        logging.debug("msg={}".format(message))
        return json.loads(message)

    def registerContainer(self):
        # Build a register-container message
        m = Message()
        m.makeRegisterContainer(self.hostname)
        self.send(m.toJSONStr())
        response = self.inboundQueues[REGISTERCONTAINERRESPONSE].get()
        logging.debug("response={}".format(response))
        if response['response_code'] != OK:
            logging.error("While registering the container, we got a bad return code: {}".format(
                response['response_code']))
        else:
            logging.info("Sucessfully registered container")

    def registerEvent(self, event_name):
        # Build a register-event message
        m = Message()
        m.makeRegisterEvent(self.hostname, event_name)
        self.send(m.toJSONStr())
        response = self.inboundQueues[REGISTEREVENTRESPONSE].get()
        logging.debug("response={}".format(response))
        if response['response_code'] != OK:
            logging.error("While registering the event {}, we got a bad return code: {}".format(
                event_name, response['response_code']))
        else:
            logging.info("Sucessfully registered event {}".format(event_name))

    def registerAction(self, action_name, action_function):
        # Put the action_function on the map of action functions
        self.actions[action_name] = action_function
        # Build a register-action message
        m = Message()
        m.makeRegisterAction(self.hostname, action_name)
        self.send(m.toJSONStr())
        response = self.inboundQueues[REGISTERACTIONRESPONSE].get()
        logging.debug("response={}".format(response))
        if response['response_code'] != OK:
            logging.error("While registering the action {}, we got a bad return code: {}".format(
                action_name, response['response_code']))
        else:
            logging.info(
                "Sucessfully registered action {}".format(action_name))

    def emitEvent(self, event_name, properties=None):
        # Build an emit-event message
        m = Message()
        m.makeEmitEvent(self.hostname, event_name, properties)
        self.send(m.toJSONStr())
        response = self.inboundQueues[DISPATCHEDEVENT].get()
        logging.debug("response={}".format(response))
        if response['response_code'] != OK:
            logging.error("While emitting the event {}, we got a bad return code: {}".format(
                event_name, response['response_code']))
        else:
            logging.info(
                "Sucessfully emitted event {}".format(event_name))


def an_action(params, result):
    logging.info("an_action:{}".format(params))
    result.Pass()


def action_no_params(params, result):
    logging.info("action_no_params:{}".format(params))
    result.Fail()
