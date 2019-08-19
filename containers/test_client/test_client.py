import socket
import time
from networking import *
import json
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d:%(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

s = socket.socket()
s.connect(("controller", 8080))

register_container = {
    'type': "register-container",
    'timestamp': time.time(),
    'data': {
        'container': {
            'container_id': socket.gethostname()
        }
    }
}

logging.debug("Phase 1 - register this container")
s.sendall(packetize(json.dumps(register_container)))
logging.debug(depacketize(receive_packet(s)[0]))
logging.debug("Phase 2 - Register an event")

register_event = {
    'type': "register-event",
    'timestamp': time.time(),
    'container_id': socket.gethostname(),
    'data': {
        'event': {
            'name': "key_on"
        }
    }
}

s.sendall(packetize(json.dumps(register_event)))
logging.debug(depacketize(receive_packet(s)[0]))

logging.debug("Phase 3 - Register an action")

register_action = {
    'type': "register-action",
    'timestamp': time.time(),
    'container_id': socket.gethostname(),
    'data': {
        'action': {
            'name': "killcar"
        }
    }
}

s.sendall(packetize(json.dumps(register_action)))
logging.debug(depacketize(receive_packet(s)[0]))

logging.debug(
    "Phase 4 - Try to reregister a container that already exists - This should fail")

register_container_again = {
    'type': "register-container",
    'timestamp': time.time(),
    'data': {
        'container': {
            'container_id': socket.gethostname()
        }
    }
}

s.sendall(packetize(json.dumps(register_container_again)))
logging.debug(depacketize(receive_packet(s)[0]))

logging.debug(
    "Phase 5 - Try to reregister an event that already exists - This should fail")

register_event_again = {
    'type': "register-event",
    'timestamp': time.time(),
    'container_id': socket.gethostname(),
    'data': {
        'event': {
            'name': "key_on"
        }
    }
}

s.sendall(packetize(json.dumps(register_event_again)))
logging.debug(depacketize(receive_packet(s)[0]))

logging.debug(
    "Phase 6 - Try to reregister an action that already exists - This should fail")

register_action_again = {
    'type': "register-action",
    'timestamp': time.time(),
    'container_id': socket.gethostname(),
    'data': {
        'action': {
            'name': "killcar"
        }
    }
}

s.sendall(packetize(json.dumps(register_action_again)))
logging.debug(depacketize(receive_packet(s)[0]))

logging.debug("Phase 7 - Emit an event that I have registered")

emit_event = {
    'type': "emit-event",
    'timestamp': time.time(),
    'container_id': socket.gethostname(),
    'data': {
        'event': {
            'name': "key_on"
        }
    }
}

s.sendall(packetize(json.dumps(emit_event)))
logging.debug(depacketize(receive_packet(s)[0]))

logging.debug(
    "Phase 8 - Emit an event that I have not registered, this should fail")

emit_event = {
    'type': "emit-event",
    'timestamp': time.time(),
    'container_id': socket.gethostname(),
    'data': {
        'event': {
            'name': "key_off"
        }
    }
}

s.sendall(packetize(json.dumps(emit_event)))
logging.debug(depacketize(receive_packet(s)[0]))

logging.debug(
    "Phase 9 - Dump all packets that come my way, waiting for action requests...")
while True:
    obj = depacketize(receive_packet(s)[0])
    logging.debug(obj)
    # Pretend to take some time doing stuff with your action...
    time.sleep(5)
    # Send a response back using the same action name we saw come in
    action_response = {
        "type": "trigger-action-response",
        "timestamp": "epochhere",
        "event_id": "uuid4",
        "data": {
            "action": {
                "name": obj['data']['action']['name'],
                "status": 0,
                "message": "OK"
            }
        }
    }
    s.sendall(packetize(json.dumps(action_response)))
logging.debug("Goodbye.")
