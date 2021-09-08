'''
Control the HV source through NI DAQ entirely.
Measure Fluid Pressure via NI DAQ as well.
DAQmxCreateAIVoltageChan: https://zone.ni.com/reference/en-XX/help/370471AA-01/daqmxcfunc/daqmxcreateaivoltagechan/
DAQmxCreateAOVoltageChan: https://pythonhosted.org/PyDAQmx/examples/analog_output.html

Author: Yitian Shao (ytshao@is.mpg.de)
Created on 2021.08.17 based on 'SteamDAQ.py'
'''
import time
import numpy as np
import matplotlib.pyplot as plt
import PyDAQmx as nidaq

Fs = 1000.0 # Samples_Per_Sec = 5000
TimeOut = 7 # The amount of time, in seconds, to wait for the function to read.
showPressure = True
OutputVolt = 7.0

'''-------------------------------------------------------------------------------'''
dt = 1.0/Fs-0.000016 # Manual correction of PC timer
readLen = int(TimeOut * Fs) # The number of samples, per channel, to read

calib = np.loadtxt('Calibration20210802.txt')
print("Calibration line a = %.16f, b = %.16f" % (calib[0],calib[1]))

daqdata = np.zeros((readLen*2,), dtype=np.float64)

daqOutput = np.zeros((readLen,), dtype=np.float64)
daqOutput[int(1*Fs):int(5*Fs)] = OutputVolt
daqOutput[int(8*Fs):int(12*Fs)] = OutputVolt
daqOutput[int(15*Fs):int(19*Fs)] = OutputVolt
daqOutput[-1] = 0.0

IO_High = np.ones((1,), dtype=np.uint8)
IO_Low = np.zeros((1,), dtype=np.uint8)

actualReadNum = nidaq.int32()  # It holds the total number of dataFs1000Old points read per channel
with nidaq.Task() as task0, nidaq.Task() as task1:
    task0.CreateAIVoltageChan("Dev1/ai2", None, nidaq.DAQmx_Val_Diff, -1, 4, nidaq.DAQmx_Val_Volts, None)
    task0.CreateAIVoltageChan("Dev1/ai3", None, nidaq.DAQmx_Val_Diff, -1, 9, nidaq.DAQmx_Val_Volts, None)
    task0.CfgSampClkTiming("", Fs, nidaq.DAQmx_Val_Rising, nidaq.DAQmx_Val_FiniteSamps, readLen)

    # task1.CreateAOVoltageChan("Dev1/ao0", None, 0, 6, nidaq.DAQmx_Val_Volts, None)
    # task1.CfgSampClkTiming("", Fs, nidaq.DAQmx_Val_Rising, nidaq.DAQmx_Val_FiniteSamps, readLen)
    # task1.WriteAnalogF64(numSampsPerChan=readLen, autoStart=True, timeout=TimeOut+1,
    # dataLayout=nidaq.DAQmx_Val_GroupByChannel, writeArray=daqOutput, reserved=None,
    # sampsPerChanWritten=nidaq.byref(actualReadNum))

    task1.CreateDOChan("Dev1/port0/line0","",nidaq.DAQmx_Val_FiniteSamps)

    task1.StartTask()
    task0.StartTask()
    print("Start sampling...")
    time0 = time.time()

    for ti in range(readLen):
        if (daqOutput[ti] > 0):
            task1.WriteDigitalLines(1, False, 10.0, nidaq.DAQmx_Val_GroupByChannel, IO_High, None, None)
        else:
            task1.WriteDigitalLines(1, False, 10.0, nidaq.DAQmx_Val_GroupByChannel, IO_Low, None, None)

        target_time = time.clock() + dt
        while time.clock() < target_time:
            pass

    task0.ReadAnalogF64(readLen, TimeOut+1, nidaq.DAQmx_Val_GroupByChannel, daqdata, len(daqdata)*2,
                        nidaq.byref(actualReadNum), None)

    print("Sample time = %.3f sec - Actual readed sample number = %d" % (time.time() - time0, actualReadNum.value))
    task0.StopTask()
    task1.StopTask()

daqdata = daqdata.reshape(2,-1).T

dispdata = daqdata.copy()
if(showPressure):
    dispdata[:,1] = (dispdata[:,1]-calib[1])*calib[0]

fig1 = plt.figure(figsize = (16,6))
fig1.suptitle(("Fs = %.0f Hz" % Fs), fontsize=12)
ax = fig1.add_subplot(111) # projection='3d'
ax.set_xlabel('Samples')

if(showPressure):
    ax.set_ylabel('Pressure (Bar)', color='tab:red')
else:
    ax.set_ylabel('Voltage (V)', color='tab:orange')

t = np.arange(actualReadNum.value)/Fs

ax.plot(t, dispdata[:,1], '-', color='tab:red')
ax.tick_params(axis='y', labelcolor='tab:red')

ax2 = ax.twinx()
ax2.plot(t, daqOutput, '--', color='tab:gray')
ax2.plot(t, dispdata[:,0], '--', color='tab:blue')
ax2.set_ylabel('Output Voltage (kV)', color='tab:blue')
ax2.tick_params(axis='y', labelcolor='tab:blue')

fig1.tight_layout()
plt.show()
'''-------------------------------------------------------------------------------'''
currentTime = time.strftime("%H-%M-%S", time.localtime())

trial = 5

np.savetxt(("Data_Fs%d_at%s_TestCamForce_t%02d.csv" % (Fs, currentTime, trial)), daqdata, delimiter=",")
print("Data saved on %s" % currentTime)