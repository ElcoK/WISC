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

sys.path.append(os.path.join( '..'))
from scripts.functions import region_exposure,region_losses,poly_files,load_sample
from scripts.utils import load_config,download_osm_file

import country_converter as coco
cc = coco.CountryConverter()

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from multiprocessing import Pool,cpu_count

def all_countries_risk():
    """Function to estimate the risk for all countries consecutively.
    """
    # specify country
    countries = ['LU','CZ','CH','EE','LV','LT','PT','ES','AT','BE','DK','IE','NL','NO','SE','UK','PL','IT','FI','FR','DE'] 
    
    for country in countries:
        losses(country, parallel = False, event_set = True) 


def all_countries_losses():
    """Function to estimate the losses for all countries consecutively.
    """
    # specify country
    countries = ['LU','CZ','CH','EE','LV','LT','PT','ES','AT','BE','DK','IE','NL','NO','SE','UK','PL','IT','FI','FR','DE'] 
    
    for country in countries:
        losses(country, parallel = False) 
        
def all_countries_exposure():
    """Function to estimate the exposure for all countries consecutively.
    """    
    # specify country
    countries = ['LU','CZ','CH','EE','LV','LT','PT','ES','AT','BE','DK','IE','NL','NO','SE','UK','PL','IT','FI','FR','DE'] 
    
    for country in countries:    
       exposure(country, include_storms = True, parallel = False) 

def exposure(country, include_storms = True, parallel = True,save=True):
    """
    Creation of exposure table of the specified country.
    
    Arguments:
        *country* (string) -- ISO2 code of country to consider.

        *include_storms* (bool) -- if set to False, it will only return a list of buildings and their characteristics (default: **True**).

        *parallel* (bool) -- calculates all regions within a country parallel. Set to False if you have little capacity on the machine (default: **True**).

        *save* (bool) -- boolean to decide whether you want to save the output to a csv file (default: **True**).
    
    Returns:
        *GeoDataframe* -- Geopandas dataframe with all buildings of the country and potential exposure to wind
        
    """
    
    #make sure the country inserted is an ISO2 country name for he remainder of the analysis
    country = coco.convert(names=country, to='ISO2')

    # get data path
    data_path = load_config()['paths']['data']

    # create country poly files
    poly_files(data_path,country)
    
    #download OSM file if it is not there yet:
    download_osm_file(country)
    
    #get list of regions for which we have poly files (should be all) 
    regions = os.listdir(os.path.join(data_path,country,'NUTS3_POLY'))
    regions = [x.split('.')[0] for x in regions]
    
    if include_storms == True:
        storms = len(regions)*[True]
        country_list = len(regions)*[country]
    
        if parallel == True:
            with Pool(cpu_count()-2) as pool: 
                country_table = pool.starmap(region_exposure,zip(regions,country_list,storms),chunksize=1) 
        else:
            country_table = []
            for region in regions:
                country_table.append(region_exposure(region,country,True))

    else:
        storms = len(regions)*[False]
        country_list = len(regions)*[country]
    
        if parallel == True:
            with Pool(cpu_count()-2) as pool: 
                country_table = pool.starmap(region_exposure,zip(regions,country_list,storms),chunksize=1) 
        else:
            country_table = []
            for region in regions:
                country_table.append(region_exposure(region,country,True))

    if save == True:
        gdf_table  = gpd.GeoDataFrame(pd.concat(country_table),crs='epsg:4326')
        gdf_table.drop(['centroid'],axis='columns',inplace=True)
        gdf_table.to_file(os.path.join(data_path,'exposure_country',country,'{}_exposure.shp'.format(country)))
    
    return gpd.GeoDataFrame(pd.concat(country_table),crs='epsg:4326')
   
def losses(country, parallel = True, event_set = False,save=True):
    """
    Creation of exposure table of the specified country
    
    Arguments:
        *country* (string) -- ISO2 code of country to consider.
    
        *parallel* (bool) -- calculates all regions within a country parallel. Set to False if you have little capacity on the machine (default: **True**).

        *event_set* (bool) -- if set to True, we will calculate the losses for the event set instead of the historical storms (default: **True**).

        *save* (bool) -- boolean to decide whether you want to save the output to a csv file (default: **True**).
        
    Returns:
        *GeoDataframe* -- Geopandas dataframe with all buildings of the country and their **losses** for each wind storm.
        
    """

    #make sure the country inserted is an ISO2 country name for he remainder of the analysis
    country = coco.convert(names=country, to='ISO2')

    # get data path
    data_path = load_config()['paths']['data']

    # create country poly files
    poly_files(data_path,country)
    
    #download OSM file if it is not there yet:
    download_osm_file(country)

    #load sample
    sample = load_sample(country)
    
    #get list of regions for which we have poly files (should be all) 
    regions = os.listdir(os.path.join(data_path,country,'NUTS3_POLY'))
    regions = [x.split('.')[0] for x in regions]
    
    if event_set == False:
        event_set = len(regions)*[False]
        samples = len(regions)*[sample]
    
        if parallel == True:
            with Pool(cpu_count()-2) as pool: 
                country_table = pool.starmap(region_losses,zip(regions,event_set,samples),chunksize=1) 
        else:
            country_table = []
            for region in regions:
                country_table.append(region_losses(region,False,sample))

    elif event_set == True:
        event_set = len(regions)*[True]
        samples = len(regions)*[sample]
    
        if parallel == True:
            with Pool(cpu_count()-2) as pool: 
                country_table = pool.starmap(region_losses,zip(regions,event_set,samples),chunksize=1) 
        else:
            country_table = []
            for region in regions:
                country_table.append(region_losses(region,True))

    if (save == True) & (event_set == False):
        gdf_table  = gpd.GeoDataFrame(pd.concat(country_table),crs='epsg:4326',geometry='geometry')
        gdf_table.drop(['centroid'],axis='columns',inplace=True)
        gdf_table.to_file(os.path.join(data_path,'losses_country','{}_losses.shp'.format(country)))
    else:
        None
    
    return gpd.GeoDataFrame(pd.concat(country_table),crs='epsg:4326')    

def risk(country,path_to_eventset,save=True,parallel=True):
    """
    Estimate risk based on event set

    Arguments:
        *country* (string) -- ISO2 code of country to consider.
        
        *path_to_eventset* (string) -- the location of the event set in the data directory
        
        *save* (bool) -- boolean to decide whether you want to save the output to a csv file (default: **True**).
        
        *parallel* (bool) -- calculates all regions within a country parallel. Set to False if you have little capacity on the machine (default: **True**).
   
    """
    # get data path
    data_path = load_config()['paths']['data']
    
    gdf_buildings = losses(country, parallel = parallel, event_set = True, save=True)
    
    if save == True:
        gdf_buildings.drop(['centroid'],axis='columns',inplace=True)

        gdf_buildings.to_file(os.path.join(data_path,'output','risk_{}.shp'.format(country)))
    
    return gdf_buildings