'''
General Functions and Classes
'''

from os import walk
import os.path as ospa
import numpy as np
import re
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from matplotlib.colors import ListedColormap
from matplotlib.patches import Arc
import pandas as pd
from scipy import signal
from scipy.interpolate import griddata
import seaborn as sns

plt.rc('font', size=10, family='Verdana') # 'Tahoma', 'DejaVu Sans', 'Verdana'"
plt.rc('axes', edgecolor='0.5', linewidth=0.75)
plt.rc('axes.spines', **{'bottom':True, 'left':True, 'right':False, 'top':False})
plt.rcParams.update({'errorbar.capsize': 4})
plt.rcParams['savefig.dpi'] = 300

plt.rcParams['xtick.top'] = True
plt.rcParams['xtick.bottom'] = True
plt.rcParams['ytick.left'] = True
plt.rcParams['ytick.right'] = True
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
plt.rcParams['errorbar.capsize'] = 4

figSize_inch = (3.2, 2.4)

plotLinewidth = 0.75
plotMarkersize = 0.8
markeredgewidth = 0
plotMarker = '.-'

''' Define Color Here '''
pltBlue = (32/255,120/255,180/255)
pltGreen = (32/255,180/255,120/255)
pltRed = (220/255,95/255,87/255)

pltLightGrey = (240/255,240/255,240/255)


biotacFs = {
  "Pac": 2200,
  "Pdc": 100,
} # The sampling frequency of BioTac depends on data type. 

biotacUnit = {
  "Pac": 0.00037,
  "Pdc": 0.0365,
} # The unit conversion of BioTac depends on data type. Pac: 0.00037kPa/bit, Pdc:  0.0365kPa/bit

def customizeCMap(cRange=[100,100],negaColor="GnBu_r",posiColor="OrRd"):
    cmap1 = cm.get_cmap(negaColor, 1000)
    cmap2 = cm.get_cmap(posiColor, 1000)
    newcmp1 = cmap1(np.linspace(0, 1, cRange[0]))
    newcmp2 = cmap2(np.linspace(0, 1, cRange[1]))
    cmap = ListedColormap(np.concatenate((newcmp1,newcmp2), axis=0))
    return cmap

def aPlot(figName='', is3D = False, dpi=72):
    ax = []
    
    fig1 = plt.figure(figsize = (12,6), dpi=dpi)
    
    fig1.suptitle(figName, fontsize=16)
    if(is3D):
        ax = fig1.add_subplot(111, projection='3d')
    else:
        ax = fig1.add_subplot(111)
        
    return ax, fig1

def onsetSegmentation(datain, segIntervalSamp, cutFreqRatio=0, disp=False, threshold=0.6):
    if(cutFreqRatio > 0):
        smoothSig = lowpassSmooth(abs(datain), cutFreqRatio=cutFreqRatio)
    
    smoothSig = smoothSig - smoothSig[0]
    
    samp = np.arange(len(datain))
    
    maxValue = np.sqrt(np.mean(np.square(smoothSig)))
    
    segPointInd = np.squeeze(np.argwhere(smoothSig > threshold * maxValue)) # Find value larger than 25% of peak as valid segment data point
    segGapInd = np.squeeze(np.argwhere(np.diff(segPointInd) > segIntervalSamp))# Index of point where gap is longer than the predetermined interval

    startInd = np.array(segPointInd[segGapInd+1])
    startInd = np.insert(startInd, 0, segPointInd[0])

    endInd = np.array(segPointInd[segGapInd])
    endInd = np.append(endInd, segPointInd[-1])
    
    if disp:
        ax0, _ = aPlot(); 
        ax0.plot(samp, datain, color='tab:grey'); 
        axb = ax0.twinx() 
        axb.plot(samp, smoothSig, color='tab:blue')
        axb.plot(segPointInd, np.ones(segPointInd.shape)*threshold *maxValue, '.', color='tab:orange')
        axb.plot(startInd, np.ones(startInd.shape)*maxValue, '*r')
        axb.plot(endInd, np.ones(endInd.shape)*maxValue, '*c')
        
    return startInd, endInd

''' Filtering '''
def movAvgSmooth(datain, winLen=100):
    dataout = np.convolve(datain, np.ones(winLen)/winLen, mode='same')
    return dataout

def lowpassSmooth(datain, cutFreqRatio = 0.05, order = 8, axis=0):
    if (cutFreqRatio > 0) and (cutFreqRatio < 0.5):
        b, a = signal.butter(order, 2 * cutFreqRatio, btype='low')
        dataout = signal.filtfilt(b, a, datain, axis=axis)
        return dataout
    else:
        print("Incorrect cutFreqRatio outside of (0, 0.5)")

def highpassFilter(datain, cutFreqRatio = 0.05, order = 8):
    b, a = signal.butter(order, 2 * cutFreqRatio, btype='highpass')
    dataout = signal.filtfilt(b, a, datain, axis=0)
    return dataout

