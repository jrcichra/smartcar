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

logging.debug("Goodbye.")
