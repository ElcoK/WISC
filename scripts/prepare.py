# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 20:48:26 2018

@author: elcok
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
from scripts.utils import load_config

def extract_buildings(area):
    """

    """
    # get data path
    data_path = load_config()['paths']['data']

    wgs = os.path.join(data_path,area,'BUILDINGS','{}_buildings_wgs.shp'.format(area))
    pbf = os.path.join(data_path,'OSM','{}.osm.pbf'.format(area))

    os.system('ogr2ogr -progress -f "ESRI shapefile" {} {} -sql "select \
              building,amenity from multipolygons where building is not null" \
              -lco ENCODING=UTF-8 -nlt POLYGON -skipfailures'.format(wgs,pbf))

def convert_buildings(area):
    """

    """    
    # get data path
    data_path = load_config()['paths']['data']

    etrs = os.path.join(data_path,area,'BUILDINGS','{}_buildings.shp'.format(area))
    wgs_nuts = os.path.join(data_path,area,'BUILDINGS','{}_buildings_wgs.shp'.format(area))
    
    os.system('ogr2ogr -f "ESRI Shapefile" {} {} -s \
              srs \EPSG:4326 -t_srs EPSG:3035'.format(etrs,wgs_nuts))
    
def get_storm_list():
    """
    
    """
    # get data path
    data_path = load_config()['paths']['data']

    EXTENSION = ('.tif')
    storm_list = []
    for root, dirs, files in os.walk(os.path.join(data_path,'STORMS')):
        for file in files:
            if file.endswith(EXTENSION):
                fname = os.path.join(data_path,'STORMS',file)
                (filepath, filename_storm) = os.path.split(fname) 
                (fileshortname_storm, extension) = os.path.splitext(filename_storm) 
                resample_storm =  os.path.join(data_path,'STORMS',fileshortname_storm+'.tif')
                storm_list.append(resample_storm)    

    return storm_list

def load_max_dam():
    """
    
    """
     # get data path
    data_path = load_config()['paths']['data']
   
    return pd.read_excel(os.path.join(data_path,'input_data','max_dam.xlsx'))


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
    poly_dir = os.path.join(data_path,country,'poly_files')
        
    if not os.path.exists(poly_dir):
        os.makedirs(poly_dir)

# =============================================================================
#   """Load country shapes and country list and only keep the required countries"""
# =============================================================================
    wb_poly = gpd.read_file(os.path.join(data_path,'input_data','NUTS3_ETRS.shp'))
    
    # filter polygon file
    country_poly = wb_poly.loc[(wb_poly['NUTS_ID'].apply(lambda x: x.startswith(country))) & (wb_poly['STAT_LEVL_']==2)]

    country_poly.crs = {'init' :'epsg:4326'}
    
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