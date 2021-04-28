# -*- coding: utf-8 -*-
"""
Created on Thu Apr  8 15:02:47 2021

Short script to convert from BEAM-DIMAP to NetCDF
BEAM-DIMAP is the best form for SNAP, whereas NetCDF is easy to work on in Python
To use this script, call it with a command line argument that points to the BEAM-DIMAP image
$python export_netcdf.py <image_to_export>

@author: Harry Carstairs
"""

import sys
from snappy import ProductIO as io
import glob

files = glob.glob('TDX_IFG*height_TC*.dim')

for f in files:
    meta = f.split('_')
    country = meta[2]
    mode = meta[3]
    datetime = meta[4]
    ML = meta[7]
    image = io.readProduct(f)
    orbit = str(image.getMetadataRoot()
                .getElement('CoSSC_Metadata')
                .getElement('cossc_product')
                .getElement('commonAcquisitionInfo')
                .getElement('acquisitionGeometry')
                .getAttribute('orbitDirection')
                .getData())
    
    target = '_'.join(['TDX',
                       'DEM',
                       country,
                       mode,
                       datetime,
                       orbit,
                       'ML'+ML+'.nc'])
    
    io.writeProduct(image,target,'NetCDF4-BEAM')