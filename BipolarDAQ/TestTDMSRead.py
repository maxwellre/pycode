import time
from os import walk
import os.path as ospa
import numpy as np
import re
import matplotlib.pyplot as plt
import pandas as pd

from nptdms import TdmsFile

# %matplotlib notebook
# %matplotlib notebook
plt.rcParams.update({'font.size': 14})

Fs = 1000

testX = np.arange(100)

print(testX[:0])

print(testX[1:])

print(testX[100:])

# dataPath = ".\Data1007 CamForceNoFluidGauge"
# subFolder = ["SiliconeOil_MedTube","SiliconeOil_Tube8mm","FR3_MedTube","FR3_Tube8mm","FR3_Tube8mmRotated"]
#
#
# for root, directories, files in walk(dataPath):
#     for fileName in files:
#         # Reading in tdms (Force sensor, time and LED signal)
#         if (fileName[-4:] == 'tdms'):
#             with TdmsFile.open(ospa.join(root, fileName)) as tdms_file:
#                 print(tdms_file)
#
#                 sensorData = tdms_file['FT sensor']
#
#                 temp = sensorData['Fx']
#                 FxData = temp[:]
#
#                 print(FxData)