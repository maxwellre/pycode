'''
Acquire touch input from touch screen
Author: Yitian Shao (ytshao@is.mpg.de)
Created on 2021.11.09
'''

import psychopy.visual as pv
from psychopy import core, gui, data, event
import time
import numpy as np
import matplotlib.pyplot as plt
import PyDAQmx as nidaq
import subprocess
from os import path

# MARCO
LED_RED = [1.0,-1.0,-1.0] # Color of red LED
LED_GREEN = [-1.0,1.0,-1.0] # Color of green LED

'''-------------------------------------------------------------------------------'''
'''GUI Design'''
# Main control monitor
window0 = pv.Window([1200, 720], screen=0, monitor="testMonitor", units="height", color=[-0.7, -0.7, -0.7])
mouse0 = event.Mouse()

message1 = pv.TextStim(window0, pos=[0.0, 0.42], text='Visual Haptic Display', height=0.05)

light1 = pv.Circle(window0, pos=[0.4, 0.42], radius=0.03, fillColor=[0, 0, 0],
                       lineWidth=4, lineColor=[-0.2, -0.2, -0.2])

button0 = pv.Rect(window0, pos=[-0.4, 0.42], width=0.06, height=0.06, fillColor=[0, 0.2, 0.8], lineWidth=0)
button0Text = pv.TextStim(window0, pos=button0.pos, text='C', height=0.05)

button1 = pv.Rect(window0, pos=[-0.4, 0.28], width=0.5, height=0.1, fillColor=[0, 0, 0],
                      lineWidth=1, lineColor='white')
button1Text = pv.TextStim(window0, pos=button1.pos, text='Touch here', height=0.05)

# Haptic screen monitor
window2 = pv.Window([2560, 1600], screen=1, fullscr=True, units="height", color=[-1.0, -1.0, -1.0])
message2 = pv.TextStim(window2, pos=[-0.2, 0], text='DEMO', height=0.4)

'''-------------------------------------------------------------------------------'''
# '''Import LeapC libraray'''
# import ctypes
# from ctypes import util
# from ctypes import CDLL
#
# libPath = ctypes.util.find_library("C:/Users/ytshao/JupyterNote/BipolarDAQ/libx64/LeapC")
# leapc = ctypes.CDLL(libPath)
# print("c shared library founded")


'''-------------------------------------------------------------------------------'''
'''Functions'''
def refreshWindow():
    message1.draw()
    light1.draw()

    button0.draw()
    button0Text.draw()

    button1.draw()
    button1Text.draw()

    window0.flip()

'''-------------------------------------------------------------------------------'''
if __name__ == '__main__':
    '''GUI Loop'''
    while True:
        refreshWindow()

        mov1 = pv.MovieStim(window2, "./Audio_Video/CarChasing2.mp4") # Play video via Psychopy
        message2.draw()
        window2.flip()

        if mouse0.isPressedIn(button0, buttons=[0]):  # ----------------------------------------- Button 0: Discharge
            # GUI update
            button0.setFillColor([-0.8, -0.8, 1.0])
            refreshWindow()
            message1.text = "Touched"
        else:
            button0.setFillColor([0, 0.2, 0.5])
            message1.text = "NA"

        if mouse0.isPressedIn(button1, buttons=[0]):  # ---------------------------------------- Button 1: CarChasing
            # GUI update
            button1.setFillColor([-0.8, -0.8, -0.8])
            refreshWindow()
            button1Text.text = "Touched"
        else:
            button1.setFillColor([0, 0, 0])
            button1Text.text = "NA"

        if 'escape' in event.getKeys():  # program ends
            core.wait(0.1)
            window0.close()
            core.quit()