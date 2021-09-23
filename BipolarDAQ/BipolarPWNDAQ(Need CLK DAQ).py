'''
Control the new bipolar HV board via NI DAQ.
(Optional) Measure Fluid Pressure via NI DAQ.
Author: Yitian Shao (ytshao@is.mpg.de)
Created on 2021.09.23 based on 'BipolarDAQ.py'
'''
import time
import numpy as np
import matplotlib.pyplot as plt
import PyDAQmx as nidaq
import sys

# MARCO
F_CLK = 10000 # DOI Clock frequency (Circuit control sampling frequency, Hz)
F_PWM = 1000 # PWM frequency (Output waveform sampling frequency, Hz)

PIN_CHARGE = 1
PIN_DISCHARGE = 0

# Parameters
AnalogInputNum = 2 # Number of analog input channels
DigitalOutputNum = 2 # Number of digital output channels

Fs = 1000.0 # Sampling frequency
MeasureTime = 6.0 # Measurement time, in seconds. (7)
showPressure = True # To display in raw unit (voltage) or converted to pressure unit

# Define control signals
HV_Off = np.zeros((1,DigitalOutputNum), dtype=np.uint8)

# PWM info
PWMpulseWidth = 1.0/F_PWM
PWMpulseCLKnum = int(F_CLK * PWMpulseWidth) # Total sample number per PWM segment
print("PWM frequency = %.1f Hz, PWM duration = %.1f us (%d CLK ticks)" % (F_PWM, 1e6*PWMpulseWidth, PWMpulseCLKnum))

'''-------------------------------------------------------------------------------'''
'''Functions'''
def Percent2PWM(direction, percentage = 0.0):
    PWMratio = percentage * 0.01
    if(PWMratio > 1.0):
        PWMratio = 1.0
    elif(PWMratio < 0.0):
        PWMratio = 0.0

    PWMout = np.zeros((PWMpulseCLKnum, 2), dtype=np.uint8)
    if(direction == 'charge'):
        PWMout[:int(PWMratio * PWMpulseCLKnum), PIN_CHARGE] = 1 # Charge cycle
    elif(direction == 'discharge'):
        PWMout[:int(PWMratio * PWMpulseCLKnum), PIN_DISCHARGE] = 1 # Discharge cycle
    else:
        sys.exit("Invalid direction is given to PWM. Indicate either 'charge' or 'discharge' for the direction")
    return PWMout

def RampPWM(direction, duration = 0.0):
    rampPWMnum = int(duration * F_PWM)
    y = np.linspace(0, 100, num=rampPWMnum)

    rampDIOout = np.array([Percent2PWM(direction, yi) for yi in y], dtype=np.uint8)
    rampDIOout = rampDIOout.reshape((-1, 2))
    return rampDIOout

'''-------------------------------------------------------------------------------'''
readLen = int(MeasureTime * Fs) # The number of samples, per channel, to read

calib = np.loadtxt('Calibration20210802.txt')
print("Calibration line a = %.16f, b = %.16f" % (calib[0],calib[1]))

daqdata = np.zeros((readLen*AnalogInputNum,), dtype=np.float64)

actualReadNum = nidaq.int32()

# Generate output signal
rampCharge = RampPWM('charge', 0.2)
flatCharge = np.zeros((int(1.0*F_CLK),DigitalOutputNum), dtype=np.uint8)
flatCharge[:,PIN_CHARGE] = 1

rampDischarge = RampPWM('discharge', 0.2)
flatDischarge = np.zeros((int(0.5*F_CLK),DigitalOutputNum), dtype=np.uint8)
flatDischarge[:,PIN_DISCHARGE] = 1

flatOff = np.zeros((int(1.0*F_CLK),DigitalOutputNum), dtype=np.uint8)

DIOout = flatOff.copy()

