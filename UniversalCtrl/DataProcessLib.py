import numpy as np
import re
import matplotlib.pyplot as plt
from scipy import signal

'''
Basic Setup
'''

'''' Figure format'''
plt.rc('font', size=10, family='Verdana')  # 'Tahoma', 'DejaVu Sans', 'Verdana'"
plt.rc('axes', edgecolor='k', linewidth=0.75, labelcolor='k')
plt.rc('axes.spines', **{'bottom': True, 'left': True, 'right': True, 'top': True})
plt.rcParams['xtick.top'] = True
plt.rcParams['xtick.bottom'] = True
plt.rcParams['ytick.left'] = True
plt.rcParams['ytick.right'] = True
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
plt.rcParams['errorbar.capsize'] = 4

''' Define Color Here '''
pltBlue = (32 / 255, 120 / 255, 180 / 255)
pltRed = (180 / 255, 32 / 255, 32 / 255)

''' Suppress warnings '''
import warnings
warnings.filterwarnings('ignore')


'''
General Functions
'''
def aPlot(figName='', figsize=(14, 6), is3D=False, dpi=72):
    ax = []

    fig1 = plt.figure(figsize=figsize, dpi=dpi)

    fig1.suptitle(figName, fontsize=16)
    if (is3D):
        ax = fig1.add_subplot(111, projection='3d')
    else:
        ax = fig1.add_subplot(111)

    return ax, fig1


def decodeData(fileName, decodeFormat, frontCode='', rearCode='', isString=False):
    segStr = re.findall(frontCode + decodeFormat + rearCode, fileName)
    if segStr:
        decoded = re.findall(decodeFormat, segStr[0])[0]
        if isString:
            return decoded
        return float(decoded)
    return None


def lowpassSmooth(datain, cutFreqRatio=0.05, order=8):
    b, a = signal.butter(order, 2 * cutFreqRatio, btype='low')
    dataout = signal.filtfilt(b, a, datain)
    return dataout


def movAvgSmooth(datain, winLen=100):
    dataout = np.convolve(datain, np.ones(winLen) / winLen, mode='same')
    return dataout


def onsetSegmentation(signal, segIntervalSamp, cutFreqRatio=0, thresholdRatio=0.25, disp=False):
    smoothSig = signal
    if (cutFreqRatio > 0):
        smoothSig = lowpassSmooth(abs(signal), cutFreqRatio=cutFreqRatio)
    else:
        smoothSig = movAvgSmooth(abs(signal), winLen=segIntervalSamp)

    smoothSig = smoothSig - smoothSig[0]

    samp = np.arange(len(signal))

    maxValue = np.sqrt(np.mean(np.square(smoothSig)))

    segPointInd = np.squeeze(np.argwhere(
        smoothSig > thresholdRatio * maxValue))  # Find value larger than 25% of peak as valid segment data point
    segGapInd = np.squeeze(np.argwhere(
        np.diff(segPointInd) > segIntervalSamp))  # Index of point where gap is longer than the predetermined interval

    startInd = np.array(segPointInd[segGapInd + 1])
    startInd = np.insert(startInd, 0, segPointInd[0])

    endInd = np.array(segPointInd[segGapInd])
    endInd = np.append(endInd, segPointInd[-1])

    if disp:
        ax0, _ = aPlot();
        ax0.plot(samp, signal, color='tab:grey');
        axb = ax0.twinx()
        axb.plot(samp, smoothSig, color='tab:blue')
        ax0.plot(startInd, np.zeros(startInd.shape), '*r')
        ax0.plot(endInd, np.zeros(endInd.shape), '*c')
        plt.show();

    return zip(startInd, endInd)

def sinSignal(sinFreq=250, sinDuration=6.0, Fs=48000, isUnipolar=False,
              completeCycle=True):  # Generate sinusoid signals with percentage range and zero start
    # Sinwave Frequency (Hz), Time duration (sec), Sampling Frequency (Hz), is Unipolar Signal or Bipolar, ensure completed cycle by adjusting time duration

    oneCycleDuration = 1.0 / sinFreq  # (secs) Time duration of one cycle

    adjustedDuration = np.ceil(sinDuration / oneCycleDuration) * oneCycleDuration

    t = np.arange(int(adjustedDuration * Fs)) / Fs

    if (isUnipolar):
        y = -0.5 * np.cos(2 * np.pi * sinFreq * t) + 0.5  # Unipolar: y starts from 0 and increases to 1.0 amplitude
    else:
        y = np.sin(
            2 * np.pi * sinFreq * t)  # Bipolar: y starts from 0 and increases to +1.0, then down to -1.0 amplitude

    y = np.insert(y, 0, 0.0)

    return y, t