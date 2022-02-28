'''
Wireless HV controller combined with DAQ for pressure measurement
Author: Yitian Shao (ytshao@is.mpg.de)
Created on 2022.02.28 based on 'ControllerWiFi.py'
'''
'''
[Note] New Protocol Codes: b'pcprogram' - b'l' - b's' - 'voooooooo=%03d-chhhhhT=%04d-diiiiiiiiT=%04d'
[Note] Charge and Discharge Time set to be longer than 1 second
'''

import sys
import time
import socket
from psychopy import core, visual, gui, data, event
import numpy as np
import matplotlib.pyplot as plt
import PyDAQmx as nidaq

'''Marco'''
LED_RED = [1.0,-1.0,-1.0]
LED_GREEN = [-1.0,1.0,-1.0]
LIGHT_GREEN = [-0.5,0.5,-0.5]
DARK_GREEN = [-1.0,-0.5,-1.0]
LIGHT_YELLOW = [0.5,0.5,-0.5]
DARK_YELLOW = [-0.5,-0.5,-1.0]
LIGHT_BLUE = [-0.5,-0.5,0.5]
DARK_BLUE = [-1.0,-1.0,-0.5]

CHARGE_MAX = 3000
DISCHARGE_MAX = 4000

'''Configuration'''
'''-------------------------------------------------------------------------------'''
''' DAQ '''
NIDev6003Num = 1
MeasureTime = 7

AnalogInputNum = 3
Fs = 1000.0 # Sampling frequency

readLen = int(MeasureTime * Fs) # The number of samples, per channel, to read

''' WiFi '''
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
button1Text = visual.TextStim(window0, pos=button1.pos, text='Measure', height=0.05)
button2Text = visual.TextStim(window0, pos=button2.pos, text='Left', height=0.05)
button3Text = visual.TextStim(window0, pos=button3.pos, text='Plot', height=0.05)
# 990+220
slider1 = visual.Slider(window0, ticks=[0, 15, 50, 100], labels=['0', '15', '50', '100'], startValue=0, pos=[-0.38, -0.3],
                        size=[0.44, 0.1], granularity=5, labelHeight=0.045, fillColor=[0.6,0,0], style='slider')
slider2 = visual.Slider(window0, ticks=[0, CHARGE_MAX], labels=['0', ("%d" % CHARGE_MAX)], startValue=1000, pos=[-0.4, 0.0],
                        size=[0.3, 0.1], granularity=1, labelHeight=0.05, fillColor=[0.6,0,0], style='slider')
