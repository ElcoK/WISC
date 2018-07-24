# -*- coding: utf-8 -*-
"""
Created on Wed Oct 26 10:00:09 2016

@author: Elco
"""

import shapefile
import os
import time
import pandas as pd
from create_table_parallel_sens import create_table
from time import strftime, localtime
import numpy as np
import shutil
from shutil import copyfile
from multiprocessing import Pool
from joblib import Parallel, delayed


curdir = os.getcwd()
drive_letter = os.path.abspath(os.sep)

#==============================================================================
# Select countries to handle and define nuts file
#==============================================================================
def run_script(country,storm_list,samples,version=None,delete=False):    
    
#==============================================================================
#    Delete folders to prevent errors in overwriting files
#==============================================================================
    if delete == True:
        shutil.rmtree(curdir+"\\%s" % (country), ignore_errors=True)

#==============================================================================
#     Create folders to write output transparently
#==============================================================================
    if not os.path.exists(curdir+"\\%s" % (country)):
        os.makedirs(curdir+"\\%s" % (country))
    if not os.path.exists(curdir+"\\%s\\NUTS2_SHAPE" % (country)):
        os.makedirs(curdir+"\\%s\\NUTS2_SHAPE" % (country))        
    if not os.path.exists(curdir+"\\%s\\NUTS2_OUTPUT" % (country)):
        os.makedirs(curdir+"\\%s\\NUTS2_OUTPUT" % (country))
    if not os.path.exists(curdir+"\\%s\\NUTS2_LANDUSE" % (country)):
        os.makedirs(curdir+"\\%s\\NUTS2_LANDUSE" % (country))        


    #==============================================================================
    # Load some required data
    #==============================================================================
    max_dam = pd.read_excel('max_dam.xlsx')
    
    country = str(country)
    if version is None:
        version = ''
    etrs = curdir+"\\%s\\BUILDINGS\\%s_buildings%s.shp" % (country,country,version)
    r = shapefile.Reader(curdir+"/NUTS3_ETRS/NUTS3_ETRS.shp")


#==============================================================================
#     Define raster input           
#==============================================================================
    inraster = curdir+"\\EUROPE_CORINE\\g100_clc12_V18_5.tif"   

##==============================================================================
##             Reproject to combine landuse with buildings in following steps
##==============================================================================
    etrs = "F:\\Dropbox\\WISC\\country_buildings\\%s\\%s_buildings.shp" % (country,country)

 
#==============================================================================
#     Create list of regions and prepare parallel computing
#==============================================================================
    NUTS_REGION = []
    country_list = []    
    inraster_list = []
    storm_list_for_pool = []
    buildings_gp_list = []
    max_dam_list = []
    samples_list = []
    for rec in enumerate(r.records()):
        w = shapefile.Writer(shapeType=shapefile.POLYGON)
        # Copy the fields to the writer
        w.fields = list(r.fields) 
        if rec[1][2].startswith(country) and len(rec[1][2])==5 and version is '':
            w._shapes.append(r.shape(rec[0]))
            w.records.append(rec[1])

            # Save the new shapefile
            w.save(curdir+"\\%s\\NUTS2_SHAPE\\%s" % (country,rec[1][2]))
            copyfile(curdir+"\\3035.prj",curdir+"\\%s\\NUTS2_SHAPE\\%s.prj" % (country,rec[1][2]))    

            # also create country list for parallel computing
            NUTS_REGION.append(rec[1][2])
            country_list.append(country)
            inraster_list.append(inraster)
            storm_list_for_pool.append(storm_list)
            buildings_gp_list.append(etrs)
            max_dam_list.append(max_dam)
            samples_list.append(samples)
               # Save the new shapefile
            w.save(curdir+"\\%s\\NUTS2_SHAPE\\%s" % (country,rec[1][2]))
            copyfile(curdir+"\\3035.prj",curdir+"\\%s\\NUTS2_SHAPE\\%s.prj" % (country,rec[1][2]))
        elif rec[1][2].startswith(country) and len(rec[1][2])==5 and any(i in version for i in rec[1][2][2]):

            w._shapes.append(r.shape(rec[0]))
            w.records.append(rec[1])

            # Save the new shapefile
            w.save(curdir+"\\%s\\NUTS2_SHAPE\\%s" % (country,rec[1][2]))
            copyfile(curdir+"\\3035.prj",curdir+"\\%s\\NUTS2_SHAPE\\%s.prj" % (country,rec[1][2]))    

            # also create country list for parallel computing
            NUTS_REGION.append(rec[1][2])
            country_list.append(country)
            inraster_list.append(inraster)
            storm_list_for_pool.append(storm_list)
            buildings_gp_list.append(etrs)
            max_dam_list.append(max_dam)
            samples_list.append(samples)
##=============================================================================
## And create the table
##=============================================================================

#    num_cores = 4
#    output_sens = Parallel(n_jobs=num_cores)(delayed(create_table)(country,i,max_dam,inraster,storm_list,etrs,samples) for i in NUTS_REGION)

#        pool = multiprocessing.Pool()
#        results = np.fromiter(pool.map(_parallel_match, args))
    
    
    pool = Pool(4)
    output = pool.starmap(create_table, zip(country_list,NUTS_REGION,max_dam_list,inraster_list,storm_list_for_pool,buildings_gp_list,samples_list)) 
    pool.close() 
    pool.join() 


    return output
#    end = time.time()
#    print(str(country) + ' took ' + str(np.float16((end - start1)/60)) + " minutes to finish. \
#    The time of finish is " + strftime("%Y-%m-%d %H:%M:%S", localtime()))  
