# -*- coding: utf-8 -*-
"""
Created on Mon Apr 26 13:54:35 2021

@author: Harry Carstairs

Call this script in folder containing interferograms (with flat earth but not topographic phase removed)
It will simply save a copy of each interferogram with SRTM phase removed

"""

from snappy import ProductIO, HashMap, GPF
import glob

def topo_removal(file):
    image = ProductIO.readProduct(file)
    p = HashMap()
    p.put('demName','SRTM 1Sec HGT')
    result = GPF.createProduct('TopoPhaseRemoval',p,image)
    # Write to temporary file
    outfile = file.split('.dim')[0] + '_noSRTM.dim'
    ProductIO.writeProduct(result,outfile,'BEAM-DIMAP')
    
files = glob.glob('TDX_IFG*.dim')

for file in files:
    print('Topographic Removal: ',file)
    print('********')
    topo_removal(file)
    
print('Done')