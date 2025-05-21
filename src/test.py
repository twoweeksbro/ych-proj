import pandas as pd
from pathlib import Path

app_dir = Path(__file__).parent


df_raw = pd.read_csv(app_dir / "data/영천시 인구수.csv", encoding='euc-kr', header=[0,1,2,3])

df_raw.head()

# 컬럼 이름 병합: ('2020', '인구', '명', '남') → '2020_인구_명_남'
df_raw.columns = ["_".join([str(i) for i in col if str(i) != "nan"]) for col in df_raw.columns]

# 첫 컬럼(읍면동명)만 따로 명확히 설정
df_raw = df_raw.rename(columns={df_raw.columns[0]: "읍면동"})

# 예시: 필요한 컬럼만 뽑기
cols_to_keep = [
    "읍면동",
    "2020_세대수_세대_소계",
    "2020_인구_명_소계",
    "2020_인구_명_남",
    "2020_인구_명_여",
    "2020_인구_명_한국인_소계",
    "2020_인구_명_외국인_소계",
    "2020_65세 이상 고령자_명_소계",
    "2020_평균연령_세_소계",
    "2020_인구밀도_명/㎢_소계",
    "2020_인구밀도_명/㎢_면적 (㎢)"
]

df_cleaned = df_raw.copy()

df_raw.columns.size


# 컬럼 이름 깔끔하게 정리
df_cleaned.columns = [
    "읍면동", "세대수", "인구소계", "남자소계", "여자소계",
    "한국인소계", "한국인남소계", "한국인여소계", "외국인소계", "외국인남소계", "외국인여소계","세대당인구","65세이상고령자소계","평균연령","인구밀도(명/㎢)", "인구밀도(명/㎢)_면적(㎢)"
]

# 숫자형 변환
df_cleaned.iloc[:, 1:] = df_cleaned.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')

df_cleaned.info()
df_cleaned.head()

import json

with open(app_dir / 'data/ychsi4326.geojson', encoding='utf-8') as f:
    geojson_data = json.load(f)

import plotly.express as px
print(geojson_data['features'][1]['properties'])

df_cleaned = df_cleaned.rename(columns={'읍면동':'ADM_NM'})

geo_names = [f['properties']['ADM_NM'] for f in geojson_data['features']]
print(sorted(geo_names))

# df_cleaned에 있는 값들
print(sorted(df_cleaned[1:]['ADM_NM'].unique()))

print(df_cleaned["65세이상고령자소계"].dtype)

import geopandas as gpd

shapefile_path = app_dir /'data/ychsi-map/ychsi.shp'
# gdf = gpd.read_file(shapefile_path, encoding='euc-kr')
gdf = gpd.read_file(shapefile_path)

gdf.crs

gdf = gdf.to_crs(epsg=4326)
gdf.to_file(app_dir / "data/ychsi4326.geojson", driver="GeoJSON")


df_cleaned[1:].to_csv(app_dir / 'data/ych_pop_clean.csv',index=False)
test = pd.read_csv(app_dir / 'data/ych_pop_clean.csv')


fig = px.choropleth_mapbox(
    test,
    geojson=geojson_data,
    locations="ADM_NM",
    featureidkey="properties.ADM_NM",
    color="65세이상고령자소계",
    color_continuous_scale="Blues",
    mapbox_style="carto-positron",
    center={"lat": 35.97326, "lon": 128.938613},
    zoom=10,
    opacity=0.7,
    title="영천시 자치구별 65세 고령인구 수"
    )


fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
fig.show()



import folium
from folium import Choropleth, GeoJson, LayerControl
from folium.features import GeoJsonTooltip, DivIcon

# 지도 생성
m = folium.Map(location=[35.97326, 128.938613], zoom_start=11, tiles='CartoDB positron')

# 1. Choropleth (고령자 수 시각화)
Choropleth(
    geo_data=geojson_data,
    name='고령자 수',
    data=test,
    columns=['ADM_NM', '65세이상고령자소계'],
    key_on='feature.properties.ADM_NM',
    fill_color='Blues',
    fill_opacity=0.7,
    line_opacity=0.5,
    legend_name='65세 이상 고령인구 수'
).add_to(m)

