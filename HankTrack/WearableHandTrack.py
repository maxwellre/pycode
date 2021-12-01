'''
Hand tracking and wearable HV controller
Program for user study: haptic feedback based on finger touch location
Created on 2021.12.01 based on 'UserStudyCaliberation.py' and 'ControllerWiFi.py'
Author: Yitian Shao (ytshao@is.mpg.de)
'''

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
calibrationFilePath = './CalibrationFile/Calibration_at21-12-37.csv'

'''GUI Design'''
window0 = visual.Window([800, 900], pos=[800, 50], monitor="testMonitor", units="height", color=[-0.7, -0.7, -0.7])
mouse0 = event.Mouse()
status0 = visual.TextStim(window0, pos=[0.0, 0.3], text='Connecting ...', height=0.05)
message1 = visual.TextStim(window0, pos=[0.0, 0.3], text='User Study', height=0.05)

light1 = visual.Circle(window0, pos=[-0.3, 0.45], radius=0.03, fillColor=[0, 0, 0],
                       lineWidth=4, lineColor=[-0.2, -0.2, -0.2])

button1 = visual.Rect(window0, pos=[0.0, 0.0], width=0.45, height=0.12, fillColor=LIGHT_BLUE,
                      lineWidth=1, lineColor='white')
button2 = visual.Rect(window0, pos=[0.0, -0.16], width=0.2, height=0.12, fillColor=LIGHT_YELLOW,
                      lineWidth=1, lineColor='white')
button3 = visual.Rect(window0, pos=[0.0, 0.16], width=0.2, height=0.12, fillColor=LIGHT_BLUE,
                      lineWidth=1, lineColor='white')

button1Text = visual.TextStim(window0, pos=button1.pos, text='Start', height=0.05)
button2Text = visual.TextStim(window0, pos=button2.pos, text='Next', height=0.05)
button3Text = visual.TextStim(window0, pos=button3.pos, text='Save', height=0.05)

'''-------------------------------------------------------------------------------------------------------------'''
'''Functions'''
def refreshWindow():
    message1.draw()
    light1.draw()
    button1.draw()
    button1Text.draw()
    # button3.draw()
    # button3Text.draw()
    window0.flip()

def command(sockObj, text, lightObj = None):
    if(lightObj):
        lightObj.setFillColor(LED_RED)
        refreshWindow()

    sockObj.sendall(text.encode())
    ans = sockObj.recv(1024)
    while ans.decode() != "command-received":
        ans = sockObj.recv(1024)

    if (lightObj):
        lightObj.setFillColor(LED_GREEN)

'''-------------------------------------------------------------------------------------------------------------'''
dispRange = [100, -100, -10, -400, 400, 300]

targetLoc = [-80.0, 80.0, 0.0]

if __name__ == '__main__':
    # Initialization
    isHapDevConnected = False # Status = True, if Haptic device is connected

    status0.draw()
    light1.draw()
    window0.flip()

    # Establish connection with the wearable haptic device ---
    sock0 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock0.connect((HOST, PORT))
    while not isHapDevConnected: # try to establish a WiFi connection
        sock0.sendall(b'request-to-connect-high-voltage-controller') # "Handshake" protocol
        ans = sock0.recv(1024)
        if ans.decode() == "high-voltage-controller-is-ready": # "Handshake" protocol matched
            isHapDevConnected = True
            print("Successful connection to high voltage controller")

    # Establish connection with Leap-motion ---
    leapc_lib.OpenConnection()

    plt.ion() # Allow both the real-time tracking display and the GUI
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

        if mouse0.isPressedIn(button1, buttons=[0]): # Start button
            button1.setFillColor(DARK_BLUE)
            command(sock0, 'button4-set-voltage', light1)
            command(sock0, 'voltlevel=%03d-chargeT=%04d-dischargeT=%04d' % (100,500,100), light1)
        else:
            button1.setFillColor(LIGHT_BLUE)

        # if mouse0.isPressedIn(button3, buttons=[0]):
        #     button3.setFillColor(DARK_BLUE)
        # else:
        #     button3.setFillColor(LIGHT_BLUE)

        data1f, trackres = getTrackData()

        if (trackres == 1):
            fingertip = data1f[DIGIT2_DISTAL[1], :]
            fingertip = fingertip - offSet
            fingertip = np.matmul(fingertip, mapRot)

            if (abs(fingertip[0] - targetLoc[0]) < 20.0) and (abs(fingertip[1] - targetLoc[1]) < 20.0) and \
                    (abs(fingertip[2] - targetLoc[2]) < 20.0):

                # command(sock0, 'button1-both', light1); command(sock0, 'button3-right', light1)
                command(sock0, 'button2-left', light1)

        core.wait(0.01)  # pause

        if 'escape' in event.getKeys(): # program ends
            core.wait(0.1)
            # sock0.close()
            leapc_lib.DestroyConnection()
            window0.close()
            core.quit()