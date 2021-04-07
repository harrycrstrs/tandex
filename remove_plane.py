# -*- coding: utf-8 -*-
"""
Created on Wed Apr  7 10:42:53 2021

@author: s1332488 Harry Carstairs

Plane fitting to height band of processed TDX images.

"""

from scipy.linalg import lstsq
import numpy as np
# rasterio as ras
# import os


def get_samples(N,array):
    # N is number of samples
    # A is Matrix containing x,y values and B is vector of z values
    X,Y = array.shape[0], array.shape[1]
    x_vals = np.random.randint(0,X,N)
    y_vals = np.random.randint(0,Y,N)
    B = array[x_vals,y_vals]
    A = np.ones((N,3))
    A[:,0] = x_vals
    A[:,1] = y_vals
    return A, B

def plane(p,x,y):
    return p[0]*x + p[1]*y + p[2]

def get_coeff(array,N):
    A,B = get_samples(N,array)
    result = lstsq(A,B)
    return result
    
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
    coeff = get_coeff(array,N)[0]
    y,x = np.meshgrid(np.arange(array.shape[1]),np.arange(array.shape[0]))
    best_fit = plane(coeff,x,y)
    residual = array - best_fit
    return residual

