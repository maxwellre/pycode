import socket

HOST = '192.168.4.1'  # The server's hostname or IP address
PORT = 80        # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'Hello, WiFi world !!')
    data = s.recv(1024)

print('Received', repr(data))



# from sockets.python3.server import Server
# class MyServer(Server):
#     def act_on(self, data, addr):
#         # Do something with data (in bytes) and return a string.
#         return data.decode()
#
# server = MyServer(listening_address=('192.168.4.1', 80))
# server.listen()


#
# host = '192.168.4.1' #socket.gethostname()   # get local machine name
# port = 8080
#
# s = socket.socket()
# s.bind((host, port))
#
# s.listen(1)
#
# client_socket, addr = s.accept()
# print("Connection from: " + str(addr))

# # create an INET, STREAMing socket
# serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# # bind the socket to a public host, and a well-known port
# serversocket.bind((socket.gethostname(), 80))
# # become a server socket
# serversocket.listen(5)