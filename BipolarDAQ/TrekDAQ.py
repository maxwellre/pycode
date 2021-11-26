'''
Control the Trek via NI DAQ.
Measure Fluid Pressure and Flow Rate via NI DAQ.
Author: Yitian Shao (ytshao@is.mpg.de)
Created on 2021.09.02 based on 'WearableCtrlDAQ.py'
'''
import time
import numpy as np
import matplotlib.pyplot as plt
import PyDAQmx as nidaq

'''-------------------------------------------------------------------------------'''
NIDev6003Num = 2
NIDev6212Num = 4

'''-------------------------------------------------------------------------------'''
AnalogInputNum = 3
AnalogOutputNum = 1
Fs = 1000.0 # Sampling frequency
MeasureTime = 8 # Measurement time, in seconds. (7)
showPressure = True # To display in raw unit (voltage) or converted to pressure unit

HV_Amplitude = 4.0

# Define control signals
HV_Off = np.zeros((1,AnalogOutputNum), dtype=np.float64)

'''-------------------------------------------------------------------------------'''
readLen = int(MeasureTime * Fs) # The number of samples, per channel, to read
intervalLen = int(1.0*Fs)
rampLen = int(0.5*Fs)
rampSig = np.arange(rampLen)/rampLen

HV_Out = np.zeros((readLen,AnalogOutputNum), dtype=np.float64)
'''-------------------------------------------------------------------------------'''
''' Construct the output signal for Trek here '''
HV_Out[intervalLen:intervalLen+rampLen,0] = rampSig*HV_Amplitude # Ramp up
HV_Out[intervalLen+rampLen:intervalLen*2+rampLen,0] = HV_Amplitude
HV_Out[intervalLen*2+rampLen:intervalLen*2+rampLen*2,0] = np.flipud(rampSig)*HV_Amplitude

HV_Out[intervalLen*4:intervalLen*6] = HV_Out[intervalLen:intervalLen*3] # Repeat one more time

'''-------------------------------------------------------------------------------'''
HV_Out[-1,:] = 0 # For safety measure, ensure zero output at the end

#plt.plot(HV_Out); plt.show()

calib = np.loadtxt('Calibration20210802.txt')
print("Calibration line a = %.16f, b = %.16f" % (calib[0],calib[1]))

daqdata = np.zeros((readLen*AnalogInputNum,), dtype=np.float64)

actualReadNum = nidaq.int32()
with nidaq.Task() as task0, nidaq.Task() as task1:
    # DAQ configuration
    task0.CreateAIVoltageChan("Dev%d/ai1" % NIDev6003Num,None, nidaq.DAQmx_Val_Diff, -1, 9, nidaq.DAQmx_Val_Volts,None)
    task0.CreateAIVoltageChan("Dev%d/ai2" % NIDev6003Num,None, nidaq.DAQmx_Val_Diff, -1, 9, nidaq.DAQmx_Val_Volts,None)
    task0.CreateAIVoltageChan("Dev%d/ai3" % NIDev6003Num,None, nidaq.DAQmx_Val_Diff, -1, 9, nidaq.DAQmx_Val_Volts,None)
    task0.CfgSampClkTiming(None, Fs, nidaq.DAQmx_Val_Rising, nidaq.DAQmx_Val_FiniteSamps, readLen)

    #task1.CreateDOChan("Dev%d/port0/line0:2" % NIDev6212Num, None, nidaq.DAQmx_Val_ChanPerLine)
    task1.CreateAOVoltageChan("Dev%d/ao0" % NIDev6212Num, None, 0, 6, nidaq.DAQmx_Val_Volts, None)

    # DAQ start
    task1.StartTask()
    task0.StartTask()
    print("Start sampling...")
    time0 = time.time()

    # task1.WriteDigitalLines(1, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, HV_Off, None, None)
    task1.WriteAnalogF64(AnalogOutputNum, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, HV_Off, None, None)
    time.sleep(1)

    # Start charging and discharging the pump
    task1.WriteAnalogF64(readLen, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, HV_Out, None, None)

    task0.ReadAnalogF64(numSampsPerChan = nidaq.DAQmx_Val_Auto, timeout = nidaq.DAQmx_Val_WaitInfinitely,
                        fillMode = nidaq.DAQmx_Val_GroupByChannel, readArray = daqdata, arraySizeInSamps = len(daqdata),
                        sampsPerChanRead = nidaq.byref(actualReadNum), reserved = None)

    # Safety measure
    task1.WriteAnalogF64(AnalogOutputNum, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, HV_Off, None, None)

    print("Total time = %.3f sec - Actual read sample number = %d" % (time.time() - time0, actualReadNum.value))

    task0.StopTask()
    task1.StopTask()
    print("Task completed!")
    task0.ClearTask()
    task1.ClearTask()

daqdata = daqdata.reshape(AnalogInputNum,-1).T

'''-------------------------------------------------------------------------------'''
fig1 = plt.figure(figsize = (16,6))
fig1.suptitle(("Fs = %.0f Hz" % Fs), fontsize=12)
ax = fig1.add_subplot(111)
ax.set_xlabel('Samples')

t = np.arange(actualReadNum.value)/Fs

# Measured pressure
ax.plot(t, (daqdata[:,2]-calib[1])*calib[0], '-', color='tab:red')
ax.set_ylabel('Pressure (Bar)', color='tab:red')
ax.tick_params(axis='y', labelcolor='tab:red')

# Reference (control) signal and flow rate (Voltage)
ax2 = ax.twinx()
ax2.plot(t, daqdata[:,0], '--', color='tab:blue')
ax2.plot(t, daqdata[:,1], '-', color='tab:brown')
ax2.set_ylabel('Voltage (V)', color='tab:blue')
ax2.tick_params(axis='y', labelcolor='tab:blue')

fig1.tight_layout()
plt.show()
'''-------------------------------------------------------------------------------'''
currentTime = time.strftime("%H-%M-%S", time.localtime())

trial = 0

np.savetxt(("Data_Fs%d_at%s_FR3U6900V_t%02d.csv" % (Fs, currentTime, trial)), daqdata, delimiter=",")
print("Data saved on %s" % currentTime)