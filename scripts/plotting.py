# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 20:48:26 2018

@author: elcok
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import cartopy.crs as ccrs
from math import log
from math import exp
from matplotlib import colors
from pylab import *
import geopandas as gpd

# make connection to all the scripts
sys.path.append(os.path.join( '..'))
from scripts.utils import load_config

# make connection to the data paths
data_path = load_config()['paths']['data']


#read data
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

world = world.loc[(world.continent == 'Africa') | (world.name.isin(['Russia','Turkey','Ukraine','Belarus','Kosovo','Montenegro',
                                                           'Bosnia and Herz.','Macedonia','Moldova','Serbia','Libya']))]

europe = gpd.read_file(os.path.join(data_path,'input_data','NUTS3_ETRS.shp'))
europe = europe.loc[(europe['STAT_LEVL_']==2)]
europe = europe.to_crs(epsg=4326)

#plot figure

# These don't need to constantly be redefined, especially edgecolor
facecolor = '#fffff2'
edgecolor = 'black'

fig, ax = plt.subplots(figsize=(10, 8),
                       subplot_kw={'projection': ccrs.PlateCarree()})

world.plot(ax = ax,color = facecolor,edgecolor=edgecolor,linewidth=0.3)

europe.plot(ax= ax, color = facecolor,edgecolor=edgecolor,linewidth=0.3)

ax.background_patch.set_facecolor('#f2f9ff')
ax.set_extent([-12, 31, 33, 70])
   # I decreased the indent of this, you only need to do it once per call to run()
#ax.set_title('Commercial sectors impacted on {}'.format(str(date)), fontsize=14,fontweight="bold")


#fig.savefig(os.path.join('..','Figures','calc','{}.png'.format(data)),dpi=60)
#plt.close(fig)
#fig.clear()