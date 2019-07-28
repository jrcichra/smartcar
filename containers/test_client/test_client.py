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
            "name": "test_client",
            "container_id": socket.gethostname()
        }
    }
}

s.sendall(packetize(json.dumps(register_container)))

print(json.loads(depacketize(receive_packet(s)[0])))
