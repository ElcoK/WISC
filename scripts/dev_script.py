# -*- coding: utf-8 -*-
"""
Created on Mon Jul 23 12:14:10 2018

@author: cenv0574
"""

import os
from osgeo import ogr
import shapely.wkt
import geopandas as gpd
from rasterstats import point_query

from utils import load_config,create_folder_structure
from prepare import poly_files,clip_osm,clip_landuse,fetch_roads

        
if __name__ == "__main__": 

    country = 'LU'
   
    region = 'LU00'
    

