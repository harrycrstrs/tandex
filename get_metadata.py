# -*- coding: utf-8 -*-
"""
Created on Tue Mar 30 13:25:34 2021

@author: s1332488

This script uses Snappy to extract the metadata from TDX interferograms

Takes one command line argument - the directory containing the interferograms

Assumes GAB or PER in file names to indicate location

"""

from snappy import ProductIO, HashMap, GPF
import glob
import sys
import os
import pandas as pd
import math

IFG_DIR = sys.argv[1]
os.chdir(IFG_DIR)
ifgs = glob.glob('*.dim')

attributes = ['file',
            'country',
            'date',
            'time',
            'imaging_mode',
            'covers_core_plots',
            'baseline',
            'orbit_direction',
            'height_of_ambiguity',
            'vertical_wavenumber',
            'incidence_angle',
            'bandwidth']
            #'range_res',
            #'azimuth_res',
            #'range_pixel',
            #'azimuth_pixel']

def check_coverage(file,p):
    if 'GAB' in file:
        region = 'POLYGON((12.24885799008746368 -0.14350824099999146, 12.24885110630293283 -0.14259615803456555, 12.24975595848531107 -0.14259626696242139, 12.24975584715663501 -0.14353065658873754, 12.24885799008746368 -0.14350824099999146))'
    elif 'PER' in file:
        region = 'POLYGON((-69.72334001018973026 -11.0329910794429793, -69.72334358246895647 -11.03207312025939579, -69.72240573287906784 -11.0320753572009469, -69.7224080470953993 -11.03302282454907512, -69.72334001018973026 -11.0329910794429793))'
    params = HashMap()
    params.put('geoRegion',region)
    
    fail = 'Empty' in GPF.createProduct('Subset',params,p).getName()
    return not fail

df = pd.DataFrame( columns = attributes )    

for file in ifgs:
    p = ProductIO.readProduct(file)
    MD = dict()
    MD['file'] = file
    if 'GAB' in file:
        MD['country'] = 'Gabon'
    elif 'PER' in file:
        MD['country'] = 'Peru'
    else:
        print('Country not identified')
    cossc = p.getMetadataRoot().getElement('CoSSC_Metadata').getElement('cossc_product')
    datetime = str(cossc.getElement('CommonAcquisitionInfo').getElement('acquisitionMode').getAttribute('datatakeStartTime').getData())
    MD['date'] = datetime.split('T')[0]
    MD['time'] = datetime.split('T')[1]
    MD['imaging_mode'] = str(cossc.getElement('commonAcquisitionInfo').getElement('acquisitionMode').getAttribute('imagingMode').getData())
    MD['covers_core_plots'] = str(check_coverage(file,p))
    MD['baseline'] = float(str(cossc.getElement('commonAcquisitionInfo').getElement('acquisitionGeometry').getAttribute('effectiveBaseline').getData()))
    MD['orbit_direction'] = str(cossc.getElement('commonAcquisitionInfo').getElement('acquisitionGeometry').getAttribute('orbitDirection').getData())
    HoA = float(str(cossc.getElement('commonAcquisitionInfo').getElement('acquisitionGeometry').getAttribute('heightOfAmbiguity').getData()))
    k = 2 * math.pi / HoA
    MD['height_of_ambiguity'] = HoA
    MD['vertical_wavenumber'] = k
    MD['incidence_angle'] = float(str(cossc.getElement('commonSceneInfo').getElement('sceneCenterCoord').getAttribute('incidenceAngle').getData()))
    MD['bandwidth'] = str(cossc.getElement('CommonAcquisitionInfo').getElement('acquisitionMode').getElement('rangeBandwidthClass').getAttribute('rgBW').getData())
    df = df.append(pd.Series(MD),ignore_index=True)

df.to_csv('metadata.csv')
# Done!



    
    

