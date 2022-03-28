import sys
import socket
import numpy
import csv
import time

'''Configuration'''
HOST = '192.168.4.1'  # The server's hostname or IP address
PORT = 80        # The port used by the server

'''-------------------------------------------------------------------------------------------------------------'''
if __name__ == '__main__':
    # Initialization
    isConnected = False

    sock0 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock0.connect((HOST, PORT))
    while not isConnected: # try to establish a WiFi connection
        sock0.sendall(b'pcprogram') # "Handshake" protocol

        for count in range(1000):
            ans = sock0.recv(1024)
            if ans.decode() == "high-voltage-controller-is-ready": # "Handshake" protocol matched
                isConnected = True
                print("Successful connection to high voltage controller")
                break

    trial = 0

    while(True):
        currentTime = time.strftime("%H-%M-%S", time.localtime())
        with open(("./CurrentData/Data%s_VR_t%02d.txt" % (currentTime, trial)), 'w') as txtFile:
            dataStr = ""
            while dataStr != "stream-end":
                datastream = sock0.recv(16384)
                if(datastream):
                    dataStr = datastream.decode()
                    print(dataStr)
                    txtFile.write(dataStr)
        trial = trial+1
        #break#debug