# 2. Tooltip (마우스 오버 시 텍스트)
GeoJson(
    geojson_data,
    name="행정구역",
    tooltip=GeoJsonTooltip(
        fields=["ADM_NM"],
        aliases=["행정동: "],
        localize=True,
        sticky=False,
        labels=True,
        style="""
            background-color: white;
            border: 1px solid black;
            border-radius: 3px;
            box-shadow: 3px;
        """
    )
).add_to(m)

# 3. DivIcon으로 지도 위에 지역명 텍스트 표시
for _, row in test.iterrows():
    folium.Marker(
        location=[row['ADM_NM'], row['lon']],
        icon=DivIcon(
            icon_size=(150,36),
            icon_anchor=(0,0),
            html=f'''
                <div style="
                    font-size: 11px;
                    font-weight: bold;
                    color: black;
                    text-align: center;
                    background-color: rgba(255,255,255,0.6);
                    padding: 2px;
                    border-radius: 3px;">
                    {row["ADM_NM"]}
                </div>
            '''
        )
    ).add_to(m)

# 4. 레이어 토글 기능 추가
LayerControl().add_to(m)

# 저장하거나 Jupyter에서 보여주기
m.save("ych_gis_map.html")
m




##### 
# 지도시각화 
import pandas as pd
from pathlib import Path
import os
import geopandas as gpd

if 'SHINY_SERVER' in os.environ:
    app_dir = Path('/home/shiny')  # shinyapps.io 환경
else:
    app_dir = Path(__file__).parent  # 로컬 환경


shapefile_path = app_dir / '../data/ychsi-map/ychsi.shp'
gdf = gpd.read_file(shapefile_path)

fruit_shapefile_path = app_dir / '../data/farm-map/경상북도_팜맵과 드론 활용 경상북도 영천시, 의성군 과수 재배현황_20211231\��õ�Ǽ�_����.shp'
fruit_gdf = gpd.read_file(fruit_shapefile_path)

fruit_gdf = fruit_gdf[fruit_gdf['emd'].str.startswith("47230")]

fruit_gdf = fruit_gdf.to_crs(epsg=4326)
fruit_geojson_path = app_dir / "../data/fruit.geojson"

fruit_gdf.to_file(fruit_geojson_path, driver = "GeoJSON")



green_gdf = gpd.read_file(app_dir / '../data/farm-map/green-map/green.shp')
(green_gdf['emd'].str.startswith('47230')).sum()
green_gdf = green_gdf.to_crs(epsg=4326)
app_dir / "../data/green.geojson"
green_gdf.to_file(app_dir / "../data/green.geojson", driver="GeoJSON")


gdf = gdf.to_crs(epsg=4326) #원정추가
gdf_boundary = gdf.copy()
gdf_boundary["geometry"] = gdf_boundary["geometry"].boundary
geojson_path = app_dir / "../data/ychsi.geojson" #원정추가







gdf_boundary.to_file(geojson_path, driver="GeoJSON")
import json
import plotly.express as px
#gdf.to_file(app_dir / "data/ychsi.geojson", driver="GeoJSON")
#with open(app_dir / 'data/ychsi.geojson', encoding='utf-8') as f:
with open(geojson_path, encoding='utf-8') as f:
    geojson_data = json.load(f)

with open(fruit_geojson_path, encoding='utf-8') as f:
    fruit_geojson = json.load(f)

fruit_geojson


auto_voice = pd.read_csv(app_dir / "../data/경상북도 영천시_자동음성통보시스템_20241120.csv")

selected_names = auto_voice['행정동명'].value_counts().index.to_list()#원정추가
selected_gdf = gdf[gdf['ADM_NM'].isin(selected_names)]  
selected_geojson = json.loads(selected_gdf.to_json())




df = auto_voice.copy()
df['색상'] = df['행정동명'].apply(lambda x: x if x in selected_names else '기타') #원정추가



# ✅ [추가] 점 → 500m 버퍼 (원) 생성   원정추가
gdf_points = gpd.GeoDataFrame(
df,
geometry=gpd.points_from_xy(df['좌표정보(Y)'], df['좌표정보(X)']),
crs="EPSG:4326"
).to_crs(epsg=5181)  # 미터 단위 좌표계

