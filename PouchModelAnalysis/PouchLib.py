'''
Library for pouch model analysis
Unit: mm
Author: Yitian Shao
Created on 2022.01.13 based on 
'''

import sys
import numpy as np

'''
Enable fast computing using c shared library and parallel programming
'''
enableFastComputing = True;

if(enableFastComputing):
    try:
        import ctypes    
        from ctypes import util
        from ctypes import CDLL
    except:
        print("ctypes unfounded, switch to normal python computing")
        enableFastComputing = False;

    if(enableFastComputing):
        try:
            libPath = ctypes.util.find_library("c/pouch_integral")
            pouch_integral = ctypes.CDLL(libPath)
            
            pouch_integral.getEpsilon0.restype = ctypes.c_double # This function has no input argument

            pouch_integral.computeVol.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, 
                                                ctypes.c_double, ctypes.c_double]
            pouch_integral.computeVol.restype = ctypes.c_double
            
            pouch_integral.computeTriCapa.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, 
                                    ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
            pouch_integral.computeTriCapa.restype = ctypes.c_double
            
            pouch_integral.computeRectCapa.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, 
                                    ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
            pouch_integral.computeRectCapa.restype = ctypes.c_double
            
            pouch_integral.computeVolSlow.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, 
                        ctypes.c_double, ctypes.c_double, ctypes.c_double]
            pouch_integral.computeVolSlow.restype = ctypes.c_double
            
            print("c shared library imported successfully!")

            pouch_integral.initOpenMP()
        except:
            print("c shared library unfounded, switch to normal python computing")
            enableFastComputing = False;
            
            
'''
General Functions
'''
def getEpsilon0():
    return pouch_integral.getEpsilon0()

def data_cut(x, y, z, ind):
    return x[ind], y[ind], z[ind]

def coordTrans2D(a, b, theta, a_translate, b_translate):
    # 2D coordinate transformation, rotate counter-clockwise by angle theta and then translate
    rotMat = np.array([[np.cos(theta), -np.sin(theta)],
                  [np.sin(theta), np.cos(theta)]])
    ab = np.matmul(rotMat, np.stack((a, b)))
    ab[0,:] += a_translate
    ab[1,:] += b_translate
    return ab

def fitPlane2Points(p1, p2, p3):
    # Fit a plane to three nonalighed points
    return np.cross(p1 - p2, p3 - p2)

def computeCornerVolume(s, f, R, intStepSize):
    # Compute the volume of a corner of a sphere cutted by two perpendicular planes
    # 's' - radius of top cutting circle
    # 'f' - the distance between the center of front cutting circle to the center of the sphere, can be negative if beta > 45 degree
    # 'R' - radius of the sphere being cutted
    # 'intStepSize'- the resolution of the integral 
    a = np.arange(f**2, s**2, intStepSize)
    cornerArea = (f * np.sqrt(a - f**2) - a * np.arccos(f/np.sqrt(a))) / (2 * np.sqrt(R**2 - a))
    return -np.sum(intStepSize * cornerArea)

def computeArcLength(r, rad):
    # 'r' - the radius of the cutting circle
    # 'rad' - radian angle of half of the cutting sector
    return rad * 2 * r

def computeCornerArea(r, rad):
    # 'r' - the radius of the cutting circle
    # 'rad' - radian angle of half of the cutting sector
    return (rad - np.sin(rad)*np.cos(rad)) * r**2
 
