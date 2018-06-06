# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 20:48:26 2018

@author: elcok
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import subprocess
from multiprocessing import Pool,cpu_count

from utils import load_config

def buildings(country, parallel = True):
    """[summary]
    
    Arguments:
       country {string} -- ISO2 code of country to consider.
    
    Keyword Arguments:
       parallel {bool} -- [description] (default: {True})
    
    Returns:
        [type] -- [description]
    """
    
    # get data path
    data_path = load_config()['paths']['data']

    # create country poly files
    poly_files(data_path,country)
    
    #get list of regions for which we have poly files (should be all) 
    regions = os.listdir(os.path.join(data_path,country,'NUTS2_POLY'))
    regions = [x.split('.')[0] for x in regions]
    
    # set path of osm countr file:
    osm_path = os.path.join(data_path,'OSM','{}.osm.pbf'.format(country))
    
    if parallel == True:
        None
    else:
        country_table = []
        for region in regions:
            region_poly = os.path.join(data_path,country,'NUTS2_POLY','{}.poly'.format(region))
            region_pbf = os.path.join(data_path,country,'NUTS2_OSM','{}.osm.pbf'.format(region))
            
            # clip osm to nuts2 region
            clip_osm(data_path,osm_path,region_poly,region_pbf)
    
            # extract buildings for the region
            extract_buildings(region,country)            
            
            # convert buildings to epsg:3035, making it compatible with landuse maps
            nuts2_buildings = convert_buildings(region,country)
            nuts2_buildings['NUTS2_ID'] = region
            country_table.append(nuts2_buildings)
    
    country_table = gpd.GeoDataFrame(pd.concat(country_table))
    
    return country_table


def extract_buildings(area,country,nuts2=True):
    """[summary]
    
    Arguments:
        area {[type]} -- [description]
        country {string} -- ISO2 code of country to consider.
    
    Keyword Arguments:
        nuts2 {bool} -- [description] (default: {True})
    
    """
    # get data path
    data_path = load_config()['paths']['data']

    wgs = os.path.join(data_path,country,'NUTS2_BUILDINGS','{}_buildings.shp'.format(area))
    if nuts2 == True:
        pbf = os.path.join(data_path,country,'NUTS2_OSM','{}.osm.pbf'.format(area))
    else:
        pbf = os.path.join(data_path,'OSM','{}.osm.pbf'.format(area))
  
    os.system('ogr2ogr -progress -f "ESRI shapefile" {} {} -sql "select \
              building,amenity from multipolygons where building is not null" \
              -lco ENCODING=UTF-8 -nlt POLYGON -skipfailures'.format(wgs,pbf))

def convert_buildings(area,country):
    """Converts the coordinate system from EPSG:4326 to EPSG:3035.

    Arguments:
        area {string} -- name of area (most often NUTS2) for which buildings should be converted to European coordinate system 

        country {string} -- ISO2 code of country to consider.

    Returns:
        geodataframe -- Geopandas dataframe with all buildings of the selected area
    """
    # get data path
    data_path = load_config()['paths']['data']

    # path to area with buildings
    etrs = os.path.join(data_path,country,'NUTS2_BUILDINGS','{}_buildings.shp'.format(area))

    # load data 
    input_ = gpd.read_file(etrs)

    input_ = input_.to_crs(epsg=3035)

    return input_
    
def get_storm_list(data_path):
    """Small function to create a list of with path strings to all storms
    
    Arguments:
        data_path {string} -- string of data path where all data is located.

    Returns:
        list -- list with the path strings of all storms
    """
   
    storm_list = []
    for root, dirs, files in os.walk(os.path.join(data_path,'STORMS')):
        for file in files:
            if file.endswith('.tif'):
                fname = os.path.join(data_path,'STORMS',file)
                (filepath, filename_storm) = os.path.split(fname) 
                (fileshortname_storm, extension) = os.path.splitext(filename_storm) 
                resample_storm =  os.path.join(data_path,'STORMS',fileshortname_storm+'.tif')
                storm_list.append(resample_storm)    

    return storm_list

def load_max_dam(data_path):
    """Small function to load the excel with maximum damages.
    
    Arguments:
        data_path {string} -- string of data path where all data is located.

    Returns:
        dataframe -- pandas dataframe with maximum damages per landuse
    """

    return pd.read_excel(os.path.join(data_path,'input_data','max_dam2.xlsx'))


def load_curves(data_path):
    """Small function to load the csv file with the different fragility curves.
    
    Arguments:
        data_path {string} -- string of data path where all data is located.

    Returns:
        dataframe -- pandas dataframe with fragility curves
    """

    return pd.read_csv(os.path.join(data_path,'input_data','CURVES.csv'),index_col=[0],names=['C1','C2','C3','C4','C5','C6'])


