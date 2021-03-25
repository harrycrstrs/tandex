# -*- coding: utf-8 -*-
"""
Created on Tue Mar 23 09:07:10 2021

@author: s1332488
"""

from snappy import ProductIO
from snappy import HashMap
from snappy import GPF
import glob
import os

aoi_g = 'POLYGON((12.24259248791666899 -0.12970155056629756, 12.29813277791832959 -0.12785363430965335, 12.30306056704971596 -0.15772826280552016, 12.24259248791666899 -0.16050013350314909, 12.24259248791666899 -0.12970155056629756))'
aoi_p = 'POLYGON((-69.73323900046604251 -11.01624899728848916, -69.7027921931213541 -11.01584634449108258, -69.70283777217426291 -11.04080977551521237, -69.73351247478349535 -11.04157027686576065, -69.73323900046604251 -11.01624899728848916))'
dem_DIR = '/disk/scratch/local.4/harry/test/'
subset_DIR = dem_DIR+'subset/'

os.chdir(dem_DIR)
files = glob.glob('*.dim')

for file in files:
    p = HashMap()
    
    if 'GAB' in file:
        aoi = aoi_g
    elif 'PER' in file:
        aoi = aoi_p
    else:
        print('Cannot identify country')
        
    p.put('geoRegion',aoi)
    p.put('copyMetadata','true')
    #p.put('sourceBands','elevation_HH')
    img = ProductIO.readProduct(file)
    subset = GPF.createProduct('Subset',p,img)
    ProductIO.writeProduct(subset,file.split('.')[0]+'_subset','GEOTIFF')