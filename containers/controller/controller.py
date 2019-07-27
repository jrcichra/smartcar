import redis
from rejson import Client, Path

r = Client(host='redis', port=6379, decode_responses=True)

# Set the key `obj` to some object
obj = {
    'answer': 42,
    'arr': [None, True, 3.14],
    'truth': {
        'coord': 'out there'
    }
}
r.jsonset('obj', Path.rootPath(), obj)

# Get something
print('Is there anybody... {}?').format(
    r.jsonget('obj', Path('.truth.coord'))
)

exit(0)
