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

AnalogInputNum = 2
Fs = 1000.0 # Sampling frequency
MeasureTime = 8 # Measurement time, in seconds. (7)
showPressure = True # To display in raw unit (voltage) or converted to pressure unit

# Define control signals
HV_Off = np.zeros((1,3), dtype=np.uint8)
HV_Charge = np.zeros((1,3), dtype=np.uint8)
HV_Discharge = np.zeros((1,3), dtype=np.uint8)
HV_Charge[0,1:] = 1 # DIO line1 controls Positive HV (charge line)
HV_Discharge[0,0] = 1 # DIO line0 controls Negative HV (discharge line)
HV_Discharge[0,2] = 1

'''-------------------------------------------------------------------------------'''
readLen = int(MeasureTime * Fs) # The number of samples, per channel, to read

calib = np.loadtxt('Calibration20210802.txt')
print("Calibration line a = %.16f, b = %.16f" % (calib[0],calib[1]))

daqdata = np.zeros((readLen*AnalogInputNum,), dtype=np.float64)

actualReadNum = nidaq.int32()
with nidaq.Task() as task0, nidaq.Task() as task1:
    # DAQ configuration
    task0.CreateAIVoltageChan("Dev1/ai2", None, nidaq.DAQmx_Val_Diff, -1, 4, nidaq.DAQmx_Val_Volts, None)
    task0.CreateAIVoltageChan("Dev1/ai3", None, nidaq.DAQmx_Val_Diff, -1, 9, nidaq.DAQmx_Val_Volts, None)
    task0.CfgSampClkTiming(None, Fs, nidaq.DAQmx_Val_Rising, nidaq.DAQmx_Val_FiniteSamps, readLen)

    task1.CreateDOChan("Dev1/port0/line0:2", None, nidaq.DAQmx_Val_ChanPerLine)

    # DAQ start
    task1.StartTask()
    task0.StartTask()
    print("Start sampling...")
    time0 = time.time()

    # Repeat charging and discharging
    for i in range(2):
        task1.WriteDigitalLines(1, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, HV_Charge, None, None)
        time.sleep(1)
        task1.WriteDigitalLines(1, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, HV_Off, None, None)
        time.sleep(1)
        task1.WriteDigitalLines(1, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, HV_Discharge, None, None)
        time.sleep(1)
        task1.WriteDigitalLines(1, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, HV_Off, None, None)
        time.sleep(1)

    task0.ReadAnalogF64(nidaq.DAQmx_Val_Auto, 1.0, nidaq.DAQmx_Val_GroupByChannel, daqdata, len(daqdata),
                        nidaq.byref(actualReadNum), None)

    # Safety measure
    task1.WriteDigitalLines(1, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, HV_Off, None, None)

    print("Total time = %.3f sec - Actual read sample number = %d" % (time.time() - time0, actualReadNum.value))

    task0.StopTask()
    task1.StopTask()
    print("Task completed!")
    task0.ClearTask()
    task1.ClearTask()

daqdata = daqdata.reshape(AnalogInputNum,-1).T

'''-------------------------------------------------------------------------------'''
dispdata = daqdata
if(showPressure):
    dispdata[:,1] = (dispdata[:,1]-calib[1])*calib[0]

fig1 = plt.figure(figsize = (16,6))
fig1.suptitle(("Fs = %.0f Hz" % Fs), fontsize=12)
ax = fig1.add_subplot(111)
ax.set_xlabel('Samples')

if(showPressure):
    ax.set_ylabel('Pressure (Bar)', color='tab:red')
else:
    ax.set_ylabel('Voltage (V)', color='tab:orange')

t = np.arange(actualReadNum.value)/Fs

# Measured pressure
ax.plot(t, dispdata[:,1], '-', color='tab:red')
ax.tick_params(axis='y', labelcolor='tab:red')

# Reference (control) signal
ax2 = ax.twinx()
ax2.plot(t, dispdata[:,0], '--', color='tab:blue')
ax2.set_ylabel('Control signal (V)', color='tab:blue')
ax2.tick_params(axis='y', labelcolor='tab:blue')

fig1.tight_layout()
plt.show()
'''-------------------------------------------------------------------------------'''
# currentTime = time.strftime("%H-%M-%S", time.localtime())
#
# trial = 0
#
# np.savetxt(("Data_Fs%d_at%s_TestBipolar_t%02d.csv" % (Fs, currentTime, trial)), daqdata, delimiter=",")
# print("Data saved on %s" % currentTime)