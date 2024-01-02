import sys
import serial
import socket
import numpy as np
import csv
import time
import matplotlib.pyplot as plt

'''Configuration'''

''' Initialize serial port '''
dataSerial = serial.Serial('com6', 115200)

'''Unit coversion'''
GSCALE = 0.001952 # 1.952 mg/digit (±16 g in High-Performance Mode)

measurementTime = 5

'''Function'''
def triggerStartMeasurement(sampleNum=10000):
    dataSerial.write(b't')
    time.sleep(0.5)
    dataSerial.write(("%d\r" % sampleNum).encode())
    time.sleep(0.5)

def twoComplement16bit(hexData):
    return -(hexData & 0x8000) | (hexData & 0x7fff)

'''-------------------------------------------------------------------------------------------------------------'''
if __name__ == '__main__':
    trial = 0 # Trial number used for saved file

    sampleNum = measurementTime * 880  # Number of total sample points (each sample contains 6 bytes: X Y Z)

    # Initialize the measurement
    triggerStartMeasurement(sampleNum)

    t0 = time.time()
    dataBytes = dataSerial.read(sampleNum * 12) # Stream data via serial port
    totalTime = time.time()-t0

    dataSerial.close()

    Fs = sampleNum/totalTime
    print("Streaming %d data in %.2f s (Fs = %.2f Hz)" % (sampleNum, totalTime, Fs))

    currentTime = time.strftime("%H-%M-%S", time.localtime())
    saveFileName = ("D:/TMPData/Data%s_t%02d_Fs%.0fHz.csv" % (currentTime, trial, Fs))
    with open(saveFileName, 'w', newline='') as csvFile:
        writer = csv.writer(csvFile)
        for i in range(0, len(dataBytes), 12):
            dataX = dataBytes[i+2:i+4] + dataBytes[i:i+2] # Group MSB and LSB together for x-axis data
            dataY = dataBytes[i+6:i+8] + dataBytes[i+4:i+6] # Group MSB and LSB together for y-axis data
            dataZ = dataBytes[i+10:i+12] + dataBytes[i+8:i+10] # Group MSB and LSB together for z-axis data

            if(len(dataX) > 0 and len(dataY) > 0 and len(dataZ) > 0):
                dataX = twoComplement16bit(int(dataX,16)) >> 2 # Convert twoComplement data for x-axis
                dataY = twoComplement16bit(int(dataY,16)) >> 2 # Convert twoComplement data for y-axis
                dataZ = twoComplement16bit(int(dataZ,16)) >> 2 # Convert twoComplement data for z-axis

                writer.writerow([dataX, dataY, dataZ])
        print("Data Saved Successfully")

    ''' Visualize data '''
    accData = np.genfromtxt(saveFileName, delimiter=',')
    t = np.arange(accData.shape[0])/Fs
    fig1, ax = plt.subplots(3,1,dpi=72, figsize=(16, 6))
    ax[0].plot(t, accData[:, 0] * GSCALE)
    ax[1].plot(t, accData[:, 1] * GSCALE)
    ax[2].plot(t, accData[:, 2] * GSCALE)
    ax[1].set_ylabel("Acceleration (g)")
    ax[2].set_xlabel("Time (s)")
    plt.show()