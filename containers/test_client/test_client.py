import socketio
import requests
# https://python-socketio.readthedocs.io/en/latest/intro.html#client-examples

sio = socketio.Client()


@sio.event
def connect():
    print('connection established')


@sio.event
def my_message(data):
    print('message received with ', data)
    sio.emit('my_response', {'response': data['message'][::-1]})
    sio.disconnect()
    exit(0)


@sio.event
def disconnect():
    print('disconnected from server')


sio.connect('http://controller:8080')
sio.wait()
