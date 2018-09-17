# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 20:48:26 2018

@author: elcok
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd

from mpl_toolkits.basemap import Basemap
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize
import matplotlib.cm
from matplotlib import colors
from mpl_toolkits.axes_grid1 import make_axes_locatable



# make connection to all the scripts
sys.path.append(os.path.join( '..'))
from scripts.utils import load_config

def loss_per_country(figure_output_path='test_country.png'):
    '''This function is used to plot the total losses per year per country.
    
    Arguments:
        figure_output_path {string} -- path to location where you want to save the figure
        
    Returns:
        A saved figure
    '''

    data_path = load_config()['paths']['data']

    countries = ['AT','BE','DK','FR','DE','IE','LU','NL','NO','SE','UK','PL','IT','FI'] 
    country_names = ['Austria','Belgium','Denmark','France','Germany','Ireland','Luxembourg','Netherlands','Norway','Sweden','United Kingdom','Poland','Italy','Finland'] 
    cols_to_load = ['Storm']+countries
        
    all_storm = pd.read_excel(os.path.join(data_path,'output_storms.xlsx'),sheet_name='total_losses') #,index_col=0)
    all_storm = all_storm[cols_to_load]
    all_storm['Storm'] = pd.to_datetime(all_storm['Storm'])
    all_storm.set_index('Storm', inplace=True)
    
    all_storm.rename(columns=dict(zip(countries, country_names)), inplace=True)
    
    loss_per_year = all_storm.resample("A").sum()
    loss_per_year['Year'] = loss_per_year.index.year
    loss_per_year.set_index('Year', inplace=True) 
    
    fig, ax_yc = plt.subplots(figsize=(10, 8))       
    
    loss_per_year.plot.bar(ax=ax_yc,stacked=True,width=0.9, ec="w", lw=0.1,colormap="Paired")
    plt.setp(ax_yc.get_xticklabels(), rotation=80)
    ax_yc.set_xlabel("Years", fontweight='bold')
    ax_yc.set_ylabel("Loss in million dollar", fontweight='bold')
    ax_yc.set_yticks(np.arange(0,26000,2500), minor=False)
    ax_yc.set_ylim(0,25000)
    ax_yc.legend(loc='upper right', frameon=True, prop={'size':12}) 
    ax_yc.patch.set_facecolor('0.98')
    
    # AND SAVE THE FIGURE
    plt.savefig(figure_output_path,dpi=600,bbox_inches='tight')
    
def loss_per_sector(figure_output_path='test_sector.png'):
    '''This function is used to plot the total losses for the following sectors: Residential,Industrial/Commercial,Transport,Other uses,Agriculture.
    
    Arguments:
        figure_output_path {string} -- path to location where you want to save the figure
        
    Returns:
        A saved figure
    '''

    data_path = load_config()['paths']['data']

    sectors = ['res','ind_com','transport','other','agri']
    sect_names = ['Residential','Industrial/Commercial','Transport','Other uses','Agriculture']
    countries = ['AT','BE','DK','FR','DE','IE','LU','NL','NO','SE','UK','PL','IT','FI'] 
    country_names = ['Austria','Belgium','Denmark','France','Germany','Ireland','Luxembourg','Netherlands','Norway','Sweden','United Kingdom','Poland','Italy','Finland'] 
    cols_to_load = ['Storm']+countries
        
    all_storm = pd.read_excel(os.path.join(data_path,'output_storms.xlsx'),sheet_name='total_losses') #,index_col=0)
    all_storm = all_storm[cols_to_load]
    all_storm['Storm'] = pd.to_datetime(all_storm['Storm'])
    all_storm.set_index('Storm', inplace=True)
    
    all_storm.rename(columns=dict(zip(countries, country_names)), inplace=True)
    
    loss_per_year = all_storm.resample("A").sum()
    loss_per_year['Year'] = loss_per_year.index.year
    loss_per_year.set_index('Year', inplace=True) 
    
    loss_per_sector = pd.DataFrame(columns=sectors,index=loss_per_year.index) 
    
    for sect in sectors:
        sect_loss = pd.read_excel(os.path.join(data_path,'output_storms.xlsx'),sheetname=sect+'_losses') 
        sect_loss = sect_loss[cols_to_load]
        sect_loss['Storm'] = pd.to_datetime(sect_loss['Storm'])
        sect_loss.set_index('Storm', inplace=True) 
        
        inb_sec = sect_loss.resample("A").sum()
        inb_sec = inb_sec.sum(axis=1)
        loss_per_sector[sect] = np.array(inb_sec)
    
    # RENAME
    loss_per_sector.rename(columns=dict(zip(sectors, sect_names)), inplace=True)
    fig, ax_ys = plt.subplots(figsize=(10, 8))       
    
    loss_per_sector.plot.bar(ax=ax_ys,stacked=True,width=0.9, ec="w", lw=0.1,colormap="Paired")
    plt.setp(ax_ys.get_xticklabels(), rotation=80)
    ax_ys.set_xlabel("Years", fontweight='bold')
    ax_ys.set_ylabel("Loss in million dollar", fontweight='bold')
    ax_ys.set_yticks(np.arange(0,26000,2500), minor=False)
    ax_ys.set_ylim(0,25000)
    ax_ys.legend(loc='upper right', frameon=True, prop={'size':12}) 
    ax_ys.patch.set_facecolor('0.98')
    
    plt.savefig(figure_output_path,dpi=600,bbox_inches='tight')
    
