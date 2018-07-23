# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 20:48:37 2018

@author: elcok
"""
import os
import sys
import numpy as np
import geopandas as gpd
import pandas as pd
from rasterstats import point_query

sys.path.append(os.path.join( '..'))
from scripts.prepare import get_storm_list,load_max_dam,load_curves,load_sample,region_exposure,region_losses,poly_files
from scripts.utils import get_num,load_config
from sklearn import metrics

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from multiprocessing import Pool,cpu_count

def exposure(country, include_storms = True, parallel = True):
    """"
    Creation of exposure table of the specified country
    
    Arguments:
        country {string} -- ISO2 code of country to consider.
    
    Keyword Arguments:
        parallel {bool} -- calculates all regions within a country parallel. Set to False if you have little capacity on the machine (default: {True})
    
    Returns:
        dataframe -- pandas dataframe with all buildings of the country and potential exposure to wind
    """

    # get data path
    data_path = load_config()['paths']['data']

    # create country poly files
    poly_files(data_path,country)
    
    #get list of regions for which we have poly files (should be all) 
    regions = os.listdir(os.path.join(data_path,country,'NUTS2_POLY'))
    regions = [x.split('.')[0] for x in regions]
    
    if include_storms == True:
        storms = len(regions)*[True]
    
        if parallel == True:
            with Pool(cpu_count()-2) as pool: 
                country_table = pool.starmap(region_exposure,zip(regions,storms),chunksize=1) 
        else:
            country_table = []
            for region in regions:
                country_table.append(region_exposure(region,True))

    else:
        storms = len(regions)*[False]
    
        if parallel == True:
            with Pool(cpu_count()-2) as pool: 
                country_table = pool.starmap(region_exposure,zip(regions,storms),chunksize=1) 
        else:
            country_table = []
            for region in regions:
                country_table.append(region_exposure(region,True))

    return gpd.GeoDataFrame(pd.concat(country_table))
   
def losses(country, parallel = True, event_set = False):
    """"
    Creation of exposure table of the specified country
    
    Arguments:
        country {string} -- ISO2 code of country to consider.
    
    Keyword Arguments:
        parallel {bool} -- calculates all regions within a country parallel. Set to False if you have little capacity on the machine (default: {True})
    
    Returns:
        dataframe -- pandas dataframe with all buildings of the country and potential exposure to wind
    """

    # get data path
    data_path = load_config()['paths']['data']

    # create country poly files
    poly_files(data_path,country)
    
    #get list of regions for which we have poly files (should be all) 
    regions = os.listdir(os.path.join(data_path,country,'NUTS2_POLY'))
    regions = [x.split('.')[0] for x in regions]
    
    if event_set == False:
        event_set = len(regions)*[False]
    
        if parallel == True:
            with Pool(cpu_count()-2) as pool: 
                country_table = pool.starmap(region_losses,zip(regions,event_set),chunksize=1) 
        else:
            country_table = []
            for region in regions:
                country_table.append(region_exposure(region,True))

    elif event_set == True:
        event_set = len(regions)*[True]
    
        if parallel == True:
            with Pool(cpu_count()-2) as pool: 
                country_table = pool.starmap(region_losses,zip(regions,event_set),chunksize=1) 
        else:
            country_table = []
            for region in regions:
                country_table.append(region_exposure(region,True))

    return gpd.GeoDataFrame(pd.concat(country_table))    


def risk(country,path_to_eventset):
    """
    Estimate risk based on event set
    """
    gdf_buildings = losses(country, event_set = True)
    
    storm_name_list = [os.path.join(path_to_eventset,x) for x in os.listdir(path_to_eventset)]

    #Numpify data
    pdZ = np.array(gdf_buildings[storm_name_list],dtype=int)
    gdf_buildings.drop(storm_name_list, axis=1, inplace=True)
   
    output_ =[]
    
    for row in pdZ:
        H,X1 = np.histogram(row, bins = 100, normed = True )
        dx = X1[1] - X1[0]
        F1 = np.cumsum(np.append(0,H))*dx
        output_.append(metrics.auc(X1, F1))
    
    gdf_buildings['Risk'] = output_