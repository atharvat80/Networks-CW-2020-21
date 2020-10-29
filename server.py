"""
Author : 000802977, Atharva Tidke
Project : Networks Coursework
"""

import socket, select, sys, pickle, logging

headerLength = 10
hostname = socket.gethostbyname(socket.gethostname())
logging.basicConfig(
    level=logging.DEBUG, 
    filename="server.log", filemode="w",
    format="%(asctime)s  %(levelname)s %(message)s")

# Validate the port number
try:
    port = int(sys.argv[1])
except:
    print("Invalid port number")
    sys.exit()


# Setup the server and listen for requests
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPV4 , TCP
server.bind((hostname, port))
server.listen(5)
print("Listening for connections on {}:{}".format(hostname, port))
logging.info("Listening for connections on {}:{}".format(hostname, port))


# Sockets is the list of connected sockets and 
# clients stores the username associated with each socket
sockets = [server]
clients = {server : "server"}


def encodeMessage(message):
    message = pickle.dumps(message)
    # Add the message length in bytes in the header so the clients knows 
    # how many bytes to receive before displaying the message
    return bytes("{:<{}}".format(len(message), headerLength), "utf-8") + message


def receiveMessage(clientSocket):
    try:
        messageHeader = clientSocket.recv(headerLength)
        # If we received no data ignore, could be the case that they sent empty message
        if not len(messageHeader):
            return False
        # Otherwise return the data we did receive
        else:
            messageLength = int(messageHeader.decode("utf-8").strip())
            messageData = clientSocket.recv(messageLength)
            return pickle.loads(messageData)
    except:
        return False


def sendMessage(from_, to, message, exceptions = []):
    for soc in to:
        # Send message to every socket in to except the sender, server and exceptions (if any)
        if soc not in [from_, server] + exceptions:
            try:
                soc.send(encodeMessage({"from": clients[from_], "message": message}))
                logging.info("Sent a message from {} to {}".format(clients[from_], clients[soc]))
            except:
                print("Error Sending message")
                logging.error("Could not send {} from {} to {}".format(message, clients[from_], clients[soc]))


def newClient(clientSocket, clientAddress, sockets = sockets, clients = clients):
    username = receiveMessage(clientSocket)
    if username != False:
        # Register the new user
        sockets.append(clientSocket)
        clients[clientSocket] = username
        
        # Welcome the user and inform the others
        sendMessage(server, [clientSocket], "Welcome to the server " + username + "!")
        sendMessage(server, sockets, username + " has joined the server.", [clientSocket])
        
        print("Accepted a new connection from {} {}:{}".format(username, clientAddress[0], clientAddress[1]))
        logging.info("Accepted a new connection from {} {}:{}".format(username, clientAddress[0], clientAddress[1]))


def removeClient(clientSocket):
    sockets.remove(clientSocket)
    del clients[clientSocket]

try:
    while True:
        r, w, x = select.select(sockets, [], sockets)
        
        # Handle sockets currently being monitored
        for notifiedSocket in r:
            # if the notified socket is the server i.e. a new client has connected
            if notifiedSocket == server:
                clientSocket, clientAddress = server.accept()
                newClient(clientSocket, clientAddress)
            
            # else a existing socket is sending a message
            else:
                message = receiveMessage(notifiedSocket)
                if message == False:
                    # Remove the client who left and notify the other clients
                    clientWhoLeft = clients[notifiedSocket]
                    removeClient(notifiedSocket)
                    print("Closed connection from", clientWhoLeft)
                    sendMessage(server, sockets, clientWhoLeft + " has left the server.")
                    logging.info("Removed client " + clientWhoLeft)
                
                # Send the list of current users
                elif message == "--list":
                    users = "\n\t@".join(clients.values())
                    sendMessage(server, [notifiedSocket], "Currently connected users are: \n\t@" + users + "\n")
                    
                else:
                    # A private message
                    if message.startswith("@"):
                        message = message.split(" ", 1)
                        if message[0][1:] in clients.values() and len(message) >= 2:
                            for soc, user in clients.items():
                                if user == message[0][1:]:
                                    sendMessage(notifiedSocket, [soc], '(whispered) '+ message[1])
                        else:
                            sendMessage(server, [notifiedSocket], 
                            "Your message could not be delievered check\n - If the user is connected using the --list command \n - Your message was not empty")
                    
                    # Change username
                    elif message.startswith("--changeName"):
                        try:
                            message = message.split(" ")
                            oldName = clients[notifiedSocket]
                            clients[notifiedSocket] = message[1]
                            sendMessage(server, [notifiedSocket], "Your username has been changed to {}.".format(message[1]))
                            sendMessage(server, sockets, "{} changed their username to {}.".format(oldName, message[1]), [notifiedSocket])
                        except:
                            sendMessage(server, [notifiedSocket], "Your username could not be changed.")

                    # A group message
                    else:
                        sendMessage(notifiedSocket, sockets, message)

        # handle socket exceptions
        for notifiedSocket in x:
            removeClient(notifiedSocket)

except KeyboardInterrupt:
    logging.info("Stopped the server")

except Exception as e:
    logging.error(e)

server.close()
sys.exit()