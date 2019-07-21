import socketio

# https://python-socketio.readthedocs.io/en/latest/intro.html#client-examples

sio = socketio.Client()


@sio.event
def connect():
    print('connection established')


@sio.event
def my_message(data):
    print('message received with ', data)
    sio.emit('my response', {'response': 'my response'})


@sio.event
def disconnect():
    print('disconnected from server')


sio.connect('http://controller:8080')
sio.wait()
