# -*- coding: utf-8 -*-
"""
Created on Mon Sep 17 19:37:33 2018

@author: cenv0574
"""

import os
import sys
import country_converter as coco
cc = coco.CountryConverter()

# make connection to all the scripts
sys.path.append(os.path.join( '..'))
from scripts.utils import load_config,create_folder_structure
from scripts.analyze import losses

if __name__ == '__main__': 

    # make connection to the data paths
    data_path = load_config()['paths']['data']
    storms_path =  load_config()['paths']['hazard_data']    
    
    # set country
    country = 'LU'
    
    #set folder structure for calculation
    create_folder_structure(data_path,country)
    
    # and estimate losses
    losses(country, parallel = True, event_set = False,save=True)
    
    