# -*- coding: utf-8 -*-
"""
Created on Wed Apr  7 10:42:53 2021

@author: s1332488 Harry Carstairs

Plane fitting to height band of processed TDX images.

"""

import scipy.optimize as op
import numpy as np
import rasterio as ras
import os

def samples(N,array):
    # N is number of samples
    # To be taken from raster in array format
    X,Y = array.shape[0], array.shape[1]
    x_vals = np.random.randint(0,X,N)
    y_vals = np.random.randint(0,Y,N)
    z_vals = array[x_vals,y_vals]
    return np.array([x_vals,y_vals,z_vals])

def residual(p,S):
    """
    # p is list of three parameters a,b,c
    # which describe a plane according to:
    # ax + by + c = z
    # This function returns the square residual
    # obtained by subtracting a plane from samples S
    # where S is in the format [[x_vals],[y_vals],[z_vals]]
    """
    left = p[0] * S[0] + p[1] * S[1] + p[2]
    right = S[2]
    return (np.square(left-right)).sum()

def get_plane(array,N):
    # Minimizes the residual to obtain 
    # best fit plane, according to N random points
    X = np.arange(array.shape[0])
    Y = np.arange(array.shape[1])
    X,Y = np.meshgrid(X,Y)
    s = samples(N,array)
    p0 = [0,0,s[2].mean()]
    result = op.minimize(residual,p0,array).x
    a,b,c = result[0],result[1],result[2]
    plane = a*X + b*Y + c
    return plane

