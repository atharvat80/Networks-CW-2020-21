"""
Author : 000802977, Atharva Tidke
Project : Networks Coursework
Based on : https://pythonprogramming.net/server-chatroom-sockets-tutorial-python-3/
"""
import socket, select, sys, pickle

headerLength = 10
hostname = socket.gethostbyname(socket.gethostname())

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
print("Listening for connections on {}:{}...".format(hostname, port))


# Connected clients (A list of sockets)
sockets = [server]
clients = {server : "server"}


def encodeMessage(message):
    message = pickle.dumps(message)
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
        if soc not in [from_, server] + exceptions:
            try:
                soc.send(encodeMessage({"from": clients[from_], "message": message}))
            except:
                print("Error Sending message")


def newClient(clientSocket, clientAddress, sockets = sockets, clients = clients):
    username = receiveMessage(clientSocket)
    if username != False:
        sockets.append(clientSocket)
        clients[clientSocket] = username
        sendMessage(server, [clientSocket], "Welcome to the server " + username + "!")
        sendMessage(server, sockets, username + " has joined the server.", [clientSocket])
        print("Accepted a new connection from", username, clientAddress[0], ":", clientAddress[1])


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
                
                elif message == "--list":
                    users = "\n @".join(clients.values())
                    sendMessage(server, [notifiedSocket], "Currently connected users are: \n @" + users + "\n")
                    
                else:
                    if message.startswith("@"):
                        message = message.split(" ", 1)
                        if message[0][1:] in clients.values() and len(message) >= 2:
                            for soc, user in clients.items():
                                if user == message[0][1:]:
                                    sendMessage(notifiedSocket, [soc], '(whispered) '+ message[1])
                        else:
                            sendMessage(server, [notifiedSocket], 
                            "Your message could not be delievered check\n - If the user is connected using the --list command \n - Your message was not empty")
                    
                    elif message.startswith("--changeName"):
                        message = message.split(" ", 1)
                        try:
                            clients[notifiedSocket] == message[1]
                            sendMessage(server, [notifiedSocket], "Your username has been changed to " + message[1]  + ".")
                        except:
                            sendMessage(server, [notifiedSocket], "Your username could not be changed.")

                    else:
                        sendMessage(notifiedSocket, sockets, message)

        # handle socket exceptions
        for notifiedSocket in x:
            removeClient(notifiedSocket)
except KeyboardInterrupt:
    server.close()
    sys.exit()