'''
Program to find parameters matching arc length defined by dash space
Unit: mm
Author: Yitian Shao
Created on 2022.01.16
'''
import time
import csv
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from PouchLib import * # This library will import numpy as np and sys

meshDensity = 1000 # For visualization resolution (= 2R/dx)
intStepSize = 0.0001 # (mm) Step size for performing integral computation

shellThickness = 0.020 # (mm) Denoted as 'l_s' in publication
epsilon_s = 3.2 # Relative permittivity of the shell
epsilon_f = 3.2 # Relative permittivity of the fluid

''' Match arc length '''
RSearchNum = 10000 # Maximum search number of R to be performed in the white loop

time0 = time.time()
# pouchStructure = np.array([6, 5, 4, 3, 2, 1])
# rectNum = np.sum(pouchStructure - 1)  # Number of rectangle pouch-cell
# triNum = rectNum * 2 - len(pouchStructure) + 1  # Number of triangle pouch-cell

# mRange = np.arange(4.5, 5.0, 0.001)
# mRange = np.linspace(12.314, 12.318, 1000) # For the design of the compact actuator on 2022.06
# mRange = np.linspace(12.3198, 12.3140, 1600)
mRange = np.logspace(np.log10(12.3198), np.log10(12.3140), 5000) # For infill volume smaller than 1.2mL (compact actuator on 2022.06)

halfArc = 24.64 # 10 # For the design of the compact actuator on 2022.06

# RRange = np.logspace(np.log10(50000), np.log10(7), RSearchNum)
# RRange = np.linspace(650, 150, RSearchNum) # For the design of the compact actuator on 2022.06
# RRange = np.logspace(np.log10(360), np.log10(100), RSearchNum) # For the design of the compact actuator on 2022.06
# RRange = np.logspace(np.log10(1000), np.log10(100), RSearchNum) # For the design of the compact actuator on 2022.06

# Binary Search (2022.08.16)
RSearchMin = 100
RSearchMax = 1500

with open('ValidArcLength.csv', 'w', newline='') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerow(('dashHalfDist', 'dashSpace', 'R', 'triArc', 'triVol', 'rectVol', 'dashLength'))

    # for c in [12.66, 8.66, 4.66]:
    for c in [72.71]: # For the design of the compact actuator on 2022.06
        for m in mRange:
            unFound = True
            RRange = [RSearchMin, RSearchMax]
            i = 0
            while (unFound):
                # R = RRange[i]
                R = (RRange[0] + RRange[1])/2

                triPouch0 = TrianglePouch(R, c, m)
                triArc = triPouch0.getFrontArc()  # Front Arc Length

                if abs(triArc - halfArc) < 0.00001:

                    triVol = triPouch0.getVolume(intStepSize)

                    # w = 24.66 - c
                    w = 1.0 # For the design of the compact actuator on 2022.06
                    rectPouch0 = RectanglePouch(triPouch0.r, w, triPouch0.m)
                    rectVol = rectPouch0.getVolume()

                    print("\n[%.0f s] c = %.6f mm, m = %.6f mm, triArc = %.6f mm, R = %.6f mm, w = %.2f mm (triVol = %.2f mm3)" %
                          (time.time() - time0, c, m, triArc, R, w, triVol))

                    writer.writerow([triPouch0.m, triPouch0.c, triPouch0.R, triArc, triVol, rectVol, w])

                    if c == 8.66: # Special design when c = 8.66mm, w = 20mm
                        w = 20
                        rectPouch0 = RectanglePouch(triPouch0.r, w, triPouch0.m)
                        rectVol = rectPouch0.getVolume()

                        print("\n[%.0f s] c = %.6f mm, m = %.6f mm, triArc = %.6f mm, R = %.6f mm, w = %.6f mm" %
                              (time.time() - time0, c, m, triArc, R, w))

                        writer.writerow([triPouch0.m, triPouch0.c, triPouch0.R, triArc, triVol, rectVol, w])


                    unFound = False
                else:
                    if triArc < halfArc: # Reduce R to increase the current arc length (triArc)
                        RRange[1] = R  # Search in lower half range
                    elif triArc > halfArc: # Increase R to decrease the current arc length (triArc)
                        RRange[0] = R # Search in higher half range
                    i += 1

                    if(i > RSearchNum) or (RRange[0] == RRange[1]):
                        unFound = False
                        print("\n[%.0f s] c = %.6f mm, m = %.6f mm, Stop: R = %.6f [%.6f  %.6f]mm, triArc = %.6f mm, " %
                              (time.time() - time0, c, m, R, RRange[0], RRange[1], triArc))
