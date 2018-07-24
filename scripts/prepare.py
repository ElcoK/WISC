# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 20:48:26 2018

@author: elcok
"""

import os
import sys
import numpy as np
import pandas as pd
import geopandas as gpd
import subprocess
import rasterio as rio
from osgeo import ogr
import shapely.wkt
from rasterstats import point_query

sys.path.append(os.path.join( '..'))
from scripts.utils import load_config,get_num

def region_exposure(region,include_storms=True,event_set=False):
    """Get exposure data for single region 
    
    Arguments:
       region {string} -- NUTS2 code of region to consider.
   
    Returns:
        GeoDataFrame -- [description]
    """    
    
    country = region[:2]
    
    data_path = load_config()['paths']['data']    
   
    osm_path = os.path.join(data_path,'OSM','{}.osm.pbf'.format(country))
    
    area_poly = os.path.join(data_path,country,'NUTS2_POLY','{}.poly'.format(region))
    area_pbf = os.path.join(data_path,country,'NUTS2_OSM','{}.osm.pbf'.format(region))
    
    clip_osm(data_path,osm_path,area_poly,area_pbf)   
    
    gdf_table = fetch_roads(data_path,country,region,regional=True)

    # convert to european coordinate system for overlap
    gdf_table = gdf_table.to_crs(epsg=3035)

    # Specify Country
    gdf_table["COUNTRY"] = country
    
    # Calculate area
    gdf_table["AREA_m2"] = gdf_table.geometry.area

    # Determine centroid
    gdf_table["centroid"] = gdf_table.geometry.centroid

    # Get land use
    nuts_eu = gpd.read_file(os.path.join(data_path,'input_data','NUTS3_ETRS.shp'))
    nuts_eu.loc[nuts_eu['NUTS_ID']==country].to_file(os.path.join(data_path,
                                country,'NUTS2_SHAPE','{}.shp'.format(country)))
    CLC_2012 = os.path.join(data_path,country,'NUTS2_LANDUSE','{}_LANDUSE.tif'.format(country))
    clip_landuse(data_path,country,CLC_2012)

    gdf_table['CLC_2012'] = point_query(list(gdf_table['centroid']),CLC_2012,nodata=-9999,interpolate='nearest')

    if (include_storms == True) & (event_set == False):
        storm_list = get_storm_list(data_path)
        for outrast_storm in storm_list:
            print(outrast_storm)
            storm_name = str(get_num(outrast_storm[-23:]))
            gdf_table[storm_name] = point_query(list(gdf_table['centroid']),outrast_storm,nodata=-9999,interpolate='nearest')        

    if (include_storms == True) & (event_set == True):
        storm_list = get_event_storm_list(data_path)
        for outrast_storm in storm_list:
            storm_name = str(get_num(outrast_storm[-23:]))
            gdf_table[storm_name] = point_query(list(gdf_table['centroid']),outrast_storm,nodata=-9999,interpolate='nearest')        


    return gdf_table        



def region_losses(region,storm_event_set=False):
    """"Estimation of the losses for all buildings in a country to the pre-defined list of storms
    
    Arguments:
        data_path {string} -- string of data path where all data is located.
        country {string} -- ISO2 code of country to consider.
    
    Keyword Arguments:
        parallel {bool} -- calculates all regions within a country parallel. Set to False if you have little capacity on the machine (default: {True})
    
    Returns:
        dataframe -- pandas dataframe with all buildings of the country and their losses for each wind storm

    """ 
    
    data_path = load_config()['paths']['data']    
    
    country = region[:2]

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
    
    output_table = region_exposure(region,include_storms=True,event_set=storm_event_set)

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

    return(gpd.GeoDataFrame(write_output))


def storm_exposure(gdf_table):
    
    data_path = load_config()['paths']['data']    
    #==============================================================================
    # Loop through storms
    #==============================================================================
    storm_list = get_storm_list(data_path)
    for outrast_storm in storm_list:
        print(outrast_storm)
        storm_name = str(get_num(outrast_storm[-23:]))
        gdf_table[storm_name] = point_query(list(gdf_table['centroid']),outrast_storm,nodata=-9999,interpolate='nearest')

    return gdf_table

def get_storm_data(storm_path):
    with rio.open(storm_path) as src:    
        # Read as numpy array
        array = src.read(1)
        array = np.array(array,dtype='float32')
        affine_storm = src.affine
    return array,affine_storm

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

def get_event_storm_list(data_path):
    storm_list = []
    for root, dirs, files in os.walk(os.path.join(data_path,'event_set')):
        for file in files:
            if file.endswith('.tif'):
                fname = os.path.join(data_path,'event_set',file)
                (filepath, filename_storm) = os.path.split(fname) 
                (fileshortname_storm, extension) = os.path.splitext(filename_storm) 
                resample_storm =  os.path.join(data_path,'event_set',fileshortname_storm+'.tif')
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

def load_osm_data(data_path,country,region='',regional=False):
    if regional==False:
        osm_path = os.path.join(data_path,'OSM','{}.osm.pbf'.format(country))
    else:
        osm_path = os.path.join(data_path,country,'NUTS2_OSM','{}.osm.pbf'.format(region))
        

    driver=ogr.GetDriverByName('OSM')
    return driver.Open(osm_path)

def fetch_roads(data_path,country,region='',regional=False):
    """
    This function directly reads the building data from osm, instead of first converting it to a shapefile
    """
    data = load_osm_data(data_path,country,region='',regional=False)
    
    sql_lyr = data.ExecuteSQL("SELECT osm_id,building,amenity from multipolygons where building is not null")
    
    roads=[]
    for feature in sql_lyr:
        if feature.GetField('building') is not None:
            osm_id = feature.GetField('osm_id')
            shapely_geo = shapely.wkt.loads(feature.geometry().ExportToWkt()) 
            if shapely_geo is None:
                continue
            highway=feature.GetField('building')
            amenity=feature.GetField('amenity')
            roads.append([osm_id,highway,amenity,shapely_geo])
    
    if len(roads) > 0:
        return gpd.GeoDataFrame(roads,columns=['osm_id','building','amenity','geometry'],crs={'init': 'epsg:4326'})
    else:
        print('No buildings in {}'.format(country))
    
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