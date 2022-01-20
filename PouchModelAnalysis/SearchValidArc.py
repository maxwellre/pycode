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
epsilon_s = 2.0 # Relative permittivity of the shell
epsilon_f = 3.2 # Relative permittivity of the fluid

''' Match arc length '''
RSearchNum = 100000

time0 = time.time()
# pouchStructure = np.array([6, 5, 4, 3, 2, 1])
# rectNum = np.sum(pouchStructure - 1)  # Number of rectangle pouch-cell
# triNum = rectNum * 2 - len(pouchStructure) + 1  # Number of triangle pouch-cell

mRange = np.arange(4.5, 5.0, 0.001)
RRange = np.logspace(np.log10(50000), np.log10(7), RSearchNum)

with open('ValidArcLength.csv', 'w', newline='') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerow(('dashHalfDist', 'dashSpace', 'R', 'triArc', 'triVol', 'rectVol', 'dashLength'))

    for c in [12.66, 8.66, 4.66]:
        for m in mRange:
            print("\n\n[%.0f s] c = %.6f mm, m = %.6f mm" % (time.time() - time0, c, m))

            unFound = True
            i = 0
            while (unFound and i < RSearchNum):
                R = RRange[i]
                triPouch0 = TrianglePouch(R, c, m)
                triArc = triPouch0.getFrontArc()  # Front Arc Length

                if abs(triArc - 10) < 0.0005:

                    triVol = triPouch0.getVolume(intStepSize)

                    w = 24.66 - c
                    rectPouch0 = RectanglePouch(triPouch0.r, w, triPouch0.m)
                    rectVol = rectPouch0.getVolume()

                    print("\n\n[%.0f s] c = %.6f mm, m = %.6f mm, triArc = %.6f mm, R = %.6f mm, w = %.6f mm" %
                          (time.time() - time0, c, m, triArc, R, w))

                    writer.writerow([triPouch0.m, triPouch0.c, triPouch0.R, triArc, triVol, rectVol, w])

                    if c == 8.66: # Special design when c = 8.66mm, w = 20mm
                        w = 20
                        rectPouch0 = RectanglePouch(triPouch0.r, w, triPouch0.m)
                        rectVol = rectPouch0.getVolume()

                        print("\n\n[%.0f s] c = %.6f mm, m = %.6f mm, triArc = %.6f mm, R = %.6f mm, w = %.6f mm" %
                              (time.time() - time0, c, m, triArc, R, w))

                        writer.writerow([triPouch0.m, triPouch0.c, triPouch0.R, triArc, triVol, rectVol, w])


                    unFound = False
                else:
                    i += 1
