# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 20:48:37 2018

@author: elcok
"""
import os
import numpy as np
import geopandas as gpd
from rasterstats import point_query,zonal_stats


from prepare import buildings,get_storm_list,clip_landuse
from utils import get_num

def exposure(data_path,country, parallel = True):
    """
    """

    input_ = buildings(country,parallel=False)
    input_["RISK_ID"] = np.empty
    input_["COUNTRY"] = np.empty
    input_["CLC_2012"] = np.zeros
    input_["AREA_m2"] = np.zeros

    #==============================================================================
    # Fill table
    #==============================================================================

    #SPECIFY COUNTRY
    input_["COUNTRY"] = country
    
    #CREATE RISK_ID
    input_["RISK_ID"] = [str(input_.index)+'_'+str(x) for x in input_.NUTS2_ID]

    #CALCULATE AREA
    input_["AREA_m2"] = input_.geometry.area

    # GET LAND USE
    nuts_eu = gpd.read_file(os.path.join(data_path,'input_data','NUTS3_ETRS.shp'))
    nuts_eu.loc[nuts_eu['NUTS_ID']==country].to_file(os.path.join(data_path,
                                country,'NUTS2_SHAPE','{}.shp'.format(country)))

    CLC_2012 = os.path.join(data_path,country,'NUTS2_LANDUSE','{}_LANDUSE.tif'.format(country))
    clip_landuse(data_path,country,CLC_2012)

    input_['CLC_2012'] = [x['median'] for x in zonal_stats(input_, CLC_2012,stats="median",nodata=-9999)]

    #==============================================================================
    # Loop through storms
    #==============================================================================

    storm_list = get_storm_list()
#    input_ = pd.Dataframe(input_)
    for outrast_storm in storm_list[:2]:
        storm_name = str(get_num(outrast_storm[-23:]))
        input_[storm_name] = [x['mean'] for x in zonal_stats(input_, outrast_storm,stats="mean",nodata=-9999)]

    return input_

    
def losses(country,regionalized = True):
    """
    """
    
def risk(country):
    """
    """