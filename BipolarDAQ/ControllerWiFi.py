# Modified on 2022.06.10 to communicate with controller for VR setup
# New setting protocol

import sys
import socket
from psychopy import core, visual, gui, data, event
import time
from psychopy.tools.filetools import fromFile, toFile
import numpy, random

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

TrialNum = 6 # Repeat *** times for measurement when press

trialMeasureIndex = 1     # Trial index of the current measurement session

'''GUI Design'''
window0 = visual.Window([800, 600], monitor="testMonitor", units="height", color=[-0.7, -0.7, -0.7])
mouse0 = event.Mouse()

status0 = visual.TextStim(window0, pos=[0.0, 0.4], text='Connecting ...', height=0.05)

message1 = visual.TextStim(window0, pos=[0.2, 0.4], text='Remote Control', height=0.05)

light1 = visual.Circle(window0, pos=[0.5, 0.4], radius=0.03, fillColor=[0, 0, 0],
                       lineWidth=4, lineColor=[-0.2, -0.2, -0.2])
button1 = visual.Rect(window0, pos=[0.275, 0.2], width=0.45, height=0.12, fillColor=LIGHT_GREEN,
                      lineWidth=1, lineColor='white')
button2 = visual.Rect(window0, pos=[0.15, 0.03], width=0.2, height=0.12, fillColor=LIGHT_YELLOW,
                      lineWidth=1, lineColor='white')
button3 = visual.Rect(window0, pos=[0.4, 0.03], width=0.2, height=0.12, fillColor=LIGHT_BLUE,
                      lineWidth=1, lineColor='white')
button1Text = visual.TextStim(window0, pos=button1.pos, text='Press', height=0.05) # 'Both'
button2Text = visual.TextStim(window0, pos=button2.pos, text='10 Hz', height=0.05) # 'Left'
button3Text = visual.TextStim(window0, pos=button3.pos, text='250 Hz', height=0.05) # 'Right'

slider1 = visual.Slider(window0, ticks=[0, 2, 4, 8, 16, 32, 64, 100],
                        labels=['0', '', '4', '8', '16', '32', '64', '100'],
                        startValue=0, pos=[-0.18, -0.3],
                        size=[0.86, 0.1], granularity=2, labelHeight=0.045, fillColor=[0.6,0,0], style='slider')
slider2 = visual.Slider(window0, ticks=[0, 100, 200, 400, 800, 1200, 1600, 2000],
                        labels=['0','','','400','','1200','','2000'], startValue=1000, pos=[-0.4, 0.0],
                        size=[0.4, 0.1], granularity=100, labelHeight=0.05, fillColor=[0.6,0,0], style='slider')
slider3 = visual.Slider(window0, ticks=[0, 4000], labels=['0', '4000'], startValue=4000, pos=[-0.4, 0.25],
                        size=[0.4, 0.1], granularity=100, labelHeight=0.05, fillColor=[0.6,0,0], style='slider')
slider1Text = visual.TextStim(window0, pos=[-0.37, -0.3], text='Voltage Level (%)', height=0.05, color='black')
slider2Text = visual.TextStim(window0, pos=[-0.4, 0.0], text='Charge (ms)', height=0.05, color='black')
slider3Text = visual.TextStim(window0, pos=[-0.4, 0.25], text='Discharge (ms)', height=0.05, color='black')

button4 = visual.Rect(window0, pos=[0.45, -0.3], width=0.2, height=0.12, fillColor=[0, 0, 0],
                      lineWidth=1, lineColor='white')
button4Text = visual.TextStim(window0, pos=button4.pos, text='Set', height=0.05)

slider4 = visual.Slider(window0, ticks=[1, 2], labels=['1', '2'], startValue=1, pos=[-0.4, 0.42],
                        size=[0.2, 0.04], granularity=1, labelHeight=0.05, fillColor=[0.6,0,0], style='rating')

'''-------------------------------------------------------------------------------------------------------------'''
'''Functions'''
def refreshWindow():
    message1.draw()
    light1.draw()
    button1.draw()
    button2.draw()
    button3.draw()
    button1Text.draw()
    button2Text.draw()
    button3Text.draw()
    slider1.draw()
    slider2.draw()
    slider3.draw()
    slider4.draw()
    slider1Text.draw()
    slider2Text.draw()
    slider3Text.draw()
    button4.draw()
    button4Text.draw()
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

'''-------------------------------------------------------------------------------------------------------------'''



'''-------------------------------------------------------------------------------------------------------------'''
if __name__ == '__main__':
    # Initialization
    isConnected = False

    status0.draw()
    light1.draw()
    window0.flip()

    sock0 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock0.connect((HOST, PORT))
    while not isConnected: # try to establish a WiFi connection
        #sock0.sendall(b'request-to-connect-high-voltage-controller') # "Handshake" protocol
        sock0.sendall(b'vrheadset')  # "Handshake" pretend to be the vr headset
        ans = sock0.recv(1024)
        if ans.decode() == "high-voltage-controller-is-ready": # "Handshake" protocol matched
            isConnected = True
            print("Successful connection to high voltage controller")

    '''GUI Setup'''
    while True:
        refreshWindow()

        if mouse0.isPressedIn(button1, buttons=[0]): # "Both"
            for i in range(TrialNum): # Repeat measurement for *** trials
                t0 = time.time()
                button1.setFillColor(DARK_GREEN)
                command(sock0, 'l', light1)
                while(time.time() - t0 < 3.9): # Wait for 4 seconds until next trial
                    time.sleep(0.1)
        else:
            button1.setFillColor(LIGHT_GREEN)

        if mouse0.isPressedIn(button2, buttons=[0]): # "Left"
            button2.setFillColor(DARK_YELLOW)
            command(sock0, 'w', light1)
        else:
            button2.setFillColor(LIGHT_YELLOW)

        if mouse0.isPressedIn(button3, buttons=[0]): # "Right"
            button3.setFillColor(DARK_BLUE)
            command(sock0, 'x', light1)
        else:
            button3.setFillColor(LIGHT_BLUE)

        if mouse0.isPressedIn(button4, buttons=[0]):
            button4.setFillColor([-0.8,-0.8,-0.8])
            command(sock0, 's', light1)
            
            command(sock0, 'voooooooo=%03d-chhhhhT=%04d-diiiiiiiiT=%04d' %
                    (slider1.getRating(), slider2.getRating(), slider3.getRating()), light1)

            # print('voltlevel=%03d-chargeT=%04d-dischargeT=%04d' %
            #       (slider1.getRating(), slider2.getRating(), slider3.getRating()))

            trialMeasureIndex = slider4.getRating()
            print('v%dc%dd%dt%d' % (slider1.getRating(), slider2.getRating(), slider3.getRating(), trialMeasureIndex))
        else:
            button4.setFillColor([0,0,0])

        core.wait(0.01)  # pause

        if 'escape' in event.getKeys(): # program ends
            core.wait(0.1)
            sock0.close()
            window0.close()
            core.quit()