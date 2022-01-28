'''
Program to find parameters matching arc length defined by dash space
Unit: mm
Author: Yitian Shao
Created on 2022.01.27 based on 'SearchValidArc.py'
'''
import time
import csv
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from PouchLib import * # This library will import numpy as np and sys

meshDensity = 100 # For visualization resolution (= 2R/dx)
intStepSize = 0.0001 # (mm) Step size for performing integral computation

shellThickness = 0.020 # (mm) Denoted as 'l_s' in publication
epsilon_s = 3.2 # Relative permittivity of the shell
epsilon_f = 3.2 # Relative permittivity of the fluid

''' Match arc length '''
RSearchNum = 1000

time0 = time.time()

mRange = np.arange(1.0, 10.0, 0.1)

with open('ExploreDesign.csv', 'w', newline='') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerow(['dashHalfDist', 'dashSpace', 'R', 'triArc', 'triFA', 'triPSA', 'triVol', 'rectVol',
                     'triCapa', 'rectCapa', 'dashLength'])

    for m in mRange:
        c = m * np.sqrt(3)
        print("\n\n[%.0f s] c = %.6f mm, m = %.6f mm" % (time.time() - time0, c, m))

        for R in np.logspace(np.log10(50000), np.log10(c), RSearchNum):
            triPouch0 = TrianglePouch(R, c, m)
            triArc = triPouch0.getFrontArc()  # Front Arc Length

            triFA = triPouch0.getFrontArea()  # Front Area
            triPSA = triPouch0.getProjectedSideArea()  # Projected Side Area

            triCapa = triPouch0.getCapacitance(shellThickness, epsilon_s, epsilon_f, intStepSize)  # Vary by materials

            triVol = triPouch0.getVolume(intStepSize)

            w = 10
            rectPouch0 = RectanglePouch(triPouch0.r, w, triPouch0.m, 2*triPouch0.m/triPouch0.dy)
            rectVol = rectPouch0.getVolume()

            rectCapa = rectPouch0.getCapacitance(shellThickness, epsilon_s, epsilon_f, intStepSize)  # Vary by materials

            print("\n\n[%.0f s] c = %.6f mm, m = %.6f mm, R = %.6f mm" % (time.time() - time0, c, m, R))

            writer.writerow([triPouch0.m, triPouch0.c, triPouch0.R, triArc, triFA, triPSA, triVol, rectVol,
                             triCapa, rectCapa, w])


