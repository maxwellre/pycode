import sys
import socket
import numpy
import csv
import time

'''Configuration'''
HOST = '192.168.4.1'  # The server's hostname or IP address
PORT = 80        # The port used by the server

'''Function'''
def connectWiFi():
    isConnected = False

    sockHandle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockHandle.connect((HOST, PORT))
    while not isConnected: # try to establish a WiFi connection
        sockHandle.sendall(b'pcprogram') # "Handshake" protocol
        # sockHandle.sendall(b'vrheadset') # Just for debugging WiFiCtrlPC

        for count in range(1000):
            ans = sockHandle.recv(1024)
            if ans.decode() == "high-voltage-controller-is-ready": # "Handshake" protocol matched
                isConnected = True
                print("Successful connection to high voltage controller")
                break
            print("Waiting ... %d" % count)
            time.sleep(0.5)

    return sockHandle

'''-------------------------------------------------------------------------------------------------------------'''
if __name__ == '__main__':
    # Initialization
    sock0 = connectWiFi()

    trial = 0

    reconnectNum = 0

    while(True):
        currentTime = time.strftime("%H-%M-%S", time.localtime())
        with open(("./TMPData/Data%s_VR_t%02d.txt" % (currentTime, trial)), 'w') as txtFile:
            dataStr = ""
            while dataStr != "stream-end":
                datastream = sock0.recv(16384)
                if(datastream):
                    dataStr = datastream.decode()
                    # print(dataStr)

                    if(dataStr == "reconnect"):
                        time.sleep(1)
                        sock0 = connectWiFi()
                        reconnectNum += 1
                        print("Reconnect %d" % reconnectNum)
                    else:
                        txtFile.write(dataStr)
            print("Data Saved Successfully")
        trial = trial+1
        #break#debug