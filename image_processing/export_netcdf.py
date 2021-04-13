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

file = sys.argv[1]
image = io.readProduct(file)
target = file.split('.dim')[0]+'.nc'
io.writeProduct(image,target,'NetCDF4-BEAM')