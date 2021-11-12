import ctypes
from ctypes import util
from ctypes import CDLL
from os import path

'''Import LeapC libraray'''
sdkPath = path.join(path.dirname(__file__), 'LeapSDK')

libPath = ctypes.util.find_library(path.join(sdkPath, 'LeapC'))
leapc = ctypes.CDLL(libPath)

libPath = ctypes.util.find_library(path.join(sdkPath, 'libExampleConnection'))
leapc_lib = ctypes.CDLL(libPath)

class LEAP_TRACKING_EVENT(ctypes.Structure):
    _fields_ = [("info", ctypes.c_void_p),("tracking_frame_id", ctypes.c_int64),
                ("nHands", ctypes.c_uint32),("pHands", ctypes.c_void_p),("framerate", ctypes.c_float)]

'''------------------------------------------------------------------------------------------------------------------'''

if __name__ == '__main__':
    leapc_lib.OpenConnection()

    while not leapc_lib.IsConnected:
        leapc_lib.millisleep(100)

    print("Leap Motion Connected")

    oneFrame = LEAP_TRACKING_EVENT()

    while True:
        leapc_lib.getOneFrame(ctypes.byref(oneFrame))
        print(oneFrame.nHands)