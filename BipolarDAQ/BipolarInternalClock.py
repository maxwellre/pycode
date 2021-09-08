'''
Control the multi-channel bipolar HV board via NI DAQ via PWM.
Author: Yitian Shao (ytshao@is.mpg.de)
Created on 2021.09.07 based on 'WearableCtrlDAQ.py'
'''
import time
import numpy as np
import matplotlib.pyplot as plt
import PyDAQmx as nidaq

# MARCO
F_CLK = 1000000.0 # DOI Clock frequency (Circuit control sampling frequency, Hz)
F_PWM = 10000 # PWM frequency (Output waveform sampling frequency, Hz)

# Parameters
MeasureTime = 2.0 # Measurement time, in seconds.

PWMnum = int(MeasureTime * F_PWM)
PWMpulseWidth = 1.0/F_PWM
PWMpulseCLKnum = int(F_CLK/F_PWM) # Total sample number
print("PWM frequency = %.1f Hz, PWM pulse width = %.1f us (%d CLK ticks)" % (F_PWM, 1e6*PWMpulseWidth, PWMpulseCLKnum))

# Define PWM signals
PWMdutyCycle = 0.5
PWMout = np.zeros((PWMpulseCLKnum,), dtype=np.uint8)
PWMout[:int(PWMdutyCycle*PWMpulseCLKnum)] = 1

DIOout = np.tile(PWMout, PWMnum)
DIOoutLen = DIOout.shape[0] # (= MeasureTime * F_PWM * int(F_CLK/F_PWM))
print("DIOoutLen = %d" % DIOoutLen)
'''-------------------------------------------------------------------------------'''

with nidaq.Task() as task1:
    # task0.CreateCOPulseChanFreq(counter = "Dev2/freqout", nameToAssignToChannel = None, units = nidaq.DAQmx_Val_Hz,
        # idleState = nidaq.DAQmx_Val_Low, initialDelay = 0.0, freq = F_CLK, dutyCycle = 0.5) # DEV2/PFI14

    task1.CreateDOChan("Dev2/port0/line0", None, nidaq.DAQmx_Val_ChanPerLine)
    task1.CfgSampClkTiming(source = "OnboardClock", rate = F_CLK, activeEdge=nidaq.DAQmx_Val_Rising,
                           sampleMode=nidaq.DAQmx_Val_FiniteSamps, sampsPerChan=DIOoutLen) #PFI14 DAQmx_Val_FiniteSamps DAQmx_Val_ContSamps

    task1.WriteDigitalLines(numSampsPerChan=DIOoutLen, autoStart=False,
                            timeout=nidaq.DAQmx_Val_WaitInfinitely, dataLayout=nidaq.DAQmx_Val_GroupByChannel,
                            writeArray=DIOout, reserved=None, sampsPerChanWritten=None)

    # ------------ start ------------ #
    task1.StartTask()
    print("Start sampling...")

    time.sleep(MeasureTime)
    task1.StopTask()
    print("Task completed!")
    task1.ClearTask()

