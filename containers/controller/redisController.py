import redis
from rejson import Client, Path
import logging
import json
import time


class redisController:
    def __init__(self, hostname, port):
        # Set class variables
        self.hostname = hostname
        self.port = port
        # Create the basic redis connection
        logging.debug("Connecting to the database with hostname: " +
                      str(hostname) + " on port: " + str(port) + ".")
        self.db = Client(host=hostname, port=port, decode_responses=True)

    def registerContainer(self, obj):
        # Internal error if we somehow don't go through the if or else
        response = {
            'type': "register-container-error",
            'timestamp': time.time(),
            'data': {
                    'message': "Internal registerContainer error",
                    'status': 503
            }
        }

        # Grab the timestamp in the packet
        timestamp = obj['timestamp']
        # Go the container being registered
        container = obj['data']['container']
        # Pull out the valuable attributes from this layer
        name = container['name']
        container_id = container['container_id']
        # Check if this container already exists in redis
        existing_container_string = self.db.jsonget(container_id)
        logging.debug(
            "Checking for an existing container returned: " + str(existing_container_string))
        if existing_container_string is not None:
            existing_container = json.loads(existing_container_string)

            response = {
                'type': "register-container-response",
                'timestamp': time.time(),
                'data': {
                    'message': "Container " + container +
                    " was already registered in redis at " +
                    str(existing_container['timestamp']),
                    'status': 1
                }
            }

            logging.warning(response['data']['messsage'])

        else:
            # Build a redis object
            robj = {
                'state': "online",
                'name': name,
                'timestamp': timestamp,
                'events': [],
                'actions': []
            }
            self.db.jsonset(container_id, Path.rootPath(), robj)

            response = {
                'type': "register-container-response",
                'timestamp': time.time(),
                'data': {
                    'message': "OK",
                    'status': 0
                }
            }

        return response

    def registerEvent(self, obj):
        # Internal error if we somehow don't go through the if or else
        response = {
            'type': "register-event-error",
            'timestamp': time.time(),
            'data': {
                    'message': "Internal registerEvent error",
                    'status': 504
            }
        }
        # Grab the timestamp in the packet
        timestamp = obj['timestamp']
        # Go the event being registered
        event = obj['data']['event']
        # Pull out the valuable attributes from this layer
        name = event['name']
        container_id = obj['container_id']
        # Check if this already exists in redis by first pulling all events for this container
        existing_events_string = self.db.jsonget(container_id, Path('.events'))
        logging.debug(
            "Checking for existing events returned: " + str(existing_events_string))
        # See if the event name we are trying to register already exists
        if existing_events_string is not None and name in existing_events_string:
            response = {
                'type': "register-event-response",
                'timestamp': time.time(),
                'data': {
                    'message': "Event " + name +
                    " was already registered in redis",
                    'status': 1
                }
            }

            logging.warning(response['data']['messsage'])

        else:
            # Insert the event into the proper container's object
            robj = {
                'name': name
            }
            self.db.jsonarrappend(container_id, Path('.events'), robj)
            response = {
                'type': "register-event-response",
                'timestamp': time.time(),
                'data': {
                    'message': "OK",
                    'status': 0
                }
            }
        return response

    def dump(self, container_id):
        s = self.db.jsonget(container_id)
        obj = None
        if s is not None:
            obj = json.loads(s)
        return obj
