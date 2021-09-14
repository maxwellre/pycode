'''
Control the multi-channel bipolar HV board via NI DAQ via PWM.
Author: Yitian Shao (ytshao@is.mpg.de)
Created on 2021.09.07 based on 'WearableCtrlDAQ.py'
'''
import time
import numpy as np
import matplotlib.pyplot as plt
import PyDAQmx as nidaq
import sys

# MARCO
F_CLK = 1000000.0 # DOI Clock frequency (Circuit control sampling frequency, Hz)
F_PWM = 2000 # PWM frequency (Output waveform sampling frequency, Hz)

# Parameters
MeasureTime = 2.0 # Measurement time, in seconds.

PWMnum = int(MeasureTime * F_PWM) # Number of PWM samples
PWMpulseWidth = 1.0/F_PWM
PWMpulseCLKnum = int(F_CLK/F_PWM) # Total sample number
print("PWM frequency = %.1f Hz, PWM pulse duration = %.1f us (%d CLK ticks)" % (F_PWM, 1e6*PWMpulseWidth, PWMpulseCLKnum))

# Safety measure
HV_Off = np.zeros((1,2), dtype=np.uint8) # Total number of channels = ?

# Define PWM signals
# dutyCycleCharge = 0.3
# dutyCycleDisharge = 0.0
# PWMout = np.zeros((PWMpulseCLKnum,2), dtype=np.uint8)
#
# chargeEndInd = int(dutyCycleCharge*PWMpulseCLKnum)
# dischargeStartInd = chargeEndInd + 20 # (At least 20us sleep in between)
# dischargeEndInd = dischargeStartInd + int(dutyCycleDisharge*PWMpulseCLKnum)
#
# PWMout[:chargeEndInd,0] = 1
# PWMout[dischargeStartInd:dischargeEndInd,1] = 1
#
# DIOout = np.tile(PWMout, (PWMnum,1))
def Percent2PWM(direction, percentage = 0.0):
    PWMout = np.zeros((PWMpulseCLKnum, 2), dtype=np.uint8)
    if(direction == 'charge'):
        PWMout[:int(percentage * 0.01 * PWMpulseCLKnum), 0] = 1 # Charge cycle
    elif(direction == 'discharge'):
        PWMout[:int(percentage * 0.01 * PWMpulseCLKnum), 1] = 1 # Discharge cycle
    else:
        sys.exit("Invalid direction is given to PWM. Indicate either 'charge' or 'discharge' for the direction")
    return PWMout

t = np.arange(PWMnum)/F_PWM
sinFreq = 10
y = -50*np.cos(2*np.pi*sinFreq*t)+50

DIOout = np.array([Percent2PWM('charge', yi) for yi in y], dtype=np.uint8)
DIOout = DIOout.reshape((-1,2))
DIOoutLen = DIOout.shape[0] # (= MeasureTime * F_PWM * int(F_CLK/F_PWM))
print("DIOout Shape: ", DIOout.shape)
DIOout[-1,:] = 0 # Ensure all channels are turned off at the end

# fig1 = plt.figure(figsize = (16,6))
# fig1.suptitle(("Sine Freq = %.0f Hz" % sinFreq), fontsize=12)
# ax = fig1.add_subplot(111)
# # ax.plot(t, y, '-', color='tab:red')
# ax.plot(DIOout[:,0], '-', color='tab:red')
# plt.show()

'''-------------------------------------------------------------------------------'''

with nidaq.Task() as task1:
    task1.CreateDOChan("Dev2/port0/line2:3", None, nidaq.DAQmx_Val_ChanPerLine)
    task1.CfgSampClkTiming(source = "OnboardClock", rate = F_CLK, activeEdge=nidaq.DAQmx_Val_Rising,
                           sampleMode=nidaq.DAQmx_Val_FiniteSamps, sampsPerChan=DIOoutLen)

    task1.WriteDigitalLines(numSampsPerChan=DIOoutLen, autoStart=False,
                            timeout=nidaq.DAQmx_Val_WaitInfinitely, dataLayout=nidaq.DAQmx_Val_GroupByScanNumber,
                            writeArray=DIOout, reserved=None, sampsPerChanWritten=None)

    # ------------ start ------------ #
    task1.StartTask()
    print("Start sampling...")

    time.sleep(MeasureTime)

    task1.StopTask()
    print("Task completed!")
    task1.ClearTask()

