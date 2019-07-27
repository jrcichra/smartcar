import json
import logging
import socket
import threading
from datetime import datetime
from redisController import redisController
from networking import *
import time

DB_HOST = "redis"
DB_PORT = 6379
CONTROLLER_PORT = 8080


def handle_container_message(client_socket, client_address, container_object, rc):
    # This function makes the appropriate calls to other functions based on the context of the packet
    # Make a generic response object in case something goes wrong where we don't hit anything else
    response = {
        'type': "generic-error-response",
        'timestamp': time.time(),
        'data': {
            'message': "Internal controller handler error",
            'status': 503
        }
    }

    if container_object['type'] == "register-container":
        response = rc.registerContainer(container_object)
    elif container_object['type'] == "register-event":
        response = rc.registerEvent(container_object)
    # elif container_object['type'] == "register-action":
    #    response = rc.registerAction(container_object)
    # elif container_object['type'] == "emit-event":
    #    response = rc.event(container_object)
    else:
        response = {
            'type': container_object['type'] + "-error",
            'timestamp': time.time(),
            'data': {
                'message': "unrecognized type: " + container_object['type'],
                'status': 1
            }
        }
    return response


def serve_container(client_socket, client_address):
    try:
        # We have a client and they've connected to us
        connected = True
        # Create the redis-controller object
        rc = redisController(DB_HOST, DB_PORT)
        # While they are here...
        while connected:
            # Block until we get a packet from them
            logging.debug("Blocking for " + client_address +
                          " waiting to receive a packet...")
            raw_packet, err = recieve_packet(client_socket)
            # See if they left
            if(err):
                logging.warning("Container at " + client_address + "has left.")
                connected = False
                break
            # If they didn't, we must have a message, and we should load it into a JSON object
            logging.debug("Parsing packet from " + client_address + "...")
            container_object = json.loads(depacketize(raw_packet))
            logging.debug("Packet from " + client_address + " is...")
            logging.debug(container_object)
            logging.debug("Handling JSON for " + client_address)
            response = handle_container_message(
                client_socket, client_address, container_object, rc)
            # Now we can send the response back
            client_socket.sendall(packetize(json.dumps(response)))
    except socket.timeout:
        logging.debug("Lost connection to " + client_address)
        client_socket.close()

# Main


# Create the server socket
logging.debug("Creating the server socket on port: " + str(CONTROLLER_PORT))
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("0.0.0.0", CONTROLLER_PORT))
logging.info("Controller server up and listening on port: " +
             str(CONTROLLER_PORT) + ".")

# Listen for other containers to connect
server_socket.listen()
while True:
    logging.debug("Waiting for containers on the main thread...")
    client_socket, client_address = server_socket.accept()
    client_address = str(client_address)
    logging.info("Received a connection from: " + client_address + ".")
    logging.debug(
        "Spawning a new thread to handle communication with " + client_address + ".")
    t = threading.Thread(target=serve_container,
                         args=(client_socket, client_address))
    t.start()
