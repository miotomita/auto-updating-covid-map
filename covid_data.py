#!/usr/bin/env python
# coding: utf-8

# In[1]:


#! pip install geopandas -t /Users/mio/.pyenv/versions/3.10.3/lib/python3.10/site-packages
#! pip install folium -t /Users/mio/.pyenv/versions/3.10.3/lib/python3.10/site-packages
#! pip install seaborn -t /Users/mio/.pyenv/versions/3.10.3/lib/python3.10/site-packages


# In[2]:


#import geopandas as gpd

#fp = "/Users/mio/Google Drive/japan_ver84/japan_ver84.shp"
#data = gpd.read_file(fp)


# In[3]:


import folium
import geopandas as gpd
import requests
import pandas as pd


# In[4]:


geojson = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json'


# In[5]:


gdf = gpd.read_file('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json')


# JHU covid data

# In[6]:


#import JHU covid data
df =  pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')


# In[7]:


df = df.groupby('Country/Region').sum().drop(['Lat','Long'], axis=1)


# In[8]:


#daily new cases
newcases = df.ffill(axis=1).diff(axis=1)
#7day moving average of new cases
newcases_rolling = newcases.T.rolling(7).mean().iloc[-1].rename('newcases_7dma').rename_axis('country').reset_index()


# In[9]:


#add ISO codes and population
#meta data
countries = pd.read_csv('https://raw.githubusercontent.com/miotomita/meta/main/countries_meta.csv')

#add to dataframe
newcases_rolling['id'] = newcases_rolling.country.map(countries.set_index('name_JHU').code_3digit.to_dict())
newcases_rolling['population'] = newcases_rolling.country.map(countries.set_index('name_JHU').population_agg.to_dict()).astype(float)

#calculate per capita numbers
newcases_rolling['newcases_per_million'] = round(newcases_rolling.newcases_7dma / newcases_rolling.population *1000000, 1)

#drop na rows
newcases_rolling = newcases_rolling[['id','country','newcases_7dma','newcases_per_million']].dropna(how='any')


# In[10]:


source = gdf.merge(newcases_rolling,on="id",how='left')


# In[11]:


max_number = source.newcases_per_million.quantile(0.95)
max_number = int(round((max_number)/100,0)*100)
max_number


# In[12]:


source.newcases_per_million = source.newcases_per_million.clip(0, max_number)


# In[13]:


worldmap = folium.Map(
    location=[10, 0], 
    zoom_start=1.45,
    zoom_control=True,
    scrollWheelZoom=False,
    dragging=True
)

folium.Choropleth(
    geo_data=geojson,
    name='choropleth',
    data=source,
    nan_fill_color='lightgrey',
    columns=['id', 'newcases_per_million'],
    key_on='feature.id',
    fill_color='OrRd',
    fill_opacity=0.7, 
    line_opacity=0.1,
    legend_name='Daily new cases per million',
    tooltip=folium.features.GeoJsonTooltip(
        fields=['name', 'newcases_per_million'],
        labels=True,
        sticky=True
    ),
    overlay=False
).add_to(worldmap)

worldmap.save("world_covid_map.html")

