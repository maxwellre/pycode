/*
"Program to compute the volume and capacitance for triangle and rectangle pouch"
"Unit: mm"
"Author: Yitian Shao"
"Created on 2022.01.13" based on 'triangle_integral.c'
*/
#include <math.h>
#include <stdio.h>
#include <omp.h>

#ifndef M_PI
    #define M_PI 3.14159265358979323846
#endif

#ifndef M_EPSILON0 // Free space permittivity (Unit: Farad per meter)
    #define M_EPSILON0 0.0000000000088541878128
#endif

/* (Utility function) */
double getEpsilon0()
{
	return M_EPSILON0;
}



/* Triangle pouch is formed by cutting front, and symmetrically two sides, then top of a sphere 
	's' is the radius of top cutting circle, 'f' is the distance between the center of front cutting circle to the center of the sphere 
	'R' is the radius of the sphere being cutted, 'h' is the distance between the center of top cutting circle to the center of the sphere 
	'n' is half length of the triangle side, 'stepSize' controls the resolution of the integral (this n is different from the n in the publication)
	Note: All input arguments must be nonnegative and 'stepSize' must be positive 
	Variable name followed by '2' indicates squared value for improving computation efficiency */

/* (Internal function) Compute the volume of a corner of a sphere cutted by two perpendicular planes */
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
double computeVol(double s, double f, double R, double h, double n, double stepSize) // slower method
{
	double s2 = s*s;
	double R2 = R*R;
	double h2 = h*h;

	double SideCornerV = sphereCorner(s2, sqrt(s2 - n*n), R2, stepSize);
	
	if (f < 0)
	{
		double frontCornerV = sphereCorner(s2, -f, R2, stepSize);
		
		printf("Front = %.3f mm3, Side = %.3f mm3\n", frontCornerV, SideCornerV);
		
		return (frontCornerV - 2*SideCornerV);
	}
	
	double frontCornerV = sphereCorner(s2, f, R2, stepSize);
	
	double upperSphereV = ( 2 * R2 * (R - h) + h * (h2 - R2) ) * M_PI/3;
	
	printf("Front = %.3f mm3, Side = %.3f mm3\n", frontCornerV, SideCornerV);
		
	return (upperSphereV - frontCornerV - 2*SideCornerV);
}

/* Compute capacitance of the triangle pouch*/
/* Note: m is replaced by n in the publication */
/* shell = l_s/epsilon_s, fluid = 1/epsilon_f, where l_s is shell thickness, epsilon denotes the relative permittivities */
/* Output unit: Farad */
double computeTriCapa(double x0, double x1, double y0, double z0, double R, double m, double shell, double fluid, double stepSize)
{
	double a = 0.0, b = 0.0, R2 = 0.0, c = 0.0, capa = 0.0, capai = 0.0; // y = ax + b, R2 = R square, capa is total capacitance, capai is used for parallel computing
	
	c = x1 - x0;
	a = m/c;
	b = a * -x0;
	R2 = R*R;
	
	double stepSize2 = stepSize * stepSize;
	
	int iMax = (int)(c/stepSize); // Need integer index for parallel computing 
	
	//Assign maximum number of threads for parallel computing
	int threadNum = omp_get_max_threads();
	omp_set_num_threads(threadNum); 
	printf("Start parallel computing: Assigned number of threads = %d\n", threadNum);
	
	#pragma omp parallel shared(capa) private(capai)
	{		
		#pragma omp for
		for(int i = 0; i < iMax; i++) // (Parallel computing) OMP Alternative of: for(double x = x0; x < x1; x += stepSize)
		{
			double x = (double)i * stepSize + x0;
			double y1 = a * x + b;
			double temp = R2 - x*x; // Temp variable facilitates the computation
			
			for(double y = y0; y < y1; y += stepSize)
			{
				capai += stepSize2 / (shell + fluid * (sqrt(temp - y*y) - z0));
			}
		}
		
		//printf("Thread %d: capai = %f\n", omp_get_thread_num(), capai); // For debug only
		
		#pragma omp critical
        {
			capa += capai;
        }
	}
	return (capa * M_EPSILON0 * 0.001); // Unit 'Farad', converted A/l from 'mm2/m' to 'm2/m' by 1/1000
}

/* Compute capacitance of the rectangle pouch*/
/* Note: m is replaced by n in the publication */
/* shell = l_s/epsilon_s, fluid = 1/epsilon_f, where l_s is shell thickness, epsilon denotes the relative permittivities */
/* Output unit: Farad */

double computeRectCapa(double y0, double y1, double z0, double r, double w, double shell, double fluid, double stepSize)
{
	double r2 = 0.0, capa = 0.0, capai = 0.0;
	
	r2 = r*r;
	
	int iMax = (int)((y1 - y0)/stepSize); // Need integer index for parallel computing 
	
	//Assign maximum number of threads for parallel computing
	int threadNum = omp_get_max_threads();
	omp_set_num_threads(threadNum); 
	printf("Parallel computing for Rectangle TEFE: Assigned number of threads = %d\n", threadNum);
	
	#pragma omp parallel shared(capa) private(capai)
	{
		#pragma omp for
		for(int i = 0; i < iMax; i++) // (Parallel computing) OMP Alternative of: for(double y = y0; y < y1; y += stepSize)
		{
			double y = (double)i * stepSize + y0;
			
			capai += stepSize / (shell + fluid * (sqrt(r2 - y*y) - z0));
		}
		
		#pragma omp critical
        {
			capa += capai;
        }		
	}
	return (capa * M_EPSILON0 * w * 0.001); // Unit 'Farad', converted A/l from 'mm2/m' to 'm2/m' by 1/1000
}

/* [Obsoleted] Compute volume using slower double integral method */

double computeVolSlow(double x0, double x1, double y0, double z0, double R, double m, double stepSize)
{
	double a = 0.0, b = 0.0, R2 = 0.0, c = 0.0, V = 0.0, Vi = 0.0; // y = ax + b, R2 = R square, V is the volume computed (half-triangle), Vi is used for parallel computing
	
	c = x1 - x0;
	a = m/c;
	b = a * -x0;
	R2 = R*R;
	
	double stepSize2 = stepSize * stepSize;
	
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
				Vi += (sqrt(temp - y*y) - z0) * stepSize2;
			}
		}
		
		//printf("Thread %d: Vi = %f\n", omp_get_thread_num(), Vi); // For debug only
		
		#pragma omp critical
        {
			V += Vi;
        }
	}
	return (2*V); // Note that only half of the volume is computed by the for-loop since the triangle pouch is symmetric about x-z plane
}