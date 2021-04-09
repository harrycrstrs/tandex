# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 11:33:16 2021

@author: s1332488
"""
import xarray as xr
from datetime import datetime
import glob

def add_time(file,reference):
    ds = xr.open_dataset(file).interp_like(reference,method='linear')
    # Same spatial grid and resolution
    # Then, add the time
    time = datetime.strptime(ds.start_date,'%d-%b-%Y %H:%M:%S.%f')
    ds = ds.assign_coords(t=time)
    
    bands = list(ds.keys())
    coh = [x for x in bands if 'coh' in x][0]
    phase = [x for x in bands if 'Phase' in x]
    intensity = [x for x in bands if 'Intensity' in x]
    
    ds['height_corrected'] = ds.height_corrected.expand_dims('t')
    ds['metadata'] = ds.metadata.expand_dims('t')
    ds['localIncidenceAngle'] = ds.localIncidenceAngle.expand_dims('t')
    ds['coh'] = ds[coh].expand_dims('t')
    ds['intensity'] = ds[intensity[0]].expand_dims('t')
    ds = ds.drop(coh)
    ds = ds.drop(intensity)
    ds = ds.drop(phase)
    ds = ds.drop('height_HH')
    
    return ds

def merge(str_pattern):
    ff = [f for f in files if str_pattern in f]
    print(str_pattern)
    print('merging '+str(len(ff))+' images')
    ref = xr.open_dataset(ff[0]) 
    DS = xr.merge([add_time(f,ref) for f in ff] , compat='override')
    DS.to_netcdf(str_pattern+'_merged.nc')
    
#------------------------------------------------------------------------

files = glob.glob('*.nc')
parameter_groups = set(['_'.join(x.split('_')[0:9]) for x in files])

for p in parameter_groups:
    merge(p)

