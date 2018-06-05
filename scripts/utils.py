# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 20:47:48 2018

@author: elcok
"""

import os
import json
import shutil
from datetime import date

def load_config():
    """Read config.json
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(config_path, 'r') as config_fh:
        config = json.load(config_fh)
    return config

def clean_dir(dirpath):
    """"This function can be used to fully clear a directory
    
    Arguments:
        dirpath {string} -- path to directory to be cleared from files
    """
    
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename)
        try:
            shutil.rmtree(filepath)
        except OSError:
            os.remove(filepath)
            
def remove_files(dirpath,startname):
    """This function can be used to delete specific files from a directory. In 
    general this function is used to clean country files from the 'calc' directory
    
    Arguments:
        dirpath {string} -- path to directory in which the files should be removed
        startname {string} -- the substring to be searched for in the files
    """
    for fname in os.listdir(dirpath):
        if fname.startswith(startname):
            os.remove(os.path.join(dirpath, fname))

def create_folder_structure(data_path,country):
    """Create the directory structure for the output
    
    Arguments:
        base_path {string} -- path to directory where folder structure should be created 
    
    Keyword Arguments:
        regionalized {bool} -- specify whether also the folders for a regionalized analyse should be created (default: {True})
    """
    
    data_path = load_config()['paths']['data']
    
    if not os.path.exists(os.path.join(data_path,'{}'.format(country))):
        os.makedirs(os.path.join(data_path,'{}'.format(country)))
    if not os.path.exists(os.path.join(data_path,'{}'.format(country),'NUTS2_SHAPE')):
        os.makedirs(os.path.join(data_path,'{}'.format(country)),'NUTS2_SHAPE')
    if not os.path.exists(os.path.join(data_path,'{}'.format(country),'NUTS2_OUTPUT')):
        os.makedirs(os.path.join(data_path,'{}'.format(country)),'NUTS2_OUTPUT')
    if not os.path.exists(os.path.join(data_path,'{}'.format(country),'NUTS2_LANDUSE')):        
        os.makedirs(os.path.join(data_path,'{}'.format(country)),'NUTS2_LANDUSE')        

def int2date(argdate: int):
    """
    If you have date as an integer, use this method to obtain a datetime.date object.

    Parameters
    ----------
    argdate : int
      Date as a regular integer value (example: 20160618)

    Returns
    -------
    dateandtime.date
      A date object which corresponds to the given value `argdate`.
    """
    year = int(argdate / 10000)
    month = int((argdate % 10000) / 100)
    day = int(argdate % 100)

    return date(year, month, day)


def get_num(x):
    return int(''.join(ele for ele in x if ele.isdigit()))
