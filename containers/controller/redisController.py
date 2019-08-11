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
        self.ignore = []  # List of ignored events at any point, also handles listens

    def ignore(self, ignore):
        # ignore should be a string
        if isinstance(ignore, str):
            self.ignore.append(ignore)
        else:
            logging.error("ignore() received a non-string. Ignoring...")

    def listen(self, listen):
        # listen should be a string
        if isinstance(listen, str):
            self.listen.remove(listen)
        else:
            logging.error("listen() received a non-string. Ignoring...")

    def handleEvent(self, obj):
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
        event_payload = event['payload']
        container_id = obj['container_id']
        # Query out the actions that take place because of this event
        redis_event = self.db.jsonget(
            "event_" + str(event_name))

        redis_parsed = {}

        # Verify the container who emitted this event is the one who registered it
        if container_id != redis_event['container_id']:
            response['data']['message'] = "container_id of request did not match container_id of registered event"
            response['data']['status'] = 507
        else:
            # Handle the ignore
            try:
                ignore = redis_event['ignore']
                if isinstance(ignore, str):
                    ignore(ignore)
                elif isinstance(ignore, list):
                    for i in ignore:
                        ignore(i)
                else:
                    logging.error("Could not handle ignore for event: " +
                                event_name + ". Not string or list!!!")
            except KeyError:
                logging.debug(
                    "No ignore found while parsing event: " + event_name)
            try:
                listen = redis_event['listen']
                if isinstance(listen, str):
                    listen(listen)
                elif isinstance(listen, list):
                    for l in listen:
                        listen(l)
            except KeyError:
                logging.debug(
                    "No listen found while parsing event: " + event_name)
            try:
                # We use this later when doing a serial execution
                brk = redis_event['break']
            except KeyError:
                logging.debug(
                    "No break found while parsing event: " + event_name)
            # You need either a serial or parallel. No support for both yet
            try:
                serial = redis_event['serial']
                # For every serial action
                for action in serial:
                    logging.debug("Serial Action that would be called: " + str(action))
                    # Call that action and block until we get a response
                    # callSerialAction(action)
                    # At the end of every call, check if we got the break event, and break the loop
                    # if gotBreak(brk):
                    #  break
            except KeyError:
                logging.debug(
                    "No serial found while parsing event: " + event_name)
                try:
                    parallel = redis_event['parallel']
                    for action in parallel:
                        logging.debug("Parallel Action that would be called: " + str(action))
                except KeyError:
                    logging.debug(
                        "No parallel found while parsing event: " + event_name)

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
                    'message': "OK",
                    'status': 0
                }
            }
        return response

    def registerAction(self, obj):
        # Internal error if we somehow don't go through the if or else
        response = {
            'type': "register-action-error",
            'timestamp': time.time(),
            'data': {
                    'message': "Internal registerAction error",
                    'status': 505
            }
        }
        # Grab the timestamp in the packet
        timestamp = obj['timestamp']
        # Go the action being registered
        action = obj['data']['action']
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

            # Append yourself to the proper container's event list

            robj = {
                'name': action_name,
                'container_id': container_id
            }

            self.db.jsonarrappend(
                "container_" + str(container_id), Path('.actions'), robj)

            # Build a response
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
