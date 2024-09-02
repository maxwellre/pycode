import os
import sys
import serial
import socket
import numpy as np
import csv
import time
import matplotlib.pyplot as plt 
import pyaudio
import wave
from threading import Thread
import re
from scipy.io import wavfile
import scipy.io
import cv2

######获取加速度
def get_acc():
    main = "./acc/a10s.out"
    f = os.popen(main)
    f.close()




#####获取音频
def get_aud():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    
    RATE = 48000
    RECORD_SECONDS = 100
    file_path = "./"
    currentTime = time.strftime("%H-%M-%S", time.localtime())
    WAVE_OUTPUT_FILENAME = ("Data%s.wav" % (currentTime))
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("开始录音,请说话......")

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("录音结束！")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(file_path + WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)   
    wf.writeframes(b''.join(frames))
    wf.close()

########            画图        #####################
##########################################################
##########################################################
    samplerate, data = wavfile.read(file_path + WAVE_OUTPUT_FILENAME)

    length = data.shape[0] / samplerate


    time_label = np.linspace(0., length, data.shape[0])
    plt.plot(time_label, data, label="Left channel")
    plt.legend()
    plt.xlabel("Time [s]")
    plt.ylabel("Amplitude")
    plt.show()

    return


#######获取视频（RGB）

def get_rgb():
    cap = cv2.VideoCapture(0,cv2.CAP_V4L2)
    frameNum=0
    fourcc =cv2.VideoWriter_fourcc(*'XVID')
    currentTime = time.strftime("%H-%M-%S", time.localtime())
    WAVE_OUTPUT_FILENAME = ("rgb%s.avi" % (currentTime))
    out =cv2.VideoWriter(WAVE_OUTPUT_FILENAME,fourcc,30,(640,480))


    while(cap.isOpened()):
        ret,frame=cap.read()
        frameNum +=1
        if ret==True:
            out.write(frame)
        #     cv2.imshow('frame',frame)
            if frameNum==3000:
                break      
        else:
            break
    
    out.release()
    cap.release()
    return





# 创建 Thread 实例
t1 = Thread(target=get_acc)
t2 = Thread(target=get_aud)
t3 = Thread(target=get_rgb)
# t4 = Thread(target=get_dep)
# 启动线程运行




t1.start()
t2.start()
t3.start()
# t4.start()
# 等待所有线程执行完毕
t1.join()  # join() 等待线程终止，要不然一直挂起
t2.join()
t3.join()
# t4.join()



########            txt-->csv        #####################
##########################################################
##########################################################
# 单位转化
GSCALE = 0.001952  # 1.952 mg/digit (±16 g in High-Performance Mode)



def twoComplement16bit(hexData):
    return -(hexData & 0x8000) | (hexData & 0x7FFF)


# 指定路径
directory_path = "./"
# 获取指定路径下的所有文件名并倒序排序
file_names = sorted(os.listdir(directory_path), reverse=True)
# 构建正则表达式
pattern = re.compile(r"Sensor(\d)_(\d{8})-(\d{6})\.txt")
# 获取最新的文件
example_file = None
for file_name in file_names:
    filepath = os.path.join(directory_path, file_name)
    if os.path.isfile(filepath) and pattern.match(file_name):
        example_file = file_name
# 提取文件名的各个部分
sensor_index = pattern.match(example_file).group(1)
date_part = pattern.match(example_file).group(2)
time_part = pattern.match(example_file).group(3)

# 传感器数量
sensorNum = 4
# 传感器数量
for index in range(sensorNum):
    txtFile = "Sensor%d_%s-%s.txt" % (index, date_part, time_part)
    txtFile = os.path.join(directory_path, txtFile)
    with open(txtFile, "r", encoding="utf-8") as file:
        dataBytes = file.read()
        print(f"文件 '{txtFile}' 共有 {len(dataBytes)} 个字符.")
        # 定义csv文件作为输出文件
        csvFile = "csv%s_%s-%s.csv" % (index, date_part, time_part)
        if not os.path.exists(csvFile):
            with open(csvFile, "w", newline="") as fd:
                writer = csv.writer(fd)
                for i in range(0, len(dataBytes), 12):
                    dataX = (dataBytes[i + 2 : i + 4] + dataBytes[i : i + 2])  # 将X轴数据的MSB和LSB组合在一起
                    dataY = (dataBytes[i + 6 : i + 8] + dataBytes[i + 4 : i + 6])  # 将Y轴数据的MSB和LSB组合在一起
                    dataZ = (dataBytes[i + 10 : i + 12] + dataBytes[i + 8 : i + 10])  # 将Z轴数据的MSB和LSB组合在一起

                    if len(dataX) > 0 and len(dataY) > 0 and len(dataZ) > 0:
                        dataX = twoComplement16bit(int(dataX, 16)) >> 2  # 转换X轴的二补码数据
                        dataY = twoComplement16bit(int(dataY, 16)) >> 2  # 转换Y轴的二补码数据
                        dataZ = twoComplement16bit(int(dataZ, 16)) >> 2  # 转换Z轴的二补码数据

                        writer.writerow([dataX, dataY, dataZ])
                print(f"csv{index}数据保存成功")
         # 可视化数据
        accData = np.genfromtxt(csvFile, delimiter=",")
        Fs = 1600 # 采样率指定1600
        t = np.arange(accData.shape[0]) / Fs
        fig1, ax = plt.subplots(3, 1, dpi=72, figsize=(16, 6))
        ax[0].plot(t, accData[:, 0] * GSCALE)
        ax[1].plot(t, accData[:, 1] * GSCALE)
        ax[2].plot(t, accData[:, 2] * GSCALE)
        # 添加标题
        ax[0].set_ylabel("Acceleration of X (g)")
        ax[1].set_ylabel("Acceleration of Y (g)")
        ax[2].set_ylabel("Acceleration of Z (g)")
        ax[2].set_xlabel("Time (s)")
        plt.show()        
    os.remove(txtFile)


##########################################################
##########################################################
##########################################################
#####                txt-->csv                ############