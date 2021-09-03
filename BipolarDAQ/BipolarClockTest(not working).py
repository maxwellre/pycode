'''
Control the new bipolar HV board via NI DAQ.
(Optional) Measure Fluid Pressure via NI DAQ.
Author: Yitian Shao (ytshao@is.mpg.de)
Created on 2021.09.02 based on 'WearableCtrlDAQ.py'
'''
import time
import numpy as np
import matplotlib.pyplot as plt
import PyDAQmx as nidaq

# MARCO
F_CLK = 52687038 # DOI Clock frequency (NI-USB6003 = 80MHz)
F_PWM = 2000 # PWM frequency (Hz)

# Parameters
AnalogInputNum = 2
Fs = 1000 # Sampling frequency (Hz)
MeasureTime = 2 # Measurement time, in seconds.

PWMpulseWidth = 1.0/F_PWM
PWMpulseCLKnum = int(F_CLK/F_PWM)
print("PWM frequency = %.1f Hz, PWM pulse width = %.1f us (%d CLK ticks)" % (F_PWM, 1e6*PWMpulseWidth, PWMpulseCLKnum))

# Define PWM signals
PWMdutyCycle = 0.1
PWMout = np.zeros((PWMpulseCLKnum,), dtype=np.uint8)
PWMout[:int(PWMdutyCycle*PWMpulseCLKnum)] = 1

DIOout = np.tile(PWMout, F_PWM)
DIOoutLen = DIOout.shape[0]
print("DIOoutLen = %d" % DIOoutLen)
'''-------------------------------------------------------------------------------'''
readLen = int(MeasureTime * Fs) # The number of samples, per channel, to read

with nidaq.Task() as task1:
    task1.CreateDOChan("Dev1/port0/line0", None, nidaq.DAQmx_Val_ChanPerLine)

    # DAQ start
    task1.StartTask()
    print("Start sampling...")

    # for i in range(3):
    task1.WriteDigitalLines(numSampsPerChan = DIOoutLen, autoStart = False,
                            timeout = nidaq.DAQmx_Val_WaitInfinitely, dataLayout = nidaq.DAQmx_Val_GroupByChannel,
                            writeArray = DIOout, reserved = None, sampsPerChanWritten = None)

    task1.StopTask()
    print("Task completed!")
    task1.ClearTask()