gdf_buffer = gdf_points.copy()
gdf_buffer["geometry"] = gdf_points.buffer(500)  # 500m 원

gdf_buffer = gdf_buffer.to_crs(epsg=4326)  # 다시 위경도로
buffer_geojson = json.loads(gdf_buffer.to_json())  # GeoJSON 변환  #원정추가

fig = px.scatter_mapbox(
#filtered_df(),
df,
lat='좌표정보(X)',
lon='좌표정보(Y)',
#color='행정동명',
color='색상',
hover_name='장소명',
hover_data={'좌표정보(X)': True, '좌표정보(Y)': True},
text='장소명',
zoom=10,
height=650,
title='경상북도 영천시 자동 음성통보시스템'
)

fig.update_layout(
mapbox_style="carto-positron",
mapbox_layers=[
{
     "sourcetype": "geojson",       # 과수
    "source": fruit_geojson,
    "type": "fill",
    "color": "rgba(0, 255, 0, 0.2)",  # 연한 초록
    "below": "traces"
},
{
    "sourcetype": "geojson",    
    "source": geojson_data,
    "type": "line", 
    "color": "black",
    "line": {"width": 1},
    "below": "traces" 
},
{
    "sourcetype": "geojson",    #원정추가가
    "source": selected_geojson,
    "type": "fill",
    "color": "rgba(0, 100, 255, 0.2)",  # ✅ 연한 파란색 채움
    "below": "traces"
},
# ✅ 선택된 읍면동 테두리 강조
{
    "sourcetype": "geojson",
    "source": selected_geojson,
    "type": "line",
    "color": "blue",
    "line": {"width": 3},
    "below": "traces"
},


# ✅ [추가] 각 점의 반경 500m 원 표시
{
    "sourcetype": "geojson",
    "source": buffer_geojson,
    "type": "fill",
    "color": "rgba(0, 0, 255, 0.1)",
    "below": "traces"
},
{
    "sourcetype": "geojson",
    "source": buffer_geojson,
    "type": "line",
    "color": "blue",
    "line": {"width": 1},
    "below": "traces"             #원정추가
}
],
mapbox_center={"lat": 35.97326, "lon": 128.938613},
margin={"r":0,"t":30,"l":0,"b":0}
)

fig.show()



###### 
# 격자 적용
x_path = app_dir / 'data/격자/1KM/nlsp_020001010.shp'

x_gdf = gpd.read_file(x_path)  # 파일 경로에 맞게 수정


import mapclassify

# 예: '인구수' 칼럼 기준으로 Jenks 분류 (5구간)
x_gdf['val'] = x_gdf['val'].fillna(0)
x_gdf = x_gdf.dropna(subset=['val'])
classifier = mapclassify.NaturalBreaks(x_gdf['val'], k=5)
classifier.bins
x_gdf['jenks_class'] = classifier.yb


# 임의로 분류 코드.
from mapclassify import UserDefined
bins = [47,238,624,1319,2722]
classifier = UserDefined(x_gdf["val"], bins=bins)
x_gdf["jenks_class"] = classifier.yb  #



# 61, 360, 1319

import plotly.express as px
x_gdf = x_gdf.to_crs(epsg=4326)
x_geojson = json.loads(x_gdf.to_json())

fig = px.choropleth_mapbox(
    x_gdf,
    geojson=x_geojson,
    locations=x_gdf.index,
    color='jenks_class',
    mapbox_style="carto-positron",
    center={"lat": x_gdf.geometry.centroid.y.mean(), 
            "lon": x_gdf.geometry.centroid.x.mean()},
    zoom=10,
    opacity=0.6,
    color_continuous_scale='Blues',
    # 호버 관련
    hover_name="gid",                  # 또는 '행정동명' 같은 이름 필드
    hover_data={"val": True, "jenks_class": True}  # 추가 정보 표시
)
fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
fig.show()



import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 10))
x_gdf.plot(
    column='jenks_class',
    cmap='Blues',
    linewidth=0.8,
    edgecolor='gray',
    legend=True,
    ax=ax
)
plt.title("인구수 기준 Natural Breaks (Jenks) 분류 지도")
plt.axis('off')
plt.show()
