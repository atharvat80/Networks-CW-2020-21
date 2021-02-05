"""
Author : 000802977, Atharva Tidke
Project : Networks Coursework
"""

import socket
import sys
import errno
import pickle
import threading

HEADERLEN = 10

with open("help.txt", "r") as f:
    helpText = f.read()

try:
    username, hostname, port = sys.argv[1], sys.argv[2], int(sys.argv[3])
except:
    print("\nOne or more arguments missing/invalid, please run the program as following:")
    print("\tpython client.py [username] [hostname] [port]\n")
    sys.exit()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    print("Trying to connect to the server...\n")
    client.connect((hostname, port))
except Exception as e:
    print("Could not connect to the server due to following error :\n", e)
    sys.exit()

client.setblocking(False)


def encodeMessage(message):
    """Add the message length in bytes in the header so the server knows 
    how many bytes to receive to get the full message"""
    message = pickle.dumps(message)
    return bytes(str(len(message)).ljust(HEADERLEN), "utf-8") + message


client.send(encodeMessage(username))
print(helpText)

# Will be used to stop the displayMessage thread once the user 
# decides to leave or there's a keyboard interrupt
isActive = True


def displayMessages():
    # Loop over received messages
    while isActive:
        try:
            while True:
                messageLength = client.recv(HEADERLEN)
                if not len(messageLength):
                    print("Connection closed by the server, press Enter to exit.")
                    sys.exit()

                messageLength = int(messageLength.decode('utf-8').strip())
                message = pickle.loads(client.recv(messageLength))
                print("[{}] > {}".format((message['from']).ljust(10), message['message']))

        except Exception as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('Following error occurred while fetching messages\n', str(e),
                      '\nPress Enter to exit')
                sys.exit()


displayMsgThread = threading.Thread(target=displayMessages)
displayMsgThread.start()

try:
    while displayMsgThread.isAlive():
        message = input()

        if message == "--leave":
            print("You have now left the server.")
            isActive = False
            sys.exit()

        elif message == "--help":
            print(helpText)

        elif message != '':
            try:
                client.send(encodeMessage(message))
            except Exception as e:
                print("Your message could not be delivered due to following error:\n", e)

except KeyboardInterrupt:
    print("You have now left the server.")
    isActive = False
    sys.exit()
