def receive_packet(socket):
    message = b""  # create an empty binary message buffer
    flag = False  # determines if we found the end or not
    err = False
    while not flag:  # while we haven't found that end \n, depicting the end of an object...
        r = socket.recv(1024)  # copy over x bytes into our buffer
        if(b"\n" in r):  # if that buffer has the \n
            flag = True  # set the flag that we found the end
        elif(not r):  # socket dropped on us
            flag = True
            err = True
        message += r  # append it onto our message
    return message, err  # return this byte array, with the \n on the end, in byte form


def packetize(s):
    # encode the string into a byte array and append on the newline character
    return (s + '\n').encode()

# converts a byte array into a string, removing the ending newline


def depacketize(b):
    # remove that last \n and decode the string back to it's original form
    return b.decode()[:-1]