''' Info and Display '''
def unifyAxesColor(ax, color='k'):
    ax.spines['top'].set_color(color)
    ax.spines['left'].set_color(color)
    ax.spines['right'].set_color(color)
    ax.spines['bottom'].set_color(color)
    ax.tick_params('both', colors='k')

def decodeActuatorInfo(rootName):
    actLabel = re.findall('Act\d+mm\d+\.\d+mL', rootName)
    if actLabel:
        actLabel = actLabel[0]
    return actLabel

def decodeDataType(fileName):
    dataType = re.findall('Pdc|Pac', fileName)
    if dataType:
        dataType = dataType[0]
    return dataType

def decodeData(fileName, numFormat, frontCode='', rearCode='', isString=False):
    segStr = re.findall(frontCode+numFormat+rearCode, fileName)
    if segStr:
        if isString:
            return segStr[0]
        else:
            numData = float(re.findall(numFormat, segStr[0])[0])
    else:
        numData = None
    return numData

def yyAxisPlot(x0, y0, x1, y1, xText=None, y0Text=None, y1Text=None):
    ax0, fig0 = aPlot(); 
    ax0.set_xlabel(xText)
    ax0.plot(x0, y0, color='tab:orange'); 
    ax0.set_ylabel(y0Text, color='tab:orange')
    ax0.tick_params(axis='y', labelcolor='tab:orange')

    ax1 = ax0.twinx()
    ax1.plot(x1, y1, color='tab:blue');
    ax1.set_ylabel(y1Text, color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    fig0.tight_layout() 

def sample2Time(ax, Fs): # Covert the xticks of current plot from samples to time using Fs
    locs, _ = plt.xticks()
    plt.xticks(locs, locs/Fs)
    ax.set_xlim(0, locs[-1])
    ax.set_xlabel('Time (secs)')

''' BioTac Finger '''
def loadRawBioTac(measureDataPath, fileName, root=None, fileName2=None):
    if fileName2 is None:
        nameLabel = decodeData(fileName, ".*.btd", isString=True)
        fileName2 = nameLabel + "_Pac.csv"
        
    ''' Read in data '''
    if root is None:
        data = np.genfromtxt(ospa.join(measureDataPath, fileName), delimiter=',')
        dataPAC = np.genfromtxt(ospa.join(measureDataPath, fileName2), delimiter=',')
    else:
        data = np.genfromtxt(ospa.join(measureDataPath, root, fileName), delimiter=',')
        dataPAC = np.genfromtxt(ospa.join(measureDataPath, root, fileName2), delimiter=',')

    t = data[:,0]
    pDC = (data[:,1] - data[0,1]) * 0.0365 # DC Pressure = (Pdc - Offset) 0.0365 kPa/bit
    tAC = data[:,2]
    tDC = data[:,3]
    eData = data[:,4:]# (No Unit)
    eData = eData - np.mean(eData[0:20,:], axis=0) # Subtract DC (the first 0.2 sec signal)
    
    t2 = dataPAC[:,0]
    pAC = (dataPAC[:,1] - dataPAC[0,1]) * 0.00037   # AC Pressure = (Pdc - Offset) 0.37 Pa/bit = (Pdc - Offset) 0.00037 kPa/bit

    outData = {}
    outData['pDC'] = pDC
    outData['tAC'] = tAC
    outData['tDC'] = tDC
    outData['eData'] = eData
    outData['pAC'] = pAC
    
#     outData['t'] = t
#     outData['t2'] = t2
    
    outData['t'] = np.arange(len(pDC))/biotacFs["Pdc"]
    outData['t2'] = np.arange(len(pAC))/biotacFs["Pac"]
    
    return outData

def examData(data, tInstance=1.5, tRange=[0, 30], dispTem=False):
    ''' Exam data '''
    ti = np.argmax(data['t']>=tInstance)
    print("Selected time instance at %.2f sec, index = %d" % (tInstance, ti))
    
    if dispTem: # Display temperature readings in addition to the dc pressure reading
        _,(ax1, ax2, ax3)  = plt.subplots(3, 1, dpi=300, figsize=(3,2))
        ax2.plot(data['t'], data['tAC'])
        ax2.set_xlim(tRange)
        ax3.plot(data['t'], data['tDC'])
        ax3.set_xlim(tRange)
    else:
        _,ax1 = plt.subplots(dpi=300, figsize=(3,1))
        
    ax1.plot(data['t'], data['pDC'])
    ax1.plot(data['t'][[ti, ti]], [0, 3], 'k')
    ax1.set_xlim(tRange)
    
    _, ax = plt.subplots(dpi=300, figsize=(3,2))
#     eData = lowpassSmooth(data['eData'], cutFreqRatio = 0.2, order = 8) # Lowpass filter electrode data 
    eData = data['eData']
    for i in range(19):
        ax.plot(data['t'], eData[:,i])
    ax.set_xlim(tRange)
    ax.plot(data['t'][[ti, ti]], [-0.1, 0.1], 'k')

# ------------------------------------------------------------------ Data Segmentation    
def segmentData(data, minInterval=100, threshold=0.6, disp=False, title="", validStartInd=0):
    startInd, endInd = onsetSegmentation(data['pDC'][validStartInd:], minInterval, cutFreqRatio=0.1, disp=disp, threshold=threshold)
    
    startInd = startInd + validStartInd
    endInd = endInd + validStartInd
    
    if disp:
        fig_local, ax_local = plt.subplots(dpi=300, figsize=(3,2))
        fig_local.suptitle(title)
        for i0,i1 in zip(startInd, endInd):
            t = data['t'][i0:i1]
            t = t-t[0]
            ax_local.plot(t, data['pDC'][i0:i1])
    
    return startInd, endInd
    
# ------------------------------------------------------------------ Data Stats
def getDuration(dataIn, peakInd, lowerThreshold):
    leftInd = peakInd
    while(leftInd > 0 and dataIn[leftInd] > lowerThreshold):
        leftInd = leftInd-1
        
    dataLen = len(dataIn)
    rightInd = peakInd
    while(rightInd < dataLen-1 and dataIn[rightInd] > lowerThreshold):
        rightInd = rightInd+1
        
    return leftInd, rightInd

def dataStats(data, startInd, endInd, Fs=100):
    peakDC = []
    triseDC = []
    tDuration = []
    
#     ax1,_ = aPlot()

    for i0,i1 in zip(startInd, endInd):
        aSignal = data['pDC'][i0:i1]

#         smData = lowpassSmooth(aSignal)
        smData = aSignal
        smData = signal.detrend(smData, type='linear')

        maxValue = np.max(smData)
        onsetInd = np.argwhere(smData > 0.10 * maxValue)[0] # When signal reach 10% of its peak (onset)
        PTopInd = np.argwhere(smData > 0.90 * maxValue)[0] # When signal reach 90% of its peak
        
        ''' To Find the steady state pressure '''
#         offInd = np.argwhere(smData[50:] > 0.20 * maxValue)[-1][0]+50
#         if(offInd == None or offInd < PTopInd):
#             offInd = smData.shape[0]

#         leftInd = PTopInd
#         RightInd = offInd
#         while(leftInd < RightInd and abs(smData[leftInd] - smData[RightInd]) > (0.05*maxValue)):
#             leftInd = leftInd+1
#             RightInd = RightInd-1
        
        rawPeakValue = np.max(aSignal)

        riseTime = (PTopInd - onsetInd)/Fs
        
        leftInd, rightInd = getDuration(data['pDC'], np.argmax(aSignal)+i0, rawPeakValue*0.2)  
        tDur = (rightInd - leftInd) / Fs
        
        peakDC.append(rawPeakValue)
        triseDC.append(riseTime)
        tDuration.append(tDur)
       
#         ax1.plot(data['t'][i0:i1], aSignal, 'k')        #         ax1.plot(aSignal[:,0], smData, 'g')
#         ax1.plot([data['t'][leftInd], data['t'][leftInd]], [0, rawPeakValue], '-r')
#         ax1.plot([data['t'][rightInd], data['t'][rightInd]], [0, rawPeakValue], '-r')
#         ax1.set_xlabel("peak=%.1fkPa - TDuration=%.3fs - riseT=%.3fs" % (rawPeakValue,tDur, riseTime))

    peakDC = np.array(peakDC)
    triseDC = np.array(triseDC)
    tDuration = np.array(tDuration)
    return peakDC, triseDC, tDuration

def nearestTimeFrameInd(t1_i, t2):
    ind = np.argmin(abs(t2 - t1_i))
    return ind

def plotPressureDC(tind, btData, yMax=0, ax=None, ylabelStr="Pressure (kPa)"):
    if ax is None:
        fig1, ax = plt.subplots(dpi=300, figsize=(3,1))
    ax.plot(btData['t'], btData['pDC'], plotMarker, linewidth=plotLinewidth, markersize=plotMarkersize, markeredgewidth=markeredgewidth, zorder=10)
    
    if yMax <= 0:
        yMax = np.amax(btData['pDC'][tind[0]:tind[-1]]) + 0.1

    for i in range(len(tind)):
        ax.plot(btData['t'][[tind[i], tind[i]]], [0, yMax], 'tab:grey', lw=0.5, zorder=0)

    ax.set_xlim([btData['t'][tind[0]]-0.1, btData['t'][tind[-1]]+0.1]);
    ax.set_ylim([-0.1, max(yMax,5)])
    unifyAxesColor(ax, color='k')

    ax.set_xlabel("Time (secs)")
    ax.set_ylabel("pDC (kPa)"); #ax.set_ylabel(ylabelStr);
    
    if ax is None:
        return fig1, ax
    return None, None
   
def plotPressureAC(tind, btData, ax=None):
    tind2 = []
    for ti in tind:
        tind2.append(nearestTimeFrameInd(btData['t'][ti], btData['t2']))
    
    ''' Preprocess: flip and filtering '''
    pACFlip = -btData['pAC'];
    
    pACFlipFilted = highpassFilter(pACFlip, cutFreqRatio = 0.01, order = 8)
    
    ''' Plot Signal waveform '''  
    if ax is None:
        fig1, ax = plt.subplots(dpi=300, figsize=(3,1))
#     ax.plot(btData['t2'], pACFlip, zorder=10)
    ax.plot(btData['t2'], pACFlipFilted, plotMarker, linewidth=plotLinewidth, markersize=plotMarkersize, markeredgewidth=markeredgewidth, zorder=10) # Highpass filtered
    
    yMin = np.amin(pACFlip[tind2[0]:tind2[-1]]) - 0.1
    yMax = np.amax(pACFlip[tind2[0]:tind2[-1]]) + 0.1
    
    for i in range(len(tind2)):
        ax.plot(btData['t2'][[tind2[i], tind2[i]]], [yMin, yMax], 'tab:grey', lw=0.5, zorder=0)
        
    ax.set_xlim([btData['t2'][tind2[0]]-0.1, btData['t2'][tind2[-1]]+0.1]);
    ax.set_ylim([yMin, yMax])
    unifyAxesColor(ax, color='k')

    ax.set_xlabel("Time (secs)")
    ax.set_ylabel("pAC (kPa)"); #ax.set_ylabel("Pressure (kPa)");
    
    if ax is None:
        return fig1, ax
    return None, None

# def plotPressureDCPlusAC(tind, btData, ax=None):
#     tind2 = []
#     for ti in tind:
#         tind2.append(nearestTimeFrameInd(btData['t'][ti], btData['t2']))
    
#     ''' Upsample pDA signal based on pAC sampling rate '''
#     pDCUpSample, t2 = signal.resample(btData['pDC'], len(btData['pAC']), t=btData['t'])

#     pDCPlusAC = pDCUpSample+btData['pAC']
#     ''' Plot Signal waveform '''  
#     if ax is None:
#         fig1, ax = plt.subplots(dpi=300, figsize=(3,1))
#     ax.plot(btData['t2'], pDCPlusAC, zorder=10)
    
#     yMin = np.amin(pDCPlusAC[tind2[0]:tind2[-1]]) - 0.1
#     yMax = np.amax(pDCPlusAC[tind2[0]:tind2[-1]]) + 0.1
    
#     for i in range(len(tind2)):
#         ax.plot(btData['t2'][[tind2[i], tind2[i]]], [yMin, yMax], 'tab:grey', lw=0.5, zorder=0)
        
#     ax.set_xlim([btData['t2'][tind2[0]]-0.1, btData['t2'][tind2[-1]]+0.1]);
#     ax.set_ylim([yMin, yMax])
#     unifyAxesColor(ax, color='k')

#     ax.set_xlabel("Time (secs)")
#     ax.set_ylabel("pDC+pAC (kPa)"); #ax.set_ylabel("Pressure (kPa)");
    
#     if ax is None:
#         return fig1, ax
#     return None, None

''' -----------------------------------------------------------------------------------------------Plot Raw BioTac Data '''
def plotElectrodeRawData(tind, btData, yMax=0, unifyRange="Symmetric"): 
#     cmap=cm.get_cmap("viridis", 100)
#     cmap=cm.get_cmap("vlag", 100)
#     cmap=cm.get_cmap("coolwarm", 100)
#     cmap=cm.get_cmap("Spectral"+"_r", 100)
#     cmap=cm.get_cmap("seismic", 100)
#     cmap=cm.get_cmap("PuOr"+"_r", 100)
    cmap=cm.get_cmap("bwr", 100)
    
    btMap = BiotacMap()
    btMap.initializeDistanceMap()
    
    frameNum = len(tind)
    
    ''' Remove DC of electrode measurement '''
    eData = btData['eData']
#     eData = eData - np.mean(eData[tind[0]:tind[0]+5,:], axis=0)
    eData = eData - eData[tind[0],:]

#     eData = lowpassSmooth(eData, cutFreqRatio = 0.2, order = 8) # Lowpass filter electrode data 
    
    eDataFrames = eData[tind,:]
    rawRange = [np.amin(eDataFrames), np.amax(eDataFrames)]
    print("Raw data range = [%.2f, %.2f]" % (rawRange[0], rawRange[1]))
    
    symmetricRange = [-max(abs(rawRange[0]),abs(rawRange[1])), max(abs(rawRange[0]),abs(rawRange[1]))]
    
    ''' Raw impedance values of 19 electrodes '''
    fig1, axes = plt.subplots(1, frameNum, dpi=300, figsize=figSize_inch)
    fig1cbar, cbarax = plt.subplots(dpi=300, figsize=(1,1))

    if unifyRange=="Raw":
        cmap = customizeCMap([int(abs(rawRange[0])),int(abs(rawRange[1]))],negaColor="Blues_r",posiColor="Oranges")
        scplt = btMap.dispRawElectrodeValue(axes, eData[tind,:], s=5, cmap=cmap, unifyRange=rawRange)
    elif unifyRange=="Symmetric":
        maxRange = int(max(abs(rawRange[0]),abs(rawRange[1])))
        cmap = customizeCMap([maxRange,maxRange],negaColor="Blues_r",posiColor="Oranges")
        scplt = btMap.dispRawElectrodeValue(axes, eData[tind,:], s=5, cmap=cmap, unifyRange=symmetricRange)
    elif type(unifyRange) != str:
        scplt = btMap.dispRawElectrodeValue(axes, eData[tind,:], s=5, cmap=cmap, unifyRange=unifyRange)

    cbar = plt.colorbar(scplt, ax=cbarax, fraction=0.05, pad=0.25, aspect=8)
    cbar.outline.set_visible(False)
    cbar.ax.get_yaxis().labelpad = 15
    
    ''' Plot Signal waveform '''  
    fig2, ax2 = plt.subplots(2, 1, dpi=300, figsize=(figSize_inch[0], figSize_inch[1]))
    plotPressureDC(tind, btData, yMax=yMax, ax=ax2[0], ylabelStr="");
    plotPressureAC(tind, btData, ax=ax2[1]);
#     plotPressureDCPlusAC(tind, btData, ax=ax2[2])
    
    return fig1, fig1cbar, fig2, ax2
    
    
def examElectrodePattern(tind, btData, oneRange=False): 
    btMap = BiotacMap()
    btMap.initializeDistanceMap()
    
    ''' Remove DC of electrode measurement '''
    eData = btData['eData']
    eData = eData - np.mean(eData[tind[0]:tind[0]+5,:], axis=0)
    
#     eData = lowpassSmooth(eData, cutFreqRatio = 0.2, order = 8) # Lowpass filter electrode data 
    
    if oneRange:
        rawRange = [np.amin(eData), np.amax(eData)]
    else:
        rawRange = [np.amin(eData[tind,:]), np.amax(eData[tind,:])]
    print("Raw data range = [%.2f, %.2f]" % (rawRange[0], rawRange[1]))
    
    frameNum = len(tind)
    rowNum = int(np.ceil(frameNum/10))
    
    ''' Raw impedance values of 19 electrodes '''
    for row_i in range(rowNum):
        tind_start = row_i * 10
        
        _, axes = plt.subplots(1, 10, dpi=300, figsize=figSize_inch)
        cmap = customizeCMap([int(abs(rawRange[0])),int(abs(rawRange[1]))],negaColor="Blues_r",posiColor="Oranges")
        scplt = btMap.dispRawElectrodeValue(axes, eData[tind[tind_start:tind_start+10],:], s=5, cmap=cmap, unifyRange=rawRange)
        axes[0].set_title("Index %d - %d" % (tind[tind_start],tind[:tind_start+10][-1]), fontdict={'fontsize':2})
        plt.show()
    
    
def generateMapResult(tind, btData, yMax=5, unifyRange=None, alpha=4000, reverseColorbar=False):    
# cmap=cm.get_cmap('inferno', 100) # cmap=cm.get_cmap('binary', 100) # cmap=cm.get_cmap('RdYlBu', 100)
    colorr = ""
    if reverseColorbar:
        colorr = "_r"
    cmap=cm.get_cmap("viridis"+colorr, 100)

    btMap = BiotacMap()
    btMap.initializeDistanceMap(alpha=alpha)

    frameNum = len(tind)
    
    ''' Raw impedance values of 19 electrodes '''
    fig3, axes = plt.subplots(1, frameNum, dpi=300, figsize=figSize_inch)
    fig3cbar, cbarax = plt.subplots(dpi=300, figsize=(0.6,0.4))
    scplt = btMap.dispRawElectrodeValue(axes, eData[tind,:], s=8, cmap=cmap, unifyRange=rawRange)
    
    cbar = plt.colorbar(scplt, ax=cbarax, fraction=0.05, pad=0.25, aspect=8)
    cbar.outline.set_visible(False)
    cbar.ax.get_yaxis().labelpad = 15
    
    ''' Remove DC of electrode measurement '''
    eData = btData['eData']
#     eData = eData - np.mean(eData[tind[0]:tind[1],:], axis=0) #     eData = eData - np.mean(eData[:20,:], axis=0) 

    eDataIncluded = eData[tind,:]
    rawRange = [np.amin(eDataIncluded), np.amax(eDataIncluded)]
    print("rawRange = [%.2f, %.2f]" % (rawRange[0], rawRange[1]))
    
    ''' map from Cubic Interpolation '''
    fig0, axes = plt.subplots(1, frameNum, dpi=300, figsize=figSize_inch)
    fig0cbar, cbarax = plt.subplots(dpi=300, figsize=(0.6,0.4))
    for i in range(frameNum):
        scplt = btMap.mapFromCubicInterp(axes[i], eData[tind[i],:], cmap=cmap, unifyRange=rawRange)
        axes[i].set_title("%.2fs" % btData['t'][tind[i]], size=3)
       
    cbar = plt.colorbar(scplt, ax=cbarax, fraction=0.05, pad=0.25, aspect=8)
    cbar.outline.set_visible(False)
    cbar.ax.get_yaxis().labelpad = 15
    cbarax.axis('off')

    ''' Smooth interpolation of impedance map '''
    mapValues = []
    mapMins = []
    mapMaxs = []
    for i in range(frameNum):
        mapValue = btMap.constructMap(eData[tind[i],:])
        mapValues.append(mapValue)
        mapMins.append(np.amin(mapValue))
        mapMaxs.append(np.amax(mapValue))
    
    if unifyRange is None:
        unifyRange = [min(mapMins), max(mapMaxs)]

    fig1, ax0 = plt.subplots(dpi=300, figsize=(3,1))
    fig1cbar, cbarax = plt.subplots(dpi=300, figsize=(0.6,0.4))
    btMap.dispMaps(ax0, mapValues, xShift=300, cbarax=cbarax, cmap=cmap, unifyRange=unifyRange, s=0.001, dispOutline=False)
    cbarax.axis('off')

    if yMax < 0:
        yMax = np.max(btData['pDC'])
    
    ''' Plot Signal waveform '''  
    fig2, ax1 = plt.subplots(dpi=300, figsize=(3,1))
    ax1.plot(btData['t'], btData['pDC'])

    for i in range(frameNum):
        ax1.plot(btData['t'][[tind[i], tind[i]]], [0, yMax], 'tab:grey', lw=0.5)

    ax1.set_xlim([btData['t'][tind[0]]-0.1, btData['t'][tind[-1]]+0.1]);
    ax1.set_ylim([-0.1, yMax])
    unifyAxesColor(ax1, color='k')

    ax1.set_xlabel("Time (secs)")
    ax1.set_ylabel("Pressure (kPa)");
    
    return fig1, fig1cbar, fig2, ax1

def cutRepeatTrial(datain, Fs, expectedTrialNum, disp=False):
    rawData = datain[:,1]
    smData = lowpassSmooth(rawData)
    
    smData = signal.detrend(smData, type='linear')
    
    samp = np.arange(len(rawData))
    
    maxRawValue = np.max(smData)
    
    ''' Fine tunning needed for individual measurement session'''
    segPointInd = np.squeeze(np.argwhere(smData[10:] > 0.25 * maxRawValue))+50 # Find value larger than 25% of peak as valid segment data point
    segGapInd = np.squeeze(np.argwhere(np.diff(segPointInd) > 1))# Index of point where large gap occurs (end and start of a seg)
    cutInd = (0.5 * (segPointInd[segGapInd] + segPointInd[segGapInd+1])).astype(int) # Cut in the middle of a end and a start point
    
    if not isinstance(cutInd,np.ndarray) or len(cutInd) != expectedTrialNum-1:
        if disp:
            ax0, _ = aPlot(); 
            ax0.plot(samp, rawData, color='k'); 
            plt.show();       
        return []
    
    avgSegLen = np.mean(np.diff(cutInd))
    cutInd = np.insert(cutInd, 0, max(cutInd[0]-avgSegLen, 0))
    
    if disp:
        ax0, _ = aPlot(); 
        ax0.plot(samp, rawData, color='k'); 
#         ax0.plot(samp, smData, color='tab:blue');
        ax0.plot(cutInd, np.zeros(cutInd.shape), '*r')
        plt.show();
    
    return cutInd

def selectConditions(dFrame, condiList):
    indList = []
    for aCondi in condiList:
        indList.extend(dFrame[dFrame['Label'] == aCondi].index)

    return indList

def getDataArray(dFrame, indList, colName, toFlat=False):
    compValue = (dFrame.loc[indList,colName]).to_numpy()  
    
    if toFlat:
        flatValue = []
        for aRow in compValue:
            flatValue.extend(aRow)
        flatValue = np.array(flatValue)
        return flatValue
            
    return compValue
    
def getMeanSTD(compValue): # Compute errorbar of data mixing all conditions (rows of input array)
    if len(compValue) == 0:
        return None, None
        
    compValue = np.array(compValue)
    
    meanValue = np.mean(compValue)
    stdValue = np.std(compValue)
    
    return meanValue, stdValue
    


'''
Class
'''

class BiotacMap:
    ''' Class of biotac mapping for impedance data visualization '''
    def __init__(self):
        ''' Biotac Electrode 1-19 layout '''
        eXY = [[278, 523], [226, 588], [226, 639], [278, 666], [226, 704], [278, 757],
               [174, 458], [213, 497], [135, 497], [174, 536], [69, 523], [122, 588],
               [122, 639], [69, 665], [122, 704], [69, 756], [174, 587], [174, 691], [174, 756]]
        eXY = np.array(eXY)
        eXY[:,1] = -eXY[:,1]+800

        self.eXY = eXY
        self.eNum = eXY.shape[0]
        
        extent = (50,300,0,400)
        self.extent = extent
        
        self.grid_x, self.grid_y = np.mgrid[extent[0]:extent[1], extent[2]:extent[3]]
        
        ''' Finger-shape mapping: Set electrode 10 eXY[9,:] as the arc center of the shape '''
        self.centerX = self.eXY[9,0]
        self.centerY = self.eXY[9,1]
        self.bottomY = self.eXY[18,1] - 20
        self.cRadius = 125

        ''' Biotac finger shape '''
        grid_x, grid_y = np.mgrid[(self.centerX-self.cRadius):(self.centerX+self.cRadius), 
                                  self.bottomY:(self.centerY+self.cRadius)]
        gridXY = np.vstack((grid_x.flatten(),grid_y.flatten())).T

        ind = (gridXY[:,1] <= self.centerY) | ((gridXY[:,1] > self.centerY) & 
              ((np.square(gridXY[:,0]-self.centerX) + np.square(gridXY[:,1]-self.centerY)) < (self.cRadius*self.cRadius)))
        self.gridXY = gridXY[ind,:]
        
    ''' Compute distance map '''    
    def initializeDistanceMap(self, alpha=100): # Alpha determine the smoothness of the interpolation: Phi = 1/(dist + Alpha)
        distMap = []
        for i in range(self.eNum):
            aDistance = np.sqrt(np.square(self.gridXY[:,0]-self.eXY[i,0]) + np.square(self.gridXY[:,1]-self.eXY[i,1]))
            distMap.append(aDistance)
            
        self.distMap = np.array(distMap)

        self.Phi = 1 / (np.square(self.distMap) + alpha)
        
        self.SumPhi = np.sum(self.Phi, axis=0)
    
    def dispElectrode(self, ax, s=100, fontsize=5, fontcolor='w'):
        for ei in range(self.eNum):
            ax.scatter(self.eXY[ei,0], self.eXY[ei,1], s=s, c='darkslategrey')
            ax.text(self.eXY[ei,0]-12, self.eXY[ei,1]-5, ("E%d" % (ei+1)), fontsize=fontsize, color=fontcolor)
        ax.set_aspect('equal',adjustable='box')
        
    def dispRawElectrodeValue(self, ax, electrodeRawValues, s=8, cmap='gray', unifyRange=[0, 1]):
        frameNum = electrodeRawValues.shape[0]
        
        for i in range(frameNum):
            self.dispFingerSurface(ax[i], color=pltLightGrey)
            self.dispFingerLayout(ax[i], color=pltLightGrey)
            
        for i in range(frameNum):
            scplt = ax[i].scatter(self.eXY[:,0], self.eXY[:,1], c=electrodeRawValues[i,:].T, cmap=cmap, s=s, vmin=unifyRange[0], vmax=unifyRange[1],zorder=10)
            ax[i].set_aspect('equal',adjustable='box')
            ax[i].axis('off')
        
        return scplt
    
    def dispFingerLayout(self, ax, lw=1, xShift=0, color='turquoise'):
        arcObj = Arc([self.centerX +xShift, self.centerY], 2*self.cRadius, 2*self.cRadius, angle=0, theta1=0.0, 
                theta2=180.0, color=color, lw=lw, zorder=1)
        ax.add_patch(arcObj)
        ax.plot([self.centerX-self.cRadius +xShift, self.centerX-self.cRadius +xShift], [self.bottomY, self.centerY], color=color, lw=lw,zorder=1)
        ax.plot([self.centerX+self.cRadius +xShift, self.centerX+self.cRadius +xShift], [self.bottomY, self.centerY], color=color, lw=lw,zorder=1)
        ax.plot([self.centerX-self.cRadius +xShift, self.centerX+self.cRadius +xShift], [self.bottomY, self.bottomY], color=color, lw=lw,zorder=1)
        ax.set_aspect('equal',adjustable='box')
        
    def dispFingerSurface(self, ax, color='turquoise'):
        ax.plot(self.gridXY[:,0], self.gridXY[:,1], color=color, lw=0.1,zorder=0)
        
    def constructMap(self, eValue):
        mapValue = np.matmul(eValue, self.Phi) / self.SumPhi
        return mapValue
        
    def dispMaps(self, ax, mapValues, xShift=0, cbarax=None, cmap=cm.get_cmap('Greys', 100), unifyRange=[0, 1], 
                 s=0.1, dispOutline=False, colorbarLabel=False):      
        frameNum = len(mapValues)
        
        for i in range(frameNum):
            scplt = ax.scatter(xShift*i+self.gridXY[:,0], self.gridXY[:,1], c=mapValues[i], cmap=cmap, s=s, norm=None, 
                       vmin=unifyRange[0], vmax=unifyRange[1])

        ax.set_aspect('equal',adjustable='box')

        ax.set_xlim([self.centerX-self.cRadius, xShift*i+self.centerX+self.cRadius])
        ax.set_ylim([self.bottomY, self.centerY + self.cRadius + 10])
        
        ax.axis('off')
        
        if cbarax is None:
            cbarax = ax
            
        cbar = plt.colorbar(scplt, ax=cbarax, fraction=0.05, pad=0.25, aspect=8)
        cbar.outline.set_visible(False)
        cbar.ax.get_yaxis().labelpad = 15
        
        if colorbarLabel:
            cbar.ax.set_ylabel(r'$\Delta_{\mathrm{Impedance}} (\Omega$)', rotation=270)
        
        if dispOutline:
            self.dispFingerLayout(ax)
        
        return cbar
        
    def mapFromCubicInterp(self, ax, eValue, cmap='gray', unifyRange=[0, 1], dispNode=False): # Cubic interpolation of electrodes 
        grid_z = griddata(self.eXY, eValue, (self.grid_x, self.grid_y), method='cubic')
        
        scplt = ax.imshow(grid_z.T, extent=self.extent, origin='lower', cmap=cmap, vmin=unifyRange[0], vmax=unifyRange[1])
        
        if dispNode:
            self.dispElectrode(ax)
            
        ax.set_aspect('equal',adjustable='box')
        ax.axis('off')
        
        return scplt

    
#  ''' Load data for actuator measurement '''
def loadDataSegment(measureDataPath, root, fileName, lpFreq=0.5, fileName2=None): 
    actLabel = decodeActuatorInfo(root)
    if actLabel:
        tubeLen = decodeData(actLabel, '\d+', rearCode='mm')
        infillVol = decodeData(actLabel, '[\d+\.]*\d+', rearCode='mL')   

        vLevel = decodeData(fileName, '\d+', frontCode='v')
        cTime = decodeData(fileName, '\d+', frontCode='c')
        dTime = decodeData(fileName, '\d+', frontCode='d')
        trialNum = decodeData(fileName, '\d+', frontCode='t')
        dLabel = "L%03dF%.1fV%03dC%04dD%04d" % (tubeLen, infillVol, vLevel, cTime, dTime)  

        print("%s --- Len=%dmm, Infill=%.1fmL, Condi: v=%d%% c=%dms d=%dms t=%d" % 
              (dLabel, tubeLen, infillVol, vLevel, cTime, dTime, trialNum))         
    
    if fileName2 is None:
        nameLabel = decodeData(fileName, ".*.btd", isString=True)
        fileName2 = nameLabel + "_Pac.csv"
    
    ''' Read in data '''
    if root is None:
        data = np.genfromtxt(ospa.join(measureDataPath, fileName), delimiter=',')
        dataPAC = np.genfromtxt(ospa.join(measureDataPath, fileName2), delimiter=',')
    else:
        data = np.genfromtxt(ospa.join(measureDataPath, root, fileName), delimiter=',')
        dataPAC = np.genfromtxt(ospa.join(measureDataPath, root, fileName2), delimiter=',')

    t = data[:,0]
    pDC = (data[:,1] - data[0,1]) * 0.0365 # DC Pressure = (Pdc - Offset) 0.0365 kPa/bit
    tAC = data[:,2]
    tDC = data[:,3]
#     eData = (4095/data[:,4:] - 1) * 10000 # (Unit: Ohm) Impedance = (4095/En - 1) 10 kOhm
    eData = data[:,4:]# (No Unit)
    eData = eData - np.mean(eData[0:20,:], axis=0) # Subtract DC (the first 0.2 sec signal)
    
    ''' Smooth impedance signal when 0 < lpFreq < 0.5, otherwise disabled'''
    if lpFreq < 0.5 and lpFreq > 0:
        for i in range(19):
            eData[:,i] = lowpassSmooth(eData[:,i], cutFreqRatio=lpFreq, order = 8)
            
    eData = eData - np.mean(eData[0:20,:], axis=0) # Subtract DC (the first 0.2 sec signal)

    outData = {}
    outData['pDC'] = pDC
    outData['tAC'] = tAC
    outData['tDC'] = tDC
    outData['eData'] = eData

    pAC = (dataPAC[:,1] - dataPAC[0,1]) * 0.00037   # AC Pressure = (Pdc - Offset) 0.37 Pa/bit = (Pdc - Offset) 0.00037 kPa/bit
    outData['pAC'] = pAC
    outData['t'] = np.arange(len(pDC))/biotacFs["Pdc"]
    outData['t2'] = np.arange(len(pAC))/biotacFs["Pac"]
    
    return outData