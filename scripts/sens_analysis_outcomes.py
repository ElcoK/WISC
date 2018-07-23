# -*- coding: utf-8 -*-
"""
Created on Sun Aug 27 09:41:23 2017

@author: cenv0574
"""

from SALib.sample import saltelli,latin
from SALib.analyze import sobol,delta
from SALib.test_functions import Ishigami
import numpy as np
import os
import multiprocessing
from sens_basescript import run_script
import time
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib

matplotlib.style.use('ggplot')

matplotlib.rcParams['font.size'] = 14.
matplotlib.rcParams['font.family'] = 'tahoma'
matplotlib.rcParams['axes.labelsize'] = 14.
matplotlib.rcParams['xtick.labelsize'] = 12.
matplotlib.rcParams['ytick.labelsize'] = 12.

if __name__ == '__main__':

    # load some basics
    curdir = os.getcwd()    
    num_cores = multiprocessing.cpu_count()-2
    
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
    for root, dirs, files in os.walk(curdir+'\\STORMS'):
        for file in files:
            for storm in storm_name_list:
                if storm in file:
                    storm_list.append(curdir+'\\STORMS\\'+file)


    for country in countries:
        dirlist = os.listdir(curdir+'\\output_sens')
        country_list  = [ x for x in dirlist if country in x]
        k = 0

        for i in range(int(len(country_list)/2)):
            if i < 1:
                out = pd.read_csv(curdir+'\\output_sens\\'+country_list[k],index_col=0)   
            else:
                out2 = pd.read_csv(curdir+'\\output_sens\\'+country_list[k],index_col=0).fillna(0)    
                out += out2
            k += 2  
        param_values = pd.read_csv(curdir+'\\output_sens\\'+country_list[1],delim_whitespace=True, header=None)
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
                plt.savefig(curdir+'\\Figures\\'+country+'_'+storms[out.ix[:,l].name]+'.png',dpi=300)
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
                plt.savefig(curdir+'\\Figures\\'+country+'_'+storms[out.ix[:,l].name]+'_SA.png',dpi=300)
                plt.clf()
            except Exception as ev: continue
#        del out
            

          

