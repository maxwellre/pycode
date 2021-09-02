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

Fs = 1000.0 # Sampling frequency
MeasureTime = 3 # Measurement time, in seconds. (7)
# showPressure = True # To display in raw unit (voltage) or converted to pressure unit

'''-------------------------------------------------------------------------------'''
dt = 1.0/Fs#-0.000016 # Manual correction of PC timer (For the Dell labtop specifically)
half_dt = 0.5*dt-0.0002
readLen = int(MeasureTime * Fs) # The number of samples, per channel, to read

calib = np.loadtxt('Calibration20210802.txt')
print("Calibration line a = %.16f, b = %.16f" % (calib[0],calib[1]))

# daqdata = np.zeros((readLen*2,), dtype=np.float64)

IO_High = np.ones((1,), dtype=np.uint8)
IO_Low = np.zeros((1,), dtype=np.uint8)

outData = np.zeros((readLen,), dtype=np.uint8)
outData[1000:2000] = 1
outData[5000:6000] = 1

actualReadNum = nidaq.int32()
with nidaq.Task() as task0, nidaq.Task() as task1:
    # task0.CreateAIVoltageChan("Dev1/ai2", None, nidaq.DAQmx_Val_Diff, -1, 4, nidaq.DAQmx_Val_Volts, None)
    # task0.CreateAIVoltageChan("Dev1/ai3", None, nidaq.DAQmx_Val_Diff, -1, 9, nidaq.DAQmx_Val_Volts, None)
    # task0.CfgSampClkTiming(None, Fs, nidaq.DAQmx_Val_Rising, nidaq.DAQmx_Val_FiniteSamps, readLen)

    task1.CreateDOChan("Dev1/port0/line0", None, nidaq.DAQmx_Val_ChanPerLine)

    task1.StartTask()
    # task0.StartTask()
    print("Start sampling...")
    # time0 = time.time()

    # task1.WriteDigitalLines(readLen, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, outData, None, None)

    for ti in range(readLen):
        task1.WriteDigitalLines(1, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, IO_High, None, None)

        target_time = time.clock() + half_dt
        while time.clock() < target_time:
            pass

        task1.WriteDigitalLines(1, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, IO_Low, None, None)

        target_time = time.clock() + half_dt
        while time.clock() < target_time:
            pass

    # task0.ReadAnalogF64(readLen, TimeOut+1, nidaq.DAQmx_Val_GroupByChannel, daqdata, len(daqdata)*2,
    #                     nidaq.byref(actualReadNum), None)

    # print("Sample time = %.3f sec - Actual readed sample number = %d" % (time.time() - time0, actualReadNum.value))
    # task0.StopTask()
    task1.StopTask()
    print("Task completed!")
    task0.ClearTask()
    task1.ClearTask()

# daqdata = daqdata.reshape(2,-1).T
#
# dispdata = daqdata
# if(showPressure):
#     dispdata[:,1] = (dispdata[:,1]-calib[1])*calib[0]
#
# fig1 = plt.figure(figsize = (16,6))
# fig1.suptitle(("Fs = %.0f Hz" % Fs), fontsize=12)
# ax = fig1.add_subplot(111)
# ax.set_xlabel('Samples')
#
# if(showPressure):
#     ax.set_ylabel('Pressure (Bar)', color='tab:red')
# else:
#     ax.set_ylabel('Voltage (V)', color='tab:orange')
#
# t = np.arange(actualReadNum.value)/Fs
#
# ax.plot(t, dispdata[:,1], '-', color='tab:red')
# ax.tick_params(axis='y', labelcolor='tab:red')
#
# ax2 = ax.twinx()
# ax2.plot(t, daqOutput, '--', color='tab:gray')
# ax2.plot(t, dispdata[:,0], '--', color='tab:blue')
# ax2.set_ylabel('Output Voltage (kV)', color='tab:blue')
# ax2.tick_params(axis='y', labelcolor='tab:blue')
#
# fig1.tight_layout()
# plt.show()
'''-------------------------------------------------------------------------------'''
# currentTime = time.strftime("%H-%M-%S", time.localtime())
#
# trial = 0
#
# np.savetxt(("Data_Fs%d_at%s_TestBipolar_t%02d.csv" % (Fs, currentTime, trial)), daqdata, delimiter=",")
# print("Data saved on %s" % currentTime)