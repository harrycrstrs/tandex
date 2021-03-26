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
import datetime

# Where are the interferograms stored?
IFG_DIR = '/disk/scratch/local.4/harry/interferograms/useful/'

# Where are you going to do your working?
WOR_DIR = '/disk/scratch/local/harry/temp/'

# parameters - each row in parameter csv file must contain values for the following
param_names = ['ifg',                  # full path to xml file (str)
               'Nlooks',                 # Window size (az?) for multilooking (int)
               'use_filter',             # T to use Goldstein Phase filtering, F otherwise
               'unw_method',             # unwrapping criteria: T,D,S or N (see snaphu docs)
               'height_method',          # H for 'phase to height', E for 'phase to elevation (see SNAP docs)
               'target_folder']          # full path to output directory (str)  

unw_dict = {'T':'TOPO','D':'DEFO','S':'SMOOTH','N':'NOSTATCOSTS'} 

def pprint(x):
    print('*************')
    print(x,flush=True)

def bash(cmd):
    """
    Send cmd to the terminal 
    Return 1 if nonzero exit code
    """
    print('Running command ------' ,flush=True)
    print(cmd ,flush=True)
    print('-------------' ,flush=True)
    exitcode = os.system(cmd)
    if exitcode != 0:
        pprint('NONZERO EXIT CODE: '+str(exitcode) )
        return 1
    else:
        return 0

