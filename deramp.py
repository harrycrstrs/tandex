"""
Author : Harry Carstairs

A script to remove the best fit plane to a 2D array of numbers

"""


import numpy as np
from scipy.linalg import lstsq

def get_samples(array,N):
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
    # But equivalent to the matrix version]
    return p[0]*x + p[1]*y + p[2]

def get_coeff(array,N):
    A,B = get_samples(array,N)
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