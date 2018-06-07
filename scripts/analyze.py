# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 20:48:37 2018

@author: elcok
"""
import os
import numpy as np
import geopandas as gpd
import pandas as pd
from rasterstats import point_query
import time

from prepare import buildings,get_storm_list,clip_landuse,load_max_dam,load_curves,load_sample
from utils import get_num

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def exposure(data_path,country, parallel = True):
    """"
    Creation of exposure table of the specified country
    
    Arguments:
        data_path {string} -- string of data path where all data is located.
        country {string} -- ISO2 code of country to consider.
    
    Keyword Arguments:
        parallel {bool} -- calculates all regions within a country parallel. Set to False if you have little capacity on the machine (default: {True})
    
    Returns:
        dataframe -- pandas dataframe with all buildings of the country and potential exposure to wind
    """

    input_ = buildings(country,parallel=False)

    #==============================================================================
    # Fill table
    #==============================================================================

    # Specify Country
    input_["COUNTRY"] = country
    
    # Calculate area
    input_["AREA_m2"] = input_.geometry.area

    # Determine centroid
    input_["centroid"] = input_.geometry.centroid

    # Get land use
    nuts_eu = gpd.read_file(os.path.join(data_path,'input_data','NUTS3_ETRS.shp'))
    nuts_eu.loc[nuts_eu['NUTS_ID']==country].to_file(os.path.join(data_path,
                                country,'NUTS2_SHAPE','{}.shp'.format(country)))

    CLC_2012 = os.path.join(data_path,country,'NUTS2_LANDUSE','{}_LANDUSE.tif'.format(country))
    clip_landuse(data_path,country,CLC_2012)

    input_['CLC_2012'] = point_query(list(input_['centroid']),CLC_2012,nodata=-9999,interpolate='nearest')
    
    print('Finished coupling land-use to buildings for {}'.format(country))
    #==============================================================================
    # Loop through storms
    #==============================================================================
    storm_list = get_storm_list(data_path)
    for outrast_storm in storm_list:
        storm_name = str(get_num(outrast_storm[-23:]))
        input_[storm_name] = point_query(list(input_['centroid']),outrast_storm,nodata=-9999,interpolate='nearest')

    print('Finished the exposure table for {}'.format(country))
    
    return input_

    
def losses(data_path,country,parallel = True,storm_event_set=False):
    """"Estimation of the losses for all buildings in a country to the pre-defined list of storms
    
    Arguments:
        data_path {string} -- string of data path where all data is located.
        country {string} -- ISO2 code of country to consider.
    
    Keyword Arguments:
        parallel {bool} -- calculates all regions within a country parallel. Set to False if you have little capacity on the machine (default: {True})
    
    Returns:
        dataframe -- pandas dataframe with all buildings of the country and their losses for each wind storm

    """ 
    
    start = time.time()


    #load storms
    if storm_event_set == False:
        storm_list = get_storm_list(data_path)
        storm_name_list = [str(get_num(x[-23:])) for x in storm_list]
    else:
        None

    #load max dam
    max_dam = load_max_dam(data_path)
  
    #load curves
    curves = load_curves(data_path)

    #load sample
    sample = load_sample(country)
    
    output_table = exposure(data_path,country, parallel = False)

    no_storm_columns = list(set(output_table.columns).difference(list(storm_name_list)))
    write_output = pd.DataFrame(output_table[no_storm_columns])

    for storm in storm_name_list:
    ##==============================================================================
    ## Calculate losses for buildings in this NUTS region
    ##==============================================================================
        max_dam_country = np.asarray(max_dam[max_dam['CODE'].str.contains(country)].iloc[:,1:],dtype='int16')    
    
        df_C2 = pd.DataFrame(output_table[['AREA_m2','CLC_2012',storm]])
        df_C3 = pd.DataFrame(output_table[['AREA_m2','CLC_2012',storm]])
        df_C4 = pd.DataFrame(output_table[['AREA_m2','CLC_2012',storm]])
    
        df_C2[storm+'_curve'] = df_C2[storm].map(curves['C2']) 
        df_C3[storm+'_curve'] = df_C3[storm].map(curves['C3'])
        df_C4[storm+'_curve'] = df_C4[storm].map(curves['C4']) 
     
        #specify shares for urban and nonurban        
        RES_URB = 1 - sample[3]/100 
        IND_URB = sample[3]/100   
    
        RES_NONURB = 0.5
        IND_NONURB = 0.5
    
        # Use pandas where to fill new column for losses
        df_C2['Loss'] = np.where(df_C2['CLC_2012'].between(0,12, inclusive=True), (df_C2['AREA_m2']*df_C2[storm+'_curve']*max_dam_country[0,0]*RES_URB+df_C2['AREA_m2']*df_C2[storm+'_curve']*max_dam_country[0,2]*IND_URB)*(sample[0]/100), 0)
        df_C2['Loss'] = np.where(df_C2['CLC_2012'].between(13,23, inclusive=True), (df_C2['AREA_m2']*df_C2[storm+'_curve']*max_dam_country[0,0]*RES_NONURB+df_C2['AREA_m2']*df_C2[storm+'_curve']*max_dam_country[0,2]*IND_NONURB)*(sample[0]/100),df_C2['Loss'])
    
        df_C3['Loss'] = np.where(df_C3['CLC_2012'].between(0,12, inclusive=True), (df_C3['AREA_m2']*df_C3[storm+'_curve']*max_dam_country[0,0]*RES_URB+df_C3['AREA_m2']*df_C3[storm+'_curve']*max_dam_country[0,2]*IND_URB)*(sample[1]/100), 0)
        df_C3['Loss'] = np.where(df_C3['CLC_2012'].between(13,23, inclusive=True), (df_C3['AREA_m2']*df_C3[storm+'_curve']*max_dam_country[0,0]*RES_NONURB+df_C3['AREA_m2']*df_C3[storm+'_curve']*max_dam_country[0,2]*IND_NONURB)*(sample[1]/100),df_C3['Loss'])
    
        df_C4['Loss'] = np.where(df_C4['CLC_2012'].between(0,12, inclusive=True), (df_C4['AREA_m2']*df_C4[storm+'_curve']*max_dam_country[0,0]*RES_URB+df_C4['AREA_m2']*df_C4[storm+'_curve']*max_dam_country[0,2]*IND_URB)*(sample[2]/100), 0)
        df_C4['Loss'] = np.where(df_C4['CLC_2012'].between(13,23, inclusive=True), (df_C4['AREA_m2']*df_C4[storm+'_curve']*max_dam_country[0,0]*RES_NONURB+df_C4['AREA_m2']*df_C4[storm+'_curve']*max_dam_country[0,2]*IND_NONURB)*(sample[2]/100),df_C4['Loss'])

#        # and write output                    
        write_output[storm] = (df_C2['Loss'].fillna(0).astype(int) + df_C3['Loss'].fillna(0).astype(int) + df_C4['Loss'].fillna(0).astype(int))

    print('Finished estimating the losses for {}'.format(country))

    end = time.time()

    print('{} took {} minutes to finish.'.format(country,str(np.float16((end - start)/60))))


    return(gpd.GeoDataFrame(write_output))
    """
    """
    
def risk(country):
    """
    """