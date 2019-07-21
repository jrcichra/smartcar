import eventlet
import socketio

# https://python-socketio.readthedocs.io/en/latest/intro.html#server-examples

sio = socketio.Server()
app = socketio.WSGIApp(sio, static_files={
    '/': {'content_type': 'text/html', 'filename': 'index.html'}
})


@sio.event
def connect(sid, environ):
    print('connect ', sid)
    sio.emit('my_message', {'message': 'tomato'})


@sio.event
def my_response(sid, data):
    print('response: ', data)
    sio.disconnect(sid)


@sio.event
def disconnect(sid):
    print('disconnect ', sid)


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8080)), app)
