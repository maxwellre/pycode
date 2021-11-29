import ctypes
import numpy as np
from ctypes import util
from ctypes import CDLL
from os import path
import matplotlib.pyplot as plt
import matplotlib.animation as animation

'''Marco'''
PALM_POSI = 0
DIGIT1_DISTAL = [1,2]
DIGIT2_DISTAL = [3,4]
DIGIT3_DISTAL = [5,6]
DIGIT4_DISTAL = [7,8]
DIGIT5_DISTAL = [9,10]

'''Configration'''
transCoordinate = True
calibrationFilePath = './CalibrationFile/Calibration_at21-12-37.csv'

'''Import LeapC libraray'''
sdkPath = path.join(path.dirname(__file__), 'LeapSDK')

libPath = ctypes.util.find_library(path.join(sdkPath, 'LeapC'))
leapc = ctypes.CDLL(libPath)

libPath = ctypes.util.find_library(path.join(sdkPath, 'libExampleConnection'))
leapc_lib = ctypes.CDLL(libPath)

leapc_lib.getOneFrame.argtypes = [ctypes.POINTER(ctypes.c_float)] # Pass pointer to a float array to acquire data
leapc_lib.getOneFrame.restype = ctypes.c_int

'''Functions'''
def getTrackData():
    onetrackData = np.zeros((33,), dtype=np.float32) # Warning: DO NOT modify the length of the array!

    trackres = leapc_lib.getOneFrame(onetrackData.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))

    onetrackData = onetrackData.reshape((-1,3))

    return onetrackData, trackres

def animUpdate(frame_i, palmPoint, digit1DistalLine, digit2DistalLine, digit3DistalLine, digit4DistalLine,
               digit5DistalLine):
    data1f, trackres = getTrackData()

    if(trackres == 1):
        #print("Frame = %d" % frame_i); print(data1f)

        if transCoordinate:
            data1f = data1f - offSet
            data1f = np.matmul(data1f, mapRot)

        palmPoint.set_data(data1f[PALM_POSI,:2])
        palmPoint.set_3d_properties(data1f[PALM_POSI,2])

        digit1DistalLine.set_data(data1f[DIGIT1_DISTAL,0], data1f[DIGIT1_DISTAL,1])
        digit1DistalLine.set_3d_properties(data1f[DIGIT1_DISTAL,2])

        digit2DistalLine.set_data(data1f[DIGIT2_DISTAL, 0], data1f[DIGIT2_DISTAL, 1])
        digit2DistalLine.set_3d_properties(data1f[DIGIT2_DISTAL, 2])

        digit3DistalLine.set_data(data1f[DIGIT3_DISTAL, 0], data1f[DIGIT3_DISTAL, 1])
        digit3DistalLine.set_3d_properties(data1f[DIGIT3_DISTAL, 2])

        digit4DistalLine.set_data(data1f[DIGIT4_DISTAL, 0], data1f[DIGIT4_DISTAL, 1])
        digit4DistalLine.set_3d_properties(data1f[DIGIT4_DISTAL, 2])

        digit5DistalLine.set_data(data1f[DIGIT5_DISTAL, 0], data1f[DIGIT5_DISTAL, 1])
        digit5DistalLine.set_3d_properties(data1f[DIGIT5_DISTAL, 2])

'''------------------------------------------------------------------------------------------------------------------'''
dispRange = [-100, -100, -100, 400, 200, 400]
if transCoordinate:
    dispRange = [100, -100, -10, -400, 400, 300]

    calibData = np.genfromtxt(calibrationFilePath, delimiter=',')
    print(calibData)
    mapRot = np.matmul(calibData[:3,:], [[-1,0,0],[0,1,0],[0,0,-1]]) # Need to rotate 180 around Y axis
    offSet = calibData[3,:]

if __name__ == '__main__':
    leapc_lib.OpenConnection()

    fig1 = plt.figure(figsize=(12, 7))  # Initialize a figure
    ax = fig1.add_subplot(111, projection='3d')

    palmPoint = ax.plot(0.0, 0.0, 0.0, '.')[0]
    digit1DistalLine = ax.plot([], [], [], '-', c='b')[0]
    digit2DistalLine = ax.plot([], [], [],'-', c='r')[0]
    digit3DistalLine = ax.plot([], [], [], '-', c='b')[0]
    digit4DistalLine = ax.plot([], [], [], '-', c='b')[0]
    digit5DistalLine = ax.plot([], [], [], '-', c='b')[0]

    if transCoordinate:
        cornerLocTrans = calibData[3:,:] - offSet  # Shifted to origin
        cornerLocTrans = np.matmul(cornerLocTrans, mapRot)
        ax.plot(cornerLocTrans[[0, 1], 0], cornerLocTrans[[0, 1], 1], cornerLocTrans[[0, 1], 2], '-', c='k')
        ax.plot(cornerLocTrans[[1, 2], 0], cornerLocTrans[[1, 2], 1], cornerLocTrans[[1, 2], 2], '-', c='k')
        ax.plot(cornerLocTrans[[2, 3], 0], cornerLocTrans[[2, 3], 1], cornerLocTrans[[2, 3], 2], '-', c='k')
        ax.plot(cornerLocTrans[[0, 3], 0], cornerLocTrans[[0, 3], 1], cornerLocTrans[[0, 3], 2], '-', c='k')

    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_zlabel('Z (mm)')
    ax.set_xlim3d([dispRange[0], dispRange[0] + dispRange[3]])
    ax.set_ylim3d([dispRange[1], dispRange[1] + dispRange[4]])
    ax.set_zlim3d([dispRange[2], dispRange[2] + dispRange[5]])
    ax.set_box_aspect([dispRange[3], dispRange[4], dispRange[5]])

    while not leapc_lib.IsConnected:
        leapc_lib.millisleep(100)
    print("Leap Motion Connected")

    # Visualize hand tracking using an Animation
    ani = animation.FuncAnimation(fig1, animUpdate, fargs=(palmPoint, digit1DistalLine, digit2DistalLine,
          digit3DistalLine, digit4DistalLine, digit5DistalLine), interval=50)

    # End
    plt.show()

    leapc_lib.DestroyConnection()

