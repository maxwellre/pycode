import sys
import socket
from psychopy import core, visual, gui, data, event
from psychopy.tools.filetools import fromFile, toFile
import numpy, random

'''Marco'''
LIGHT_GREEN = [-0.5,0.5,-0.5]
DARK_GREEN = [-1.0,-0.5,-1.0]
LIGHT_YELLOW = [0.5,0.5,-0.5]
DARK_YELLOW = [-0.5,-0.5,-1.0]
LIGHT_BLUE = [-0.5,-0.5,0.5]
DARK_BLUE = [-1.0,-1.0,-0.5]

'''Configuration'''
HOST = '192.168.4.1'  # The server's hostname or IP address
PORT = 80        # The port used by the server
'''-------------------------------------------------------------------------------'''
'''Functions'''
def command(sockObj, text):
    sockObj.sendall(text.encode())
    ans = sockObj.recv(1024)
    while ans.decode() != "command-received":
        ans = sockObj.recv(1024)

'''-------------------------------------------------------------------------------'''
'''Initialization'''
isConnected = False

'''-------------------------------------------------------------------------------'''
if __name__ == '__main__':
    window0 = visual.Window([800,600], monitor="testMonitor", units="height", color = [-0.8, -0.8, -0.8])
    mouse0 = event.Mouse()

    status0 = visual.TextStim(window0, pos=[0.0, 0.4], text='Connecting ...', height=0.05)
    status0.draw()
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
    message1 = visual.TextStim(window0, pos=[0.0,0.4],text='Remote Control', height = 0.05)
    button1 = visual.rect.Rect(window0, pos=[0.0,0.1], width=0.4, height=0.12, fillColor = LIGHT_GREEN,
                               lineWidth = 2, lineColor='white')
    button2 = visual.rect.Rect(window0, pos=[-0.25,-0.1], width=0.4, height=0.12, fillColor = LIGHT_YELLOW,
                               lineWidth = 2, lineColor='white')
    button3 = visual.rect.Rect(window0, pos=[0.25,-0.1], width=0.4, height=0.12, fillColor = LIGHT_BLUE,
                               lineWidth = 2, lineColor='white')

    button1Text = visual.TextStim(window0, pos=[0.0,0.1], text='Both', height = 0.05)
    button2Text = visual.TextStim(window0, pos=[-0.25,-0.1], text='Left', height = 0.05)
    button3Text = visual.TextStim(window0, pos=[0.25,-0.1], text='Right', height = 0.05)

    while True:
        message1.draw()
        button1.draw()
        button2.draw()
        button3.draw()
        button1Text.draw()
        button2Text.draw()
        button3Text.draw()
        window0.flip()  # refresh window

        if mouse0.isPressedIn(button1, buttons=[0]):
            button1.setFillColor(DARK_GREEN)
            command(sock0, 'button1-both')
        else:
            button1.setFillColor(LIGHT_GREEN)

        if mouse0.isPressedIn(button2, buttons=[0]):
            button2.setFillColor(DARK_YELLOW)
            command(sock0, 'button2-left')
        else:
            button2.setFillColor(LIGHT_YELLOW)

        if mouse0.isPressedIn(button3, buttons=[0]):
            button3.setFillColor(DARK_BLUE)
            command(sock0, 'button3-right')
        else:
            button3.setFillColor(LIGHT_BLUE)

        core.wait(0.01)  # pause

        if 'escape' in event.getKeys(): # program ends
            core.wait(0.5)
            sock0.close()
            window0.close()
            core.quit()