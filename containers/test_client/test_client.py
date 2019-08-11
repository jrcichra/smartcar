import socket
import time
from networking import *
import json

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

print("Phase 1 - register this container")
s.sendall(packetize(json.dumps(register_container)))
print(json.loads(depacketize(receive_packet(s)[0])))
print("Phase 2 - Register an event")

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
print(json.loads(depacketize(receive_packet(s)[0])))

print("Phase 3 - Register an action")

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
print(json.loads(depacketize(receive_packet(s)[0])))

print("Phase 4 - Try to reregister a container that already exists - This should fail")

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
print(json.loads(depacketize(receive_packet(s)[0])))

print("Phase 5 - Try to reregister an event that already exists - This should fail")

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
print(json.loads(depacketize(receive_packet(s)[0])))

print("Phase 5 - Try to reregister an action that already exists - This should fail")

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
print(json.loads(depacketize(receive_packet(s)[0])))

print("Phase 6 - Emit an event that I have registered")

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
print(json.loads(depacketize(receive_packet(s)[0])))

print("Test Client Container Completed")
