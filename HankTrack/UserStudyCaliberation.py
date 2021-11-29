import ctypes
import numpy as np
import time
from ctypes import util
from ctypes import CDLL
from os import path
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import socket
from psychopy import core, visual, gui, data, event
from psychopy.tools.filetools import fromFile, toFile
from HandTrackLib import *

'''Marco'''
LED_RED = [1.0,-1.0,-1.0]
LED_GREEN = [-1.0,1.0,-1.0]
LIGHT_GREEN = [-0.5,0.5,-0.5]
DARK_GREEN = [-1.0,-0.5,-1.0]
LIGHT_YELLOW = [0.5,0.5,-0.5]
DARK_YELLOW = [-0.5,-0.5,-1.0]
LIGHT_BLUE = [-0.5,-0.5,0.5]
DARK_BLUE = [-1.0,-1.0,-0.5]

'''Configuration'''
HOST = '192.168.4.1'  # The server's hostname or IP address
PORT = 80        # The port used by the server

'''Import LeapC libraray'''
sdkPath = path.join(path.dirname(__file__), 'LeapSDK')

libPath = ctypes.util.find_library(path.join(sdkPath, 'LeapC'))
leapc = ctypes.CDLL(libPath)

libPath = ctypes.util.find_library(path.join(sdkPath, 'libExampleConnection'))
leapc_lib = ctypes.CDLL(libPath)

leapc_lib.getOneFrame.argtypes = [ctypes.POINTER(ctypes.c_float)] # Pass pointer to a float array to acquire data
leapc_lib.getOneFrame.restype = ctypes.c_int

'''GUI Design'''
window0 = visual.Window([800, 900], pos=[800,50], monitor="testMonitor", units="height", color=[-0.7, -0.7, -0.7])
mouse0 = event.Mouse()
status0 = visual.TextStim(window0, pos=[0.0, 0.3], text='Connecting ...', height=0.05)
message1 = visual.TextStim(window0, pos=[0.0, 0.3], text='Caliberation', height=0.05)

light1 = visual.Circle(window0, pos=[-0.3, 0.45], radius=0.03, fillColor=[0, 0, 0],
                       lineWidth=4, lineColor=[-0.2, -0.2, -0.2])

button1 = visual.Rect(window0, pos=[0.0, 0.0], width=0.45, height=0.12, fillColor=LIGHT_BLUE,
                      lineWidth=1, lineColor='white')
button2 = visual.Rect(window0, pos=[0.0, -0.16], width=0.2, height=0.12, fillColor=LIGHT_YELLOW,
                      lineWidth=1, lineColor='white')
button3 = visual.Rect(window0, pos=[0.0, 0.16], width=0.2, height=0.12, fillColor=LIGHT_BLUE,
                      lineWidth=1, lineColor='white')

button1Text = visual.TextStim(window0, pos=button1.pos, text='Caliberate', height=0.05)
button2Text = visual.TextStim(window0, pos=button2.pos, text='Next', height=0.05)
button3Text = visual.TextStim(window0, pos=button3.pos, text='Save', height=0.05)

'''-------------------------------------------------------------------------------------------------------------'''
'''Functions'''
def refreshWindow():
    message1.draw()
    light1.draw()
    button1.draw()
    button1Text.draw()
    button3.draw()
    button3Text.draw()
    window0.flip()

# def command(sockObj, text, lightObj = None):
#     if(lightObj):
#         lightObj.setFillColor(LED_RED)
#         refreshWindow()
#
#     sockObj.sendall(text.encode())
#     ans = sockObj.recv(1024)
#     while ans.decode() != "command-received":
#         ans = sockObj.recv(1024)
#
#     if (lightObj):
#         lightObj.setFillColor(LED_GREEN)

'''-------------------------------------------------------------------------------------------------------------'''

dispRange = [-100, -100, -100, 400, 200, 400]

