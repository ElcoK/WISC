# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 20:47:48 2018

@author: elcok
"""

import os
import json
import shutil

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