'''----------------------------------------------------------------------------------------------------------------------''' 
'''
Classes
'''
class TrianglePouch:
    # Triangle pouch is formed by cutting front, and symmetrically two sides, then top of a sphere 
    # 'R' - radius of the sphere being cutted
    # 'c' - heigh of the triangle
    # 'm' - half width of the triangle bottom (replaced by 'n' in the publication)
    #  --------------------------------------
    # 'f' - distance between the center of front cutting circle to the center of the sphere
    # 's' - radius of the top cutting circle
    # 'r' - radius of the front cutting circle
    # 'h' - distance between the center of top cutting circle to the center of the sphere
    # 'n' - half length of the triangle side (excluded in the publication)
    # 'intStepSize' controls the resolution of the integral
    #  --------------------------------------
    # 'meshDensity' - density of vertices of the mesh of the pouch
    # 'adPlotDensity' - density of vertices of additive plot
    # 'addAd' - construct additive plot 
    # 'dispCircle' - Display full circle for additive plot
    #  --------------------------------------------------------------------------------------------------------------------
    def __init__(self, R = 50, c = 20, m = 34.641, meshDensity = 100, adPlotDensity = 100, addAd = False, dispCircle = False):
        self.R = R
        self.c = c
        self.m = m
        self.meshDensity = meshDensity
        self.adPlotDensity = adPlotDensity
        self.triangle = []
        self.frontCircle = []
        self.frontLine = []
        self.leftCircle = []
        self.leftLine = []
        self.rightCircle = []
        self.rightLine = []     
        
        if(self.c <= 0):
            print("Invalid value: c must be greater than 0!")
            
        if(self.c > 2*self.R):
            sys.exit("Invalid value: c cannot be greater than R!")
            
        self.beta = np.arctan(self.m/self.c) # Angle Beta (viewing from the top)
        
        self.s = 0.5 * (self.m**2/self.c + self.c) # Radius of the top cutting circle, 0 < s < R 
        self.f = 0.5 * (-self.m**2/self.c + self.c) # f can be negative if beta > 45 degree    
        self.r = np.sqrt(self.R**2 - self.f**2) # Radius of the front cutting circle, 0 < r < R
        
        #if(self.f < 0):
            #print("Beta angle is greater 45 degree")
        
        if(self.m > self.r):
            print("m = %f, c = %f, r = %f, f = %f" % (self.m, self.c, self.r, self.f))
            sys.exit("Invalid value: m cannot be greater than r!")
        elif(self.m == self.r):
            print("Warning: h equals 0!")
            
        if(self.f >= self.R):
            print("m = %f, c = %f, r = %f, f = %f" % (self.m, self.c, self.r, self.f))
            sys.exit("Invalid f!")
        if(self.r < self.m):
            print("m = %f, c = %f, r = %f, f = %f" % (self.m, self.c, self.r, self.f))
            sys.exit("Invalid r!")
            
        self.h = np.sqrt(self.r**2 - self.m**2) # (mm) Cutting height of the sphere, Pouch height will be 2(r-h)
        self.alpha = np.arccos(self.h/self.r) # Angle Alpha (viewing from the front) 
        
        self.n = self.s * np.cos(self.beta)
        self.rSide = np.sqrt(self.n**2 + self.h**2)
        
        # Triangle coordinates (can be updated)
        self.triangleTopX = self.R - self.s # Note: Triangle mirror point 1
        self.triangleBottomX = self.c + self.triangleTopX # Note: Triangle mirror point 2
        self.cCenterX = self.n * np.cos(self.beta) + self.triangleTopX
        self.cCenterY = -self.n * np.sin(self.beta)
        
        # Generate the mesh of the triangle pouch
        self.dx = 2*R/self.meshDensity
        self.dy = self.dx
        x = np.outer(np.linspace(0, 2*R, self.meshDensity+1), np.ones(self.meshDensity+1))
        y = np.outer(np.ones(self.meshDensity+1), np.linspace(-R, R, self.meshDensity+1))
        z2 = R**2 - (x-R)**2 - (y**2) # Supposed to be square of z when on the sphere, but can be negative

        # Keep sphere upper surface
        keepInd = (z2 >= 0)
        x, y, z2 = data_cut(x, y, z2, keepInd)
        z = np.sqrt(z2) # Square root of z2

        # Cut the sphere
        keepInd = (z >= self.h)
        x, y, z = data_cut(x, y, z, keepInd)

        # Cut the Front Face (surface crossing the pouch)
        keepInd = (x <= self.f + self.R)
        x, y, z = data_cut(x, y, z, keepInd)

        # Cut the left-side face
        pNormVector = fitPlane2Points(np.array([self.triangleTopX, 0, self.h]), 
                                      np.array([self.cCenterX, self.cCenterY, -self.rSide]), 
                                      np.array([self.triangleBottomX, -self.m, self.h]))
        keepInd = (np.matmul(pNormVector, np.stack((x - self.cCenterX, y - self.cCenterY, z))) >= 0)
        x, y, z = data_cut(x, y, z, keepInd)

        # Cut the right-side face
        pNormVector2 = fitPlane2Points(np.array([self.triangleTopX, 0, self.h]), 
                                       np.array([self.cCenterX, -self.cCenterY, -self.rSide]), 
                                      np.array([self.triangleBottomX, self.m, self.h]))
        keepInd = (np.matmul(pNormVector2, np.stack((x - self.cCenterX, y + self.cCenterY, z))) <= 0)
        x, y, z = data_cut(x, y, z, keepInd)
        
        self.triangle = np.stack((x, y, z - self.h)) # Vertex coordinate of the triangle pouch
               
        if(addAd):
            self.__additiveLine(not dispCircle)
 
        ###print("Estimate Tri V = %.3f (mm3)" % np.sum(self.triangle[2,:] * self.dx * self.dy)) # Debug 
        
    def printInfo(self):
        print("(Unzeroed coordinate) c = %.2f mm, m = %.2f mm, r = %.2f mm, h = %.2f mm, s = %.2f mm, f = %.2f mm, n = %.2f mm, rSide = %.2f mm" % 
              (self.c, self.m, self.r, self.h, self.s, self.f, self.n, self.rSide))
        print("Spatial resolution dx = %f mm, dy = %f mm" % (self.dx, self.dy))
        print("Angle: Alpha = %.1f degree, Beta = %.1f degree" % (180*self.alpha/np.pi, 180*self.beta/np.pi))
        print("triangle with top at (%.2f, %.2f, %.2f) and left bottom at (%.2f, %.2f, %.2f)" % 
              (self.triangleTopX, 0, 0, self.triangleBottomX, -self.m, 0))

    # Private function for adding additive sketch for clear illustration
    def __additiveLine(self, dispCurve = True):
        # 'dispCurve' decides whether to display a curve or the entire circle
        
        # Front circle and line
        fAngle = np.linspace(0, 2*np.pi, self.adPlotDensity)
        x = (self.R + self.f) * np.ones(self.adPlotDensity)
        y = self.r * np.cos(fAngle)
        z = self.r * np.sin(fAngle)
        self.frontCircle = np.stack((x, y, z - self.h)) # Vertex coordinate of the front circle (Zero offset)
        if(dispCurve):
            keepInd = (z >= self.h)
            self.frontCircle = self.frontCircle[:, keepInd]
        
        self.frontLine = np.array([[self.R + self.f, self.R + self.f], [-self.m, self.m],
                                   [0.0, 0.0]]) # Coordinate of the front line
        
        # Side circle and line
        x, y = coordTrans2D(self.rSide * np.cos(fAngle), np.zeros(self.adPlotDensity), -self.beta, 
                            self.cCenterX, self.cCenterY)
        z = self.rSide * np.sin(fAngle)
        self.leftCircle = np.stack((x, y, z - self.h)) # Vertex coordinate of the left-side circle (Zero offset)
        if(dispCurve):
            keepInd = (z >= self.h)
            self.leftCircle = self.leftCircle[:, keepInd]
            
        self.leftLine = np.array([[self.triangleTopX, self.triangleBottomX], [0, -self.m], [0.0, 0.0]])
        ###leftRadiusLine = np.array([[triangleTopX, cCenterX], [0, cCenterY], [h, 0]])# For reference only

        x, y = coordTrans2D(self.rSide * np.cos(fAngle), np.zeros(self.adPlotDensity), self.beta, 
                            self.cCenterX, -self.cCenterY)
        self.rightCircle = np.stack((x, y, z - self.h)) # Vertex coordinate of the right-side circle (Zero offset)
        if(dispCurve):
            keepInd = (z >= self.h)
            self.rightCircle = self.rightCircle[:, keepInd]
            
        self.rightLine = np.array([[self.triangleTopX, self.triangleBottomX], [0, self.m], [0.0, 0.0]])
    
    # Private function for updating the coordinate of the mesh and lines
    def __updateCoordinate(self, movedx = 0, movedy = 0, movedz = 0):
        if(self.triangle.size == 0):
            sys.exit("Warning: Insufficient mesh density!")
            
        self.triangle[0,:] += movedx
        self.triangle[1,:] += movedy
        self.triangle[2,:] += movedz
        
        if(len(self.frontCircle)):
            self.frontCircle[0,:] += movedx
            self.frontCircle[1,:] += movedy
            self.frontCircle[2,:] += movedz

        if(len(self.frontLine)):
            self.frontLine[0,:] += movedx
            self.frontLine[1,:] += movedy
            self.frontLine[2,:] += movedz

        if(len(self.leftCircle)):
            self.leftCircle[0,:] += movedx
            self.leftCircle[1,:] += movedy
            self.leftCircle[2,:] += movedz

        if(len(self.leftLine)):
            self.leftLine[0,:] += movedx
            self.leftLine[1,:] += movedy
            self.leftLine[2,:] += movedz

        if(len(self.rightCircle)):
            self.rightCircle[0,:] += movedx
            self.rightCircle[1,:] += movedy
            self.rightCircle[2,:] += movedz

        if(len(self.rightLine)):
            self.rightLine[0,:] += movedx
            self.rightLine[1,:] += movedy
            self.rightLine[2,:] += movedz
        
        self.triangleTopX += movedx
        self.triangleBottomX += movedx
        self.cCenterX += movedx
        self.cCenterY += movedy
           
    def transformPouch(self, x = 0, y = 0, z = 0, flip = False):
        if(self.triangle.size == 0):
            sys.exit("Warning: Insufficient mesh density!")
            
        # Flip along the x axis
        if(flip):
            self.triangle[0,:] *= -1
            
            if(len(self.frontCircle)):
                self.frontCircle[0,:] *= -1
                
            if(len(self.frontLine)):
                self.frontLine[0,:] *= -1
                
            if(len(self.leftCircle)):
                self.leftCircle[0,:] *= -1
                
            if(len(self.leftLine)):
                self.leftLine[0,:] *= -1
                
            if(len(self.rightCircle)):
                self.rightCircle[0,:] *= -1
                
            if(len(self.rightLine)):
                self.rightLine[0,:] *= -1
                
            self.triangleTopX *= -1
            self.triangleBottomX *= -1
            self.cCenterX *= -1
            self.cCenterX *= -1
            
            # After flip, shift to align the current top to: the bottom before flipping
            self.__updateCoordinate(-self.triangleTopX -self.triangleBottomX, -self.m, 0)        
        
        # Translation
        self.__updateCoordinate(x, y, z)
        
                
    def displayPouch(self, ax, dispAdditive = False):
        if(self.triangle.size == 0):
            sys.exit("Warning: Insufficient mesh density!")
            
        ax.scatter3D(self.triangle[0,:], self.triangle[1,:], self.triangle[2,:], 
                 s = 1, edgecolor="k", facecolor=(0,0,0,0))
        
        if(dispAdditive):
            # Additive plot
            # Plot front circle
            if(len(self.frontCircle)):
                ax.plot(self.frontCircle[0,:], self.frontCircle[1,:], self.frontCircle[2,:], '--', c = 'g')
                
            # Plot front line
            if(len(self.frontLine)):
                ax.plot(self.frontLine[0,:], self.frontLine[1,:], self.frontLine[2,:], c = 'g')
                
            # Plot left circle
            if(len(self.leftCircle)):
                ax.plot(self.leftCircle[0,:], self.leftCircle[1,:], self.leftCircle[2,:], '--', c = 'b')
                
            # Plot left line
            if(len(self.leftLine)):
                ax.plot(self.leftLine[0,:], self.leftLine[1,:], self.leftLine[2,:], c = 'b')
                
            # Plot right circle
            if(len(self.rightCircle)):
                ax.plot(self.rightCircle[0,:], self.rightCircle[1,:], self.rightCircle[2,:], '--', c = 'b')
                
            # Plot right line
            if(len(self.rightLine)):
                ax.plot(self.rightLine[0,:], self.rightLine[1,:], self.rightLine[2,:], c = 'b')
 
    def getVolume(self, intStepSize):   
        if(enableFastComputing):
            #print("Fast compute volume = %f", pouch_integral.computeVol(self.s, self.f, self.R, self.h, self.n, intStepSize))
            #print("2D Integral compute volume = %f", pouch_integral.computeVolSlow(-self.s, self.f, 0.0, self.h, self.R, self.m, intStepSize)) # Check error
            return pouch_integral.computeVol(self.s, self.f, self.R, self.h, self.n, intStepSize)
        
        # Normal computing when fast computing is unavailable       
        sideCornerVol = computeCornerVolume(self.s, np.sqrt(self.s**2 - self.n**2), self.R, intStepSize)

        if (self.f < 0): # Beta > 45 degree 
            frontCornerVol = computeCornerVolume(self.s, -self.f, self.R, intStepSize)
            return frontCornerVol - 2*sideCornerVol

        frontCornerVol = computeCornerVolume(self.s, self.f, self.R, intStepSize)

        domeVol = ( 2 * self.R**2 * (self.R - self.h) + self.h * (self.h**2 - self.R**2) ) * np.pi/3
    
        return domeVol - frontCornerVol - 2*sideCornerVol
    
    def getFrontArea(self):
        return computeCornerArea(self.r, self.alpha)
    
    def getFrontArc(self):
        return computeArcLength(self.r, self.alpha)
    
    def getProjectedSideArea(self):
        # Area of two side-cutting circle projected onto the front-cutting circle
        sideArea = computeCornerArea(self.rSide, np.arcsin(self.n/self.rSide))
        return sideArea * np.sin(self.beta) * 2
    
    def getCapacitance(self, l_s, epsilon_s, epsilon_f, intStepSize = 0.001):
        if(not enableFastComputing):
            sys.exit("Unable to compute Capacitance without Fast Computing!")
        
        shellFactor = l_s/epsilon_s
        fluidFactor = 1.0/epsilon_f
        
        return pouch_integral.computeTriCapa(-self.s, self.f, 0.0, self.h, self.R, self.m, shellFactor, fluidFactor, intStepSize)

    # def getTotalForce(self, epsilon_r, voltage, zThick, epsilon_0 = 8.854e-12, intStepSize = 0.001):
        # if(not enableFastComputing):
            # sys.exit("Unable to compute Force without Fast Computing!")          
        # return pouch_integral.computeTriTEFE(-self.s, self.f, 0.0, self.h - zThick, self.R, self.m, 
                                                    # voltage, intStepSize) * 0.5 * epsilon_0 * epsilon_r
  
