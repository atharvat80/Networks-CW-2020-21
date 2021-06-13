"""
Author      : Atharva Tidke
Description : Server file for the networks coursework
"""

import socket
import select
import sys
import json
import logging

HEADERLEN = 20
HELPTEXT = """
Here is the list of commands available to you:

    --rename [username]   Change your username
    --help                Displays this message again
    --leave               Leave the server
    --listall             List all connected users
    --list                List all other connected users
    @username message     Whisper something to a connected users
"""

logging.basicConfig(
    level=logging.DEBUG,
    filename="server.log", filemode="w",
    format="%(asctime)s %(levelname)s %(message)s")

# Read and validate port number of the server
try:
    port = int(sys.argv[1])
    if port < 1 or port > 65535:
        raise ValueError
except Exception as e:
    print("Following error occurred while reading the port number:\n", str(e))
    print("This is because the port number was either not provided or was provided and invalid.")
    sys.exit()

# Setup the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPV4 , TCP
hostname = socket.gethostbyname(socket.gethostname())
try:
    server.bind((hostname, port))
    server.listen()
except Exception as e:
    print("Following error occurred while setting up the server:\n", str(e))
    sys.exit()
else:
    logging.info("Listening for connections on %s:%d" % (hostname, port))
    print("Listening for connections on %s:%d" % (hostname, port))

# Sockets is the list of connected sockets
sockets = [server]
# clients stores the username associated with each socket in sockets
clients = {server: "Server"}


def encode_msg(message):
    """Adds the message length in bytes as the header of the message so the clients knows 
    how many bytes to receive before displaying the message"""
    message = json.dumps(message)
    header = str(len(message)).ljust(HEADERLEN)
    return (header + message).encode()


def receive_msg(client_socket):
    """Identifies message length, receives, decodes and returns it
    returns False if empty or can't be decoded"""
    try:
        message_header = client_socket.recv(HEADERLEN)
        if not len(message_header):
            return False
        else:
            message_length = int(message_header.decode("utf-8").strip())
            message_data = client_socket.recv(message_length)
            return json.loads(message_data)
    except Exception as exp:
        logging.error(str(exp) + " while receiving message from " + clients[client_socket])
        return False


def send_msg(sender, receivers, message, exceptions=None):
    """Sends a message to every socket in receivers except sockets in exceptions (if any)"""
    exceptions = [server] if exceptions is None else exceptions + [server]
    for receiver in receivers:
        if receiver not in exceptions:
            try:
                receiver.send(encode_msg({"from": clients[sender], "message": message}))
            except Exception as exc:
                logging.error("%s while sending message from %s to %s" % (str(exc), clients[sender], clients[receiver]))


def new_client(client_socket, client_address):
    """Handle new client by validating their username, update sockets and clients if valid"""
    username = receive_msg(client_socket)
    if (username is not False) and (len(username.strip()) > 0) and (username not in clients.values()):
        sockets.append(client_socket)
        clients[client_socket] = username
        send_msg(server, [client_socket], "Welcome to the server %s!\n%s" % (username, HELPTEXT))
        send_msg(server, sockets, "%s has joined" % username, [client_socket])
        logging.info("New connection from %s:%s as user %s" % (client_address[0], client_address[1], username))
        print("New connection from %s:%s as user %s" % (client_address[0], client_address[1], username))
    else:
        client_socket.send(encode_msg({
            "from": "Server",
            "message": "Your chosen user is invalid or not available, please try again with a different username."
        }))
        client_socket.close()


def remove_client(client_socket):
    """Remove the client by removing client_socket from sockets and clients"""
    send_msg(server, sockets, clients[client_socket] + " left the server")
    logging.info("Closed connection from " + clients[client_socket])
    sockets.remove(client_socket)
    del clients[client_socket]
    client_socket.close()


def send_client_list(client_socket, full=True):
    """Send list of connected users to the socket that requested it"""
    usernames = list(clients.values())
    usernames.remove('Server')
    if not full:
        usernames.remove(clients[client_socket])
    if len(usernames) == 0:
        send_msg(server, [client_socket], "You are the only connected client")
    else:
        send_msg(server, [client_socket], "Currently connected users are: \n  @" + "\n  @".join(usernames))


def change_name(client_socket, old_name, new_name):
    """Validate and update the username if client wants to change it"""
    if new_name != '' and new_name not in clients.values():
        clients[client_socket] = new_name
        send_msg(server, [client_socket], "Your username has been changed from @%s to @%s" % (old_name, new_name))
        send_msg(server, sockets, "%s changed their name to %s" % (old_name, new_name), [client_socket])
        logging.info("@%s changed their name to @%s" % (old_name, new_name))
    else:
        send_msg(server, [client_socket], "Can't change your username to %s" % new_name)


def private_msg(sender, receiver, message):
    """Send message from sender to receiver"""
    receiver_soc = None
    for soc_name in clients.keys():
        if clients[soc_name] == receiver:
            receiver_soc = soc_name
            break
    if receiver_soc is None:
        send_msg(server, [sender], receiver + " not found in active users")
    elif sender != receiver_soc:
        send_msg(sender, [sender, receiver_soc], '(whispered) ' + message)
        logging.info("%s sent '%s' to %s" % (clients[sender], message, receiver))


def group_msg(sender, message):
    """Send a group message"""
    send_msg(sender, sockets, message)
    logging.info(clients[sender] + " sent '%s' to everyone" % message)


def handle_msg(message, sender):
    """Handle incoming messages by parsing parsing it according to the protocol detailed in the documentation"""
    if message is False:
        remove_client(sender)
    elif message == "--leave":
        logging.info(clients[sender] + " asked to leave the chat")
        remove_client(sender)
    elif message == "--help":
        send_msg(server, [sender], HELPTEXT)
        logging.info(clients[sender] + " asked for the help text")
    elif message == "--listall":
        send_client_list(sender)
        logging.info(clients[sender] + " requested the list of all connected clients")
    elif message == "--list":
        send_client_list(sender, False)
        logging.info(clients[sender] + " requested the list of other connected clients")
    elif message.startswith("--rename"):
        new_name = message[8:].strip()
        change_name(sender, clients[sender], new_name)
    elif message.startswith('--'):
        send_msg(server, [sender], "Command not recognised." + HELPTEXT)
    else:
        if message.startswith("@"):
            try:
                to, message = message[1:].split(" ", 1)
                if message.strip() == '':
                    raise ValueError
            except ValueError:
                send_msg(server, [sender], "Can't send an empty message")
            else:
                private_msg(sender, to, message)
        else:
            group_msg(sender, message)


# Loop over all connected sockets
try:
    while True:
        r, w, x = select.select(sockets, [], sockets)
        for notifiedSocket in r:
            if notifiedSocket == server:
                clientSocket, clientAddress = server.accept()
                new_client(clientSocket, clientAddress)
            else:
                received_message = receive_msg(notifiedSocket)
                handle_msg(received_message, notifiedSocket)

        # handle socket exceptions
        for notifiedSocket in x:
            remove_client(notifiedSocket)

except KeyboardInterrupt:
    logging.info("Server stopped using keyboard interrupt")

except Exception as e:
    logging.error(e)

# Close all connections
for soc in sockets[1:]:
    remove_client(soc)
server.close()
logging.info("Server shut down")
