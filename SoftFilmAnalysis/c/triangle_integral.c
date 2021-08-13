/*
"Program to compute the volume of a triangle pouch"
"Unit: mm"
"Author: Yitian Shao"
"Created on 2021.06.04"
*/
#include <math.h>
#include <stdio.h>
#include <omp.h>

#ifndef M_PI
    #define M_PI 3.14159265358979323846
#endif

/* Triangle pouch is formed by cutting front, and symmetrically two sides, then top of a sphere */
/* 's' is the radius of top cutting circle, 'f' is the distance between the center of front cutting circle to the center of the sphere */
/* 'R' is the radius of the sphere being cutted, 'h' is the distance between the center of top cutting circle to the center of the sphere */
/* 'n' is half length of the triangle side, 'stepSize' controls the resolution of the integral */
/* Note: All input arguments must be nonnegative and 'stepSize' must be positive */

/* Compute the volume of a corner of a sphere cutted by two perpendicular planes */
double sphereCorner(double s2, double f, double R2, double stepSize)
{
	double cornerV = 0.0, Vi = 0.0;
	double f2 = f*f;
	
	int iMax = (int)((s2 - f2)/stepSize); // Need integer index for parallel computing 
	
	//Assign maximum number of threads for parallel computing
	int threadNum = omp_get_max_threads();
	omp_set_num_threads(threadNum); 
	printf("Parallel computing for sphere corner: Assigned number of threads = %d\n", threadNum);
	
	#pragma omp parallel shared(cornerV) private(Vi)
	{		
		#pragma omp for
		for(int i = 1; i < iMax; i++) //for(double x = f2; x < s2; x += stepSize)
		{
			double x = (double)i * stepSize + f2;
			Vi -= stepSize * (f * sqrt(x - f2) - x * acos(f/sqrt(x))) / (2 * sqrt(R2 - x));	
		}
		
		#pragma omp critical
        {
			cornerV += Vi;
        }
	}
	return cornerV;
}

/* Compute the volume of the triangle pouch through boolean substration method */
/* Output unit: mm3 */
double computeVol(double s, double f, double R, double h, double n, double stepSize)
{
	double s2 = s*s;
	double R2 = R*R;
	double h2 = h*h;
	
	double frontCornerV = sphereCorner(s2, f, R2, stepSize);
	
	double SideCornerV = sphereCorner(s2, sqrt(s2 - n*n), R2, stepSize);
	
	double upperSphereV = ( 2 * R2 * (R - h) + h * (h2 - R2) ) * M_PI/3;
	
	printf("Front = %.3f mm3, Side = %.3f mm3\n", frontCornerV, SideCornerV);
		
	return (upperSphereV - frontCornerV - 2*SideCornerV);
}

/* Compute the Total Electric Field Energy below the entire area of triangle pouch */
/* Output unit: (U/l)^2 * A -> (V/mm)^2 * mm^2 = V^2 */
/* Note that input arguments are for half of the triangle pouch */
/* Note that input x1 must be greater than x0 */
/* Note that in reality, z0 is smaller than h due to thickness of the pouch, therefore z0 = h - thickness */
double computeTriTEFE(double x0, double x1, double y0, double z0, double R, double m, double U, double stepSize)
{
	double a = 0.0, b = 0.0, R2 = 0.0, c = 0.0, stepSize2 = 0.0, V = 0.0, Vi = 0.0; // y = ax + b, R2 = R square, V is (A/l^2), Vi is used for parallel computing
	
	c = x1 - x0; 
	a = m/c;
	b = a * -x0;
	R2 = R*R;
	stepSize2 = stepSize*stepSize; // Area dA
	
	int iMax = (int)(c/stepSize); // Need integer index for parallel computing 
	
	//Assign maximum number of threads for parallel computing
	int threadNum = omp_get_max_threads();
	omp_set_num_threads(threadNum); 
	printf("Parallel computing for Triangle TEFE: Assigned number of threads = %d\n", threadNum);
	
	#pragma omp parallel shared(V) private(Vi)
	{		
		#pragma omp for
		for(int i = 0; i < iMax; i++) // OMP Alternative of: for(double x = x0; x < x1; x += stepSize)
		{
			double x = (double)i * stepSize + x0;
			double y1 = a * x + b;
			double temp = R2 - x*x; // Temp variable facilitates the computation
			
			for(double y = y0; y < y1; y += stepSize)
			{
				double l = sqrt(temp - y*y) - z0; // l is the vertical distance between electrodes			
				//if(l < 0.02) printf("l = %f\n", l); // For debug only
				
				Vi += stepSize2 / (l*l);
			}
		}
				
		#pragma omp critical
        {
			V += Vi;
        }
	}
	
	// Note that only half of the Total Electric Field Energy is computed by the for-loop since the triangle pouch is symmetric about x-axis
	return (2 * V * U*U); // Total Electric Field Energy defined as (A/l^2) * U^2
}