'''----------------------------------------------------------------------------------------------------------------------'''

class RectanglePouch:
    def __init__(self, r = 10, w = 50, m = 0, meshDensity = 100, adPlotDensity = 100, addAd = False, dispCircle = False):
        self.r = r
        self.w = w
        self.m = m
        self.meshDensity = meshDensity
        self.adPlotDensity = adPlotDensity
        self.frontCircle = []
        self.frontLine = []
        self.leftLine = []
        self.rightLine = []
        
        if(self.m > self.r):
            sys.exit("Invalid value: m must be smaller than r")
        
        self.alpha = np.arcsin(self.m/self.r) # Angle Alpha (viewing from the front) 
        self.zCut = np.sqrt(self.r**2 - self.m**2) # Supposed to be the h of the triangle pouch
    
        # Generate the mesh of the rectangle pouch
        self.dy = 2*self.m/self.meshDensity
        self.dx = self.dy
        xRows = np.arange(0.0, self.w, self.dy)
        yCols = np.arange(-r + 0.000001, r - 0.000001, self.dy)    
               
        x = np.outer(xRows, np.ones(yCols.size))
        y = np.outer(np.ones(xRows.size), yCols)
        z = np.sqrt(self.r**2 - y**2)
        
        keepInd = (z >= self.zCut)
        x, y, z = data_cut(x, y, z, keepInd)
        self.rectangle = np.stack((x, y, z - self.zCut))

        if(addAd):
            self.__additiveLine(not dispCircle)
            
        ###print("Estimate Rect V = %.3f (mm3)" % np.sum(self.rectangle[2,:] * self.dx * self.dy)) # Debug 
    
    # Private function for adding additive sketch for clear illustration
    def __additiveLine(self, dispCurve = True):
        # 'dispCurve' decides whether to display a curve or the entire circle
        fAngle = np.linspace(0, 2*np.pi, self.adPlotDensity)
        x = self.w * np.ones(self.adPlotDensity)
        y = self.r * np.cos(fAngle)
        z = self.r * np.sin(fAngle)
        self.frontCircle = np.stack((x, y, z - self.zCut)) # Vertex coordinate of the front circle (Zero offset) 
        
        if(dispCurve):
            keepInd = (z >= self.zCut)
            self.frontCircle = self.frontCircle[:, keepInd]
        
        # Coordinate of the front line
        self.frontLine = np.array([[self.w, self.w], [-self.m, self.m], [0.0, 0.0]]) 
        # Coordinate of the left line
        self.leftLine = np.array([[0, self.w], [-self.m, -self.m], [0.0, 0.0]]) 
        # Coordinate of the right line
        self.rightLine = np.array([[0, self.w], [self.m, self.m], [0.0, 0.0]]) 
        
    
    def transformPouch(self, movedx = 0, movedy = 0, movedz = 0):
        if(self.rectangle.size == 0):
            sys.exit("Warning: Insufficient mesh density!")
            
        self.rectangle[0,:] += movedx
        self.rectangle[1,:] += movedy
        self.rectangle[2,:] += movedz
        
        if(len(self.frontCircle)):
            self.frontCircle[0,:] += movedx
            self.frontCircle[1,:] += movedy
            self.frontCircle[2,:] += movedz

        if(len(self.frontLine)):
            self.frontLine[0,:] += movedx
            self.frontLine[1,:] += movedy
            self.frontLine[2,:] += movedz

        if(len(self.leftLine)):
            self.leftLine[0,:] += movedx
            self.leftLine[1,:] += movedy
            self.leftLine[2,:] += movedz

        if(len(self.rightLine)):
            self.rightLine[0,:] += movedx
            self.rightLine[1,:] += movedy
            self.rightLine[2,:] += movedz
            
    def displayPouch(self, ax, dispAdditive = False):
        if(self.rectangle.size == 0):
            sys.exit("Warning: Insufficient mesh density!")
            
        ax.scatter3D(self.rectangle[0,:], self.rectangle[1,:], self.rectangle[2,:], 
                         s = 1, edgecolor="k", facecolor=(0,0,0,0))
        
        if(dispAdditive):
            # Additive plot
            # Plot front circle
            if(len(self.frontCircle)):
                ax.plot(self.frontCircle[0,:], self.frontCircle[1,:], self.frontCircle[2,:], '--', c = 'g')
                
            # Plot front line
            if(len(self.frontLine)):
                ax.plot(self.frontLine[0,:], self.frontLine[1,:], self.frontLine[2,:], c = 'g')
                
            # Plot left line
            if(len(self.leftLine)):
                ax.plot(self.leftLine[0,:], self.leftLine[1,:], self.leftLine[2,:], c = 'r')
                
            # Plot right line
            if(len(self.rightLine)):
                ax.plot(self.rightLine[0,:], self.rightLine[1,:], self.rightLine[2,:], c = 'r')
    
    def getVolume(self): 
        return (self.alpha * self.r**2 - self.zCut * self.m) * self.w
    
    def getCapacitance(self, l_s, epsilon_s, epsilon_f, intStepSize = 0.001):
        if(not enableFastComputing):
            sys.exit("Unable to compute Capacitance without Fast Computing!")
        
        shellFactor = l_s/epsilon_s
        fluidFactor = 1.0/epsilon_f
        
        return pouch_integral.computeRectCapa(0.0, self.m, self.zCut, self.r, self.w, shellFactor, fluidFactor, intStepSize)
 
