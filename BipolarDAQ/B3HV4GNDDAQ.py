'''
Control the new bipolar HV board (electrode-array) via NI DAQ.
(Optional) Measurement via NI DAQ.
Author: Yitian Shao (ytshao@is.mpg.de)
Created on 2021.09.09
'''
import time
import numpy as np
import matplotlib.pyplot as plt
import PyDAQmx as nidaq
import sys

# MARCO
# F_CLK = 1000000.0 # DOI Clock frequency (Circuit control sampling frequency, Hz)
# F_PWM = 10000 # PWM frequency (Output waveform sampling frequency, Hz)

# Parameters
# MeasureTime = 2.0 # Measurement time, in seconds.
#
# PWMnum = int(MeasureTime * F_PWM)
# PWMpulseWidth = 1.0/F_PWM
# PWMpulseCLKnum = int(F_CLK/F_PWM) # Total sample number
# print("PWM frequency = %.1f Hz, PWM pulse width = %.1f us (%d CLK ticks)" % (F_PWM, 1e6*PWMpulseWidth, PWMpulseCLKnum))
#
# # Define PWM signals
# PWMdutyCycle = 0.5
# PWMout = np.zeros((PWMpulseCLKnum,), dtype=np.uint8)
# PWMout[:int(PWMdutyCycle*PWMpulseCLKnum)] = 1
#
# DIOout = np.tile(PWMout, PWMnum)
# DIOoutLen = DIOout.shape[0] # (= MeasureTime * F_PWM * int(F_CLK/F_PWM))
# print("DIOoutLen = %d" % DIOoutLen)

NodeIntvTime = 1

HV_Off = np.zeros((1,10), dtype=np.uint8) # Total number of channels = 10

'''-------------------------------------------------------------------------------'''
''' Functions'''

def zipNode(HVi, GNDi, chargeTime = 0.1, dischargeTime = 0.07):
    if (HVi <= 0) or (HVi > 3) or (GNDi <= 0):
        sys.exit("Invalid node index");

    chargeInd = (HVi-1)*2
    dischargeInd = chargeInd+1
    groundInd = GNDi+5

    for i in range(20):
        HV_Output = np.zeros((1, 10), dtype=np.uint8)
        HV_Output[0, [chargeInd, groundInd]] = 1  # Charge
        task1.WriteDigitalLines(1, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, HV_Output, None, None)
        time.sleep(chargeTime)

        task1.WriteDigitalLines(1, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, HV_Off, None, None)
        time.sleep(0.001)

        HV_Output = np.zeros((1, 10), dtype=np.uint8)
        HV_Output[0, [dischargeInd, groundInd]] = 1  # Discharge
        task1.WriteDigitalLines(1, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, HV_Output, None, None)
        time.sleep(dischargeTime)

        task1.WriteDigitalLines(1, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, HV_Off, None, None)
        time.sleep(0.001)

    task1.WriteDigitalLines(1, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, HV_Off, None, None)

'''-------------------------------------------------------------------------------'''
if __name__ == '__main__':
    with nidaq.Task() as task1:
        # DAQ configuration
        task1.CreateDOChan("Dev2/port0/line0:5,Dev2/port0/line10:13", None, nidaq.DAQmx_Val_ChanPerLine)

        # DAQ start
        task1.StartTask()
        print("Start sampling...")
        time0 = time.time()

        task1.WriteDigitalLines(1, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, HV_Off, None, None)
        time.sleep(1)

        for i in range(1):
            # Selective charging and discharging
            zipNode(HVi=1, GNDi=1)
            time.sleep(NodeIntvTime)
            zipNode(HVi=1, GNDi=2)
            time.sleep(NodeIntvTime)
            zipNode(HVi=1, GNDi=3)
            time.sleep(NodeIntvTime)
            zipNode(HVi=1, GNDi=4)
            time.sleep(NodeIntvTime)
            zipNode(HVi=2, GNDi=4)
            time.sleep(NodeIntvTime)
            zipNode(HVi=3, GNDi=4)
            time.sleep(NodeIntvTime)
            zipNode(HVi=3, GNDi=3)
            time.sleep(NodeIntvTime)
            zipNode(HVi=3, GNDi=2)
            time.sleep(NodeIntvTime)
            zipNode(HVi=3, GNDi=1)
            time.sleep(NodeIntvTime)
            zipNode(HVi=2, GNDi=1)
            time.sleep(NodeIntvTime)

        # Safety measure
        task1.WriteDigitalLines(1, False, 1.0, nidaq.DAQmx_Val_GroupByChannel, HV_Off, None, None)

        print("Total time = %.3f sec - Actual read sample number = %d" % (time.time() - time0, 0))

        task1.StopTask()
        print("Task completed!")
        task1.ClearTask()

'''-------------------------------------------------------------------------------'''
# fig1 = plt.figure(figsize = (16,6))
# fig1.suptitle(("Fs = %.0f Hz" % Fs), fontsize=12)
# ax = fig1.add_subplot(111)
# ax.set_xlabel('Samples')
#
# t = np.arange(actualReadNum.value)/Fs
#
# if(showPressure):
#     # Measured pressure
#     ax.plot(t, (daqdata[:,1]-calib[1])*calib[0], '-', color='tab:red')
#     ax.set_ylabel('Pressure (Bar)', color='tab:red')
#     ax.tick_params(axis='y', labelcolor='tab:red')
# else:
#     ax.plot(t, daqdata[:,1], '-', color='tab:orange')
#     ax.set_ylabel('Voltage (V)', color='tab:orange')
#     ax.tick_params(axis='y', labelcolor='tab:orange')
#
# # Reference (control) signal
# ax2 = ax.twinx()
# ax2.plot(t, daqdata[:,0], '--', color='tab:blue')
# ax2.set_ylabel('Control signal (V)', color='tab:blue')
# ax2.tick_params(axis='y', labelcolor='tab:blue')
#
# fig1.tight_layout()
# plt.show()
'''-------------------------------------------------------------------------------'''
# currentTime = time.strftime("%H-%M-%S", time.localtime())
#
# trial = 0
#
# np.savetxt(("Data_Fs%d_at%s_Pattern_t%02d.csv" % (Fs, currentTime, trial)), daqdata, delimiter=",")
# print("Data saved on %s" % currentTime)