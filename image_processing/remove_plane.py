# -*- coding: utf-8 -*-
"""
Created on Wed Apr  7 10:42:53 2021

@author: s1332488 Harry Carstairs

Plane fitting to height band of processed TDX images (from NetCDF format)

NB depends on xarray, which may be difficult to set up in same environment as snappy?
I have two separate environments for working with these two packages (pysnap and XR)

Call from command line:
        $ python remove_plane <file.nc> <N_samples>

"""

from scipy.linalg import lstsq
import numpy as np
import xarray as xr
import sys


def get_samples(N,array):
    """
    Takes a selection of N samples from a 2D array

    Parameters
    ----------
    N : int
        number of samples to take
    array : (m x n) numpy array 

    Returns
    -------
    A : (N x 3) numpy array 
        Matrix with 3 columns: the first two contain X and Y values, the third contains 1s
    B : (N x 1) numpy array
        Matrix of Z values
        
    The best fit plane to the sampled points is specified by p, in 
    A x p = B
    Where p is a (3 x 1) matrix
    N > 3 , i.e. the problem is over-specified
    so we are looking for least squares solution
    """
    X,Y = array.shape[0], array.shape[1]
    x_vals = np.random.randint(0,X,N)
    y_vals = np.random.randint(0,Y,N)
    B = array[x_vals,y_vals]
    not_nan = ~np.isnan(B)
    B = B[not_nan]
    A = np.ones((N,3))
    A[:,0] = x_vals
    A[:,1] = y_vals
    A = A[not_nan]
    return A, B

def plane(p,x,y):
    # Equation of a plane
    # [Broken down into x and y
    # But equivalent to the matrix version described above]
    return p[0]*x + p[1]*y + p[2]

def get_coeff(array,N):
    A,B = get_samples(N,array)
    result = lstsq(A,B) # Scipy.optimise finds least squares solution 
    return result[0]    # First component is the array p itself
    
def remove_plane(array,N):
    """

    Parameters
    ----------
    array : 2D numpy array
    N : int, number of sample points to take

    Returns
    -------
    residual : array with best-fit plane subtracted - same shape as input

    """
    coeff = get_coeff(array,N)
    y,x = np.meshgrid(np.arange(array.shape[1]),np.arange(array.shape[0]))
    best_fit = plane(coeff,x,y)
    residual = array - best_fit
    return residual

def correct_DEM(file,N):
    """

    Parameters
    ----------
    file : str
        path to NetCDF4 file with a variable named height_HH
        height_HH is the surface from which to subtract the best fitting plane
    N : int
        number of samples to take from height_HH to estimate best fitting plane

    Returns
    -------
    None. NetCDF file with appended name is saved.

    """
    with xr.open_dataset(file) as ds:
        height = ds.height_HH.data 
        corrected_height = remove_plane(height,N)
        corrected_height = xr.DataArray(data=corrected_height,coords=ds.coords,dims=ds.dims)
        ds['height_corrected'] = corrected_height
        ds.to_netcdf(file.split('.nc')[0]+'_deramped.nc')

#-----------------------------------------------#

correct_DEM(sys.argv[1],int(sys.argv[2]))