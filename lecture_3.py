import socket
import threading

def receiver(address):
    with socket.socket() as s:
        s.bind(address)
        s.listen(1)
        while True:
            connection, (peer_ip,) = s.accept()
            with connection:
                message = connection.recv(1024).decode()
                print("{}: {}".format(peer_ip, message))

def sender(address):
    with socket.socket() as s:
        s.connect(address)
        s.send(bytes("Hello from breakout room 2!", 'utf-8'))

def start():
    threading.Thread(target=receiver, args=(('',8080),)).start()
    threading.Thread(target=sender, args=(('3.129.5.255', 8080),)).start()

if __name__ == "__main__":
    start()