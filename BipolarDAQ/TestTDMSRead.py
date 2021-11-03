import time
from os import walk
import os.path as ospa
import numpy as np
import re
import matplotlib.pyplot as plt
import pandas as pd
import subprocess
import os

from nptdms import TdmsFile

# plt.rcParams.update({'font.size': 14})
# Fs = 1000

# root = os.path.dirname(__file__)
# print(root)
# # filePath = "C:\\Users\\ytshao\\JupyterNote\\BipolarDAQ\\Audio_Video\\Frog.mp4"
# filePath = os.path.join(root, 'Audio_Video','Frog.mp4')
# print(filePath)
# wmp = "C:\\Program Files (x86)\\Windows Media Player\\wmplayer.exe"
# # subprocess.run("dir", shell=True)
# subprocess.call([wmp, '/fullscreen', filePath])

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