/* Compute the Total Electric Field Energy below the entire area of rectange pouch that connects the triangle pouch */
/* Output unit: (U/l)^2 * A -> (V/mm)^2 * mm^2 = V^2 */
/* Note that input arguments are for half of the rectangle pouch */
/* Note that input y1 must be greater than y0 */
/* Note that in reality, z0 is smaller than h due to thickness of the pouch, therefore z0 = h - thickness */
double computeRectTEFE(double y0, double y1, double z0, double r, double w, double U, double stepSize)
{
	double r2 = 0.0, V = 0.0, Vi = 0.0;
	
	r2 = r*r;
	
	int iMax = (int)((y1 - y0)/stepSize); // Need integer index for parallel computing 
	
	//Assign maximum number of threads for parallel computing
	int threadNum = omp_get_max_threads();
	omp_set_num_threads(threadNum); 
	printf("Parallel computing for Rectangle TEFE: Assigned number of threads = %d\n", threadNum);
	
	#pragma omp parallel shared(V) private(Vi)
	{
		#pragma omp for
		for(int i = 0; i < iMax; i++) // OMP Alternative of: for(double y = y0; y < y1; y += stepSize)
		{
			double y = (double)i * stepSize + y0;
			
			double l = sqrt(r2 - y*y) - z0; // l is the vertical distance between electrodes
			//if(l < 0.02) printf("l = %f\n", l); // For debug only
			
			Vi += stepSize / (l * l);
		}
		
		#pragma omp critical
        {
			V += Vi;
        }		
	}
	// Note that only half of the Total Electric Field Energy is computed by the for-loop since the rectangle pouch is symmetric about x-axis
	return (2 * V * U*U * w); // Total Electric Field Energy defined as (A/l^2) * U^2
}

/****************** [Obsoleted] Slower double integral method
double compute(double x0, double x1, double y0, double z0, double R, double m, double stepSize)
{
	double a = 0.0, b = 0.0, R2 = 0.0, c = 0.0, V = 0.0, Vi = 0.0; // y = ax + b, R2 = R square, V is the volume computed (half-triangle), Vi is used for parallel computing
	
	c = x1 - x0;
	a = m/c;
	b = a * -x0;
	R2 = R*R;
	
	int iMax = (int)(c/stepSize); // Need integer index for parallel computing 
	
	//Assign maximum number of threads for parallel computing
	int threadNum = omp_get_max_threads();
	omp_set_num_threads(threadNum); 
	printf("Start parallel computing: Assigned number of threads = %d\n", threadNum);
	
	#pragma omp parallel shared(V) private(Vi)
	{		
		#pragma omp for
		for(int i = 0; i < iMax; i++) // OMP Alternative of: for(double x = x0; x < x1; x += stepSize)
		{
			double x = (double)i * stepSize + x0;
			double y1 = a * x + b;
			double temp = R2 - x*x; // Temp variable facilitates the computation
			
			for(double y = y0; y < y1; y += stepSize)
			{
				Vi += (sqrt(temp - y*y) - z0) * stepSize * stepSize;
			}
		}
		
		//printf("Thread %d: Vi = %f\n", omp_get_thread_num(), Vi); // For debug only
		
		#pragma omp critical
        {
			V += Vi;
        }
	}
	return (2*V); // Note that only half of the volume is computed by the for-loop since the triangle pouch is symmetric about x-axis
}
******************/