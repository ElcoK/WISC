# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 14:18:26 2018

@author: cenv0574
"""

from SALib.sample import latin
import os
import sys

sys.path.append(os.path.join( '..'))
from scripts.utils import load_config,get_num

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