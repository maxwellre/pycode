import serial
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import sounddevice as sd

from DataProcessLib import *

def triggerStartLaserVibrometerMeasurement():
    arduinoSerial.write(b't')

''' 
Audio Settings
'''
AudioFs = 44100  # (Hz) Must match the sampling frequency of the audio output

''' Initialize serial port '''
arduinoSerial = serial.Serial('com3', 115200)

''' Prepare drive signals '''
segmentTime = 1.5 # (secs) Time duration of each sinwave segment
segmentInterval = 1.0 # (secs) Time duration of the paused interval between every two sinwaves
amplitudeCap = 1.01 # Cap of the output amplitude to prevent excessively loud sound

octaveFrequencies = [5.010e+01, 6.310e+01, 7.940e+01,
                     1.000e+02, 1.259e+02, 1.585e+02, 1.995e+02, 2.512e+02, 3.162e+02, 3.981e+02,
                     5.012e+02, 6.310e+02, 7.943e+02] # 50Hz to 794Hz (exclude 1000Hz)
segmentGain = [0.0235, 0.012, 0.01370403, 0.03, 0.05052622, 0.06882767,
0.112,  0.11949221, 0.15370989, 0.19613606, 0.25,       0.31842742,
0.41088783]

''' Constructing audio signal to drive the voice coil actuator '''
pauseSegment = np.zeros(shape=(1, int(AudioFs * segmentInterval)))
outputSignal = pauseSegment
# outputSignal = np.empty(1)

# Insert the starting pulse at the beginning ------------------ begnining pulse
y, _ = sinSignal(sinFreq=100, sinDuration=0.1, Fs=AudioFs)
window = signal.windows.tukey(y.shape[0], alpha=1);
y = np.multiply(y, window)
outputSignal = np.append(outputSignal, y)
outputSignal = np.append(outputSignal, pauseSegment)

for n in range(2):
    for i in range(len(octaveFrequencies)):
        y, _ = sinSignal(sinFreq=octaveFrequencies[i], sinDuration=segmentTime, Fs=AudioFs)

        window = signal.windows.tukey(y.shape[0], alpha=0.2);
        y = np.multiply(y, window)
        y = y * segmentGain[i]

        outputSignal = np.append(outputSignal, y)
        outputSignal = np.append(outputSignal, pauseSegment)

# Limit output votlage (sound level) for device safety
outputSignal[outputSignal > amplitudeCap] = amplitudeCap
outputSignal[outputSignal < -amplitudeCap] = -amplitudeCap

print("Time duration of the entire output signal = %.1f secs" % (outputSignal.shape[0] / AudioFs))

_,ax = plt.subplots(2,1, dpi=300, figsize=(10,4))
t = np.arange(outputSignal.shape[0]) / AudioFs
ax[0].plot(t, outputSignal)
ax[0].set_xlabel("Time (secs)")
ax[0].set_ylabel("Amplitude")
ax[1].specgram(outputSignal, Fs=AudioFs, NFFT=65536)
ax[1].set_ylim([0, 1000])
ax[1].set_xlabel("Time (secs)")
ax[1].set_ylabel("Frequency (Hz)")
# plt.show()

sd.default.samplerate = AudioFs

''' Start '''
triggerStartLaserVibrometerMeasurement()
sd.play(outputSignal, blocking=True)

