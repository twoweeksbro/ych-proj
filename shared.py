from pathlib import Path
import geopandas as gpd
import pandas as pd
import json

app_dir = Path(__file__).parent



# ychsi.shp
shapefile_path = app_dir / 'data/ychsi-map/ychsi.shp'
gdf = gpd.read_file(shapefile_path)
gdf = gdf.to_crs(epsg=4326)  
gdf_boundary = gdf.copy()

# gdf_boundary["geometry"] = gdf_boundary["geometry"].boundary
geojson_path = app_dir / "data/ychsi.geojson"  # 원정추가
# gdf_boundary.to_file(geojson_path, driver="GeoJSON")
with open(geojson_path, encoding='utf-8') as f:
    geojson_data = json.load(f)


gdf_green = gpd.read_file(app_dir / "data/farm-map/green-map/green.shp")
gdf_green_single = gdf_green.dissolve()
# gdf_green_single.to_file(app_dir / "data/green_single.geojson", driver="GeoJSON")

with open(app_dir / "data/green_single.geojson", encoding='utf-8') as f:
    geojson_green_single = json.load(f)

fruit_path = app_dir / "data/green.geojson"
with open(fruit_path, encoding='utf-8') as f:
    geojson_fruit = json.load(f)
    
    
    



auto_voice = pd.read_csv(app_dir / "data/경상북도 영천시_자동음성통보시스템_20241120.csv")

# ✅ [추가] 점 → 500m 버퍼 (원) 생성   원정추가
gdf_points = gpd.GeoDataFrame(
    auto_voice,
    geometry=gpd.points_from_xy(auto_voice['좌표정보(Y)'],
                                auto_voice['좌표정보(X)']),
    crs="EPSG:4326"
    ).to_crs(epsg=5181)  # 미터 단위 좌표계

gdf_buffer = gdf_points.copy()
gdf_buffer["geometry"] = gdf_points.buffer(500)  # 500m 원

gdf_buffer = gdf_buffer.to_crs(epsg=4326)  # 다시 위경도로
geojson_buffer = json.loads(gdf_buffer.to_json())  # GeoJSON 변환  #원정추가


# grid 인구 격자
gdf_grid = gpd.read_file(app_dir / "data/grid/500M/nlsp_030001010.shp")
gdf_grid = gdf_grid.dropna(subset=['val'])
gdf_grid = gdf_grid[gdf_grid['val'] != 0 ]

from mapclassify import UserDefined

bins = [18,113,297,619,1110]
classifier = UserDefined(gdf_grid['val'],bins=bins)
gdf_grid['jenks_class'] = classifier.yb
gdf_grid = gdf_grid.to_crs(epsg=4326)
geojson_grid = json.loads(gdf_grid.to_json())



