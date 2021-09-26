'''
Control the new bipolar HV board (electrode-array) via NI DAQ.
(Optional) Measurement via NI DAQ.
Author: Yitian Shao (ytshao@is.mpg.de)
Created on 2021.09.17 based on 'B3HV4GNDDAQ.py'
'''
import time
import numpy as np
import matplotlib.pyplot as plt
import PyDAQmx as nidaq
import sys

# MARCO
F_CLK = 1000.0 # DOI Clock frequency (Circuit control sampling frequency, Hz)

NODE_NUM = 12 # 3HV * 4GND array of nodes

CHARGE_XY = [[0,6],[0,7],[0,8],[0,9],
             [2,6],[2,7],[2,8],[2,9],
            [4,6],[4,7],[4,8],[4,9]]

DISCHARGE_XY = [[1,6],[1,7],[1,8],[1,9],
                [3,6],[3,7],[3,8],[3,9],
                [5,6],[5,7],[5,8],[5,9]]

# Parameters
frameChargeRepNum =36 # Number of repetitions of charge per animation frame (per node) = 20
frameDischargeRepNum = 40 # Number of repetitions of discharge per animation frame (per node) = 12
frameIntvTime = 0.01 # (sec) Time pause interval between two frames

# animation = np.array([
# [0, 0, 0, 0,
# 0, 0, 0, 0,
# 1, 0, 0, 0],
# [0, 0, 0, 0,
# 0, 1, 0, 0,
# 0, 0, 0, 0],
#
# [-1, -1, -1, -1,
# -1, -1, -1, -1,
# -1, -1, -1, -1],
#
# [0, 0, 0, 0,
# 0, 0, 0, 0,
# 0, 0, 0, 1],
# [0, 0, 0, 0,
# 0, 0, 1, 0,
# 0, 0, 0, 0],
#
# [-1, -1, -1, -1,
# -1, -1, -1, -1,
# -1, -1, -1, -1],
#
# [0, 0, 0, 1,
# 0, 0, 0, 0,
# 0, 0, 0, 0],
# [0, 0, 0, 0,
# 0, 0, 1, 0,
# 0, 0, 0, 0],
#
# [-1, -1, -1, -1,
# -1, -1, -1, -1,
# -1, -1, -1, -1],
#
# [1, 0, 0, 0,
# 0, 0, 0, 0,
# 0, 0, 0, 0],
# [0, 0, 0, 0,
# 0, 1, 0, 0,
# 0, 0, 0, 0],
#
# [-1, -1, -1, -1,
# -1, -1, -1, -1,
# -1, -1, -1, -1]
# ])

nodeSeq = [0, 1, 2, 3, 7, 11, 10, 9, 8, 4]
animation = np.empty((0,12))
for nodeSi in nodeSeq:
    temp = np.zeros((1,12))
    temp[0,nodeSi] = 1
    animation = np.append(animation, temp, axis=0)
    animation = np.append(animation, -1*np.ones((1,12)), axis=0)
print(animation)

# animation = np.array([
# # [0, 0, 0, 0,
# # 0, 0, 0, 0,
# # 0, 0, 0, 1],
# #
# # [0, 0, 0, 0,
# # 0, 0, 0, 0,
# # 0, 0, 0, 0],
# #
# # [0, 0, 0, 0,
# # 0, 1, 0, 0,
# # 0, 0, 0, 0],
#
# [-1, -1, -1, -1,
# -1, -1, -1, -1,
# -1, -1, -1, -1]
# ])

# animation = np.tile(animation, (3, 1))

frameNum = animation.shape[0]

dischargeNode = np.arange(start=0, stop=NODE_NUM * frameDischargeRepNum, step=NODE_NUM)
chargeNode = dischargeNode[:frameChargeRepNum]

DIOout = np.empty((0,10), dtype=np.uint8)
for animFrame in animation:
    oneFrame = np.zeros((NODE_NUM*frameDischargeRepNum*2,10), dtype=np.uint8)

    chargeInd = np.where(animFrame == 1)[0]
    for i in chargeInd:
        oneFrame[(chargeNode+i)*2, CHARGE_XY[i][0]] = 1
        oneFrame[(chargeNode+i)*2, CHARGE_XY[i][1]] = 1

    dischargeInd = np.where(animFrame == -1)[0]
    for i in dischargeInd:
        oneFrame[(dischargeNode+i)*2, DISCHARGE_XY[i][0]] = 1
        oneFrame[(dischargeNode+i)*2, DISCHARGE_XY[i][1]] = 1

    DIOout = np.append(DIOout, oneFrame, axis=0)
    # DIOout = np.append(DIOout, np.zeros((int(frameIntvTime*F_CLK),10), dtype=np.uint8), axis=0)

# Safety measure
DIOout[-1,:] = 0 # Ensure all channels are turned off at the end

DIOoutLen = DIOout.shape[0] # (= MeasureTime * F_PWM * int(F_CLK/F_PWM))
print("DIOout Shape: ", DIOout.shape)

measureTime = (DIOoutLen/F_CLK)
print("Total time = %.3f sec" % measureTime)
'''-------------------------------------------------------------------------------'''
# ''' Functions'''
dispOutput = 0
if dispOutput:
    fig1 = plt.figure(figsize = (16,6))
    fig1.suptitle(("CLK Freq = %.0f Hz" % F_CLK), fontsize=12)
    ax = fig1.add_subplot(111)
    t = np.arange(DIOoutLen)/F_CLK
    for i in range(10):
        ax.plot(t, DIOout[:,i]+i*2, '.-')
    plt.show()
'''-------------------------------------------------------------------------------'''
if __name__ == '__main__':
    with nidaq.Task() as task1:
        # DAQ configuration
        task1.CreateDOChan("Dev2/port0/line0:5,Dev2/port0/line10:13", None, nidaq.DAQmx_Val_ChanPerLine)
        task1.CfgSampClkTiming(source="OnboardClock", rate=F_CLK, activeEdge=nidaq.DAQmx_Val_Rising,
                               sampleMode=nidaq.DAQmx_Val_FiniteSamps, sampsPerChan=DIOoutLen)

        task1.WriteDigitalLines(numSampsPerChan=DIOoutLen, autoStart=False,
                                timeout=nidaq.DAQmx_Val_WaitInfinitely, dataLayout=nidaq.DAQmx_Val_GroupByScanNumber,
                                writeArray=DIOout, reserved=None, sampsPerChanWritten=None)

        # ------------ start ------------ #
        task1.StartTask()
        print("Start sampling...")

        time.sleep(measureTime)

        task1.StopTask()
        print("Task completed!")
        task1.ClearTask()

'''-------------------------------------------------------------------------------'''