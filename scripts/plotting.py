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
import cartopy.crs as ccrs
import geopandas as gpd

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
        sect_loss = pd.read_excel('output_storms.xlsx',sheetname=sect+'_losses') 
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
    
def risk_map():
    """This function is used to plot the total losses for the following sectors: Residential,Industrial/Commercial,Transport,Other uses,Agriculture.
    
    Arguments:
        figure_output_path {string} -- path to location where you want to save the figure
        
    Returns:
        A saved figure
    """

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
    
    #ax.set_title('Commercial sectors impacted on {}'.format(str(date)), fontsize=14,fontweight="bold")
    
    
    #fig.savefig(os.path.join('..','Figures','calc','{}.png'.format(data)),dpi=60)
    #plt.close(fig)
    #fig.clear()