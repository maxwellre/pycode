import sys
import socket
import numpy as np
import csv
import time
import matplotlib.pyplot as plt

'''Configuration'''
HOST = '192.168.4.1'  # The server's hostname or IP address
PORT = 80 # The port used by the server

'''Unit coversion'''
GSCALE = 0.001952 # 1.952 mg/digit (±16 g in High-Performance Mode)

measurementTime = 3

'''Function'''
def twoComplement16bit(hexData):
    return -(hexData & 0x8000) | (hexData & 0x7fff)
def connectWiFi(sampNum = 2):
    isConnected = False

    sockHandle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockHandle.connect((HOST, PORT))

    settingMsg = ("sample%d" % sampleNum).encode()
    while not isConnected: # try to establish a WiFi connection
        sockHandle.sendall(settingMsg) # "Handshake" protocol containing settings
        for count in range(1000):
            ans = sockHandle.recv(1024)
            if ans.decode() == "accnet-ready": # "Handshake" protocol matched
                isConnected = True
                print("Successful connection to ACC network")
                ans = sockHandle.recv(1024) # Clean buffer
                break
            print("Waiting ... %d" % count)
            time.sleep(0.5)

    return sockHandle

'''-------------------------------------------------------------------------------------------------------------'''
if __name__ == '__main__':
    trial = 0 # Trial number used for saved file
    retryNum = 3 # Number of retry to get data from streaming buffer before data receiver stopped

    sampleNum = measurementTime *100 #* 2230  # Number of total sample points (each contains 6 bytes: X Y Z)

    # Initialization
    sock0 = connectWiFi()

    currentTime = time.strftime("%H-%M-%S", time.localtime())

    dataBytes = ""

    t0 = time.time()
    while(retryNum > 0):
        datastream = sock0.recv(256)
        if (datastream):
            dataBytes = dataBytes + datastream.decode()
        else:
            retryNum = retryNum - 1
            time.sleep(0.5)

    totalTime = time.time()-t0
    Fs = sampleNum/totalTime
    print("Streaming %d data in %.2f s (Fs = %.2f Hz)" % (sampleNum, totalTime, Fs))

    saveFileName = ("D:/TMPData/Data%s_t%02d_Fs%.0fHz.csv" % (currentTime, trial, Fs))
    with open(saveFileName, 'w', newline='') as csvFile:
        writer = csv.writer(csvFile)
        for i in range(0, len(dataBytes), 12):
            dataX = dataBytes[i+2:i+4] + dataBytes[i:i+2]
            dataY = dataBytes[i+6:i+8] + dataBytes[i+4:i+6]
            dataZ = dataBytes[i+10:i+12] + dataBytes[i+8:i+10]
            # print([dataX, dataY, dataZ])
            if(len(dataX) > 0 and len(dataY) > 0 and len(dataZ) > 0):
                dataX = twoComplement16bit(int(dataX,16)) >> 2
                dataY = twoComplement16bit(int(dataY,16)) >> 2
                dataZ = twoComplement16bit(int(dataZ,16)) >> 2
                # print([dataX, dataY, dataZ])
                writer.writerow([dataX, dataY, dataZ])
        print("Data Saved Successfully")

    ''' Visualize data '''
    accData = np.genfromtxt(saveFileName, delimiter=',')
    t = np.arange(accData.shape[0])/Fs
    fig1, ax = plt.subplots(3,1,dpi=72, figsize=(8, 5))
    ax[0].plot(t, accData[:, 0] * GSCALE)
    ax[1].plot(t, accData[:, 1] * GSCALE)
    ax[2].plot(t, accData[:, 2] * GSCALE)
    ax[1].set_ylabel("Acceleration (g)")
    ax[2].set_xlabel("Time (s)")
    plt.show()