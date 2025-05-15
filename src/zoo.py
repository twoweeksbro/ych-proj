import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px


# .shp 파일만 지정하면 나머지(.dbf, .shx, .prj 등)는 자동 로딩
shapefile_path = "../data/ych-map/sig.shp"


gdf = gpd.read_file(shapefile_path, encoding='euc-kr')


# gdf = gdf.to_crs(epsg=4623)
gdf.to_file("korea_districts.geojson", driver="GeoJSON")

auto_voice = pd.read_csv("../data/경상북도 영천시_자동음성통보시스템_20241120.csv")
auto_voice['좌표정보(X)']
auto_voice['좌표정보(Y)']

auto_voice.head()
auto_voice['장소명'].value_counts().index.to_list()

import json
with open('korea_districts.geojson', encoding='utf-8') as f:
    geojson_data = json.load(f)

geojson_data.keys()

fig = px.scatter_mapbox(
    auto_voice,
    lat='좌표정보(X)',
    lon='좌표정보(Y)',
    color='행정동명',
    hover_name='장소명',
    hover_data={'좌표정보(X)': True, '좌표정보(Y)' : True},
    text='장소명',
    zoom=10,
    height=650,
    title='자동 음성'
)

fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_layers=[
       {
        "sourcetype": "geojson",
        "source": geojson_data,
        "type": "line", "color": "black", "line": {"width": 1}
        }
    ],
    mapbox_center={"lat": 35.97326, "lon": 128.938613},
    margin={"r":0,"t":30,"l":0,"b":0})
fig.show()