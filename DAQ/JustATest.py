import PyDAQmx as nidaq
import numpy as np
import time
import matplotlib.pyplot as plt

IO_High = np.ones((1,), dtype=np.uint8)
IO_Low = np.zeros((1,), dtype=np.uint8)

# data = np.array([0,1,1,0,1,0,1,0], dtype=np.uint8)
# data = np.ones((2000,), dtype=np.uint8)

# sampNum = 100000000
# sampNum = 200
# data = np.ones((sampNum,), dtype=np.uint8)
#
# data[int(sampNum/2):] = 0
# data = np.tile(data, 5)
# print(data)

task = nidaq.Task()
task.CreateDOChan("Dev1/port0/line1","",nidaq.DAQmx_Val_FiniteSamps)

task.StartTask()
task.WriteDigitalLines(1,False,10.0,nidaq.DAQmx_Val_GroupByChannel,IO_High,None,None)
time.sleep(1)
task.WriteDigitalLines(1,False,10.0,nidaq.DAQmx_Val_GroupByChannel,IO_Low,None,None)
task.StopTask()