if __name__ == '__main__':
    # Initialization
    isHapDevConnected = False # Status = True, if Haptic device is connected

    status0.draw()
    light1.draw()
    window0.flip()

    # Establish connection with the wearable haptic device ---
    # sock0 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock0.connect((HOST, PORT))
    # while not isConnected: # try to establish a WiFi connection
    #     sock0.sendall(b'request-to-connect-high-voltage-controller') # "Handshake" protocol
    #     ans = sock0.recv(1024)
    #     if ans.decode() == "high-voltage-controller-is-ready": # "Handshake" protocol matched
    #         isConnected = True
    #         print("Successful connection to high voltage controller")

    # Establish connection with Leap-motion ---
    leapc_lib.OpenConnection()

    # Display setup ----------------------------------------------------------------------------------------------------
    fig1 = plt.figure()  # Initialize a figure
    figmanager = plt.get_current_fig_manager()
    figmanager.window.setGeometry(50, 50, 750, 900)
    ax = fig1.add_subplot(111, projection='3d')

    palmPoint = ax.plot(0.0, 0.0, 0.0, '.')[0]
    digit1DistalLine = ax.plot([], [], [], '-', c='b')[0]
    digit2DistalLine = ax.plot([], [], [],'-', c='r')[0]
    digit3DistalLine = ax.plot([], [], [], '-', c='b')[0]
    digit4DistalLine = ax.plot([], [], [], '-', c='b')[0]
    digit5DistalLine = ax.plot([], [], [], '-', c='b')[0]

    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_zlabel('Z (mm)')
    ax.set_xlim3d([dispRange[0], dispRange[0] + dispRange[3]])
    ax.set_ylim3d([dispRange[1], dispRange[1] + dispRange[4]])
    ax.set_zlim3d([dispRange[2], dispRange[2] + dispRange[5]])
    ax.set_box_aspect([dispRange[3], dispRange[4], dispRange[5]])

    plt.ion()
    plt.show()
    # ------------------------------------------------------------------------------------------------------------------

    while not leapc_lib.IsConnected:
        leapc_lib.millisleep(100)
    print("Leap Motion Connected")

    # Visualize hand tracking using an Animation ---
    ani = animation.FuncAnimation(fig1, animUpdate, fargs=(palmPoint, digit1DistalLine, digit2DistalLine,
          digit3DistalLine, digit4DistalLine, digit5DistalLine), interval=100)

    cornerLocCum = None # Cumulative corner locations

    '''MAIN LOOP'''
    while True:
        refreshWindow()

        if mouse0.isPressedIn(button1, buttons=[0]):
            button1.setFillColor(DARK_BLUE)

            cornerLoc = np.empty((4,3), dtype=np.float32)
            for i in range(4):
                message1.text = "Place index finger on marker %d" % i
                button2.setFillColor(LIGHT_YELLOW)
                message1.draw()
                button2.draw()
                button2Text.draw()
                window0.flip()
                plt.pause(0.5)

                while not mouse0.isPressedIn(button2, buttons=[0]):
                    plt.pause(0.1)  # pause
                button2.setFillColor(DARK_YELLOW)
                button2.draw()
                button2Text.draw()
                window0.flip()

                data1f,_ = getTrackData()
                cornerLoc[i,:] = data1f[DIGIT2_DISTAL[1], :]
                plt.pause(0.5)

            print(cornerLoc) # Show the tracked location of the corners

            # Cumulative correction of the calibration
            if cornerLocCum is None:
                cornerLocCum = cornerLoc
            else:
                cornerLocCum = 0.8*cornerLocCum + 0.2*cornerLoc

            # Compute plane norm vector ---
            planeNorm = np.matmul(np.linalg.inv(cornerLocCum[:3, :]), np.ones((3, 1)))
            calibScore = np.matmul(cornerLocCum[3, :], planeNorm)

            message1.text = "Calibration score = %.6f" % calibScore
            print(message1.text)

            ax.plot(cornerLocCum[[0, 1], 0], cornerLocCum[[0, 1], 1], cornerLocCum[[0, 1], 2], '-', c='y')[0]
            ax.plot(cornerLocCum[[1, 2], 0], cornerLocCum[[1, 2], 1], cornerLocCum[[1, 2], 2], '-', c='y')[0]
            ax.plot(cornerLocCum[[2, 3], 0], cornerLocCum[[2, 3], 1], cornerLocCum[[2, 3], 2], '-', c='y')[0]
            ax.plot(cornerLocCum[[0, 3], 0], cornerLocCum[[0, 3], 1], cornerLocCum[[0, 3], 2], '-', c='y')[0]

        else:
            button1.setFillColor(LIGHT_BLUE)

        if mouse0.isPressedIn(button3, buttons=[0]):
            if cornerLocCum is not None:
                button3.setFillColor(DARK_BLUE)

                # Compute rotation matrix for coordinate transform ---
                ampXY = np.sqrt(planeNorm[0] ** 2 + planeNorm[1] ** 2)
                rotXY = np.array([[planeNorm[1] / ampXY, -planeNorm[0] / ampXY, 0],
                                  [planeNorm[0] / ampXY, planeNorm[1] / ampXY, 0],
                                  [0.0, 0.0, 1.0]])
                ampXYZ = np.sqrt(planeNorm[0] ** 2 + planeNorm[1] ** 2 + planeNorm[2] ** 2)
                rotYZ = np.array([[1.0, 0.0, 0.0],
                                  [0, planeNorm[2] / ampXYZ, -ampXY / ampXYZ],
                                  [0, ampXY / ampXYZ, planeNorm[2] / ampXYZ]])
                mapRot = np.matmul(rotYZ, rotXY).T

                # Visualize transformed plane ---
                cornerLocTrans = cornerLocCum.copy()
                cornerLocTrans = cornerLocTrans - cornerLocCum[0, :]  # Shifted to origin
                cornerLocTrans = np.matmul(cornerLocTrans, mapRot)
                ax.plot(cornerLocTrans[[0, 1], 0], cornerLocTrans[[0, 1], 1], cornerLocTrans[[0, 1], 2], '-', c='r')
                ax.plot(cornerLocTrans[[1, 2], 0], cornerLocTrans[[1, 2], 1], cornerLocTrans[[1, 2], 2], '-', c='r')
                ax.plot(cornerLocTrans[[2, 3], 0], cornerLocTrans[[2, 3], 1], cornerLocTrans[[2, 3], 2], '-', c='r')
                ax.plot(cornerLocTrans[[0, 3], 0], cornerLocTrans[[0, 3], 1], cornerLocTrans[[0, 3], 2], '-', c='r')

                currentTime = time.strftime("%H-%M-%S", time.localtime())
                np.savetxt(("Calibration_at%s.csv" % currentTime), np.append(mapRot, cornerLocCum, axis=0),
                           delimiter=",") # First 3 rows: Rotation matrix, Last 4 rows: Corner location with the 4th row as the transition vector

                plt.pause(0.5)
                print("Data saved on %s" % currentTime)
        else:
            button3.setFillColor(LIGHT_BLUE)

        core.wait(0.01)  # pause

        if 'escape' in event.getKeys(): # program ends
            core.wait(0.1)
            # sock0.close()
            leapc_lib.DestroyConnection()
            window0.close()
            core.quit()