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
    if to == "all":
        for soc in sockets:
            if soc not in [from_, server] + exceptions:
                soc.send(encodeMessage({"from": clients[from_], "message": message}))
    else:
        for soc, user in clients:
            if user == to:
                soc.send(encodeMessage({"from": clients[from_], "message": message}))


def newClient(clientSocket, clientAddress, sockets = sockets, clients = clients):
    username = receiveMessage(clientSocket)
    if username is False:
        pass
    else:
        sockets.append(clientSocket)
        clients[clientSocket] = username
        clientSocket.send(encodeMessage({
            "from":"server", 
            "message": "Welcome to the server " + username + "!"
        }))
        sendMessage(server, "all", username + " has joined the server.", [clientSocket])
        print("Accepted a new connection from", username, clientAddress[0], ":", clientAddress[1])


def removeClient(clientSocket):
    sockets.remove(clientSocket)
    del clients[clientSocket]


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
            if message is False:
                # Remove the client who left and notify the other clients
                clientWhoLeft = clients[notifiedSocket]
                removeClient(notifiedSocket)
                print("Closed connection from", clientWhoLeft)
                sendMessage(server, "all", clientWhoLeft + " has left the server.")
            else:
                sendMessage(notifiedSocket, "all", message)

    # handle socket exceptions
    for notifiedSocket in x:
        removeClient(notifiedSocket)