def risk_map(figure_output_path='test_risk_map.png'):
    """This function is used to create a map with the total risk per region.
    
    Arguments:
        figure_output_path {string} -- path to location where you want to save the figure
        
    Returns:
        A saved figure
    """

    data_path = load_config()['paths']['data']

    countries = ['LU','AT','BE','DK','FR','DE','IE','NL','NO','SE','UK','PL','IT','FI','CH','EE','LV','LT','PT','ES','CZ'] 

    NUTS3 = gpd.read_file(os.path.join(data_path,'input_data','NUTS3_ETRS.shp'))
    NUTS3 = NUTS3.to_crs(epsg=4326)
    NUTS3 = NUTS3[NUTS3.STAT_LEVL_==3]
    NUTS3['Sum'] = 0
   
    for country in countries:
        output_table = pd.DataFrame()
        for root, dirs, files in os.walk(os.path.join("F:\Dropbox\VU_DATA\WISC","output_risk",country)):
            for file in files:
                nuts_name = file[:-9]
                output_table = pd.DataFrame(pd.read_csv(os.path.join("F:\Dropbox\VU_DATA\WISC","output_risk",country,file),index_col=0,encoding='cp1252')['Risk'])
                output_table['Risk'] = output_table['Risk'].astype(float)

                output_table = output_table.replace([np.inf, -np.inf], np.nan).dropna(how='all')
                output_table.loc[output_table.Risk<0.5] = 0
                # TOTAL
                NUTS3.loc[NUTS3.NUTS_ID==nuts_name,'Sum'] = output_table['Risk'].sum(axis=0)/1000000

    NUTS3 = NUTS3[NUTS3.Sum>0]            
    NUTS3.to_file(os.path.join(data_path,"NUTS3.shp"))

    fig, ax1 = plt.subplots(figsize=(10,20))

    #Let's create a basemap of Europe
    x1 = -18.
    x2 = 38.
    y1 = 33.
    y2 = 71.
     
    m = Basemap(resolution='i',projection='merc', llcrnrlat=y1,urcrnrlat=y2,llcrnrlon=x1,urcrnrlon=x2,lat_ts=(x1+x2)/2)
    m.drawcountries(linewidth=0.5)
    m.drawcoastlines(linewidth=0.5)
                
    m.drawmapboundary(fill_color='#46bcec')
    m.fillcontinents(color='white',lake_color='#46bcec')
    m.drawcoastlines(linewidth=.5)
    m.readshapefile(os.path.join(data_path,"NUTS3"), 'nuts3')
    
    cmap = plt.get_cmap('OrRd')   
    norm = Normalize()
    
    # make a color map of fixed colors
    bounds=[0.05,1,5,10,50,100,500,1000]
    norm = colors.BoundaryNorm(bounds, cmap.N)
    
    # add values
    df_poly = pd.DataFrame({
            'shapes': [Polygon(np.array(shape), True) for shape in m.nuts3],
            'area': [NUTS_ID['NUTS_ID'] for NUTS_ID in m.nuts3_info],
            'value_': [Sum['Sum'] for Sum in m.nuts3_info]
        })
    pc1 = PatchCollection(df_poly.shapes, edgecolor='k', linewidths=0.1,cmap=cmap, zorder=2)
    pc1.set_facecolor(cmap(norm(df_poly['value_'].fillna(0).values)))
    ax1.add_collection(pc1)    
        
    # ADD COLORBAR
    mapper = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)
    mapper.set_array(df_poly['value_'])
    fig.patch.set_facecolor('white')
    
    divider = make_axes_locatable(ax1)
    cax = divider.new_vertical(size="5%", pad=0.2, pack_start=True)
    fig.add_axes(cax)
    cbar = fig.colorbar(mapper, cax=cax, orientation="horizontal")
    cbar.set_label('Risk in million Dollar (2012)', rotation=0,fontsize=14)
    
    fig.savefig(figure_output_path,dpi=600,bbox_inches='tight')  
        