DIOout = np.append(DIOout, rampCharge, axis=0)
DIOout = np.append(DIOout, flatCharge, axis=0)
DIOout = np.append(DIOout, np.flipud(rampCharge), axis=0)

DIOout = np.append(DIOout, flatOff, axis=0)

DIOout = np.append(DIOout, rampDischarge, axis=0)
DIOout = np.append(DIOout, flatDischarge, axis=0)
DIOout = np.append(DIOout, np.flipud(rampDischarge), axis=0)

DIOout = np.append(DIOout, flatOff, axis=0)

# plt.figure(figsize = (16,6)); plt.plot(DIOout[:,0]); plt.plot(DIOout[:,1]+1.2); plt.show();

DIOoutLen = DIOout.shape[0]
print("DIOout Shape: ", DIOout.shape)
DIOout[-1,:] = 0 # Ensure all channels are turned off at the end

with nidaq.Task() as task0, nidaq.Task() as task1:
    # DAQ configuration
    task0.CreateAIVoltageChan("Dev1/ai2", None, nidaq.DAQmx_Val_Diff, -1, 4, nidaq.DAQmx_Val_Volts, None)
    task0.CreateAIVoltageChan("Dev1/ai3", None, nidaq.DAQmx_Val_Diff, -1, 9, nidaq.DAQmx_Val_Volts, None)
    task0.CfgSampClkTiming(None, Fs, nidaq.DAQmx_Val_Rising, nidaq.DAQmx_Val_FiniteSamps, readLen)

    task1.CreateDOChan("Dev1/port0/line0:1", None, nidaq.DAQmx_Val_ChanPerLine)
    #task1.CfgSampClkTiming(source="None", rate=F_CLK, activeEdge=nidaq.DAQmx_Val_Rising,
                           # sampleMode=nidaq.DAQmx_Val_FiniteSamps, sampsPerChan=DIOoutLen)

    task1.WriteDigitalLines(numSampsPerChan=DIOoutLen, autoStart=True,
                            timeout=nidaq.DAQmx_Val_WaitInfinitely, dataLayout=nidaq.DAQmx_Val_GroupByScanNumber,
                            writeArray=DIOout, reserved=None, sampsPerChanWritten=None)

    # DAQ start
    task0.StartTask()
    task1.StartTask()
    print("Start sampling...")
    time0 = time.time()

    time.sleep(MeasureTime)


    task0.ReadAnalogF64(numSampsPerChan = nidaq.DAQmx_Val_Auto, timeout = nidaq.DAQmx_Val_WaitInfinitely,
                        fillMode = nidaq.DAQmx_Val_GroupByChannel, readArray = daqdata, arraySizeInSamps = len(daqdata),
                        sampsPerChanRead = nidaq.byref(actualReadNum), reserved = None)


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

if(showPressure):
    # Measured pressure
    ax.plot(t, (daqdata[:,1]-calib[1])*calib[0], '-', color='tab:red')
    ax.set_ylabel('Pressure (Bar)', color='tab:red')
    ax.tick_params(axis='y', labelcolor='tab:red')
else:
    ax.plot(t, daqdata[:,1], '-', color='tab:orange')
    ax.set_ylabel('Voltage (V)', color='tab:orange')
    ax.tick_params(axis='y', labelcolor='tab:orange')

# Reference (control) signal
ax2 = ax.twinx()
ax2.plot(t, daqdata[:,0], '--', color='tab:blue')
ax2.set_ylabel('Control signal (V)', color='tab:blue')
ax2.tick_params(axis='y', labelcolor='tab:blue')

fig1.tight_layout()
plt.show()
'''-------------------------------------------------------------------------------'''
currentTime = time.strftime("%H-%M-%S", time.localtime())

trial = 0

# np.savetxt(("Data_Fs%d_at%s_Tube8mmU7kV_t%02d.csv" % (Fs, currentTime, trial)), daqdata, delimiter=",")
# print("Data saved on %s" % currentTime)