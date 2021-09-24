# -*- coding: utf-8 -*-

"""
Created on Mon Mar 22 2021

@author: Harry Carstairs

Code for producing Interferograms from TanDEM-X images 

Takes one command line argument: filename of a text file where each line is the 
    path to a TDX COSSC image (xml file)
    
Each COSSC image is processed in turn and saved with a customised name to the location
    specified by OUT_FOLDER
"""

from snappy import ProductIO
from snappy import GPF
from snappy import HashMap
import sys
import os.path as path

# OUT_FOLDER set to storage place of interferograms
OUT_FOLDER = '/disk/scratch/local.4/harry/interferograms/'
# STORAGE_DIR set to storage place of COSSC images (top of the file structure)
STORAGE_DIR = '/disk/scratch/local.4/harry/'


def ifg_file(TDX_path):
    """
    TDX_path: string - path to TDX cossc image
    Returns the customised path of the interferogram 
    Here format is TDX_IFG_[GAB/PER]_[SM/HS]_YYYYMMDDTHHMMSS.dim
    where GAB/PER refer to country, SM = stripmap and HS = high res,
    and the datetime of the start of the acquisition follows.
    """
    country_mode = TDX_path.split('/')[5].split('_')
    country,mode = country_mode[0], country_mode[1]
    if country == 'Gabon':
        country = 'GAB'
    elif country == 'Peru':
        country = 'PER'
    else:
        raise 'Country not recognised'
    datetime = TDX_path.split('/')[-1].split('_')[-2]
    
    OUT_FILE = '_'.join(['TDX','IFG',country,mode,datetime])+'.dim'
    return OUT_FOLDER + OUT_FILE

def do_ifg(path):
    """
    Takes filepath of TDX xml file
    Uses snappy to create interferogram 
    Add in parameters to p if required (see gpt Interferogram -h for details)
    """
    target = ifg_file(path)
    image = ProductIO.readProduct(path)
    p = HashMap()
    image = GPF.createProduct('Interferogram',p,image)
    ProductIO.writeProduct(image,target,'BEAM-DIMAP')
    
# Here is the main program----------------------------------------

with open(sys.argv[1],'r') as file:
    COSSC_list = file.readlines()
    N = len(COSSC_list)
    print('Processing '+str(N)+' TDX images')
    print('Starting...')
    for i in range(N):
        print('***')
        print('Calculating Interferogram '+str(i+1)+' of '+str(N))
        try: 
            cossc = path.join(STORAGE_DIR,COSSC_list[i][2:-1])
            do_ifg(cossc) # here is where it happens
        except:
            print(cossc)
            print(path.exists(cossc))
            print('UNSUCCESSFUL')  
        
        print('*************')
        print('[DONE]')
        print('*************')
    