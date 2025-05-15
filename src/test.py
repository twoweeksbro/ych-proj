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
    df_cleaned[1:],
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




fig = px.choropleth_mapbox(
    df_cleaned,
    locations='읍면동'
    color='65세이상고령자소계',
    hover_name='장소명',
    hover_data={'좌표정보(X)': True, '좌표정보(Y)' : True},
    text='장소명',
    zoom=10,
    height=650,
    title='경상북도 영천시 자동 음성통보시스템'
)

fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_layers=[
        {
        "sourcetype": "geojson",
        # "source": geojson_data,
        "type": "line", "color": "black", "line": {"width": 1}
        }
    ],
    mapbox_center={"lat": 35.97326, "lon": 128.938613},
    margin={"r":0,"t":30,"l":0,"b":0})



