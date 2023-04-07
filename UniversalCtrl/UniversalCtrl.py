# Created on 2023.01.18 based on 'ControllerWiFi.py'
# Communicate with HV controller for vibration output
# New setting protocol for frequency control!

import sys
import socket
from psychopy import core, visual, gui, data, event
import time
import numpy as np
from psychopy.tools.filetools import fromFile, toFile
# import random

'''Marco'''
LED_RED = [1.0,-1.0,-1.0]
LED_GREEN = [-1.0,1.0,-1.0]
LIGHT_GREEN = [-0.5,0.5,-0.5]
DARK_GREEN = [-1.0,-0.5,-1.0]
LIGHT_YELLOW = [0.5,0.5,-0.5]
DARK_YELLOW = [-0.5,-0.5,-1.0]
LIGHT_BLUE = [-0.5,-0.5,0.5]
DARK_BLUE = [-1.0,-1.0,-0.5]
LIGHT_PINK = [0.5,-0.5,0.5]
DARK_PINK = [0.0,-1.0,-0.5]

'''Configuration'''
HOST = '192.168.4.1'  # The server's hostname or IP address
PORT = 80        # The port used by the server

trialNum = 1 # Repeat *** times for measurement when press

trialMeasureIndex = 1     # Trial index of the current measurement session

'''GUI Design'''
window0 = visual.Window([800, 600], monitor="testMonitor", units="height", color=[-0.7, -0.7, -0.7])
mouse0 = event.Mouse()

status0 = visual.TextStim(window0, pos=[0.0, 0.4], text='Connecting ...', height=0.05)

message1 = visual.TextStim(window0, pos=[0.2, 0.4], text='Remote Control', height=0.05)

light1 = visual.Circle(window0, pos=[0.5, 0.4], radius=0.03, fillColor=[0, 0, 0],
                       lineWidth=4, lineColor=[-0.2, -0.2, -0.2])

''' Buttons '''
button1 = visual.Rect(window0, pos=[0.05, 0.26], width=0.12, height=0.1, fillColor=LIGHT_GREEN,
                      lineWidth=1, lineColor='white')
button1Text = visual.TextStim(window0, pos=button1.pos, text='DC', height=0.05) # ------------------------------ 'Green'


button2 = visual.Rect(window0, pos=[0.36, 0.26], width=0.4, height=0.12, fillColor=LIGHT_YELLOW,
                      lineWidth=1, lineColor='white')
button2Text = visual.TextStim(window0, pos=button2.pos, text='Rep. Measure', height=0.05) # ------------------- 'Yellow'


button3 = visual.Rect(window0, pos=[0.1, 0.1], width=0.2, height=0.1, fillColor=LIGHT_PINK,
                      lineWidth=1, lineColor='white')
button3Text = visual.TextStim(window0, pos=button3.pos, text='Pulse', height=0.05) # -------------------------- 'Pink'


button4 = visual.Rect(window0, pos=[0.35, 0.1], width=0.2, height=0.1, fillColor=LIGHT_BLUE,
                      lineWidth=1, lineColor='white')
button4Text = visual.TextStim(window0, pos=button4.pos, text='Sine', height=0.05) # ------------------------------ 'Blue'


''' Button (Set) '''
buttonS = visual.Rect(window0, pos=[0.46, -0.36], width=0.2, height=0.12, fillColor=[0, 0, 0],
                      lineWidth=1, lineColor='white')
buttonSText = visual.TextStim(window0, pos=buttonS.pos, text='Set', height=0.05)

''' Sliders '''
slider1 = visual.Slider(window0, ticks=[0, 2, 4, 8, 16, 32, 50, 64, 100],
                        labels=['0', '', '4', '8', '16', '32', '50', '64', '100'],
                        startValue=100, pos=[-0.18, -0.35], size=[0.86, 0.1], granularity=2,
                        labelHeight=0.045, fillColor=[0.6,0,0], style='slider')
slider1Text = visual.TextStim(window0, pos=[-0.37, -0.35], text='Voltage Level (%)', height=0.05, color='black')

freqTicks = [1, 2, 4, 10, 20, 40, 80, 160, 240, 400, 800]
slider2 = visual.Slider(window0, ticks=np.log2(freqTicks),
                        labels=['1','2','4','10','20','40','80','160', '.', '400', '800'],
                        startValue=2, pos=[0.0, -0.1], size=[1.2, 0.1], granularity=0.001,
                        labelHeight=0.05, fillColor=[0.6,0,0], style='slider')
slider2Text = visual.TextStim(window0, pos=[-0.25, -0.01], text='Freq (Hz)', height=0.05, color='brown')


slider3 = visual.Slider(window0, ticks=[0, 1000, 2000, 4000], labels=['0', '', '2000', '4000'], startValue=2000,
                        pos=[-0.4, 0.25], size=[0.4, 0.1], granularity=200, labelHeight=0.05, fillColor=[0.6,0,0],
                        style='slider')
