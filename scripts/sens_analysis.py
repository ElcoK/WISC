# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 09:39:33 2017

@author: cenv0574
"""

from SALib.sample import saltelli,latin
from SALib.analyze import sobol,delta
from SALib.test_functions import Ishigami
import numpy as np
import os
import multiprocessing
#from sens_basescript import run_script
import time


if __name__ == '__main__':

    # load some basics
    curdir = os.getcwd()    
    num_cores = multiprocessing.cpu_count()-2
    
    # specify country
    countries = ['CZ','CH','EE','LV','LT','PT','ES','AT','BE','DK','IE','NL','NO','SE','UK','PL','IT','FI','FR','DE'] 
    
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
    storm_name_list = ['19991203','19900125','20090124','20070118','19991226']
    storm_list = []
    for root, dirs, files in os.walk(curdir+'\\STORMS'):
        for file in files:
            for storm in storm_name_list:
                if storm in file:
                    storm_list.append(curdir+'\\STORMS\\'+file)
#
#    countries_out = []
#    for country in countries:
#        start = time.time()
#        out = run_script(country,storm_list,param_values,version=None,delete=False)
#        end = time.time()
#        countries_out.append(out)