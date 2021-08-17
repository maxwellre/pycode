'''
https://nidaqmx-python.readthedocs.io/en/latest/
PyDAQmx Info: https://www.pythonforthelab.com/blog/controlling-a-national-instruments-card-with-python/
DAQmxCreateAIVoltageChan: https://zone.ni.com/reference/en-XX/help/370471AA-01/daqmxcfunc/daqmxcreateaivoltagechan/
DAQmxCreateAOVoltageChan: https://pythonhosted.org/PyDAQmx/examples/analog_output.html

Author: Yitian Shao (ytshao@is.mpg.de)
'''
import time
import numpy as np
import matplotlib.pyplot as plt
import PyDAQmx as nidaq

Fs = 1000 # Samples_Per_Sec = 5000
TimeOut = 20 # The amount of time, in seconds, to wait for the function to read.
showPressure = True
OutputVolt = 7.0

'''-------------------------------------------------------------------------------'''
readLen = TimeOut * Fs # The number of samples, per channel, to read

calib = np.loadtxt('Calibration20210802.txt')
print("Calibration line a = %.16f, b = %.16f" % (calib[0],calib[1]))

daqdata = np.zeros((readLen,), dtype=np.float64)

daqOutput = np.zeros((readLen,), dtype=np.float64)
daqOutput[1*Fs:5*Fs] = OutputVolt
daqOutput[8*Fs:12*Fs] = -OutputVolt
daqOutput[15*Fs:19*Fs] = OutputVolt
daqOutput[-1] = 0.0

actualReadNum = nidaq.int32()  # It holds the total number of dataFs1000Old points read per channel
with nidaq.Task() as task0, nidaq.Task() as task1:
    task0.CreateAIVoltageChan("Dev1/ai3", None, nidaq.DAQmx_Val_Diff, -1, 9, nidaq.DAQmx_Val_Volts, None)
    task0.CfgSampClkTiming("", Fs, nidaq.DAQmx_Val_Rising, nidaq.DAQmx_Val_FiniteSamps, readLen)

    task1.CreateAOVoltageChan("Dev1/ao0", None, 0, 6, nidaq.DAQmx_Val_Volts, None)
    task1.CfgSampClkTiming("", Fs, nidaq.DAQmx_Val_Rising, nidaq.DAQmx_Val_FiniteSamps, readLen)
    task1.WriteAnalogF64(numSampsPerChan=readLen, autoStart=True, timeout=TimeOut+1, dataLayout=nidaq.DAQmx_Val_GroupByChannel,
                   writeArray=daqOutput, reserved=None, sampsPerChanWritten=nidaq.byref(actualReadNum))

    task0.StartTask()
    print("Start sampling...")
    time0 = time.time()
    task0.ReadAnalogF64(readLen, TimeOut+1, nidaq.DAQmx_Val_GroupByChannel, daqdata, len(daqdata),
                        nidaq.byref(actualReadNum), None)
    print("Sample time = %.3f sec - Actual readed sample number = %d" % (time.time() - time0, actualReadNum.value))
    task0.StopTask()
    task1.StopTask()

fig1 = plt.figure(figsize = (16,6))
fig1.suptitle(("Fs = %.0f Hz" % Fs), fontsize=12)
ax = fig1.add_subplot(111) # projection='3d'
ax.set_xlabel('Samples')

if(showPressure):
    ax.set_ylabel('Pressure (Bar)', color='tab:red')
else:
    ax.set_ylabel('Voltage (V)', color='tab:red')

t = np.arange(actualReadNum.value)/Fs
if(showPressure):
    ax.plot(t, (daqdata-calib[1])*calib[0], '-', color='tab:red')
else:
    ax.plot(t, daqdata, '-', color='tab:orange')

ax.tick_params(axis='y', labelcolor='tab:red')

ax2 = ax.twinx()
ax2.plot(t, daqOutput, '--', color='tab:blue')
ax2.set_ylabel('Output Voltage (kV)', color='tab:blue')
ax2.tick_params(axis='y', labelcolor='tab:blue')

fig1.tight_layout()
plt.show()
'''-------------------------------------------------------------------------------'''
currentTime = time.strftime("%H-%M-%S", time.localtime())

trial = 6

np.savetxt(("Data_Fs%d_at%s_MLSi20B7kV_t%02d.csv" % (Fs, currentTime, trial)), daqdata, delimiter=",")

# bar = 0.000
#
# np.savetxt(("%.3fbar_%d.csv" % (bar, trial)), daqdata, delimiter=",")

print("Data saved on %s" % currentTime)