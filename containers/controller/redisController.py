import redis
from rejson import Client, Path
import logging
import json
import time
import yaml


class redisController:
    def __init__(self, hostname, port):
        # Set class variables
        self.hostname = hostname
        self.port = port
        # Create the basic redis connection
        logging.debug("Connecting to the database with hostname: " +
                      str(hostname) + " on port: " + str(port) + ".")
        self.db = Client(host=hostname, port=port, decode_responses=True)
        self.ignore_list = []  # List of ignored events at any point, also handles listens

    def ignoreEvent(self, ignore):
        # ignore should be a string
        if isinstance(ignore, str):
            self.ignore_list.append(ignore)
        else:
            logging.error("ignoreEvent() received a non-string. Ignoring...")

    def listenEvent(self, listen):
        # listen should be a string
        if isinstance(listen, str):
            try:
                self.ignore_list.remove(listen)
            except ValueError:
                logging.warning("listenEvent() recieved " + listen +
                                ", which was not found in the ignore list. Not removing...")
        else:
            logging.error("listenEvent() received a non-string. Ignoring...")

    def setConfig(self, path):
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
            logging.debug("Printing the config.yml...")
            logging.debug(config)
            logging.debug("Setting the config for this object...")
            self.config = config

    def registerContainer(self, obj):
        # Internal error if we somehow don't go through the if or else
        response = {
            'type': "register-container-error",
            'timestamp': time.time(),
            'data': {
                    'name': 'unknown',
                    'message': "Internal registerContainer error",
                    'status': 503
            }
        }

        # Grab the timestamp in the packet
        timestamp = obj['timestamp']
        # Go the container being registered
        container = obj['data']['container']
        # Pull out the valuable attributes from this layer
        container_id = container['container_id']
        # Check if this container already exists in redis
        existing_container = self.db.jsonget(
            "container_" + str(container_id))
        logging.debug(
            "Checking for an existing container returned: " + str(json.dumps(existing_container)))
        if existing_container is not None:

            response = {
                'type': "register-container-response",
                'timestamp': time.time(),
                'data': {
                    'name': container_id,
                    'message': "Container id:" + container_id +
                    " was already registered in redis at " +
                    str(existing_container['timestamp']),
                    'status': 1
                }
            }

            logging.warning(response['data']['message'])

        else:
            # Build a redis object
            robj = {
                'state': "online",
                'container_id': container_id,
                'timestamp': timestamp,
                'events': [],
                'actions': []
            }
            self.db.jsonset("container_" + str(container_id),
                            Path.rootPath(), robj)

            response = {
                'type': "register-container-response",
                'timestamp': time.time(),
                'data': {
                    'name': container_id,
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
        event = obj['data']['name']
        # Pull out the valuable attributes from this layer
        event_name = event['name']
        container_id = obj['container_id']
        # Check if this already exists in redis by first pulling all events for this container
        existing_events = self.db.jsonget("event_" + str(event_name))
        logging.debug(
            "Checking for existing events returned: " + str(json.dumps(existing_events)))
        # See if the event name we are trying to register already exists
        if existing_events is not None:
            response = {
                'type': "register-event-response",
                'timestamp': time.time(),
                'data': {
                    'message': "Event " + event_name +
                    " was already registered in redis",
                    'status': 1
                }
            }

            logging.warning(response['data']['message'])

        else:

            # Create the base event object, add more as we go through the config parsing
            robj = {
                'name': event_name,
                'container_id': container_id
            }

            # Get data from the config.yml file and put it into redis
            try:
                # Grab the whole object for the event
                event_config = self.config[event_name]
                try:
                    robj['ignore'] = event_config['ignore']
                except KeyError:
                    logging.debug(
                        "No ignore found while registering event: " + event_name)
                try:
                    robj['listen'] = event_config['listen']
                except KeyError:
                    logging.debug(
                        "No listen found while registering event: " + event_name)
                try:
                    robj['break'] = event_config['break']
                except KeyError:
                    logging.debug(
                        "No break found while registering event: " + event_name)
                try:
                    robj['parallel'] = event_config['parallel']
                except KeyError:
                    logging.debug(
                        "No parallel found while registering event: " + event_name)
                try:
                    robj['serial'] = event_config['serial']
                except KeyError:
                    logging.debug(
                        "No serial found while registering event: " + event_name)

            except KeyError:
                logging.warn(
                    "Missing event in config.yml, cannot preform actions for this event. Please check your config.yml")

            self.db.jsonset("event_" + str(event_name),
                            Path.rootPath(), robj)

            # Append yourself to the proper container's event list

            robj = {
                'name': event_name
            }

            self.db.jsonarrappend(
                "container_" + str(container_id), Path('.events'), robj)

            # Build a response

            response = {
                'type': "register-event-response",
                'timestamp': time.time(),
                'data': {
                    'name': event_name,
                    'message': "OK",
                    'status': 0
                }
            }
        return response

    def registerAction(self, obj, events):
        # Internal error if we somehow don't go through the if or else
        response = {
            'type': "register-action-error",
            'timestamp': time.time(),
            'data': {
                    'name': "unknown",
                    'message': "Internal registerAction error",
                    'status': 505
            }
        }
        # Grab the timestamp in the packet
        timestamp = obj['timestamp']
        # Go the action being registered
        action = obj['data']['name']
        # Pull out the valuable attributes from this layer
        action_name = action['name']
        container_id = obj['container_id']
        # Check if this already exists in redis by first pulling all actions for this container
        existing_actions = self.db.jsonget("action_" + str(
            action_name))
        logging.debug(
            "Checking for existing actions returned: " + str(json.dumps(existing_actions)))
        # See if the action name we are trying to register already exists
        if existing_actions is not None:
            response = {
                'type': "register-action-response",
                'timestamp': time.time(),
                'data': {
                    'name': action_name,
                    'message': "Action " + action_name +
                    " was already registered in redis",
                    'status': 1
                }
            }

            logging.warning(response['data']['message'])

        else:
            # Insert the action into the proper container's object
            robj = {
                'name': action_name,
                'container_id': container_id
            }
            self.db.jsonset("action_" + str(action_name),
                            Path.rootPath(), robj)

            # Tell the events waiting for your registration that you're ready, stop blocking!
            # loop through every event that is currently happening and tell them an action that was registered
            # they should be programmed to ignore any action that does not match what they're looking for
            for event in events:
                logging.debug("Inside registerAction() - sending action: " +
                              action_name + " into the queue for event: " + str(event))
                events[event]['action_queue'].put(action_name)

            robj = {
                'name': action_name,
                'container_id': container_id
            }

            self.db.jsonarrappend(
                "container_" + str(container_id), Path('.actions'), robj)

            # Look in the current event list for any blocked event that is looking for this action

            # Build a response
            response = {
                'type': "register-action-response",
                'timestamp': time.time(),
                'data': {
                    'name': action_name,
                    'message': "OK",
                    'status': 0
                }
            }
        return response

    def queryEvent(self, s):
        return self.db.jsonget("event_" + str(s))

    def queryAction(self, s):
        return self.db.jsonget("action_" + str(s))

    def queryContainer(self, s):
        return self.db.jsonget("container_" + str(s))

    def dump(self, container_id):
        s = self.db.jsonget(container_id)
        obj = None
        if s is not None:
            obj = json.loads(s)
        return obj

    def isIgnored(self, event):
        return event in self.ignore_list
