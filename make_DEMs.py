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
from snappy import ProductUtils
import sys
import os.path as path
import os
import pandas as pd
import glob
import datetime

# Where are the interferograms stored?
IFG_DIR = '/disk/scratch/local.4/harry/interferograms/'

# Where are you going to do your working?
WOR_DIR = '/disk/scratch/local/harry/temp/'

# Areas to crop to (needs a better long-term solution)
aoi_g = 'POLYGON((12.24259248791666899 -0.12970155056629756, 12.29813277791832959 -0.12785363430965335, 12.30306056704971596 -0.15772826280552016, 12.24259248791666899 -0.16050013350314909, 12.24259248791666899 -0.12970155056629756))'
aoi_p = 'POLYGON((-69.73323900046604251 -11.01624899728848916, -69.7027921931213541 -11.01584634449108258, -69.70283777217426291 -11.04080977551521237, -69.73351247478349535 -11.04157027686576065, -69.73323900046604251 -11.01624899728848916))'

# parameters - each row in parameter csv file must contain values for the following
param_names = ['ifg',                    # full path to xml file (str)
               'Nlooks',                 # Window size (az?) for multilooking (int)
               'removeTOPO',             # Remove topographic phase of SRTM (T/F)
               'use_filter',             # T to use Goldstein Phase filtering, F otherwise
               'unw_method',             # unwrapping criteria: T,D,S (see snaphu docs)
               'tiles',                  # Number of tiles (rows/cols) to chunk data into for unwrapping
               'height_method',          # H for 'phase to height', E for 'phase to elevation (see SNAP docs)
               'target_folder']          # full path to output directory (str)  

unw_dict = {'T':'TOPO','D':'DEFO','S':'SMOOTH'} 

def pprint(x): 
    # flush print with spacing to monitor progress via logfile
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
    if not (params.unw_method in ['T','D','S']):
        issues.append('unw_method must be T,D, or S')
    if not (params.height_method in ['E','H']):
        issues.append('height_method must be E or H')
    if not path.exists(params.target_folder):
        try: os.makedirs(params.target_folder)
        except: issues.append('unable to create target folder')
    if (type(params.tiles) != int) or params.tiles < 1:
        issues.append('Number of tiles must be positive integer')
    if not (params.removeTOPO in ['T','F']):
        issues.append('remove TOPO must be T or F')
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
    return df

