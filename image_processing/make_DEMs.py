# -*- coding: utf-8 -*-
"""
Created on Mon Apr 26 14:24:05 2021

@author: Harry Carstairs

This script takes a command line argument for the number of range looks .
Call this script inside a folder containing TDX interferograms (with SRTM phase removed).
For each interferogram, an unwrapped, terrain-corrected phase height image will be processed and saved.

"""

from snappy import ProductIO, HashMap, GPF, ProductUtils
import snappy
import glob
from scipy.linalg import lstsq
import numpy as np
import sys
import os
sys.path.append('/home/s1332488/code/tandex')
from deramp import remove_plane

def createP(function, inputProduct, writeout=False, **kwargs):
    # pythonic version of GPF.createProduct()
    # function is string of SNAP operator
    # inputProduct is SNAP product object
    # kwargs contains any parameters to pass to the operator
    p = HashMap()
    for arg in kwargs:
        p.put(arg,kwargs.get(arg))
    result = GPF.createProduct(function,p,inputProduct)
    if writeout != False:
        ProductIO.writeProduct(result,writeout,'BEAM-DIMAP')
    else:
        return result

def get_data(imageBand):
    # takes SNAP image band object and returns a numpy array containing the data in that band
    W,H = imageBand.getRasterWidth(), imageBand.getRasterHeight()
    array = np.zeros(W*H)
    imageBand.readPixels(0,0,W,H,array)
    return array.reshape(H,W).transpose()

def zero_phase(wrapped_phase):
    # Return phase values centered roughly on zero
    vals,binedges=np.histogram(wrapped_phase,bins=50)
    binsize = binedges[1] - binedges[0]
    peak = binedges[vals.argmax()] + 0.5*binsize
    recentered = wrapped_phase - peak
    return recentered

def cost_fun(recentered,offset):
    # Calculates how many 'jumps' remain after "quasi-unwrapping"
    # The quasi unwrapping simply assumes all values are within a 
    # 2pi interval and determines the offset required to center them
    if offset < 0:
        a = recentered + (recentered < offset)*2*np.pi
    else:
        a = recentered - (recentered > offset)*2*np.pi
    cost1 = (np.abs(a[:-1] - a[1:]) > 5).sum()
    cost2 = (np.abs(a[:,:-1] - a[:,1:]) > 5).sum()
    return cost1+cost2

def unwrap(zeroed_phase):
    # Quasi unwrapping, where we assume all values lie already within one 2pi interval
    vals,binedges=np.histogram(zeroed_phase,bins=50)
    binsize = binedges[1] - binedges[0]
    initial_guess = binedges[vals.argmin()] + 0.5*binsize
    tryout = np.linspace(initial_guess-0.2,initial_guess+0.2,25)
    costs = [cost_fun(zeroed_phase,offset) for offset in tryout]
    fit = np.polyfit(tryout,costs,2)
    offset = -fit[1]/(2*fit[0])
    if offset < 0:
        unwrapped = zeroed_phase + (zeroed_phase < offset)*2*np.pi
    else:
        unwrapped = zeroed_phase - (zeroed_phase > offset)*2*np.pi
    return unwrapped

def get_kz(image):
    # Get array of wavenumber values for every pixel
    W = image.getBandAt(0).getRasterWidth()
    H = image.getBandAt(0).getRasterHeight()
    rangeT = np.asarray(image.getTiePointGrid('slant_range_time')
                    .readPixels(0,0,W,H,np.zeros(W*H,dtype=np.float32))
                   ).reshape(H,W).transpose()
    theta = np.asarray(image.getTiePointGrid('incident_angle')
                  .readPixels(0,0,W,H,np.zeros(W*H,dtype=np.float32))
                  ).reshape(H,W).transpose()
    c = 3*10**8
    metadata = image.getMetadataRoot()
    freq = float(str(metadata
              .getElement('Abstracted_Metadata')
              .getAttribute('radar_frequency')
              .getData()))
    wavelength = c / (freq*10**6)
    theta = np.deg2rad(theta)
    baseline = float(str(metadata
                         .getElement('CoSSC_Metadata')
                         .getElement('cossc_product')
                         .getElement('commonAcquisitionInfo')
                         .getElement('acquisitionGeometry')
                         .getAttribute('effectiveBaseline')
                         .getData()))
    HoA = float(str(metadata
                    .getElement('CoSSC_Metadata')
                    .getElement('cossc_product')
                    .getElement('commonAcquisitionInfo')
                    .getElement('acquisitionGeometry')
                    .getAttribute('heightOfAmbiguity')
                    .getData()))
    R = 0.5 * c * rangeT*10**-9
    kz = 4*np.pi*baseline / (wavelength*R*np.sin(theta))
    if HoA < 0:
        kz = -kz
    return kz