def load_sample(country):
    """Will load the ratio of each curve and landuse to be used.
    
    Arguments:
        country {string} -- ISO2 code of country to consider.

    Returns:
        tuple -- tuple of ratios for the selected country
    """

    dict_  = dict([('AT', ( 5, 0,95,20)), 
                         ('BE', ( 0,45,55,50)), 
                         ('DK', ( 0,20,80,20)),
                         ('FR', (10,50,40,20)), 
                         ('DE', ( 5,75,20,50)),
                         ('IE', (35,65, 0,30)), 
                         ('LU', (50,50, 0,20)),
                         ('NL', ( 0,45,55,20)), 
                         ('NO', (0,100, 0,20)),
                         ('SE', ( 0,10,90,50)),
                         ('UK', ( 5,30,65,50))])

    return dict_[country]
    
def poly_files(data_path,country):

    """
    This function will create the .poly files from the nuts shapefile. These
    .poly files are used to extract data from the openstreetmap files.
    
    This function is adapted from the OSMPoly function in QGIS.
    
    Arguments:
        data_path: base path to location of all files.
        
        country: string name of country ISO2.
   
    Returns:
        .poly file for each nuts2 in a new dir in the working directory.
    """     
   
# =============================================================================
#     """ Create output dir for .poly files if it is doesnt exist yet"""
# =============================================================================
    poly_dir = os.path.join(data_path,country,'NUTS2_POLY')
        
    if not os.path.exists(poly_dir):
        os.makedirs(poly_dir)

# =============================================================================
#   """Load country shapes and country list and only keep the required countries"""
# =============================================================================
    wb_poly = gpd.read_file(os.path.join(data_path,'input_data','NUTS3_ETRS.shp'))
    
    # filter polygon file
    country_poly = wb_poly.loc[(wb_poly['NUTS_ID'].apply(lambda x: x.startswith(country))) & (wb_poly['STAT_LEVL_']==2)]

    country_poly.crs = {'init' :'epsg:3035'}

    country_poly = country_poly.to_crs({'init': 'epsg:4326'})
    
# =============================================================================
#   """ The important part of this function: create .poly files to clip the country 
#   data from the openstreetmap file """    
# =============================================================================
    num = 0
    # iterate over the counties (rows) in the world shapefile
    for f in country_poly.iterrows():
        f = f[1]
        num = num + 1
        geom=f.geometry

#        try:
        # this will create a list of the different subpolygons
        if geom.geom_type == 'MultiPolygon':
            polygons = geom
        
        # the list will be lenght 1 if it is just one polygon
        elif geom.geom_type == 'Polygon':
            polygons = [geom]

        # define the name of the output file, based on the ISO3 code
        attr=f['NUTS_ID']
        
        # start writing the .poly file
        f = open(poly_dir + "/" + attr +'.poly', 'w')
        f.write(attr + "\n")

        i = 0
        
        # loop over the different polygons, get their exterior and write the 
        # coordinates of the ring to the .poly file
        for polygon in polygons:
            polygon = np.array(polygon.exterior)

            j = 0
            f.write(str(i) + "\n")

            for ring in polygon:
                j = j + 1
                f.write("    " + str(ring[0]) + "     " + str(ring[1]) +"\n")

            i = i + 1
            # close the ring of one subpolygon if done
            f.write("END" +"\n")

        # close the file when done
        f.write("END" +"\n")
        f.close()

def clip_landuse(data_path,country,outrast_lu):
    """Clip the landuse from the European Corine Land Cover (CLC) map to the considered country
    
    Arguments:
        data_path {string} -- string of data path where all data is located.
        country {string} -- ISO2 code of country to consider.
        outrast_lu {string} -- string path to location of Corine Land Cover dataset 
    """
    
    inraster = os.path.join(data_path,'input_data','g100_clc12_V18_5.tif')
    
    inshape = os.path.join(data_path,country,'NUTS2_SHAPE','{}.shp'.format(country))
   
    subprocess.call(["gdalwarp","-q","-overwrite","-srcnodata","-9999","-co","compress=lzw","-tr","100","-100","-r","near",inraster, outrast_lu, "-cutline", inshape,"-crop_to_cutline"])
 
    

def clip_osm(data_path,osm_path,area_poly,area_pbf):
    """ Clip the an area osm file from the larger continent (or planet) file and save to a new osm.pbf file. 
    This is much faster compared to clipping the osm.pbf file while extracting through ogr2ogr.
    
    This function uses the osmconvert tool, which can be found at http://wiki.openstreetmap.org/wiki/Osmconvert. 
    
    Either add the directory where this executable is located to your environmental variables or just put it in the 'scripts' directory.
    
    Arguments:
        osm_path: path string to the osm.pbf file of the continent associated with the country.
        
        area_poly: path string to the .poly file, made through the 'create_poly_files' function.
        
        area_pbf: path string indicating the final output dir and output name of the new .osm.pbf file.
        
    Returns:
        a clipped .osm.pbf file.
    """ 
    print('{} started!'.format(area_pbf))

    osm_convert_path = os.path.join(data_path,'osmconvert','osmconvert64')
    try: 
        if (os.path.exists(area_pbf) is not True):
            os.system('{}  {} -B={} --complete-ways -o={}'.format(osm_convert_path,osm_path,area_poly,area_pbf))
        print('{} finished!'.format(area_pbf))

    except:
        print('{} did not finish!'.format(area_pbf))