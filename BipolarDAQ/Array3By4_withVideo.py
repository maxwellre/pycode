'''
Control the new bipolar HV board (electrode-array) via NI DAQ.
(Optional) Measurement via NI DAQ.
Author: Yitian Shao (ytshao@is.mpg.de)
Created on 2021.11.01 based on 'Array3By4_Demo.py'
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

F_CLK = 100000.0 # DOI Clock frequency (Circuit control sampling frequency, Hz)
F_PWM = 1000  # PWM frequency (Output waveform sampling frequency, Hz)

NODE_NUM = 12 # 3HV * 4GND array of nodes (must not be modified without hardware update)
Channel_Num = 10 # 3HV*2 + 4GND channels (must not be modified without hardware update)

CHARGE_XY = [[0,6],[0,7],[0,8],[0,9],
             [2,6],[2,7],[2,8],[2,9],
            [4,6],[4,7],[4,8],[4,9]] # Info of charging channels (must not be modified without hardware update)

DISCHARGE_XY = [[1,6],[1,7],[1,8],[1,9],
                [3,6],[3,7],[3,8],[3,9],
                [5,6],[5,7],[5,8],[5,9]] # Info of discharging channels (must not be modified without hardware update)

MEDIA_PLAYER_PATH = "C:\\Program Files (x86)\\Windows Media Player\\wmplayer.exe" # Path of windows media player
MEDIA_PLAYER_CMD = "/fullscreen" # Enable fullscreen for windows media player

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
button1Text = pv.TextStim(window0, pos=button1.pos, text='Movie: Car Chasing', height=0.05)

button2 = pv.Rect(window0, pos=[-0.4, 0.12], width=0.5, height=0.1, fillColor=[0, 0, 0],
                      lineWidth=1, lineColor='white')
button2Text = pv.TextStim(window0, pos=button2.pos, text='Clip: Baby', height=0.05)

button3 = pv.Rect(window0, pos=[-0.4, -0.04], width=0.5, height=0.1, fillColor=[0, 0, 0],
                      lineWidth=1, lineColor='white')
button3Text = pv.TextStim(window0, pos=button3.pos, text='Clip: Heartbeat', height=0.05)

# button4 = pv.Rect(window0, pos=[-0.4, -0.20], width=0.5, height=0.1, fillColor=[0, 0, 0],
#                       lineWidth=1, lineColor='red')
# button4Text = pv.TextStim(window0, pos=button4.pos, text='Clip: Ocean Waves', height=0.05)

button5 = pv.Rect(window0, pos=[-0.4, -0.36], width=0.5, height=0.1, fillColor=[0, 0, 0],
                      lineWidth=1, lineColor='white')
button5Text = pv.TextStim(window0, pos=button5.pos, text='Movie: Frog', height=0.05)

# Haptic screen monitor
# window2 = pv.Window([2560, 1600], screen=2, fullscr=True, units="height", color=[-1.0, -1.0, -1.0])
# message2 = pv.TextStim(window2, pos=[-0.2, 0], text='DEMO', height=0.4)

'''-------------------------------------------------------------------------------'''
'''Functions'''
def refreshWindow():
    message1.draw()
    light1.draw()

    button0.draw()
    button0Text.draw()

    button1.draw()
    button1Text.draw()

    button2.draw()
    button2Text.draw()

    button3.draw()
    button3Text.draw()

    # button4.draw()
    # button4Text.draw()

    button5.draw()
    button5Text.draw()

    window0.flip()

def Percent2PWM(CLKnum, pinCharge, pinDischarge, pinGND, percentage = np.NAN):
    PWMout = np.zeros((CLKnum, Channel_Num), dtype=np.uint8)

    if (np.isnan(percentage)): # No output
        return PWMout

    PWMratioInd = int(percentage * 0.01 * CLKnum)-1
    if (PWMratioInd < 0):
        PWMratioInd = 0
    elif (PWMratioInd >= CLKnum-1):
        PWMratioInd = CLKnum-2

    PWMout[:PWMratioInd, pinCharge] = 1 # Charge cycle

    PWMout[(PWMratioInd+1):-1, pinDischarge] = 1 # Discharge cycle, must skip 1 tick for safety

    PWMout[:, pinGND] = 1  # GND

    return PWMout

def sinSignal(sinDuration = 10.0, sinFreq = 250): # Generate sinusoid signals with percentage range and zero start
    # Total time duration (sec), Frequency (Hz)
    t = np.arange(int(sinDuration * F_PWM)) / F_PWM
    y = -50 * np.cos(2 * np.pi * sinFreq * t) + 50 # y ranged from 0 to 100 (%) to be passed to Percent2PWM()

    return y

def Animation2DIO(animation, frameChargeRepNum=720, frameDischargeRepNum=800):
    dischargeNode = np.arange(start=0, stop=NODE_NUM * frameDischargeRepNum,
                              step=NODE_NUM)  # Discharge node discrete indices
    chargeNode = dischargeNode[:frameChargeRepNum]  # Charging node indices

    DIOBlock = np.empty((0, Channel_Num), dtype=np.uint8)
    for animFrame in animation:
        # Each frame: Node number * Repetition of tick per node * (1 active tick + 1 empty tick)
        oneFrame = np.zeros((NODE_NUM * frameDischargeRepNum * 2, Channel_Num), dtype=np.uint8)

        chargeInd = np.where(animFrame == 1)[0]
        for i in chargeInd:
            oneFrame[(chargeNode + i) * 2, CHARGE_XY[i][0]] = 1
            oneFrame[(chargeNode + i) * 2, CHARGE_XY[i][1]] = 1

        dischargeInd = np.where(animFrame == -1)[0]
        for i in dischargeInd:
            oneFrame[(dischargeNode + i) * 2, DISCHARGE_XY[i][0]] = 1
            oneFrame[(dischargeNode + i) * 2, DISCHARGE_XY[i][1]] = 1

        DIOBlock = np.append(DIOBlock, oneFrame, axis=0)

    return DIOBlock

def dischargeAll(dischargeDuration = 1.0):
    # dischargeDuration (sec)
    dischargeTicks = dischargeDuration*F_CLK
    return Animation2DIO(-np.ones((1,12)), frameChargeRepNum=0,
                         frameDischargeRepNum=int(dischargeTicks*0.5/NODE_NUM))

''' Debug Tool'''
def checkOutput(DIOout):
    fig1 = plt.figure(figsize = (16,6))
    fig1.suptitle(("CLK Freq = %.0f Hz" % F_CLK), fontsize=12)
    ax = fig1.add_subplot(111)
    t = np.arange(DIOout.shape[0] )/F_CLK
    for i in range(10):
        ax.plot(t, DIOout[:,i]*0.5+i-0.25, '-')
    ax.set_yticks(range(10))
    ax.set_yticklabels(['Charge 1','Discharge 1','Charge 2','Discharge 2','Charge 3','Discharge 3',
                        'Ground 1','Ground 2','Ground 3','Ground 4'])
    ax.set_xlabel('Time (sec)')
    plt.show()

'''-------------------------------------------------------------------------------'''
# Parameters
frameIntvTime = 0.01 # (sec) Time pause interval between two frames

# PWM info
PWMpulseWidth = 1.0 / F_PWM
PWMpulseCLKnum = int(F_CLK * PWMpulseWidth)  # Total sample number per PWM segment
print("PWM frequency = %.1f Hz, PWM duration = %.1f us (%d CLK ticks)" % (F_PWM, 1e6 * PWMpulseWidth, PWMpulseCLKnum))

'''-------------------------------------------------------------------------------'''
if __name__ == '__main__':
    isIdle = False # Status of the program: idle or busy

    videoName = None

    DIOout = np.zeros((1, Channel_Num), dtype=np.uint8) # Initial state: all channels turned off

    videoPath = path.join(path.dirname(__file__), 'Audio_Video')
    audioPath = path.join(path.dirname(__file__), 'Audio')

    # mov1 = pv.MovieStim(window2, "./Audio_Video/CarChasing2.mp4") # Play video via Psychopy
    # message2.draw()
    # window2.flip()

    with nidaq.Task() as task1:
        # DAQ configuration
        task1.CreateDOChan("Dev2/port0/line0:5,Dev2/port0/line10:13", None, nidaq.DAQmx_Val_ChanPerLine)

        '''GUI Loop'''
        while True:
            refreshWindow()

            if mouse0.isPressedIn(button0, buttons=[0]): # ----------------------------------------- Button 0: Discharge
                # GUI update
                button0.setFillColor([-0.8, -0.8, 1.0])
                refreshWindow()

                # Video info
                videoName = None

                # Construct DAQ output
                DIOout = dischargeAll(2.0) # (sec)

                isIdle = True
            else:
                button0.setFillColor([0, 0.2, 0.5])

            if mouse0.isPressedIn(button1, buttons=[0]): # ---------------------------------------- Button 1: CarChasing
                # GUI update
                button1.setFillColor([-0.8, -0.8, -0.8])
                refreshWindow()

                # Video info
                fileName = "CarChasing2"
                videoName = "%s.mp4" % fileName

                # Load source sigal and construct DAQ output
                tactileSig = np.loadtxt(path.join(audioPath, "%s_1000Hz.csv" % fileName))

                actNode = 6  # Range from 0 to 11

                DIOout = np.empty((0, Channel_Num), dtype=np.uint8)

                oneBlock = np.array([Percent2PWM(PWMpulseCLKnum, CHARGE_XY[actNode][0], DISCHARGE_XY[actNode][0],
                                                 CHARGE_XY[actNode][1], yi) for yi in tactileSig], dtype=np.uint8)
                DIOout = np.append(DIOout, oneBlock.reshape((-1, Channel_Num)), axis=0)
                for discharge_i in [1, 3, 5]: # Discharge for 0.2 second
                    dischargeBlock = np.zeros((int(0.2 * F_CLK), Channel_Num), dtype=np.uint8)
                    dischargeBlock[:, [discharge_i, 6, 7, 8, 9]] = 1
                    DIOout = np.append(DIOout, dischargeBlock, axis=0)

                isIdle = True
            else:
                button1.setFillColor([0, 0, 0])

            if mouse0.isPressedIn(button2, buttons=[0]): # ---------------------------------------------- Button 2: Baby
                # GUI update
                button2.setFillColor([-0.8, -0.8, -0.8])
                refreshWindow()

                # Video info
                videoName = "Baby.mp4"

                # Construct DAQ output
                animation = np.array([
                    [1, 0, 0, 0,
                     0, 0, 0, 0,
                     1, 0, 0, 0],
                    [0, 0, 0, 0,
                     0, 1, 0, 0,
                     0, 0, 0, 0],
                    [-1, -1, -1, -1,
                     -1, -1, -1, -1,
                     -1, -1, -1, -1],
                    [0, 0, 0, 1,
                     0, 0, 0, 0,
                     0, 0, 0, 1],
                    [0, 0, 0, 0,
                     0, 0, 1, 0,
                     0, 0, 0, 0],
                    [-1, -1, -1, -1,
                     -1, -1, -1, -1,
                     -1, -1, -1, -1]
                ])

                animation = np.tile(animation, (10, 1))

                DIOout = Animation2DIO(animation, frameChargeRepNum=560, frameDischargeRepNum=600)

                isIdle = True
            else:
                button2.setFillColor([0, 0, 0])

            if mouse0.isPressedIn(button3, buttons=[0]): # ----------------------------------------- Button 3: Heartbeat
                # GUI update
                button3.setFillColor([-0.8, -0.8, -0.8])
                refreshWindow()

                # Video info
                videoName = "Heartbeat.mp4"

                # Construct DAQ output
                animation = np.array([
                    [1, 0, 0, 0,
                     0, 0, 0, 0,
                     0, 0, 0, 0],
                    [0, 1, 0, 0,
                     1, 1, 0, 0,
                     0, 0, 0, 0],
                    [-1, -1, -1, -1,
                     -1, -1, -1, -1,
                     -1, -1, -1, -1],
                    [0, 0, 0, 0,
                     0, 0, 0, 0,
                     0, 0, 0, 1],
                    [0, 0, 0, 0,
                     0, 0, 1, 1,
                     0, 0, 1, 0],
                    [-1, -1, -1, -1,
                     -1, -1, -1, -1,
                     -1, -1, -1, -1]
                ])

                animation = np.tile(animation, (9, 1))

                DIOout = Animation2DIO(animation, frameChargeRepNum=720, frameDischargeRepNum=800)

                isIdle = True
            else:
                button3.setFillColor([0, 0, 0])

            # if mouse0.isPressedIn(button4, buttons=[0]): # ----------------------------------------------- Button 4: Sea
            #     # GUI update
            #     button4.setFillColor([-0.8, -0.8, -0.8])
            #     refreshWindow()
            #
            #     # Video info
            #     videoName = "Sea.mp4"
            #
            #     # Construct DAQ output
            #     # Construct DAQ output
            #     animation = np.array([
            #         [0, 0, 0, 0,
            #          0, 1, 1, 0,
            #          0, 0, 0, 0],
            #         [-1, -1, -1, -1,
            #          -1, -1, -1, -1,
            #          -1, -1, -1, -1],
            #         [1, 0, 0, 0,
            #          1, 0, 0, 0,
            #          1, 0, 0, 0]
            #     ])
            #     DIOout = Animation2DIO(animation, frameChargeRepNum=400, frameDischargeRepNum=420)
            #
            #     DIOout = np.append(DIOout, dischargeAll(1.0), axis=0)  # Discharge all nodes
            #
            #     ySig = sinSignal(sinDuration=18, sinFreq=0.3)
            #     ySigA = ySig.copy()
            #     ySigA[0::2] = np.NAN
            #     ySigB = ySig.copy()
            #     ySigB = 100 - ySigB
            #     ySigB[1::2] = np.NAN
            #
            #     ySigA = np.power(ySigA*0.01, 1.6) * 100
            #     ySigB = np.power(ySigB*0.01, 1.6) * 100
            #     # plt.plot(ySigA);plt.plot(ySigB);plt.show()
            #
            #     actNode = 7  # Range from 0 to 11
            #     NodeA = np.array([Percent2PWM(PWMpulseCLKnum, CHARGE_XY[actNode][0], DISCHARGE_XY[actNode][0],
            #                                      CHARGE_XY[actNode][1], yi) for yi in ySigA], dtype=np.uint8)
            #     actNode = 0  # Range from 0 to 11
            #     NodeB = np.array([Percent2PWM(PWMpulseCLKnum, CHARGE_XY[actNode][0], DISCHARGE_XY[actNode][0],
            #                                   CHARGE_XY[actNode][1], yi) for yi in ySigB], dtype=np.uint8)
            #
            #     oneBlock = np.bitwise_or(NodeA, NodeB)  # Extremely danger operation! Two nodes must be aligned
            #     DIOout = np.append(DIOout, oneBlock.reshape((-1, Channel_Num)), axis=0)
            #
            #     DIOout = np.append(DIOout, dischargeAll(2.0), axis=0)  # Discharge all nodes
            #
            #     isIdle = True
            # else:
            #     button4.setFillColor([0, 0, 0])

            if mouse0.isPressedIn(button5, buttons=[0]): # ---------------------------------------------- Button 5: Frog
                # GUI update
                button5.setFillColor([-0.8, -0.8, -0.8])
                refreshWindow()

                # Video info
                videoName = "Frog.mp4"

                # Construct DAQ output
                animation = np.array([
                    [1, 0, 1, 1,
                     0, 0, 0, 1,
                     0, 0, 1, 1],
                ])
                DIOout = Animation2DIO(animation, frameChargeRepNum=800, frameDischargeRepNum=1000)

                ySig = sinSignal(sinDuration=1.6, sinFreq=5)

                actNode = 6  # Range from 0 to 11
                oneBlock = np.array([Percent2PWM(PWMpulseCLKnum, CHARGE_XY[actNode][0], DISCHARGE_XY[actNode][0],
                                              CHARGE_XY[actNode][1], yi) for yi in ySig], dtype=np.uint8)
                DIOout = np.append(DIOout, oneBlock.reshape((-1, Channel_Num)), axis=0)

                DIOout = np.append(DIOout, dischargeAll(0.2), axis=0) # Discharge all nodes

                ySig = sinSignal(sinDuration=4.0, sinFreq=5)
                actNode = 6  # Range from 0 to 11
                NodeA = np.array([Percent2PWM(PWMpulseCLKnum, CHARGE_XY[actNode][0], DISCHARGE_XY[actNode][0],
                                                 CHARGE_XY[actNode][1], yi) for yi in ySig], dtype=np.uint8)

                actNode = 7  # Range from 0 to 11
                NodeB = np.array([Percent2PWM(PWMpulseCLKnum, CHARGE_XY[actNode][0], DISCHARGE_XY[actNode][0],
                                              CHARGE_XY[actNode][1], yi) for yi in ySig], dtype=np.uint8)
                oneBlock = np.bitwise_or(NodeA, NodeB) # Extremely danger operation! Two nodes must be aligned
                DIOout = np.append(DIOout, oneBlock.reshape((-1, Channel_Num)), axis=0)

                DIOout = np.append(DIOout, dischargeAll(0.2), axis=0) # Discharge all nodes

                animation = np.array([
                    [0, 0, 0, 0,
                     1, 0, 0, 0,
                     1, 0, 0, 0],
                    [-1, -1, -1, -1,
                     -1, -1, -1, -1,
                     -1, -1, -1, -1],
                    [1, 1, 0, 0,
                     0, 1, 0, 0,
                     1, 0, 0, 0],
                    [-1, -1, -1, -1,
                     -1, -1, -1, -1,
                     -1, -1, -1, -1],
                    [0, 1, 1, 0,
                     0, 1, 0, 0,
                     0, 0, 0, 0]
                ])
                DIOout = np.append(DIOout, Animation2DIO(animation, frameChargeRepNum=800, frameDischargeRepNum=1600), axis=0)

                DIOout = np.append(DIOout, dischargeAll(0.2), axis=0) # Discharge all nodes

                animation = np.array([
                    [0, 1, 1, 0,
                     1, 0, 0, 1,
                     0, 0, 0, 1],
                    [-1, -1, -1, -1,
                     -1, -1, -1, -1,
                     -1, -1, -1, -1],
                    [0, 0, 0, 0,
                     0, 0, 0, 0,
                     0, 1, 1, 0],
                    [-1, -1, -1, -1,
                     -1, -1, -1, -1,
                     -1, -1, -1, -1],
                    [0, 0, 0, 0,
                     0, 0, 0, 0,
                     1, 1, 1, 1],
                    [-1, -1, -1, -1,
                     -1, -1, -1, -1,
                     -1, -1, -1, -1],
                    [0, 0, 0, 0,
                     0, 1, 1, 0,
                     1, 1, 1, 0],
                    [-1, -1, -1, -1,
                     -1, -1, -1, -1,
                     -1, -1, -1, -1],
                    [0, 0, 0, 0,
                     1, 1, 1, 0,
                     0, 0, 0, 0],
                    [-1, -1, -1, -1,
                     -1, -1, -1, -1,
                     -1, -1, -1, -1],
                    [0, 1, 1, 0,
                     0, 0, 0, 0,
                     0, 0, 0, 0],
                ])
                DIOout = np.append(DIOout, Animation2DIO(animation, frameChargeRepNum=800, frameDischargeRepNum=2000), axis=0)

                DIOout = np.append(DIOout, dischargeAll(1.0), axis=0) # Discharge all nodes at the end

                isIdle = True
            else:
                button5.setFillColor([0, 0, 0])

            if 'escape' in event.getKeys():  # program ends
                core.wait(0.1)
                print("Demo Ended")
                task1.ClearTask()
                # window2.close()
                window0.close()
                core.quit()

            if isIdle: # --------------------------------------------------------------------- State: Output with DIOout
                isIdle = False

                light1.setFillColor(LED_RED)
                refreshWindow()

                # Safety measure and output buffer info
                DIOout[-1, :] = 0  # Ensure all channels are turned off at the end

                DIOoutLen = DIOout.shape[0]  # (= MeasureTime * F_PWM * int(F_CLK/F_PWM))
                print("DIOout Shape: ", DIOout.shape)
                measureTime = (DIOoutLen / F_CLK)
                print("Total time = %.3f sec" % measureTime)

                # checkOutput(DIOout) # Debug tool

                # Play video using external media player
                if(videoName):
                    subprocess.Popen([MEDIA_PLAYER_PATH, MEDIA_PLAYER_CMD, path.join(videoPath, videoName)])

                # Initialize DAQ
                task1.CfgSampClkTiming(source="OnboardClock", rate=F_CLK, activeEdge=nidaq.DAQmx_Val_Rising,
                                       sampleMode=nidaq.DAQmx_Val_FiniteSamps, sampsPerChan=DIOoutLen)
                task1.WriteDigitalLines(numSampsPerChan=DIOoutLen, autoStart=False,
                                        timeout=nidaq.DAQmx_Val_WaitInfinitely,
                                        dataLayout=nidaq.DAQmx_Val_GroupByScanNumber,
                                        writeArray=DIOout, reserved=None, sampsPerChanWritten=None)

                time.sleep(1.0)
                task1.StartTask()
                print("Display running ...")
                time.sleep(measureTime + 0.1)
                task1.StopTask()
                print("Display finished")

                light1.setFillColor(LED_GREEN)

'''-------------------------------------------------------------------------------'''