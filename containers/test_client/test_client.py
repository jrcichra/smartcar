import socket
import time
from networking import *
import json

s = socket.socket()
s.connect(("controller", 8080))

register_container = {
    "type": "register-container",
    "timestamp": time.time(),
    "data": {
        "container": {
            "container_id": socket.gethostname()
        }
    }
}

print("Phase 1 - register this container")
s.sendall(packetize(json.dumps(register_container)))
print(json.loads(depacketize(receive_packet(s)[0])))
print("Phase 2 - Register an event")

register_event = {
    "type": "register-event",
    "timestamp": time.time(),
    "container_id": socket.gethostname(),
    "data": {
        "event": {
            "name": "key_on"
        }
    }
}

s.sendall(packetize(json.dumps(register_event)))
print(json.loads(depacketize(receive_packet(s)[0])))
