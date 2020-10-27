import socket, select, sys, pickle

d = {"from":"Server", "message": "You are not connected to the server"}

def padMsg(msg):
	msg = pickle.dumps(msg)
	"""Pad message to the left so that it can be sent in chunks of constant size"""
	headerSize = 10
	return bytes(f"{len(msg):<{headerSize}}", "utf-8") + msg

# Validate the port number
try:
	port = int(sys.argv[1])
except:
	print("Invalid port number")
	sys.exit()

# Setup the server and listen for requests
hostname = socket.gethostbyname(socket.gethostname())
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPV4 , TCP
server.bind((hostname, port))
server.listen(5)
print(f"Listening for connections on {hostname}:{port}...")

while True:
	clientsocket, clientaddress = server.accept()
	print(f"Connection from {clientaddress} has been established.")
	clientsocket.send(padMsg(d))