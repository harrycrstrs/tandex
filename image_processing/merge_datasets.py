# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 11:33:16 2021

@author: Harry Carstairs

This script merges phase height images of the:
     same pass;
     same number of looks;
     and same region.
(It determines this by looking for a pattern in the file names).
The result is a net CDF file where TIME is one of the dimensions.

Call this script inside the folder where the unmerged net CDF files are.
"""

import xarray as xr
from datetime import datetime
import glob

def add_time(file):
    ds = xr.open_dataset(file)
    # Same spatial grid and resolution
    # Then, add the time
    time = file.split('_')[4]
    time = datetime.strptime(time,'%Y%m%dT%H%M%S')
    ds = ds.assign_coords(t=time)
    
    ds['height'] = ds.height_HH.expand_dims('t')
    ds['metadata'] = ds.metadata.expand_dims('t')
    #ds['localIncidenceAngle'] = ds.localIncidenceAngle.expand_dims('t')
    ds['coh'] = ds.coh_HH.expand_dims('t')
    #ds['intensity'] = ds[intensity[0]].expand_dims('t')
    ds = ds.drop('Phase_HH')
    ds = ds.drop('height_HH')
    ds = ds.drop('coh_HH')
    ds = ds.drop('elevation')
    return ds

def merge(patterns):
    ff = [f for f in files if all([P in f.split('_') for P in patterns])]
    OUT = '_'.join(patterns).split('.nc')[0]+'_merged.nc'
    print('merging '+str(len(ff))+' images')
    ref = xr.open_dataset(ff[0])
    LAT,LON,ELEV = ref.lat, ref.lon, ref.elevation
    datasets = [add_time(f) for f in ff]
    datasets = [ds.interp(lat=LAT,lon=LON) for ds in datasets]
    DS = xr.merge(datasets)
    DS['elevation'] = ELEV
    DS.to_netcdf(OUT)
    
#------------------------------------------------------------------------

def get_pattern(filename):
    p = filename.split('_')
    p.pop(4)
    return p

files = glob.glob('*.nc')
parameter_groups = [list(X) for X in set(tuple(X) for X in [get_pattern(x) for x in files])]

for p in parameter_groups:
    merge(p)