slider3Text = visual.TextStim(window0, pos=[-0.4, 0.25], text='Vib Time (ms)', height=0.05, color='black')


slider4 = visual.Slider(window0, ticks=[1, 2, 4, 6, 10], labels=['1','','','6','Max'], startValue=6, pos=[-0.4, 0.42],
                        size=[0.2, 0.04], granularity=1, labelHeight=0.05, fillColor=[0.6,0,0], style='rating')

'''-------------------------------------------------------------------------------------------------------------'''
'''Functions'''
def refreshWindow():
    message1.draw()
    light1.draw()
    button1.draw()
    button2.draw()
    button3.draw()
    button4.draw()
    button1Text.draw()
    button2Text.draw()
    button3Text.draw()
    button4Text.draw()

    slider1.draw()
    slider2.draw()
    slider3.draw()
    slider4.draw()
    slider1Text.draw()
    slider2Text.draw()
    slider3Text.draw()

    buttonS.draw()
    buttonSText.draw()
    window0.flip()

def command(sockObj, text, lightObj = None):
    if(lightObj):
        lightObj.setFillColor(LED_RED)
        refreshWindow()

    # Acknowledge table: find the correct answer string
    acknowledgeStr = None
    if (text == 's'):
        acknowledgeStr = "ready-to-change"
    elif (len(text) > 1):
        acknowledgeStr = "setting-changed"
    else:
        acknowledgeStr = "command-received"

    sockObj.sendall(text.encode())
    ans = sockObj.recv(1024)
    while ans.decode() != acknowledgeStr:
        ans = sockObj.recv(1024)

    if (lightObj):
        lightObj.setFillColor(LED_GREEN)

def connectWiFi():
    isConnected = False

    sockHandle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockHandle.connect((HOST, PORT))
    while not isConnected: # try to establish a WiFi connection
        sockHandle.sendall(b'vrheadset') # "Handshake" protocol

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



'''-------------------------------------------------------------------------------------------------------------'''
if __name__ == '__main__':
    # Initialization
    sock0 = connectWiFi()

    status0.draw()
    light1.draw()
    window0.flip()

    '''GUI Setup'''
    while True:
        freqRating = np.exp2(slider2.getRating())
        if (freqRating >= 10):
            freqRating = (freqRating * 0.1).astype(int) * 10
        else:
            freqRating = (freqRating * 10).astype(int) * 0.1
        slider2Text.text = ("Freq: %.2f Hz" % freqRating)
        refreshWindow()

        if mouse0.isPressedIn(button1, buttons=[0]): # --------------------------------------- "Green"
            button1.setFillColor(DARK_GREEN)
            command(sock0, 'l', light1)
            # trialNum = slider4.getRating()
            # for i in range(trialNum): # Repeat measurement for *** trials
            #     t0 = time.time()
            #     button1.setFillColor(DARK_GREEN)
            #     command(sock0, 'l', light1)
            #     while(time.time() - t0 < 3.9): # Wait for 4 seconds until next trial
            #         time.sleep(0.1)
        else:
            button1.setFillColor(LIGHT_GREEN)


        if mouse0.isPressedIn(button2, buttons=[0]): # --------------------------------------- "Yellow"

            trialNum = slider4.getRating()

            for i in range(trialNum):  # Repeat measurement for *** trials
                t0 = time.time()
                button2.setFillColor(DARK_YELLOW)
                command(sock0, 'w', light1)
                while (time.time() - t0 < 3.9):  # Wait for 4 seconds until next trial
                    time.sleep(0.1)
        else:
            button2.setFillColor(LIGHT_YELLOW)


        if mouse0.isPressedIn(button3, buttons=[0]): # --------------------------------------- "Pink"
            button3.setFillColor(DARK_PINK)
            command(sock0, 'w', light1)
        else:
            button3.setFillColor(LIGHT_PINK)


        if mouse0.isPressedIn(button4, buttons=[0]):  # --------------------------------------- "Blue"
            button4.setFillColor(DARK_BLUE)
            command(sock0, 'x', light1)
        else:
            button4.setFillColor(LIGHT_BLUE)


        if mouse0.isPressedIn(buttonS, buttons=[0]): # --------------------------------------- "Set"
            buttonS.setFillColor([-0.8,-0.8,-0.8])
            command(sock0, 's', light1)

            command(sock0, 'Vo=%03d-Fr=%03d-Ti=%04d' %
                    (slider1.getRating(), freqRating, slider3.getRating()), light1)

            trialMeasureIndex = slider4.getRating()
            print('%d-%d-%d-t%d' % (slider1.getRating(), slider2.getRating(), slider3.getRating(), trialMeasureIndex))
        else:
            buttonS.setFillColor([0,0,0])

        core.wait(0.01)  # pause

        if 'escape' in event.getKeys(): # program ends
            core.wait(0.1)
            sock0.close()
            window0.close()
            core.quit()