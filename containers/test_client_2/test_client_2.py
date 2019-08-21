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
logging.debug("Phase 2 - Register key_off event")

register_event_two = {
    'type': "register-event",
    'timestamp': time.time(),
    'container_id': socket.gethostname(),
    'data': {
        'event': {
            'name': "key_off"
        }
    }
}

s.sendall(packetize(json.dumps(register_event_two)))
logging.debug(depacketize(receive_packet(s)[0]))

logging.debug("Phase 3 - Emit key_off event")

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

logging.debug("Phase 4 - Register start_recording action")


register_action = {
    'type': "register-action",
    'timestamp': time.time(),
    'container_id': socket.gethostname(),
    'data': {
        'action': {
            'name': "stop_recording"
        }
    }
}

s.sendall(packetize(json.dumps(register_action)))
logging.debug(depacketize(receive_packet(s)[0]))

logging.debug(
    "Phase 5 - Dump all packets that come my way, waiting for action requests...")
while True:
    obj = depacketize(receive_packet(s)[0])
    logging.debug(obj)
    # Pretend to take some time doing stuff with your action...
    time.sleep(5)
    # Send a response back using the same action name we saw come in
    action_response = {
        "type": "trigger-action-response",
        "timestamp": "epochhere",
        "event_id": json.loads(obj)['event_id'],
        "data": {
            "action": {
                "name": obj['data']['action']['name'],
                "status": 0,
                "message": "OK"
            }
        }
    }
    logging.debug(
        "I am sending an action response since I 'handled' this action...")
    s.sendall(packetize(json.dumps(action_response)))
logging.debug("Goodbye.")
