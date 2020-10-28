import socket, sys, errno, pickle, threading
headerLength = 10

with open("help.txt", "r") as f:
    helpText = f.read()

# Validate given arguments
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
    message = pickle.dumps(message)
    # Add the message length in bytes in the header so the server knows 
    # how many bytes to receive before the message ends
    return bytes("{:<{}}".format(len(message), headerLength), "utf-8") + message
    

# Send username and print helptext
client.send(encodeMessage(username))
print(helpText)

# Will be used to stop the displayMessage thread once the user 
# decides to leave or there's a keyboard interrupt
isActive = True

def displayMessages():
    while isActive:
        # Loop over received messages
        try:
            while True: 
                messageLength = client.recv(headerLength)
                if not len(messageLength):
                    print("Connection closed by the server.")
                    sys.exit()
                        
                messageLength = int(messageLength.decode('utf-8').strip())
                message = pickle.loads(client.recv(messageLength))
                print("[{}] > {}".format((message['from']).ljust(10), message['message']))
        
        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('Reading error: ' + str(e))
                sys.exit()

        except Exception as e:
            print('Reading error: ' + str(e))
            sys.exit()

# Start displaying incoming messages using a new thread
displayMsgThread = threading.Thread(target=displayMessages)
displayMsgThread.setDaemon(True)
displayMsgThread.start()

# Check for keyboard interrupt
try:
    while isActive:
        message = input() #f"[{username}] > "
        
        # Leave the server, kill displayMsThread
        if message == "--leave":
            print("You have now left the server.")
            isActive = False
            sys.exit()
        
        # Print help text
        elif message == "--help":
            print(helpText)
        
        # Otherwise send message to server
        else:
            try:
                client.send(encodeMessage(message))
            except Exception as e:
                print("Your message could not be delivered due to following error:\n", e)

# Kill displayMsThread
except KeyboardInterrupt:
    isActive = False