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
from scripts.utils import get_num,load_config,download_osm_file
from sklearn import metrics

import country_converter as coco
cc = coco.CountryConverter()

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from multiprocessing import Pool,cpu_count

def all_countries_losses():
    
    # specify country
    countries = ['LU','CZ','CH','EE','LV','LT','PT','ES','AT','BE','DK','IE','NL','NO','SE','UK','PL','IT','FI','FR','DE'] 
    
    for country in countries:
        losses(country, include_storms = True, parallel = False) 
        
def all_countries_exposure():
    
    # specify country
    countries = ['LU','CZ','CH','EE','LV','LT','PT','ES','AT','BE','DK','IE','NL','NO','SE','UK','PL','IT','FI','FR','DE'] 
    
#    countries_append = []
    for country in countries:    
       exposure(country, include_storms = True, parallel = False) 
        

def exposure(country, include_storms = True, parallel = True,save=True):
    """"
    Creation of exposure table of the specified country
    
    Arguments:
        country {string} -- country to consider.
    
    Keyword Arguments:
        parallel {bool} -- calculates all regions within a country parallel. Set to False if you have little capacity on the machine (default: {True})
    
    Returns:
        dataframe -- pandas dataframe with all buildings of the country and potential exposure to wind
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

    if save == True:
        gdf_table  = gpd.GeoDataFrame(pd.concat(country_table),crs='epsg:4326')
        gdf_table.drop(['centroid'],axis='columns',inplace=True)

        gdf_table.to_file(os.path.join(data_path,'output','exposure_{}.shp'.format(country)))
    
    return gpd.GeoDataFrame(pd.concat(country_table),crs='epsg:4326')
   
def losses(country, parallel = True, event_set = False,save=True):
    """"
    Creation of exposure table of the specified country
    
    Arguments:
        country {string} -- country to consider.
    
    Keyword Arguments:
        parallel {bool} -- calculates all regions within a country parallel. Set to False if you have little capacity on the machine (default: {True})
    
    Returns:
        dataframe -- pandas dataframe with all buildings of the country and potential exposure to wind
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
                country_table.append(region_losses(region,False))

    elif event_set == True:
        event_set = len(regions)*[True]
    
        if parallel == True:
            with Pool(cpu_count()-2) as pool: 
                country_table = pool.starmap(region_losses,zip(regions,event_set),chunksize=1) 
        else:
            country_table = []
            for region in regions:
                country_table.append(region_losses(region,True))

    if save == True:
        gdf_table  = gpd.GeoDataFrame(pd.concat(country_table),crs='epsg:4326')
        gdf_table.drop(['centroid'],axis='columns',inplace=True)

        gdf_table.to_file(os.path.join(data_path,'output','losses_{}.shp'.format(country)))
    
    return gpd.GeoDataFrame(pd.concat(country_table),crs='epsg:4326')    


def risk(country,path_to_eventset,save=True):
    """
    Estimate risk based on event set
    """
    # get data path
    data_path = load_config()['paths']['data']
    
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
    
    if save == True:
        gdf_buildings.drop(['centroid'],axis='columns',inplace=True)

        gdf_buildings.to_file(os.path.join(data_path,'output','risk_{}.shp'.format(country)))
    
    return gdf_buildings