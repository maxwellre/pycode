'''
General Functions and Classes
'''

from os import walk
import os.path as ospa
import numpy as np
import re
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
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

def aPlot(figName='', is3D = False, dpi=72):
    ax = []
    
    fig1 = plt.figure(figsize = (6,3), dpi=dpi)
    
    fig1.suptitle(figName, fontsize=16)
    if(is3D):
        ax = fig1.add_subplot(111, projection='3d')
    else:
        ax = fig1.add_subplot(111)
        
    return ax, fig1
	
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

def decodeData(fileName, numFormat, frontCode='', rearCode=''):
    segStr = re.findall(frontCode+numFormat+rearCode, fileName)
    if segStr:
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

def lowpassSmooth(datain, cutFreqRatio = 0.05, order = 8):
    b, a = signal.butter(order, 2 * cutFreqRatio, btype='low')
    dataout = signal.filtfilt(b, a, datain)
    return dataout

def loadDataSegment(measureDataPath, root, fileName, lpFreq=0.5):
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

    ''' Read in data '''
    data = np.genfromtxt(ospa.join(measureDataPath, root, fileName), delimiter=',')

    t = data[:,0]
    pDC = (data[:,1] - data[0,1]) * 0.0365 # DC Pressure = (Pdc - Offset) 0.0365 kPa/bit
    tAC = data[:,2]
    tDC = data[:,3]
    eData = (4095/data[:,4:] - 1) * 10000 # (Unit: Ohm) Impedance = (4095/En - 1) 10 kOhm
    
    ''' Smooth impedance signal when 0 < lpFreq < 0.5, otherwise disabled'''
    if lpFreq < 0.5 and lpFreq > 0:
        for i in range(19):
            eData[:,i] = lowpassSmooth(eData[:,i], cutFreqRatio=lpFreq, order = 8)
            
    eData = eData - np.mean(eData[0:20,:], axis=0) # Subtract DC (the first 0.2 sec signal)

    outData = {}
    outData['t'] = t
    outData['pDC'] = pDC
    outData['tAC'] = tAC
    outData['tDC'] = tDC
    outData['eData'] = eData
    
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
    for i in range(19):
        ax.plot(data['t'], data['eData'][:,i])
    ax.set_xlim(tRange)
    ax.plot(data['t'][[ti, ti]], [-0.1, 0.1], 'k')
    
def generateMapResult(tind, btData, yMax=5, unifyRange=None, alpha=4000, reverseColorbar=True):    
# cmap=cm.get_cmap('inferno', 100) # cmap=cm.get_cmap('binary', 100) # cmap=cm.get_cmap('RdYlBu', 100)
    colorr = ""
    if reverseColorbar:
        colorr = "_r"
    cmap=cm.get_cmap("viridis"+colorr, 100)

    btMap = BiotacMap()
    btMap.initializeDistanceMap(alpha=alpha)

    frameNum = len(tind)
    
    ''' Remove DC of electrode measurement '''
    eData = btData['eData']
    eData = eData - np.mean(eData[tind[0]:tind[1],:], axis=0) 

    fig0, axes = plt.subplots(1, frameNum, dpi=300, figsize=figSize_inch)
    for i in range(frameNum):
        btMap.mapFromCubicInterp(axes[i], eData[tind[i],:])
        axes[i].set_title("%.2fs" % btData['t'][tind[i]], size=3)

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
    fig1cbar, cbarax = plt.subplots(dpi=300, figsize=(1,1))
    btMap.dispMaps(ax0, mapValues, xShift=300, cbarax=cbarax, cmap=cmap, unifyRange=unifyRange, s=0.001, dispOutline=False)

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
    
    def dispFingerLayout(self, ax, lw=1):
        arcObj = Arc([self.centerX, self.centerY], 2*self.cRadius, 2*self.cRadius, angle=0, theta1=0.0, 
                theta2=180.0, color='turquoise', lw=lw)
        ax.add_patch(arcObj)
        ax.plot([self.centerX-self.cRadius, self.centerX-self.cRadius], [self.bottomY, self.centerY], color='turquoise', lw=lw)
        ax.plot([self.centerX+self.cRadius, self.centerX+self.cRadius], [self.bottomY, self.centerY], color='turquoise', lw=lw)
        ax.plot([self.centerX-self.cRadius, self.centerX+self.cRadius], [self.bottomY, self.bottomY], color='turquoise', lw=lw)
        ax.set_aspect('equal',adjustable='box')
        
    def dispFingerSurface(self, ax):
        ax.plot(self.gridXY[:,0], self.gridXY[:,1], color='turquoise', lw=0.1)
        
    def constructMap(self, eValue):
        mapValue = np.matmul(eValue, self.Phi) / self.SumPhi
        return mapValue
        
    def dispMaps(self, ax, mapValues, xShift=0, cbarax=None, cmap=cm.get_cmap('Greys', 100), unifyRange=[0, 1], 
                 s=0.1, dispOutline=False):      
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
        cbar.ax.set_ylabel(r'$\Delta_{\mathrm{Impedance}} (\Omega$)', rotation=270)
        
        if dispOutline:
            self.dispFingerLayout(ax)
        
        return cbar
        
    def mapFromCubicInterp(self, ax, eValue, dispNode=False): # (Obsolete) Interpolation cubically between electrodes 
        grid_z = griddata(self.eXY, eValue, (self.grid_x, self.grid_y), method='cubic')
        
        ax.imshow(grid_z.T, extent=self.extent, origin='lower', cmap='gray')
        
        if dispNode:
            self.dispElectrode(ax)
            
        ax.set_aspect('equal',adjustable='box')
        ax.axis('off')