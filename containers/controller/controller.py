import json
import logging
import socket
import threading
from datetime import datetime
from redisController import redisController
from networking import *
import time
import queue
import uuid

DB_HOST = "redis"
DB_PORT = 6379
CONTROLLER_PORT = 8080

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d:LINE %(lineno)d:TID %(thread)d:%(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

modes = ["serial", "parallel"]
# Thread independent hash of container ids and a socket, so we can send stuff.
# I am using thread locks instead of another thread + a queue, much nicer :-)
connections = {}


def isSupportedMode(mode):
    return mode in modes


def handleAction(action, mode, read_queue, q):
    # check redis and make sure its actually an action that exists...if it doesn't a lot we'll need to look at queues or something...

    redis_action = rc.queryAction(action)
    if redis_action is None:
        logging.warn("Action: " + action +
                     " does not exist (yet) in redis...cannot call action. Waiting on queue instead...")
        # block on this queue until the action we are looking for is registered
        while q.get() != action:
            logging.debug(
                "We didn't find it in redis, but something came in the queue, but it was not the action we wanted...")
        # now check the db, if its not there then something is internally wrong
        logging.debug("We got the action we wanted to see...")
        redis_action = rc.queryAction(action)
        if redis_action is None:
            logging.error(
                "WTF, how can it not be there? We found the action in the 'just registered' queue")

    # Validate the fields are there that we care about...mainly the container_id
    try:
        container_id = redis_action['container_id']
        logging.debug("Found action: " + action)
        logging.debug("Container who owns action is: " + container_id)
        # check the mode they passed into this function: (parallel vs serial to start)
        if not isSupportedMode(mode):
            logging.error(
                "The mode passed in is not a supported mode!!! Treating as serial...")
        # Do something for these modes, default to serial

        # No matter what, we send something to the proper container
        message = {
            'type': "trigger-action",
            'timestamp': time.time(),
            'data': {
                'name': action
            }
        }
        # Determine which socket we need to send this to and lock the sock!
        try:
            logging.debug(
                "Dumping all things in the 'connections' structure...")
            global connections
            logging.debug(connections)
            connection = connections[container_id]
            write_lock = connection['write_lock']
            socket = connection['socket']
            read_queue = connection['read_queue']
            with write_lock:
                # No matter the mode, we want to send something!
                socket.sendall(packetize(json.dumps(message)))
            if mode == "parallel":
                # Don't block per action, we don't care what the result is (yet)
                # The responses will go into the read_queue though, for later
                return
            else:  # if mode == "serial" or something else...
                # wait for a reply from the socket that is a result from this request (this should block)
                response = read_queue.get()
                return response
        except KeyError as e:
            logging.debug(e)
            logging.error(
                "Not sure how, but this connection does not have a connection in the connection hash!")

    except KeyError as e:
        logging.debug(
            "Could not find a container_id in the redis action of " + action)


def handleEvent(obj, rc, read_queue, q):
    # Internal error if we somehow don't go through the if or else
    response = {
        'type': "emit-event-error",
        'timestamp': time.time(),
        'data': {
                'message': "Internal emit-event error",
                'status': 506
        }
    }
    # Grab the timestamp in the packet
    timestamp = obj['timestamp']
    # Go the event being handled
    event = obj['data']['event']
    # Pull out the valuable attributes from this layer
    event_name = event['name']
    # There may or may not be a payload per event, we should pass it if it exists..., for now don't worry
    # event_payload = event['payload']

    container_id = obj['container_id']
    # Query out the actions that take place because of this event
    redis_event = rc.queryEvent(event_name)
    logging.debug(
        "Checking for an existing event returned: " + str(json.dumps(redis_event)))
    redis_parsed = {}

    # Verify the container who emitted this event is the one who registered it
    if redis_event is None:
        response['data']['message'] = "Cannot emit an event which does not exist"
        response['data']['status'] = 508
    elif container_id != redis_event['container_id']:
        response['data']['message'] = "container_id of request did not match container_id of registered event"
        response['data']['status'] = 507
    else:
        # Handle the ignore
        try:
            ignore = redis_event['ignore']
            if isinstance(ignore, str):
                rc.ignoreEvent(ignore)
            elif isinstance(ignore, list):
                for i in ignore:
                    rc.ignoreEvent(ignore)
            else:
                logging.error("Could not handle ignore for event: " +
                              event_name + ". Not string or list!!!")
        except KeyError as e:
            logging.debug(
                "No ignore found while parsing event: " + event_name)
        try:
            listen = redis_event['listen']
            if isinstance(listen, str):
                rc.listenEvent(listen)
            elif isinstance(listen, list):
                for l in listen:
                    rc.listenEvent(l)
        except KeyError as e:
            logging.debug(
                "No listen found while parsing event: " + event_name)
        try:
            # We use this later when doing a serial execution
            brk = redis_event['break']
        except KeyError as e:
            logging.debug(
                "No break found while parsing event: " + event_name)
        # You need either a serial or parallel. No support for both yet
        try:
            serial = redis_event['serial']
            # For every serial action
            for action in serial:
                logging.debug(
                    "Serial Action being called: " + str(action))
                # Call that action and block until we get a response (block happens in the function)
                handleAction(action, "serial", read_queue, q)
        except KeyError as e:
            logging.debug(
                "No serial found while parsing event: " + event_name)
            try:
                parallel = redis_event['parallel']
                for action in parallel:
                    logging.debug(
                        "Parallel Action being called: " + str(action))
                    # Call that action but don't block waiting for a response, instead, collect
                    # them outside of here (by draining the queue later)
                    # TODO this needs to become a thread per action so we don't block on missing actions
                    # like we would on serial
                    handleAction(action, "parallel", read_queue, q)
                # For now, drain the queue here
                logging.debug("Draining the parallel results:")
                while not read_queue.empty():
                    logging.debug(read_queue.get())
            except KeyError as e:
                logging.debug(
                    "No parallel found while parsing event: " + event_name)
        response = {
            'type': "emit-event-response",
            'timestamp': time.time(),
            'data': {
                'message': "OK",
                'status': 0
            }
        }
    return response


def handle_container_message(client_socket, client_address, container_object, rc, connection, events):
    # This function makes the appropriate calls to other functions based on the context of the packet

    # Make a generic response object in case something goes wrong where we don't hit anything else
    response = {
        'type': "generic-error-response",
        'timestamp': time.time(),
        'data': {
            'message': "Internal controller handler error",
            'status': 503
        }
    }

    if container_object['type'] == "register-container":
        response = rc.registerContainer(container_object)
        if response['data']['status'] == 0:
            # If we got a good register container response, add it to the list of lock n socks...
            # We'll likely be communicating with it soon and we need to lock the sock!
            try:
                container_id = container_object['data']['container']['id']
                global connections
                connections[container_id] = connection
            except KeyError as e:
                logging.error(e)
                logging.error(
                    "KeyError when trying to add connection to the global connection list")
    elif container_object['type'] == "register-event":
        response = rc.registerEvent(container_object)
    elif container_object['type'] == "register-action":
        response = rc.registerAction(container_object, events)
    elif container_object['type'] == "emit-event":
        # Events may block because they trigger a serial process, need to spawn a thread
        # There also needs to be an event id to prevent overlaps from occuring. This will go in the action packets to keep track what event this is for
        event_id = str(uuid.uuid4())
        # add our queue to the events hash with the key being the event_id
        events[event_id] = {
            'name': container_object['data']['event'],
            'read_queue': queue.Queue(),
            'action_queue': queue.Queue()
        }
        # Spawn that thread
        t = threading.Thread(target=handleEvent, args=(
            container_object, rc, events[event_id]['read_queue'], events[event_id]['action_queue']))
        t.start()
        response = {
            'type': "emit-event-response",
            'timestamp': time.time(),
            'data': {
                'message': "OK",
                'status': 0
            }
        }
        #handleEvent(container_object, rc, read_queue)
    elif container_object['type'] == "trigger-action-response":
        # We know that an emit-event thread is listening for this response. We'll put this in their queue so it unblocks
        # Figure out who this owns to based on the data
        try:
            # Read what event_id this is
            event_id = container_object['event_id']
            # Pull the queue for this event id
            q = events[event_id]
            # Send what we got to the proper queue, which should unblock that event process
            q.put(container_object)
            # No response needed since this is a response
            return
        except KeyError as e:
            logging.error(
                "We're missing the event id, can't determine which queue is blocked / waiting for this")
    else:
        response = {
            'type': container_object['type'] + "-error",
            'timestamp': time.time(),
            'data': {
                'message': "unrecognized type: " + container_object['type'],
                'status': 1
            }
        }
    return response


def serve_container(client_socket, client_address, rc):
    try:
        # We have a client and they've connected to us
        connected = True
        # Create locks for this container
        connection = {
            'socket': client_socket,
            'write_lock': threading.Lock(),
            'read_queue': queue.Queue()
        }
        # Hash of current events and their queues because we could be handling
        # multiple events at similar times, ones blocked, one's not, yikes! This is insane
        events = {}

        # While they are here...
        while connected:
            # Block until we get a packet from them
            logging.debug("Blocking for " + client_address +
                          " waiting to receive a packet...")
            # This is the only place we read a packet, so no lock is needed.
            raw_packet, err = receive_packet(client_socket)
            # See if they left
            if(err):
                logging.warning("Container at " + client_address + "has left.")
                connected = False
                break
            # If they didn't, we must have a message, and we should load it into a JSON object
            logging.debug("Parsing packet from " + client_address + "...")
            container_object = json.loads(depacketize(raw_packet))
            logging.debug("Packet from " + client_address + " is...")
            logging.debug(container_object)
            logging.debug("Handling JSON for " + client_address)
            response = handle_container_message(
                client_socket, client_address, container_object, rc, connection, events)
            # Now we can send the response back, if there is something
            if response is not None:
                with connection['write_lock']:
                    client_socket.sendall(packetize(json.dumps(response)))
    except socket.timeout:
        logging.debug("Lost connection to " + client_address)
        client_socket.close()

# Main


# Create the server socket
logging.debug("Creating the server socket on port: " + str(CONTROLLER_PORT))
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("0.0.0.0", CONTROLLER_PORT))
logging.info("Controller server up and listening on port: " +
             str(CONTROLLER_PORT) + ".")

# Connect to the database
rc = redisController(DB_HOST, DB_PORT)

# Path to the config yaml
rc.setConfig("config.yml")

# Listen for other containers to connect
server_socket.listen()
while True:
    logging.debug("Waiting for containers on the main thread...")
    client_socket, client_address = server_socket.accept()
    client_address = str(client_address)
    logging.info("Received a connection from: " + client_address + ".")
    logging.debug(
        "Spawning a new thread to handle communication with " + client_address + ".")
    t = threading.Thread(target=serve_container,
                         args=(client_socket, client_address, rc))
    t.start()