def check_p(params):
    """
    Ensures input parameters all make sense
    Takes a row from the parameter dataframe
    Returns a list of issues (of length 0 if none)
    """
    issues = []
    if path.exists(IFG_DIR+params.ifg) == False:
        issues.append( 'interfergoram not found' )
    if type(params.Nlooks) != int:
        issues.append( 'Nlooks not an integer' )
    elif (params.Nlooks < 1):
        issues.append('Nlooks must be 1 or more')
    if not (params.use_filter in ['T','F']):
        issues.append('use_filter must be T or F')
    if not (params.unw_method in ['T','D','S','N']):
        issues.append('unw_method must be T,D,S or N')
    if not (params.height_method in ['E','H']):
        issues.append('height_method must be E or H')
    if not path.exists(params.target_folder):
        try: os.makedirs(params.target_folder)
        except: issues.append('unable to create target folder')
    return issues

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
    df = pd.read_csv(param_file,names=param_names,header=0)
    for _,row in df.iterrows():
        issues = check_p(row)
        if len(issues) > 0 :
            pprint(issues)
            raise Exception('Problem with parameters - see above')
        else:
            pass
    return df

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
    
    ifg is in format 
        TDX_IFG_[GAB/PER]_[SM/HS]_YYYYMMDDTHHMMSS.dim
    
    Returns : path of output file according to the naming convention:
        TDX_DEM_[GAB/PER]_ML$$_f[T/F]_unw#_[H/E]_YYYYMMDDTHHMMSS.dim
        $$ is number of looks for phase
        [T/F] is T if filtering applied
        # is T,D,S, or N depending on unwrapping method
        [H/E] is H for height method, E for elevation method
    """
    country_mode = params.ifg.split('_')[2] + '_' + params.ifg.split('_')[3]
    date = params.ifg.split('.')[0].split('_')[-1]
    ml,fil,unw = str(params.Nlooks),params.use_filter,params.unw_method
    hmethod = params.height_method
    outfile = 'TDX_DEM_'+country_mode+'_ML'+ml+'_f'+fil+'_unw'+unw+'_'+hmethod+'_'+date+'.dim'
    
    return path.join(params.target_folder,outfile)

def multilook(image,Nlooks):
    pprint('Multi-looking' )
    p = HashMap()
    p.put('nRgLooks', Nlooks)
    return GPF.createProduct('Multilook',p,image)

def goldstein(image):
    pprint('Phase Filtering')
    p = HashMap()
    return GPF.createProduct('GoldsteinPhaseFiltering',p,image)

def snaphu_unwrapping(ifg,unw_method):
    pprint('Beginning snaphu_unwrapping' )
    export_dir = path.join(WOR_DIR,'snaphuExport/')
    snaphu_dir = path.join(export_dir,ifg.split('.')[0].split('/')[-1])
    # -----------------------Clear up any old snaphuexports first!
    os.chdir(snaphu_dir)
    pprint('**Current Working Directory: '+ os.getcwd())
    pprint('Clearing snaphuExport directory' )
    bash('rm -r *')
    # ---------------------------Run snaphu export command
    exitcode = bash(' '.join(['gpt',
                        'SnaphuExport',
                        '-PtargetFolder=' + export_dir,
                        '-PstatCostMode=' + unw_method,
                        '-PnumberOfProcessors=12',
                        '-PnumberOfTileCols=1',
                        '-PnumberOfTileRows=1',
                        #'-ProwOverlap=300',
                        #'-PcolOverlap=300',
                        ifg]))
    if exitcode == 1:
        return 'SnaphuExport FAILURE'
    else:
        pass
    #------------------- Extract snaphu unwrapping command
    with open('snaphu.conf','r') as file:
        line = file.readlines()[6]
        cmd = ' '.join(line.split()[1:])
    exitcode = bash(cmd)
    if exitcode == 1:
        return 'SNAPHU UNWRAPPING FAIL'
    else:
        pass
    # ----------------------------Snaphu Import
    unwrapped_phase = glob.glob('./UnwPhase*.hdr')[0]
    pprint('Reading Unwrapped phase as: ' )
    pprint(unwrapped_phase )
    exitcode = bash(' '.join(['gpt',
                        'SnaphuImport',
                        ifg,
                        unwrapped_phase]))
    if exitcode == 1:
        return 'SNAPHU IMPORT FAIL'
    else:
        pass
    pprint('Reading in target.dim' )
    product = ProductIO.readProduct('target.dim')
    return product

def get_elevation(phase):
    pprint('Getting elevation' )
    p = HashMap()
    p.put('demName','SRTM 1Sec HGT')
    return GPF.createProduct('phaseToElevation',p,phase)

def get_height(phase):
    pprint('Getting height' )
    p = HashMap()
    return GPF.createProduct('phaseToHeight',p,phase)

def terrain_cor(image):
    pprint('Performing Terrain Correction' )
    p = HashMap()
    p.put('alignToStandardGrid','true')
    p.put('demName','SRTM 1Sec HGT')
    p.put('saveDEM','true')
    p.put('saveLocalIncidenceAngle','true')
    return GPF.createProduct('Terrain-Correction',p,image)

def create_DEM(params):
    """
    params: set of parameters, given as row of dataframe (see get_params())
    
    This is the main function, and results in a terrain corrected DEM
    
    If everything runs smoothly, then it returns the time taken to process (str)
    If there is an error with any of the snaphu commands, it returns a
    description of where the error occured (str)

    """
    pprint('Starting inteferogram file: '+params.ifg )
    startT = datetime.datetime.now()
    pprint('Time now: '  +datetime.datetime.strftime(startT,'%d/%m %H%M') )
    # ------------------------------------------
    ifg_file = path.join(IFG_DIR,params.ifg)
    temp_file = path.join(WOR_DIR,'TDX_IFG_TEMP.dim')
    # ------------------------------------------
    
    pprint('Reading Interferogram' )
    image = ProductIO.readProduct(ifg_file)
    image = multilook(image,params.Nlooks)
    
    if params.use_filter == 'T':
        image = goldstein(image)
    else:
       pass

    pprint('Writing product to '+temp_file )
    ProductIO.writeProduct(image,temp_file,'BEAM-DIMAP' )

    pprint('Time Elapsed on this product: '+str(datetime.datetime.now() - startT))
    
    image = snaphu_unwrapping(temp_file,unw_dict.get(params.unw_method))
    
    if type(image) == str: # If there was a failure in the unwrapping
        return image
    else:
        pass
    
    pprint('Time Elapsed on this product' )
    pprint(str(datetime.datetime.now() - startT) )
    
    if params.height_method == 'H':
        image = get_height(image)
    else:
        image = get_elevation(image)
        
    
    
    image = terrain_cor(image)
    
    pprint('Writing product to '+target_file(params) )
    ProductIO.writeProduct(image,target_file(params),'BEAM-DIMAP')
    
    T = str(datetime.datetime.now() - startT)
    pprint('Total Time Elapsed on this product: ' +T)
    return T
    

#-----------------------------------#
# Main program
#-----------------------------------#

def main():
    t = datetime.datetime.strftime(datetime.datetime.now(),'%d/%m %H%M')
    pprint('Program started' )
    pprint(t )
    pprint('.......................' )
    
    with open('summary_file.txt','a') as summary_file:
        summary_file.write('-------PROGRAM START------------- \n')
        summary_file.write(t +' \n')
        
        for _,row in get_params().iterrows():
            summary_file.write('-------------PARAMS---------------- \n')
            summary_file.write(str(row)+'\n')
            summary_file.write('---Result (exit code if fail or time taken) \n')
            
            summary_file.write(create_DEM(row)+'\n') # where it all happens
            
        summary_file.write('-------PROGRAM END------------- \n')
        t = datetime.datetime.strftime(datetime.datetime.now(),'%d/%m %H%M')
        summary_file.write(t + ' \n')
        
main()