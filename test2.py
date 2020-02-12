#!/usr/bin/python3
import socket
import json
import sys
import time

my_socket = socket.socket()
my_host = socket.gethostname()
my_port = 8080
my_socket.connect((my_host, my_port))
container_name = 'testpython'

if sys.argv[1] == 'container':
    data = {
        'type': 'register-container',
        'timestamp': 1581476610,
        'name': container_name,
    }
elif sys.argv[1] == 'action':
    data = {
        'type': 'register-action',
        'timestamp': 1581476610,
        'name': 'doathing',
        'container_name': container_name
    }
elif sys.argv[1] == 'event':
    data = {
        'type': 'register-event',
        'timestamp': 1581476610,
        'name': 'icandosomething',
        'container_name': container_name
    }

my_socket.sendall(json.dumps(data).encode('utf-8'))

print(my_socket.recv(99999))

my_socket.close()
