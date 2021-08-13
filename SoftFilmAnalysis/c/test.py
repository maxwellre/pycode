import ctypes
from ctypes import util
from ctypes import CDLL
import time


libPath = ctypes.util.find_library("./triangle_integral")
triangle_integral = ctypes.CDLL(libPath)

triangle_integral.computeVol.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, 
                                    ctypes.c_double, ctypes.c_double]
triangle_integral.computeVol.restype = ctypes.c_double

time0 = time.time()
V = triangle_integral.computeVol(26.296411310760284, 21.843588689239716, 50, 42.52644767877184, 25.158589393088, 1e-06)

#V = triangle_integral.computeVol(50.0, 0.0, 50, 0.0, 35.35533905932738, 0.0001)

print("Volume of the triangle pouch V = %.3f mm3 (Computed in %.10f sec)" % (V, time.time()-time0))    


triangle_integral.computeTriTEFE.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, 
                                    ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
triangle_integral.computeTriTEFE.restype = ctypes.c_double

time0 = time.time()
V = triangle_integral.computeTriTEFE(-26.296411310760284, 21.843588689239716, 0.0, 42.52644767877184 -0.02, 50.0, 14.641, 10000, 0.001)
print("TEFE of the triangle pouch = %.3f V2 (Computed in %.10f sec)" % (V, time.time()-time0))   


triangle_integral.computeRectTEFE.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, 
                                    ctypes.c_double, ctypes.c_double, ctypes.c_double]
triangle_integral.computeRectTEFE.restype = ctypes.c_double

time0 = time.time()
V = triangle_integral.computeRectTEFE(0.0, 14.641, 42.52644767877184 -0.02, 44.97618962490396, 20.0, 10000, 1e-06)
print("TEFE of the triangle pouch = %.3f V2 (Computed in %.10f sec)" % (V, time.time()-time0)) 