# ------------------------------------- #

def phaseToHeight(inputfile,NLOOKS):
    """
    This is the central processing chain
    inputfile is a string of an interferogram file name
    NLOOKS is the number of range looks to be used for multi-looking
                                    #
    Multi-looking, Goldstein phase filtering, unwrapping and terrain correction are performed
    The output is then written to file in BEAM-DIMAP format
    """
    
    TEMP1 = 'ML_fl_temp.dim'
    TEMP2 = 'height_temp.dim'
    OUT = '_'.join([inputfile.split('.dim')[0],
                    'ML',
                    str(NLOOKS),
                    'height_TC.dim'
                    ])
    image = ProductIO.readProduct(inputfile)
    
    # SNAP Processing -------------------------------
    image = createP('Multilook',image,nRgLooks=NLOOKS)
    image = createP('GoldsteinPhaseFiltering',image,
                    alpha=0.2,
                    useCoherenceMask=True,
                    coherenceThreshold=0.2,
                    writeout=TEMP1)
    
    # Numpy processing -----------------------------
    image = ProductIO.readProduct(TEMP1)
    phase = image.getBand([x for x in list(image.getBandNames()) if 'Phase' in x][0])
    phase_data = get_data(phase)
    recentered = zero_phase(phase_data)
    unwrapped = unwrap(recentered)
    unw_deramped = remove_plane(unwrapped, 10000)
    height = unw_deramped / get_kz(image)
    height = height.transpose().flatten()
    
    # Write to target Product--------------------------
    W = image.getBandAt(0).getRasterWidth()
    H = image.getBandAt(0).getRasterHeight()
    targetP = snappy.Product('height_product','height_type',W,H)
    ProductUtils.copyMetadata(image,targetP)
    ProductUtils.copyTiePointGrids(image,targetP)
    targetP.setProductWriter(ProductIO.getProductWriter('BEAM-DIMAP'))
    for band in ['Phase','coh']:
        bandname= [x for x in list(image.getBandNames()) if band in x][0]
        ProductUtils.copyBand(bandname,image,band,targetP,True)
    targetP.setProductReader(ProductIO.getProductReader('BEAM-DIMAP'))
    ProductIO.writeProduct(targetP,TEMP2,'BEAM-DIMAP')
    targetB = targetP.addBand('height', snappy.ProductData.TYPE_FLOAT32)
    targetB.setUnit('m')
    targetP.setProductWriter(ProductIO.getProductWriter('BEAM-DIMAP'))
    targetP.writeHeader(TEMP2)
    targetB.writePixels(0,0,W,H,height)
    targetP.closeIO()
    
    # Terrain correction-------------------------
    image = ProductIO.readProduct(TEMP2)
    image = createP('Terrain-Correction',
                    image,
                    alignToStandardGrid='true',
                    demName='SRTM 1Sec HGT',
                    saveDEM='true')
    ProductIO.writeProduct(image,OUT,'BEAM-DIMAP')
    
#-----------------------------------------------------------

def main():
    NLOOKS = int(sys.argv[1])
    files = [f for f in glob.glob('TDX_IFG*.dim') if 'height' not in f]
    N = len(files)
    i=1
    for f in files:
        print('******')
        print('Processing: '+str(i)+' of '+str(N))
        print(f)
        print('...')
        phaseToHeight(f,NLOOKS)
        print('Done')
        i+=1
        
main()