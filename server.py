"""
Author      : 000802977, Atharva Tidke
Description : Server file for the networks coursework
"""

import socket
import select
import sys
import pickle
import logging

HEADERLEN = 10
hostname = socket.gethostbyname(socket.gethostname())
logging.basicConfig(
    level=logging.DEBUG,
    filename="server.log", filemode="w",
    format="%(asctime)s  %(levelname)s %(message)s")

try:
    port = int(sys.argv[1])
except:
    print("Error: Invalid port number")
    sys.exit()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPV4 , TCP
server.bind((hostname, port))
server.listen()
logging.info("Listening for connections on {}:{}".format(hostname, port))
print("Listening for connections on {}:{}".format(hostname, port))


# Sockets is the list of connected sockets and 
# clients stores the username associated with each socket
sockets = [server]
clients = {server: "Server"}


def encodeMessage(message):
    """Adds the message length in bytes as the header of the message so the clients knows 
    how many bytes to receive before displaying the message"""
    message = pickle.dumps(message)
    return bytes(str(len(message)).ljust(HEADERLEN), "utf-8") + message


def receiveMessage(clientSocket):
    """Identifies message length, receives, decodes and returns it
    returns False if empty or can't be decoded"""
    try:
        messageHeader = clientSocket.recv(HEADERLEN)
        if not len(messageHeader):
            return False
        else:
            messageLength = int(messageHeader.decode("utf-8").strip())
            messageData = clientSocket.recv(messageLength)
            return pickle.loads(messageData)
    except:
        return False


def sendMessage(from_, to, message, exceptions=[]):
    """Sends a message to every socket in 'to' except the sender, server 
    and sockets in exceptions (if any)"""
    for soc in to:
        if soc not in [from_, server] + exceptions:
            try:
                soc.send(encodeMessage({"from": clients[from_], "message": message}))
            except Exception as e:
                print("Error Sending message\n",e)
                logging.error("Could not send {} from {} to {}".format(
                    message, clients[from_], clients[soc]))


def newClient(clientSocket, clientAddress):
        username = receiveMessage(clientSocket)
        if username != False and username not in clients.values():
            sockets.append(clientSocket)
            clients[clientSocket] = username
            sendMessage(server, [clientSocket], "Welcome to the server " + username + "!")
            sendMessage(server, sockets, username+" has joined the server.", [clientSocket])
            logging.info("Accepted a new connection from {} {}:{}".format(
                username, clientAddress[0], clientAddress[1]))
            print("Accepted a new connection from {} {}:{}".format(
                username, clientAddress[0], clientAddress[1]))
        else:
            clientSocket.send(encodeMessage({
                "from": "Server", 
                "message": "Your chosen user is invalid or not available," 
                          + " please try again with a different username."}))
            clientSocket.close()


def removeClient(clientSocket):
    sendMessage(server, sockets, clients[clientSocket] + " has left the server.")
    logging.info("Removed client " + clients[clientSocket])
    print("Closed connection from", clients[clientSocket])
    sockets.remove(clientSocket)
    del clients[clientSocket]


def sendClientList(clientSocket):
    users = "\n  @".join(clients.values())
    sendMessage(server, [clientSocket], "Currently connected users are: \n  @" + users + "\n")
    logging.info("{} requested the list of connected clients".format(clients[clientSocket]))


def changeName(clientSocket, oldname, newname):
    clients[clientSocket] = newname
    sendMessage(server, [clientSocket], 
        "Your username has been changed from @{} to @{}".format(oldname, newname))
    sendMessage(server, sockets, 
        "@{} changed their name to @{}".format(oldname, newname), [clientSocket])
    logging.info("@{} changed their name to @{}".format(oldname, newname))
    


def privateMsg(sender, receiver, message):
    sender_soc = None
    for soc in clients.keys():
        if clients[soc] == receiver:
            sender_soc = soc
            break    
   
    if sender_soc != None:
        sendMessage(sender, [sender_soc], '(whispered) '+message)
        logging.info("{} sent a message to {}".format(clients[sender], receiver))
    else:
        sendMessage(server, [sender], to + " not found in active users.")


def groupMsg(sender, message):
    sendMessage(sender, sockets, message)
    logging.info(clients[sender] + " sent a group message")


try:
    while True:
        r, w, x = select.select(sockets, [], sockets)
        for notifiedSocket in r:
            if notifiedSocket == server:
                clientSocket, clientAddress = server.accept()
                newClient(clientSocket, clientAddress)
            else:
                message = receiveMessage(notifiedSocket)
                if message == False: 
                    removeClient(notifiedSocket)
                elif message == "--list":
                    sendClientList(notifiedSocket)
                else:
                    if message.startswith("@"):
                        try:
                            to, message = message[1:].split(" ", 1)
                            privateMsg(notifiedSocket, to, message)
                        except:
                            sendMessage(server, [notifiedSocket], "Can't send an empty message.")
                    elif message.startswith("--changeName"):
                        newname = message[12:].lstrip()
                        if newname != '' and newname not in clients.values():
                            changeName(notifiedSocket, clients[notifiedSocket], newname)
                        else:
                            sendMessage(server, [notifiedSocket], "Can't change your username to " + newname)
                    else:
                        groupMsg(notifiedSocket, message)
        
        # handle socket exceptions
        for notifiedSocket in x:
            removeClient(notifiedSocket)

except KeyboardInterrupt:
    logging.info("Server stopped using keyboard interrupt")

except Exception as e:
    logging.error(e)

server.close()
logging.info("Server shut down")