import socket, sys, errno, pickle, threading
headerLength = 10

# Validate given arguments
try:
    username = sys.argv[1]
    port = int(sys.argv[2])
    hostname = sys.argv[3]
except:
    print("Arguments missing, please specify the username you would like to connect as and the port and hostname of the server")
    sys.exit()


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    print("Connecting to the server...\n")
    client.connect((hostname, port))
except Exception as e:
    print("Could not connect to the server due to following error :\n", e)
    sys.exit()

client.setblocking(False)

# Encode python dictionaries as byte objects so they can be transported
# This also adds the length of the message at the beginning so check how many bytes to read 
def encodeMessage(message):
    message = pickle.dumps(message)
    return bytes(f"{len(message):<{headerLength}}", "utf-8") + message
    

# Send username
client.send(encodeMessage(username))


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
                print(f"[{(message['from']).ljust(10)}] > {message['message']}")  
        
        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('Reading error: ' + str(e))
                sys.exit()

        except Exception as e:
            print('Reading error: ' + str(e))
            sys.exit()

# Start displaying incoming messages
threading.Thread(target=displayMessages).start()

# Check for keyboard interrupt
try:
    while True:
        message = input() #f"[{username}] > "
        # send message if not empty
        if message.strip() == "leave":
            print("You have now left the server.")
            isActive = False
            sys.exit()
        elif message:
            try:
                client.send(encodeMessage(message))
            except Exception as e:
                print("Your message could not be delivered due to following error:\n", e)

except KeyboardInterrupt:
    isActive = False