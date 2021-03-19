# -*- coding: utf-8 -*-
"""
Created on Thu Mar 18 09:11:00 2021

@author: s1332488

Code for producing DEMs from TanDEM-X images 
"""

# IMPORTS
from snappy import ProductIO
from snappy import GPF
from snappy import HashMap
import sys
import os.path as path
import os
import pandas as pd
import glob

# parameters - each row in parameter csv file must contain values for the following
param_names = ['image',                  # full path to xml file (str)
               'AOI',                    # WKT of polygon of interest (str)
               'NlooksCoh',              # Window size for coherence estimation (int)
               'Nlooks',                 # Window size (az?) for multilooking (int)
               'use_filter',             # T to use Goldstein Phase filtering, F otherwise
               'unw_method',             # unwrapping criteria: T,D,S or N (see snaphu docs)
               'height_method',          # H for 'phase to height', E for 'phase to elevation (see SNAP docs)
               'target_folder']          # full path to output directory (str)  

unw_dict = {'T':'TOPO','D':'DEFO','S':'SMOOTH','N':'NOSTATCOSTS'} 

def get_params():
    """
    Reads from csv file with each row containing the parameters required for a DEM
    The columns of the csv file should match the param_names defined in this code
    Returns: pandas dataframe
    """
    try:
        param_file = sys.argv[1]
    except:
        param_file = ' '
    while path.exists(param_file) == False:
        param_file = input('Please provide valid path to the parameter file: ')
    
    return pd.read_csv(param_file,names=param_names,header=0)

def shape(product):
    """
    Convenience method for getting the shape of a product in SNAP
    (Not currently used but left for reference)
    """
    band = product.getBandAt(0)
    return band.getRasterWidth(), band.getRasterHeight()

def target_file(params):
    """
    params : a single row of the dataframe produced by get_params()
    
    Returns : path of output file according to the naming convention:
        TDX_DEM_COH**_ML$$_f[T/F]_unw#_[H/E]_YYYYMMDDTHHMMSS.dim
        where ** is number of looks for coherence
        $$ is number of looks for phase
        [T/F] is T if filtering applied
        # is T,D,S, or N depending on unwrapping method
        [H/E] is H for height method, E for elevation method
    """
    date = params.image.split('/')[-1].split('.')[0].split('_')[-1]
    coh = str(params.NlooksCoh)
    ml,fil,unw = str(params.Nlooks),params.use_filter,params.unw_method
    hmethod = params.height_method
    outfile = 'TDX_DEM_COH'+coh+'_ML'+ml+'_f'+fil+'_unw'+unw+'_'+hmethod+'_'+date
    return path.join(params.target_folder,outfile)

def copy_to_SSD(image_path):
    """

    Parameters
    ----------
    image_path : string
        path to tandem-X xml file 

    Returns
    -------
    outfile : path to image, stored in local SSD using BEAM-DIMAP format

    """
    TEMP_DIR = '/disk/scratch/local/harry/temp/' # SSD for fast reading 
    outfile = TEMP_DIR + image_path.split('/')[-1].split('.')[0] + '.dim'
    if path.exists(outfile) == False:
        img = ProductIO.readProduct(image_path)
        ProductIO.writeProduct(img, outfile, 'BEAM-DIMAP')
    else: # Skips this step if file already exists
        print('***')
        print(image_path.split('/')[0])
        print('[Subset already copied to local]')
        print('***')
    return outfile 

def interferogram(image,NlooksCoh):
    p = HashMap()
    p.put('cohWinRg',NlooksCoh)
    return GPF.createProduct('Interferogram',p,image)

def multilook(image,Nlooks):
    p = HashMap()
    p.put('nRgLooks', Nlooks)
    return GPF.createProduct('Multilook',p,image)

def goldstein(image):
    p = HashMap()
    return GPF.createProduct('GoldsteinPhaseFiltering',p,image)

def snaphu_unwrapping(ifg,unw_method):
    export_dir = '/disk/scratch/local/harry/temp/snaphuExport/'
    export = '-PtargetFolder='+export_dir
    snaphu_dir = path.join(export_dir,ifg.split('.')[0].split('/')[-1])
    unw_method = '-PstatCostMode=' + unw_method
    # ---------------------------Run snaphu export command
    os.system(' '.join(['gpt',
                        'SnaphuExport',
                        export,
                        unw_method,
                        ifg]))
    #------------------- Extract snaphu unwrapping command
    os.chdir(snaphu_dir)
    print('**Current Working Directory**')
    print(os.getcwd())
    with open('snaphu.conf','r') as file:
        line = file.readlines()[6]
        cmd = ' '.join(line.split()[1:])
    os.system(cmd)
    # ----------------------------Snaphu Import
    unwrapped_phase = glob.glob('./UnwPhase*.hdr')[0]
    os.system(' '.join(['gpt',
                        'SnaphuImport',
                        ifg,
                        unwrapped_phase]))
    return ProductIO.readProduct('target.dim')

def get_elevation(phase):
    p = HashMap()
    p.put('demName','SRTM 1Sec HGT')
    return GPF.createProduct('phaseToElevation',p,phase)

def get_height(phase):
    p = HashMap()
    return GPF.createProduct('phaseToHeight',p,phase)

def terrain_cor(image):
    p = HashMap()
    p.put('alignToStandardGrid','true')
    p.put('demName','SRTM 1Sec HGT')
    p.put('saveDEM','true')
    p.put('saveLocalIncidenceAngle','true')
    return GPF.createProduct('Terrain-Correction',p,image)

def create_DEM(params):
    """
    params: set of parameters, given as row of dataframe (see get_params())
    
    This is the main function.

    """
    ifg_file = '/disk/scratch/local/harry/temp/INTERFEROGRAM.dim'
    file = copy_to_SSD(params.image)
    image = ProductIO.readProduct(file)
    image = interferogram(image,params.NlooksCoh)
    image = multilook(image,params.Nlooks)
    if params.use_filter == 'T':
        image = goldstein(image)
    else:
       pass
    ProductIO.writeProduct(image,ifg_file,'BEAM-DIMAP')
    image = snaphu_unwrapping(ifg_file,unw_dict.get(params.unw_method))
    if params.height_method == 'H':
        image = get_height(image)
    else:
        image = get_elevation(image)
    image = terrain_cor(image)
    ProductIO.writeProduct(image,target_file(params)+'_DEM_TC.dim','BEAM-DIMAP')
    

#-----------------------------------#
# Main program
#-----------------------------------#

for _,row in get_params().iterrows():
    create_DEM(row)
