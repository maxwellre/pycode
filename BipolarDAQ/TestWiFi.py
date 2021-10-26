import sys
import socket
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
window0 = visual.Window([800, 600], monitor="testMonitor", units="height", color=[-0.4, -0.4, -0.4])
mouse0 = event.Mouse()

status0 = visual.TextStim(window0, pos=[0.0, 0.4], text='Connecting ...', height=0.05)

message1 = visual.TextStim(window0, pos=[0.0, 0.4], text='Remote Control', height=0.05)

light1 = visual.Circle(window0, pos=[0.3, 0.4], radius=0.03, fillColor=[0, 0, 0],
                       lineWidth=4, lineColor=[-0.2, -0.2, -0.2])
button1 = visual.Rect(window0, pos=[0.0, 0.2], width=0.4, height=0.12, fillColor=LIGHT_GREEN,
                      lineWidth=2, lineColor='white')
button2 = visual.Rect(window0, pos=[-0.25, 0], width=0.4, height=0.12, fillColor=LIGHT_YELLOW,
                      lineWidth=2, lineColor='white')
button3 = visual.Rect(window0, pos=[0.25, 0], width=0.4, height=0.12, fillColor=LIGHT_BLUE,
                      lineWidth=2, lineColor='white')
button1Text = visual.TextStim(window0, pos=button1.pos, text='Both', height=0.05)
button2Text = visual.TextStim(window0, pos=button2.pos, text='Left', height=0.05)
button3Text = visual.TextStim(window0, pos=button3.pos, text='Right', height=0.05)

slider1 = visual.Slider(window0, ticks=[0, 1, 2, 3], labels=['0', '10', '15', '100'], startValue=0, pos=[-0.3, -0.2],
                        size=[0.4, 0.1], granularity=1, labelHeight=0.05, fillColor=[0.6,0,0])
slider1Text = visual.TextStim(window0, pos=[-0.3, -0.4], text='Voltage Level (%)', height=0.05)

button4 = visual.Rect(window0, pos=[0.2, -0.3], width=0.3, height=0.12, fillColor=[0, 0, 0],
                      lineWidth=2, lineColor='white')
button4Text = visual.TextStim(window0, pos=button4.pos, text='Set Voltage', height=0.05)

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
    slider1Text.draw()
    button4.draw()
    button4Text.draw()
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
        sock0.sendall(b'request-to-connect-high-voltage-controller') # "Handshake" protocol
        ans = sock0.recv(1024)
        if ans.decode() == "high-voltage-controller-is-ready": # "Handshake" protocol matched
            isConnected = True
            print("Successful connection to high voltage controller")

    '''GUI Setup'''
    while True:
        refreshWindow()

        if mouse0.isPressedIn(button1, buttons=[0]):
            button1.setFillColor(DARK_GREEN)
            command(sock0, 'button1-both', light1)
        else:
            button1.setFillColor(LIGHT_GREEN)

        if mouse0.isPressedIn(button2, buttons=[0]):
            button2.setFillColor(DARK_YELLOW)
            command(sock0, 'button2-left', light1)
        else:
            button2.setFillColor(LIGHT_YELLOW)

        if mouse0.isPressedIn(button3, buttons=[0]):
            button3.setFillColor(DARK_BLUE)
            command(sock0, 'button3-right', light1)
        else:
            button3.setFillColor(LIGHT_BLUE)

        if mouse0.isPressedIn(button4, buttons=[0]):
            button4.setFillColor([-0.8,-0.8,-0.8])
            command(sock0, 'button4-set-voltage', light1)
            command(sock0, 'voltlevel=%03d' % slider1.getRating(), light1)
        else:
            button4.setFillColor([0,0,0])

        core.wait(0.01)  # pause

        if 'escape' in event.getKeys(): # program ends
            core.wait(0.1)
            sock0.close()
            window0.close()
            core.quit()