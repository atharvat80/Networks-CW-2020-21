"""
Author : 000802977, Atharva Tidke
Project : Networks Coursework
"""

import socket
import sys
import errno
import json
import threading

HEADERLEN = 20

# Read username and server address
try:
    username, hostname, port = sys.argv[1], sys.argv[2], int(sys.argv[3])
except Exception as exc:
    print(exc)
    print("\nOne or more arguments missing/invalid, please run the program as following:")
    print("\tpython client.py [username] [hostname] [port]\n")
    sys.exit()

# Connect to the server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    print("Trying to connect to the server at %s:%s" % (hostname, port))
    client.connect((hostname, port))
except Exception as e:
    print("Could not connect to the server due to following error :\n", e)
    sys.exit()
else:
    print("Successfully connected to server!\n")
    client.setblocking(False)


def encode_msg(msg):
    """Add the message length in bytes in the header so the server knows 
    how many bytes to receive to get the full message"""
    msg = json.dumps(msg)
    header = str(len(msg)).ljust(HEADERLEN)
    return (header + msg).encode()


# Send username to the server
client.send(encode_msg(username))

# Will be used to stop the display_msg thread once the user 
# decides to leave or there's a keyboard interrupt
isActive = True


def display_msgs():
    """Receive and display messages"""
    while isActive:
        try:
            msg_len = client.recv(HEADERLEN)
            if not len(msg_len):
                print("Connection closed by the server, press Enter to exit.")
                sys.exit()
        except Exception as err:
            if err.errno != errno.EAGAIN and err.errno != errno.EWOULDBLOCK:
                print('Following error occurred while fetching messages\n%s\nPress Enter to exit' % err)
                sys.exit()
        else:
            msg_len = int(msg_len.decode('utf-8').strip())
            msg = json.loads(client.recv(msg_len))
            print("[{}] > {}".format((msg['from']).ljust(10), msg['message']))


# Create a separate thread for displaying messages so incoming messages
# can be displayed while waiting for user input
displayMsgThread = threading.Thread(target=display_msgs)
displayMsgThread.start()

try:
    # DisplayMsgThread is alive until client is connected to the server so,
    # keep taking user input until it is alive
    while displayMsgThread.is_alive():
        # Read message and truncate if it's too long to send
        message = input()
        message = (message[:10**HEADERLEN]) if len(message) > 10**HEADERLEN else message
        if message != '':
            try:
                client.send(encode_msg(message))
            except Exception as e:
                print("Your message could not be delivered due to following error:\n", e)

except KeyboardInterrupt:
    print("You have now left the server.")
    isActive = False
    sys.exit()
