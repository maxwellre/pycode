'''
Triangle Communication between WiFi Controller, VR Headset, and PC
Program for user study: haptic feedback based on finger touch location in VR
Author: Yitian Shao (ytshao@is.mpg.de)
Created on 2022.02.24 based on 'ControllerWiFi.py'
'''
'''
Important: Handshake with WiFi controller is switched to 'p' for PC client! (2022.02.24)
'''
import sys
import socket
import select
from psychopy import core, visual, gui, data, event
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
button1Text = visual.TextStim(window0, pos=button1.pos, text='NA', height=0.05)
button2Text = visual.TextStim(window0, pos=button2.pos, text='Left', height=0.05)
button3Text = visual.TextStim(window0, pos=button3.pos, text='NA', height=0.05)
# 990+220
slider1 = visual.Slider(window0, ticks=[0, 15, 50, 100], labels=['0', '15', '50', '100'], startValue=0, pos=[-0.38, -0.3],
                        size=[0.44, 0.1], granularity=5, labelHeight=0.045, fillColor=[0.6,0,0], style='slider')
slider2 = visual.Slider(window0, ticks=[0, 1000], labels=['0', '1000'], startValue=600, pos=[-0.4, 0.0],
                        size=[0.4, 0.1], granularity=1, labelHeight=0.05, fillColor=[0.6,0,0], style='slider')
slider3 = visual.Slider(window0, ticks=[0, 1000], labels=['0', '1000'], startValue=250, pos=[-0.4, 0.25],
                        size=[0.4, 0.1], granularity=1, labelHeight=0.05, fillColor=[0.6,0,0], style='slider')
slider1Text = visual.TextStim(window0, pos=[-0.37, -0.3], text='Voltage Level (%)', height=0.05, color='black')
slider2Text = visual.TextStim(window0, pos=[-0.4, 0.0], text='Charge (ms)', height=0.05, color='black')
slider3Text = visual.TextStim(window0, pos=[-0.4, 0.25], text='Discharge (ms)', height=0.05, color='black')

button4 = visual.Rect(window0, pos=[0.05, -0.3], width=0.2, height=0.12, fillColor=[0, 0, 0],
                      lineWidth=1, lineColor='white')
button4Text = visual.TextStim(window0, pos=button4.pos, text='Set', height=0.05)

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

    sockObj.sendall(text.encode())
    ans = sockObj.recv(64)
    while ans.decode() != "command-received":
        ans = sockObj.recv(64)

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
        sock0.sendall(b'pcprogram') # "Handshake" protocol

        for count in range(1000):
            ans = sock0.recv(1024)
            if ans.decode() == "high-voltage-controller-is-ready": # "Handshake" protocol matched
                isConnected = True
                print("Successful connection to high voltage controller")
                break

    '''GUI Setup'''
    while True:
        refreshWindow()

        if mouse0.isPressedIn(button1, buttons=[0]):
            button1.setFillColor(DARK_GREEN)
            #command(sock0, 'b', light1)
        else:
            button1.setFillColor(LIGHT_GREEN)

        if mouse0.isPressedIn(button2, buttons=[0]):
            button2.setFillColor(DARK_YELLOW)
            command(sock0, 'l', light1)
        else:
            button2.setFillColor(LIGHT_YELLOW)

        if mouse0.isPressedIn(button3, buttons=[0]):
            button3.setFillColor(DARK_BLUE)
            #command(sock0, 'r', light1)
        else:
            button3.setFillColor(LIGHT_BLUE)

        if mouse0.isPressedIn(button4, buttons=[0]):
            button4.setFillColor([-0.8,-0.8,-0.8])
            command(sock0, 's', light1)
            command(sock0, 'voooooooo=%03d-chhhhhT=%04d-diiiiiiiiT=%04d' %
                    (slider1.getRating(),slider2.getRating(),slider3.getRating()), light1)

            print('voltlevel=%03d-chargeT=%04d-dischargeT=%04d' %
                  (slider1.getRating(),slider2.getRating(),slider3.getRating()))
        else:
            button4.setFillColor([0,0,0])

        datastream = sock0.recv(16384)
        if (datastream):
            print(datastream.decode())

        core.wait(0.01)  # pause

        if 'escape' in event.getKeys(): # program ends
            core.wait(0.1)
            sock0.close()
            window0.close()
            core.quit()