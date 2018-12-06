# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 20:47:48 2018

@author: elcok
"""

import os
import json
import shutil
from datetime import date
import urllib.request

def load_config():
    """Read config.json
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(config_path, 'r') as config_fh:
        config = json.load(config_fh)
    return config

def clean_dir(dirpath):
    """This function can be used to fully clear a directory.
    
    Arguments:
        *dirpath* (string) -- path to directory to be cleared from files
    """
    
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename)
        try:
            shutil.rmtree(filepath)
        except OSError:
            os.remove(filepath)
            
def remove_files(dirpath,startname):
    """This function can be used to delete specific files from a directory. In 
    general this function is used to clean country files from the 'calc' directory.
    
    Arguments:
        *dirpath* (string) -- path to directory in which the files should be removed
        
        *startname* (string) -- the substring to be searched for in the files
    """
    for fname in os.listdir(dirpath):
        if fname.startswith(startname):
            os.remove(os.path.join(dirpath, fname))

def create_folder_structure(data_path,country):
    """Create the directory structure for the output.
    
    Arguments:
        *base_path (string) -- path to directory where folder structure should be created.
        
        *regionalized* (bool) -- specify whether also the folders for a regionalized analyse should be created (default: **True**)
    """
    
    data_path = load_config()['paths']['data']
    
    if not os.path.exists(os.path.join(data_path,country)):
        os.makedirs(os.path.join(data_path,country))
    if not os.path.exists(os.path.join(data_path,country,'NUTS3_SHAPE')):
        os.makedirs(os.path.join(data_path,country,'NUTS3_SHAPE'))
    if not os.path.exists(os.path.join(data_path,country,'NUTS3_OSM')):        
        os.makedirs(os.path.join(data_path,country,'NUTS3_OSM')) 
    if not os.path.exists(os.path.join(data_path,country,'NUTS3_POLY')):        
        os.makedirs(os.path.join(data_path,country,'NUTS3_POLY')) 

    if not os.path.exists(os.path.join(data_path,'exposure_country')):        
        os.makedirs(os.path.join(data_path,'exposure_country'))        
    if not os.path.exists(os.path.join(data_path,'losses_country')):        
        os.makedirs(os.path.join(data_path,'losses_country')) 
    if not os.path.exists(os.path.join(data_path,'output_exposure')):        
        os.makedirs(os.path.join(data_path,'output_exposure'))        
    if not os.path.exists(os.path.join(data_path,'output_losses')):        
        os.makedirs(os.path.join(data_path,'output_losses')) 
    if not os.path.exists(os.path.join(data_path,'output_risk')):        
        os.makedirs(os.path.join(data_path,'output_risk')) 
    if not os.path.exists(os.path.join(data_path,'output_exposure',country)):        
        os.makedirs(os.path.join(data_path,'output_exposure',country)) 
    if not os.path.exists(os.path.join(data_path,'output_losses',country)):        
        os.makedirs(os.path.join(data_path,'output_losses',country)) 
    if not os.path.exists(os.path.join(data_path,'output_risk',country)):        
        os.makedirs(os.path.join(data_path,'output_risk',country)) 
    if not os.path.exists(os.path.join(data_path,'output_sens',country)):        
        os.makedirs(os.path.join(data_path,'output_sens',country)) 

def int2date(argdate: int):
    """
    If you have date as an integer, use this method to obtain a datetime.date object.

    Arguments:
        *argdate* (int) -- Date as a regular integer value (example: **20160618**)

    Returns:
        *dateandtime.date* -- A date object which corresponds to the given value **argdate**.
    """
    year = int(argdate / 10000)
    month = int((argdate % 10000) / 100)
    day = int(argdate % 100)

    return date(year, month, day)

def get_num(x):
    """Grab all integers from string.
    
    Arguments:
        *x* (string) -- string containing integers
        
    Returns:
        *integer* -- created from string
    """
    
    return int(''.join(ele for ele in x if ele.isdigit()))

def country_dict_geofabrik():
    """ Create a dictionary to convert ISO2 codes to Geofabrik country names.
    
    Returns:
        *dictionary* -- lookup between ISO2 codes and Geofabrik country names.
    
    """
   
    countries = ['LU','CZ','CH','EE','LV','LT','PT','ES','AT','BE','DK','IE','NL','NO','SE','UK','PL','IT','FI','FR','DE'] 
    countries_geofabrik = ['luxembourg','czech-republic','switzerland','estonia','latvia','lithuania','portugal','spain',
                           'austria','belgium','denmark','ireland-and-northern-ireland','netherlands','norway','sweden',
                           'great-britain','poland','italy','finland','france','germany']

    return dict(zip(countries,countries_geofabrik))

def download_osm_file(country):
    """ Download OSM file from Geofabrik.
    
    Arguments:
        *country* (string) -- ISO2 string code of country
        
    Returns:
        *downloaded OSM file*
    """
    
    lookup = country_dict_geofabrik()
    
    data_path = load_config()['paths']['data']
    osm_path  = os.path.join(data_path,'OSM')
    osm_path_in = os.path.join(data_path,'OSM','{}.osm.pbf'.format(country) )
    
    url = 'http://download.geofabrik.de/europe/{}-latest.osm.pbf'.format(lookup[country])
    if '{}.osm.pbf'.format(country) not in os.listdir(osm_path):
                urllib.request.urlretrieve(url, osm_path_in)
