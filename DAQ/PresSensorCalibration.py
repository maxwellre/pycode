import time
from os import walk
import os.path as ospa
import numpy as np
import re
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

Fs = 1000

dataPath = ".\dataFs1000Final_Aug"

presVolt = []
for root, directories, files in walk(dataPath):
    for fileName in files:
        pressure = float(re.split("bar", fileName, 1)[0])
        data = np.genfromtxt(ospa.join(root, fileName), delimiter=',')
        voltage = np.mean(data)

        presVolt.append([pressure, voltage])
presVolt = np.array(presVolt)

print("Collected: ", presVolt.shape)

fig1 = plt.figure(figsize = (16,6))
fig1.suptitle(("Fs = %.0f Hz" % Fs), fontsize=12)
ax = fig1.add_subplot(111)
ax.set_xlabel('Pressure (Bar)')
ax.set_ylabel('Voltage (V)')

ind = (presVolt[:,0] < 0.3) # Only check data up to 0.25 bar
print("Fitted: ", ind.shape)

ax.plot(presVolt[ind,0], presVolt[ind,1], '.', color='tab:red')

'''Linear Regression of the data'''
regr = LinearRegression(fit_intercept =True).fit(presVolt[ind,0].reshape(-1, 1), presVolt[ind,1])
lineX = np.array([0.0, 0.25]).reshape(-1, 1)
lineY = regr.predict(lineX)
ax.plot(lineX, lineY, '-', color='k')
print('Coefficient and intercept of the fitting line: ', regr.coef_, regr.intercept_)

a = 1.0/regr.coef_[0]
b = regr.intercept_

# np.savetxt("Calibration20210802.txt", [a, b], delimiter=",", fmt='%.16f')
# testVolt = 4.425; testPres = (testVolt - b)*a; ax.plot(testPres, testVolt, '.', color='b')
y_pred = (presVolt[:,1] - b) * a
print("Linear Regression R2 = %f\n" % r2_score(presVolt[:,0] , y_pred))

plt.show()