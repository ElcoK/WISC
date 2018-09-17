# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 14:18:26 2018

@author: cenv0574
"""

from SALib.sample import latin
from SALib.analyze import delta

import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
import numpy as np
from multiprocessing import Pool,cpu_count

sys.path.append(os.path.join( '..'))
from scripts.functions import region_sens_analysis,poly_files
from scripts.utils import load_config,download_osm_file

import country_converter as coco
cc = coco.CountryConverter()

matplotlib.style.use('ggplot')

matplotlib.rcParams['font.size'] = 14.
matplotlib.rcParams['font.family'] = 'tahoma'
matplotlib.rcParams['axes.labelsize'] = 14.
matplotlib.rcParams['xtick.labelsize'] = 12.
matplotlib.rcParams['ytick.labelsize'] = 12.


def calculate(country,parallel=True,save=True):

    # set data path    
    data_path = load_config()['paths']['data']
    
    #make sure the country inserted is an ISO2 country name for he remainder of the analysis
    country = coco.convert(names=country, to='ISO2')

    # get data path
    data_path = load_config()['paths']['data']

    # create country poly files
    poly_files(data_path,country)
    
    #download OSM file if it is not there yet:
    download_osm_file(country)

    samples,storm_list = prepare_sens_analysis()

    #get list of regions for which we have poly files (should be all) 
    regions = os.listdir(os.path.join(data_path,country,'NUTS2_POLY'))
    regions = [x.split('.')[0] for x in regions]
    
    if parallel == True:
        samples = len(regions)*[samples]
        storms = len(regions)*[storm_list]
        save = len(regions)*[save]
        
        with Pool(cpu_count()-2) as pool: 
            country_table = pool.starmap(region_sens_analysis,zip(regions,samples,storms,save),chunksize=1) 
    else:
        country_table = []
        for region in regions:
            country_table.append(region_sens_analysis(region,samples,storms,save))
    
    return country_table            
                
def prepare_sens_analysis(storm_name_list=[]):
    
    data_path = load_config()['paths']['data']
    
    # set parameters for sensitivity analysis
    problem = {
        'num_vars': 5,
        'names': ['c2', 'c3', 'c4','lu1','lu2'],
        'bounds': [[0, 100],
                   [0, 100],
                   [0, 100],
                   [0,50],
                   [0,50]]}

    param_values = latin.sample(problem,5000)

    # rescale parameters for vulnerability curves (should add up to 100)    
    rescale = param_values[:,:3]
    for i in range(len(rescale)):
        inb = (rescale[i]*100)/sum(rescale[i])
        param_values[i,:3] = inb
    
   
    # select storms to assess
    if len(storm_name_list) == 0:
        storm_name_list = ['19991203','19900125','20090124','20070118','19991226']

    storm_list = []
    for root, dirs, files in os.walk(os.path.join(data_path,'STORMS')):
        for file in files:
            for storm in storm_name_list:
                if storm in file:
                    storm_list.append(os.path.join(data_path,'STORMS',file))
                    
    return param_values,storm_name_list


def read_outcomes_sens_analysis():
    
    # load some basics
    data_path = load_config()['paths']['data']
    
    # specify country
    countries = ['LU','CZ','CH','EE','LV','LT','PT','ES','AT','BE','DK','IE','NL','NO','SE']

       # done: LU 
    country_full_names =    {
    'CZ': 'Czech Republic', 
    'CH': 'Switzerland', 
    'EE': 'Estonia', 
    'LV': 'Latvia', 
    'LT': 'Lithuania', 
    'PT': 'Portugal', 
    'ES': 'Spain', 
    'AT': 'Austria', 
    'BE': 'Belgium', 
    'DK': 'Denmark', 
    'LU': 'Luxembourg', 
    'NL': 'Netherlands', 
    'IE': 'Ireland', 
    'UK': 'United Kingdom',
    'NO': 'Norway',
    'SE': 'Sweden'}

    storms = {
              '19991203':'Anatol',
              '19900125':'Daria',
              '20090124':'Klaus',
              '20070118':'Kyrill',
              '19991226':'Lothar'
              }
       
    # set parameters for sensitivity analysis
    problem = {
        'num_vars': 5,
        'names': ['c2', 'c3', 'c4','lu1','lu2'],
        'bounds': [[0, 100],
                   [0, 100],
                   [0, 100],
                   [0,50],
                   [0,50]]}


    # select storms to assess
    storm_name_list = ['19991203','19900125','20090124','20070118','19991226']
    storm_list = []
    for root, dirs, files in os.walk(os.path.join(data_path,'STORMS')):
        for file in files:
            for storm in storm_name_list:
                if storm in file:
                    storm_list.append(os.path.join(data_path,'STORMS',file))

    for country in countries:
        dirlist = os.listdir(os.path.join(data_path,'output_sens'))
        country_list  = [ x for x in dirlist if country in x]
        k = 0

        for i in range(int(len(country_list)/2)):
            if i < 1:
                out = pd.read_csv(os.path.join(data_path,'output_sens',country_list[k],index_col=0))   
            else:
                out2 = (os.path.join(data_path,'output_sens',country_list[k],index_col=0)) .fillna(0)    
                out += out2
            k += 2  
        param_values = pd.read_csv(os.path.join(data_path,'output_sens',country_list[1]),delim_whitespace=True, header=None)
        
        #Estimate outcome of sensitvity analysis    
        param_values = np.asarray(param_values)
        for l in range(5):
            try:
                storm = np.asarray(out.ix[:,l])
                Si = delta.analyze(problem, param_values, storm , print_to_console=True)
    
                # create histogram                
                plt.hist(storm, bins='auto', ec="k", lw=0.1)   
                plt.autoscale(tight=True)
                plt.title(country_full_names[country]+', '+storms[out.ix[:,l].name])
                plt.ylabel('Frequency')
                plt.xlabel('Total damage in Million Euro')
                plt.savefig(os.path.join(data_path,'Figures',country+'_'+storms[out.ix[:,l].name]+'.png'),dpi=300)
                plt.clf()
                
                # create pie chart
                delta_ = (Si['delta'])/sum(Si['delta'])*100
                colors = ['yellowgreen', 'gold', 'lightskyblue', 'lightcoral','peru']
                labels = ['c2', 'c3', 'c4','lu1','lu2']
                patches, texts = plt.pie(delta_, colors=colors, startangle=90, radius=0.4,
                                         center=(0.5,0.5))
                plt.axis('equal')
                plt.legend(patches, loc="best", labels=['%s : %1.1f%%' % (l, s) for l, s in zip(labels, delta_)])
                plt.title(country_full_names[country]+', '+storms[out.ix[:,l].name])
                plt.savefig(os.path.join(data_path,'Figures',country+'_'+storms[out.ix[:,l].name]+'_SA.png'),dpi=300)
                plt.clf()
            except Exception as ev: continue