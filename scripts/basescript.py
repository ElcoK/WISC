# -*- coding: utf-8 -*-
"""
Created on Tue Jun  5 10:41:21 2018

@author: elcok
"""

import os
from utils import load_config,create_folder_structure

from prepare import poly_files,buildings
from analyze import exposure

if __name__ == "__main__":

    # set path
    data_path = load_config()['paths']['data']
    
    # set country
    country = 'LU'
    
    create_folder_structure(data_path,country)
    
    exp_data = exposure(data_path,country,parallel=False)
    
    exp_data.to_file(os.path.join(data_path,country,'test.shp'))
    