def get_overlap(product,params):
    x,y = shape(product)
    x /= (params.Nlooks * params.tiles)
    y /= (params.Nlooks * params.tiles)
    x_overlap = int(0.35 * x)
    y_overlap = int(0.35 *y)
    return (x_overlap, y_overlap)

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
        TDX_DEM_[GAB/PER]_ML$$_f[T/F]_unw#_[H/E]_tiles%%__YYYYMMDDTHHMMSS.dim
        $$ is number of looks for phase
        [T/F] is T if filtering applied
        # is T,D,S, or N depending on unwrapping method
        [H/E] is H for height method, E for elevation method
        %% is number of tiles (sqrt of) used for unwrapping
        ££ is pixel overlapp
    """
    parts = ['TDX','DEM']
    parts.append(params.ifg.split('_')[2]) # country
    parts.append(params.ifg.split('_')[3]) # mode
    parts.append('ML'+str(params.Nlooks))  # multilooks
    parts.append('f'+params.use_filter)    # filtering
    parts.append('unw'+params.unw_method)  # unwrapping
    parts.append(params.height_method)     # height conversion method
    parts.append('tiles'+str(params.tiles))# number of unwrapping tiles
    parts.append(params.ifg.split('.')[0].split('_')[-1]) # finally, the datetime
    # Now put an underscore between each element
    outfile = '_'.join(parts) + '.dim'
    return path.join(params.target_folder,outfile)

def crop(image,ifg):
    p = HashMap()
    if 'GAB' in ifg:
        pprint('Cropping to GABON AOI')
        aoi = aoi_g
    elif 'PER' in ifg:
        pprint('Cropping to PERU AOI')
        aoi = aoi_p
    else:
        print('Cannot identify country')
    p.put('geoRegion',aoi)
    p.put('copyMetadata','true')
    return GPF.createProduct('Subset',p,image)
    

def multilook(image,Nlooks):
    pprint('Multi-looking' )
    p = HashMap()
    p.put('nRgLooks', Nlooks)
    return GPF.createProduct('Multilook',p,image)

def goldstein(image):
    pprint('Phase Filtering')
    p = HashMap()
    return GPF.createProduct('GoldsteinPhaseFiltering',p,image)

def snaphu_unwrapping(ifg,unw_method,tiles,overlap):
    pprint('Beginning snaphu_unwrapping' )
    export_dir = path.join(WOR_DIR,'snaphuExport/')
    snaphu_dir = path.join(export_dir,ifg.split('.')[0].split('/')[-1])
    # -----------------------Clear up any old snaphuexports first!
    try:
        os.chdir(snaphu_dir)
        bash('rm -r *')
    except:
        os.mkdir(snaphu_dir)
        os.chdir(snaphu_dir)
    # ---------------------------Run snaphu export command
    cmd_list = ['gpt',
                'SnaphuExport',
                '-PtargetFolder=' + export_dir,
                '-PstatCostMode=' + unw_method,
                '-PnumberOfProcessors=12',
                '-PnumberOfTileCols='+str(tiles),
                '-PnumberOfTileRows='+str(tiles)]
    if tiles != 1:
        cmd_list.append('-ProwOverlap='+str(overlap[0]))
        cmd_list.append('-PcolOverlap='+str(overlap[1]))
    cmd_list.append(ifg)
    exitcode = bash(' '.join(cmd_list))
    if exitcode == 1:
        return 'SnaphuExport FAILURE'
    #------------------- Extract snaphu unwrapping command
    with open('snaphu.conf','r') as file:
        line = file.readlines()[6]
        cmd = ' '.join(line.split()[1:]) #+['-S']??
    exitcode = bash(cmd)
    if exitcode == 1:
        return 'SNAPHU UNWRAPPING FAIL'
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
    pprint('Reading in target.dim' )
    product = ProductIO.readProduct('target.dim')
    return product

def get_elevation(phase):
    pprint('Getting elevation' )
    p = HashMap()
    p.put('demName','SRTM 1Sec HGT')
    elv = GPF.createProduct('phaseToElevation',p,phase)
    band = list(elv.getBandNames())[0]
    ProductUtils.copyBand(band,elv,'elevation',phase,True)
    return phase

def get_height(phase):  
    pprint('Getting height' )
    p = HashMap()
    height = GPF.createProduct('phaseToHeight',p,phase)
    band = list(height.getBandNames())[0]
    ProductUtils.copyBand(band,height,'height',phase,True)
    return phase
 
def terrain_cor(image):
    pprint('Performing Terrain Correction' )
    p = HashMap()
    p.put('alignToStandardGrid','true')
    p.put('demName','SRTM 1Sec HGT')
    p.put('saveDEM','true')
    p.put('saveLocalIncidenceAngle','true')
    return GPF.createProduct('Terrain-Correction',p,image)

def topo_removal(image):
    pprint('Topographic Removal')
    p = HashMap()
    p.put('demName','SRTM 1Sec HGT')
    result = GPF.createProduct('TopoPhaseRemoval',p,image)
    # Write to temporary file
    ProductIO.writeProduct(result,path.join(WOR_DIR,'removed_SRTM'),'BEAM-DIMAP')
    return ProductIO.readProduct(path.join(WOR_DIR,'removed_SRTM.dim'))

def create_DEM(params):
    """
    params: set of parameters, given as row of dataframe (see get_params())
    
    This calls the processing steps defined above to create a DEM according to those parameters
    
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
    target = target_file(params)
    # ------------------------------------------
    if not os.path.exists(target): # If not already completed
    
        pprint('Reading Interferogram' )
        image = ProductIO.readProduct(ifg_file)
        overlap = get_overlap(image, params)
        
        if params.removeTOPO == 'T':
            image = topo_removal(image)
        image = multilook(image,params.Nlooks)
        
        if params.use_filter == 'T':
            image = goldstein(image)
    
        pprint('Writing product to '+temp_file )
        ProductIO.writeProduct(image,temp_file,'BEAM-DIMAP' )
        pprint('Time Elapsed on this product: '+str(datetime.datetime.now() - startT))
        image = snaphu_unwrapping(temp_file,
                                  unw_dict.get(params.unw_method),
                                  params.tiles,
                                  overlap)
        if type(image) == str: # If there was a failure in the unwrapping
            return image
        
        pprint('Time Elapsed on this product' )
        pprint(str(datetime.datetime.now() - startT) )
        
        if params.height_method == 'H':
            image = get_height(image)
        else:
            image = get_elevation(image)
            
        image = terrain_cor(image)
        
        pprint('Writing product to '+target)
        ProductIO.writeProduct(image,target,'BEAM-DIMAP')
    
    else:
        return 'Skipped as target file already existed'
    
    # Writes cropped tif version too just for fun
    image = crop(image,params.ifg)
    ProductIO.writeProduct(image,target.split('.dim')[0]+'_subset','GEOTIFF')
    
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
    pprint(sys.argv[1])
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