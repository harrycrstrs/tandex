# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 09:25:07 2021

@author: Harry Carstairs

A simple operation to spatially subset net CDF files.
Saves a subsetted copy of each .nc file with _subset appended to its name.
"""

import xarray as xr
import glob

files = glob.glob('*.nc')

gabon = {'lat1':-0.12785363430965335,'lat2':-0.16050013350314909,'lon1':12.24259248791666899,'lon2':12.30306056704971596}
peru = {'lat1':-11.01584634449108258,'lat2':-11.04157027686576065,'lon1':-69.73351247478349535,'lon2':-69.7027921931213541}

for f in files:
    
    target = f.split('.nc')[0] + '_subset.nc'
    
    if 'GAB' in f:
        aoi = gabon
    elif 'PER' in f:
        aoi = peru
        
    with xr.open_dataset(f) as ds:
        LAT = slice(aoi.get('lat1'),aoi.get('lat2'))
        LON = slice(aoi.get('lon1'),aoi.get('lon2'))
        ds = ds.sel(lat=LAT, lon=LON)
        ds.to_netcdf(target)
        