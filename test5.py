from PIL import Image
import pydeck as pdk
from folium.plugins import HeatMapWithTime
from branca.element import Figure
from folium.plugins import TimestampedGeoJson
import folium
import seaborn as sns
import pandas as pd
from pathlib import Path
import pandas as pd  # library for data analysis
import numpy as np
import json  # library to handle JSON files
from geopy.geocoders import Nominatim
# convert an address into latitude and longitude values
import requests  # library to handle requests

import streamlit as st  # creating an app
from streamlit_folium import folium_static
from shapely import wkt
import geopandas as gpd
import plotly.express as px

#file = 'ipc'
file1 = 'merged_wb'
file2 = 'merged_mh'
file3 = 'merged_ap'
file4 = 'merged_ct'

bbsr = 'new'
ctk = 'ctk.csv'


def get_map(data):
    mymap = folium.Map(location=[20.509834585478302,
                                 84.60220092022696], zoom_start=4, tiles=None)
    folium.TileLayer('CartoDB positron', name="Light Map",
                     control=False).add_to(mymap)
    mymap.choropleth(
        geo_data=data,
        name='Choropleth',
        data=data,
        columns=['Id', 'Total IPC Crimes'],
        key_on="feature.properties.Id",
        fill_color='YlOrRd',
        # threshold_scale=myscale,
        fill_opacity=1,
        line_opacity=0.2,
        legend_name='Total Ipc crimes in %',
        smooth_factor=0
    )

    def style_function(x): return {'fillColor': '#ffffff',
                                   'color': '#000000',
                                   'fillOpacity': 0.1,
                                   'weight': 0.1}

    def highlight_function(x): return {'fillColor': '#000000',
                                       'color': '#000000',
                                       'fillOpacity': 0.50,
                                       'weight': 0.1}

    NIL = folium.features.GeoJson(
        data,
        style_function=style_function,
        control=False,
        highlight_function=highlight_function,
        tooltip=folium.features.GeoJsonTooltip(
            fields=['District', 'Total IPC Crimes'],
            aliases=['District : ', 'Total IPC Crimes : '],
            style=(
                "background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
        )
    )
    mymap.add_child(NIL)
    mymap.keep_in_front(NIL)
    folium.LayerControl().add_to(mymap)
    return mymap


def convert(d_in):
    d_in['geometry'] = d_in['geometry'].apply(wkt.loads)
    d_in = gpd.GeoDataFrame(d_in, geometry='geometry', crs='epsg:4326')
    return d_in


def line_graph(crime_name, data):
    chart_data = pd.concat([
        data['District'],
        data[crime_name],
    ], axis=1)
    chart_data = chart_data.sort_values(['District'])
    chart_data = chart_data.rename(columns={'District': 'x'})
    chart_data = chart_data.dropna()
    import plotly.graph_objs as go
    charts = []
    line_cfg = {'line': {'shape': 'spline', 'smoothing': 0.3},
                'mode': 'lines'}
    charts.append(go.Scatter(
        x=chart_data['x'], y=chart_data[crime_name], name=crime_name,
        **line_cfg
    ))
    figure = go.Figure(data=charts, layout=go.Layout({
        'legend': {'orientation': 'h'},
        'title': {'text': crime_name},
        'xaxis': {'title': {'text': 'District'}},
        'yaxis': {'tickformat': '.0f', 'title': {'text': crime_name},
                  'type': 'linear'}
    }))
    return figure


def bar_graph(crime_name, data):
    chart_data = pd.concat([
        data['District'],
        data[crime_name],
    ], axis=1)
    chart_data = chart_data.sort_values(['District'])
    chart_data = chart_data.rename(columns={'District': 'x'})
    chart_data = chart_data.dropna()
    import plotly.graph_objs as go
    charts = []
    charts.append(go.Bar(
        x=chart_data['x'],
        y=chart_data[crime_name]
    ))
    figure = go.Figure(data=charts, layout=go.Layout({
        'barmode': 'group',
        'legend': {'orientation': 'h'},
        'title': {'text': crime_name},
        'xaxis': {'title': {'text': 'District'}},
        'yaxis': {'tickformat': '.0f',
                  'title': {'text': crime_name},
                  'type': 'linear'}
    }))
    return figure


def get_heatmap(file_name):
    data = pd.read_csv(file_name)
    data.drop(columns=['Unnamed: 0'], inplace=True)
    data['DateTime'] = pd.to_datetime(data['DateTime'])
    data['hour'] = data['DateTime'].apply(lambda x: x.hour+1)

    lat_long_list = []
    for i in range(1, 25):
        temp = []
        for index, instance in data[data['hour'] == i].iterrows():
            temp.append([instance['Latitude'], instance['Longitude']])
        lat_long_list.append(temp)

    fig = Figure(width=800, height=400)
    map_heat = folium.Map(location=[20.44, 85.8327], zoom_start=10)
    fig.add_child(map_heat)
    HeatMapWithTime(lat_long_list, radius=6.5, auto_play=False,
                    position='bottomright').add_to(map_heat)
    return map_heat, data


def map_layer(ip_data):
    locs_map = folium.Map(location=[20.290838, 85.845339],
                          zoom_start=9, tiles="OpenStreetMap")

    feature_th = folium.FeatureGroup(name='Theft')
    feature_gh = folium.FeatureGroup(name='Grievous Hurt')
    feature_rob = folium.FeatureGroup(name='Robbery')
    feature_cbt = folium.FeatureGroup(name='Criminal Breach of Trust')
    feature_assault = folium.FeatureGroup(name='Assault')
    feature_ua = folium.FeatureGroup(name='Unlawful Assembly')
    feature_ex = folium.FeatureGroup(name='Extortion')

    for i, v in ip_data.iterrows():
        popup = """
        case_list : <b>%s</b><br>
        PeopleAffected : <b>%d</b><br>
        """ % (v['case_list'],  v['PeopleAffected'])

        if v['case_list'] == 'Theft':
            folium.CircleMarker(location=[v['Latitude'], v['Longitude']],
                                radius=4,
                                tooltip=popup,
                                color='#FFFF00',
                                fill_color='#FFBA00',
                                fill=True).add_to(feature_th)
        elif v['case_list'] == 'Grievous Hurt':
            folium.CircleMarker(location=[v['Latitude'], v['Longitude']],
                                radius=4,
                                tooltip=popup,
                                color='#087FBF',
                                fill_color='#087FBF',
                                fill=True).add_to(feature_gh)
        elif v['case_list'] == 'Robbery':
            folium.CircleMarker(location=[v['Latitude'], v['Longitude']],
                                radius=4,
                                tooltip=popup,
                                color='#FF0700',
                                fill_color='#FF0700',
                                fill=True).add_to(feature_rob)
        elif v['case_list'] == 'Criminal Breach of Trust':
            folium.CircleMarker(location=[v['Latitude'], v['Longitude']],
                                radius=4,
                                tooltip=popup,
                                color='#00FF00',
                                fill_color='#FF0700',
                                fill=True).add_to(feature_cbt)
        elif v['case_list'] == 'Assault':
            folium.CircleMarker(location=[v['Latitude'], v['Longitude']],
                                radius=4,
                                tooltip=popup,
                                color='#9900FF',
                                fill_color='#FF0700',
                                fill=True).add_to(feature_assault)
        elif v['case_list'] == 'Unlawful Assembly':
            folium.CircleMarker(location=[v['Latitude'], v['Longitude']],
                                radius=4,
                                tooltip=popup,
                                color='#FF6600',
                                fill_color='#FF0700',
                                fill=True).add_to(feature_ua)
        elif v['case_list'] == 'Extortion':
            folium.CircleMarker(location=[v['Latitude'], v['Longitude']],
                                radius=4,
                                tooltip=popup,
                                color='#993300',
                                fill_color='#FF0700',
                                fill=True).add_to(feature_ex)

    feature_th.add_to(locs_map)
    feature_gh.add_to(locs_map)
    feature_rob.add_to(locs_map)
    feature_cbt.add_to(locs_map)
    feature_assault.add_to(locs_map)
    feature_ua.add_to(locs_map)
    feature_ex.add_to(locs_map)
    folium.LayerControl(collapsed=False).add_to(locs_map)
    return locs_map


image = Image.open('Cet.png')
st.image(image, width=700)

st.write("""
# Crime Data Analysis
""")


@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def get_data(file):
    data = pd.read_csv(file)
    data.drop(['Unnamed: 0'], axis=1, inplace=True)
    return data


data_wb = pd.read_csv('merged_wb')
data_mh = pd.read_csv('merged_mh')
data_ap = pd.read_csv('merged_ap')
data_ct = pd.read_csv('merged_ct')
data_od = pd.read_csv('ipc')

data_wb = convert(data_wb)
data_mh = convert(data_mh)
data_ap = convert(data_ap)
data_ct = convert(data_ct)
data_od = convert(data_od)

map1 = get_map(data_wb)
map2 = get_map(data_mh)
map3 = get_map(data_ap)
map4 = get_map(data_ct)
map5 = get_map(data_od)


state_map = st.sidebar.multiselect(
    "Input For State Map", ['West Bengal', 'Maharashtra', 'Odisha', 'Andhra Pradesh', 'Chattisgarh'], key=2)


try:
    if state_map[0] == 'West Bengal':
        data = data_wb
        folium_static(map1)
    elif state_map[0] == 'Maharashtra':
        data = data_mh
        folium_static(map2)
    elif state_map[0] == 'Andhra Pradesh':
        data = data_ap
        folium_static(map3)
    elif state_map[0] == 'Chattisgarh':
        data = data_ct
        folium_static(map4)
    elif state_map[0] == 'Odisha':
        data = data_od
        folium_static(map5)
except:
    st.error("👈 Choose a State")

st.text("")
st.write("👇 Select A Crime ")
try:
    crime = st.multiselect(" ", data.columns[2:])
except:
    st.error("☝️First Choose a State")

try:
    line = line_graph(crime[0], data)
    st.plotly_chart(line)

    bar = bar_graph(crime[0], data)
    st.plotly_chart(bar)

    pie = px.pie(data, values=crime[0],
                 names='District', title=f'{crime[0]} Data By Districts')
    st.plotly_chart(pie)

except:
    st.error("☝️Give a Input For Generating Charts/Graphs ")

st.markdown("## **Crime Data Analysis Of Bhubaneswar & Cuttack**")

bbsr_map, bbsr_data = get_heatmap(bbsr)
ctk_map, ctk_data = get_heatmap(ctk)

bbsr_layer = map_layer(bbsr_data)
ctk_layer = map_layer(ctk_data)

st.write("Animation Of Heatmap Showing Crime Location On Hourly Basis")

if st.checkbox("👈 Bhubaneswar", False, key=1):
    folium_static(bbsr_map)

if st.checkbox("👈 Cuttack", False, key=2):
    folium_static(ctk_map)

st.text("")
st.write("Geo Location of Crimes With Detailed Info")

if st.checkbox("👈 Bhubaneswar", False, key=3):
    folium_static(bbsr_layer)

if st.checkbox("👈 Cuttack", False, key=4):
    folium_static(ctk_layer)