slider3 = visual.Slider(window0, ticks=[0, DISCHARGE_MAX], labels=['0', ("%d" % DISCHARGE_MAX)], startValue=DISCHARGE_MAX, pos=[-0.4, 0.25],
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
    ans = sockObj.recv(1024)
    while ans.decode() != "command-received":
        ans = sockObj.recv(1024)

    if (lightObj):
        lightObj.setFillColor(LED_GREEN)

'''-------------------------------------------------------------------------------------------------------------'''



'''-------------------------------------------------------------------------------------------------------------'''
if __name__ == '__main__':
    trial = 0

    # Initialization of DAQ
    calib = np.loadtxt('Calibration20210802.txt')
    print("Calibration line a = %.16f, b = %.16f" % (calib[0], calib[1]))

    isMeasuring = False
    daqdata = np.zeros((readLen * AnalogInputNum,), dtype=np.float64)
    task0 = nidaq.Task()
    # DAQ configuration of Anaglog Inputs
    task0.CreateAIVoltageChan("Dev%d/ai1" % NIDev6003Num, None, nidaq.DAQmx_Val_Diff, -1, 9, nidaq.DAQmx_Val_Volts,
                              None)
    task0.CreateAIVoltageChan("Dev%d/ai2" % NIDev6003Num, None, nidaq.DAQmx_Val_Diff, -1, 9, nidaq.DAQmx_Val_Volts,
                              None)
    task0.CreateAIVoltageChan("Dev%d/ai3" % NIDev6003Num, None, nidaq.DAQmx_Val_Diff, -1, 9, nidaq.DAQmx_Val_Volts,
                              None)
    task0.CfgSampClkTiming(None, Fs, nidaq.DAQmx_Val_Rising, nidaq.DAQmx_Val_FiniteSamps, readLen)

    # Initialization of WiFi
    isConnected = False

    status0.draw()
    light1.draw()
    window0.flip()

    sock0 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock0.connect((HOST, PORT))
    while not isConnected: # try to establish a WiFi connection
        sock0.sendall(b'pcprogram')  # "Handshake" new protocol
        ans = sock0.recv(1024)
        if ans.decode() == "high-voltage-controller-is-ready": # "Handshake" protocol matched
            isConnected = True
            print("Successful connection to high voltage controller")

    '''GUI Setup'''
    while True:
        refreshWindow()

        if mouse0.isPressedIn(button1, buttons=[0]) and (not isMeasuring):
            button1.setFillColor(DARK_GREEN)

            # Take measurement
            daqdata = np.zeros((readLen * AnalogInputNum,), dtype=np.float64)
            actualReadNum = nidaq.int32()

            isMeasuring = True
            light1.setFillColor(LED_RED)
            refreshWindow()

            task0.StartTask()
            print("Start sampling...")
            time0 = time.time()
            time.sleep(0.5)

            sock0.sendall(b'l')

            ans = sock0.recv(1024)
            while ans.decode() != "command-received":
                ans = sock0.recv(1024)

            time.sleep(0.5)

            task0.ReadAnalogF64(numSampsPerChan=nidaq.DAQmx_Val_Auto, timeout=nidaq.DAQmx_Val_WaitInfinitely,
                                fillMode=nidaq.DAQmx_Val_GroupByChannel, readArray=daqdata,
                                arraySizeInSamps=len(daqdata),
                                sampsPerChanRead=nidaq.byref(actualReadNum), reserved=None)

            task0.StopTask()
            print("Task completed in %.6f sec" % (time.time() - time0))

            light1.setFillColor(LED_GREEN)

            daqdata = daqdata.reshape(AnalogInputNum, -1).T

            currentTime = time.strftime("%H-%M-%S", time.localtime())

            np.savetxt(("Data/Data_Fs%d_at%s_Si20Vl%03d_t%02d.csv" % (Fs, currentTime, slider1.getRating(), trial)),
                       daqdata, delimiter=",")
            print("Data saved on %s" % currentTime)
            trial = trial + 1
            isMeasuring = False

        else:
            button1.setFillColor(LIGHT_GREEN)

        if mouse0.isPressedIn(button2, buttons=[0]):
            button2.setFillColor(DARK_YELLOW)
            command(sock0, 'l', light1)
        else:
            button2.setFillColor(LIGHT_YELLOW)

        if mouse0.isPressedIn(button3, buttons=[0]):
            button3.setFillColor(DARK_BLUE)

            '''-------------------------------------------------------------------------------'''
            # Plot data
            fig1 = plt.figure(figsize=(16, 6))
            fig1.suptitle(("Fs = %.0f Hz" % Fs), fontsize=12)
            ax = fig1.add_subplot(111)
            ax.set_xlabel('Time (sec)')

            t = np.arange(actualReadNum.value) / Fs

            # Measured pressure
            ax.plot(t, (daqdata[:, 2] - calib[1]) * calib[0], '-', color='tab:red')
            ax.set_ylabel('Pressure (Bar)', color='tab:red')
            ax.tick_params(axis='y', labelcolor='tab:red')

            # Reference (control) signal and flow rate (Voltage)
            ax2 = ax.twinx()
            ax2.plot(t, daqdata[:, 0], '--', color='tab:blue')
            ax2.plot(t, daqdata[:, 1], '-', color='tab:brown')
            ax2.set_ylabel('Voltage (V)', color='tab:blue')
            ax2.tick_params(axis='y', labelcolor='tab:blue')

            fig1.tight_layout()
            plt.show()

        else:
            button3.setFillColor(LIGHT_BLUE)

        if mouse0.isPressedIn(button4, buttons=[0]):
            button4.setFillColor([-0.8,-0.8,-0.8])
            command(sock0, 's', light1)
            
            command(sock0, 'voooooooo=%03d-chhhhhT=%04d-diiiiiiiiT=%04d' %
                    (slider1.getRating(), slider2.getRating(), slider3.getRating()), light1)

            print('voltlevel=%03d-chargeT=%04d-dischargeT=%04d' %
                  (slider1.getRating(),slider2.getRating(),slider3.getRating()))
        else:
            button4.setFillColor([0,0,0])

        core.wait(0.01)  # pause

        if 'escape' in event.getKeys(): # program ends
            core.wait(0.1)
            sock0.close()
            window0.close()
            core.quit()