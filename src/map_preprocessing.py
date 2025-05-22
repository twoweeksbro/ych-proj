# 팜맵 클러스터링
import geopandas as gpd
from shapely.geometry import Polygon

# GeoJSON 불러오기
gdf = gpd.read_file("green.geojson")

# 좌표계 설정 (GeoJSON은 보통 WGS84 / EPSG:4326)
gdf = gdf.set_crs("EPSG:4326")

# 병합 거리 (0.0003도는 약 30m 수준 — 조정 가능)
merge_distance = 0.0001

# 버퍼를 약간 준 후 union → dissolve
gdf_buffered = gdf.copy()
gdf_buffered["geometry"] = gdf_buffered.buffer(merge_distance)
merged = gpd.GeoDataFrame(geometry=[gdf_buffered.unary_union], crs=gdf.crs)

# 버퍼 제거: 실제 병합된 형태로 폴리곤 복원
merged["geometry"] = merged.buffer(-merge_distance)

merged = merged.explode(index_parts=False)

merged["geometry"] = merged["geometry"].simplify(0.0001, preserve_topology=True)

merged.to_file("merged_simplified3.geojson", driver="GeoJSON")





# --------------------------------------------------------------
# 음성통보시스템 geojson변환
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import json

# CSV 파일 경로
csv_path = "./경상북도 영천시_자동음성통보시스템_20241120.csv"

# CSV 파일 불러오기
df = pd.read_csv(csv_path)

# 위도, 경도 컬럼명을 확인하고 GeoDataFrame 생성
if '좌표정보(X)' in df.columns and '좌표정보(Y)' in df.columns:
    lon_col, lat_col = '좌표정보(Y)', '좌표정보(X)'
elif '경도' in df.columns and '위도' in df.columns:
    lon_col, lat_col = '경도', '위도'
else:
    raise ValueError("위도/경도에 해당하는 컬럼명이 없습니다.")

# GeoDataFrame 생성 (WGS84 좌표계)
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]), crs="EPSG:4326")

# 정확한 거리 계산을 위해 UTM (또는 지역에 맞는 투영좌표계)로 변환 → EPSG:5181 (한국 중부)
gdf_utm = gdf.to_crs(epsg=5181)

# 500m 버퍼 생성
gdf_utm["geometry"] = gdf_utm.buffer(500)

# 다시 WGS84로 변환
gdf_buffer = gdf_utm.to_crs(epsg=4326)

# GeoJSON으로 저장
output_path = "./buffer_500m_output.geojson"
gdf_buffer.to_file(output_path, driver="GeoJSON")

# --------------------------------------------------------------------
# 커버 되지않는 범위 구하기
import fiona
import geopandas as gpd
from shapely.geometry import shape

# 1. 파일 불러오기 (fiona 사용)
with fiona.open("./merged_simplified3.geojson") as src:
    main_geoms = [shape(feature["geometry"]) for feature in src]
    crs = src.crs

main_gdf = gpd.GeoDataFrame(geometry=main_geoms, crs=crs)

# 2. 버퍼 파일 로딩
buffer_gdf = gpd.read_file("./buffer_500m_output.geojson")

# 3. 동일한 투영계 (면적계산용 EPSG:5181)로 변환
main_gdf = main_gdf.to_crs(epsg=5181)
buffer_gdf = buffer_gdf.to_crs(epsg=5181)

# 4. 차집합 연산
difference_gdf = gpd.overlay(main_gdf, buffer_gdf, how='difference')

# 5. 넓이 계산 (제곱미터 → 헥타르)
area_sqm = difference_gdf.geometry.area.sum()
area_ha = area_sqm / 10000

# 6. GeoJSON 저장
output_path = "./difference_area.geojson"
difference_gdf.to_file(output_path, driver="GeoJSON")

print(f"겹치지 않는 면적: {area_ha:.2f} 헥타르")
print(f"GeoJSON 저장 경로: {output_path}")
# ------------------------------------------------------------------
# 전체농지면적
import geopandas as gpd
from shapely.geometry import shape
import json

# GeoJSON 수동 로딩
with open("./merged_simplified3.geojson", encoding='utf-8') as f:
    geojson_data = json.load(f)

# 각 Feature의 geometry 수동 변환
features = geojson_data["features"]
geometries = [shape(feature["geometry"]) for feature in features]

# GeoDataFrame 생성
gdf = gpd.GeoDataFrame(geometry=geometries, crs="EPSG:4326")

# 면적 계산을 위해 미터 단위 좌표계로 변환 (예: UTM-K: EPSG 5181)
gdf = gdf.to_crs(epsg=5181)

# 전체 면적 계산 (제곱미터)
total_area_sqm = gdf.geometry.area.sum()

# 헥타르 단위로 변환
total_area_hectares = total_area_sqm / 10000

total_area_hectares

# ------------------------------------------------------------------
# 노인격자 shp -> geojson
from shapely.geometry import Polygon
import geopandas as gpd
import shapefile
import pandas as pd
from shapely.geometry import Point

# 정사각형 생성 함수 (중심점 기준, 단위: meter)
def create_square(center, size=500):
    half = size / 2
    return Polygon([
        (center.x - half, center.y - half),
        (center.x + half, center.y - half),
        (center.x + half, center.y + half),
        (center.x - half, center.y + half)
    ])

# SHP 파일 로드
sf = shapefile.Reader("./500M/nlsp_030001010.shp")

# 속성과 geometry 추출
records = [dict(zip([field[0] for field in sf.fields[1:]], rec)) for rec in sf.records()]
geometries = [Polygon(shape.points) for shape in sf.shapes() if shape.shapeType == shapefile.POLYGON]

# 중심점 기반 정사각형 생성
square_list = []
record_list = []

for rec, geom in zip(records, geometries):
    center = Polygon(geom).centroid
    square = create_square(center, size=500)
    square_list.append(square)
    record_list.append(rec)

# GeoDataFrame 생성 및 좌표계 설정
df = pd.DataFrame(record_list)
gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries(square_list), crs="EPSG:5179")

# WGS84 좌표계로 변환
gdf = gdf.to_crs("EPSG:4326")

# 저장
output_path = "./elderly_grid_squares.geojson"
gdf.to_file(output_path, driver="GeoJSON")

output_path

# ---------------------------------------------------------
# 노인 인구수 구하기
import pandas as pd
import geopandas as gpd
import json
from shapely.geometry import shape

# GeoJSON 수동 로딩
with open("./elderly_grid_squares.geojson", encoding="utf-8") as f:
    grid_data = json.load(f)

features = grid_data["features"]
geometries = [shape(f["geometry"]) for f in features]
attributes = [f["properties"] for f in features]

# 안전한 GeoDataFrame 생성 (index 일치 + GeoSeries 활용)
df = pd.DataFrame(attributes)
geo_series = gpd.GeoSeries(geometries, index=df.index)
gdf_grid = gpd.GeoDataFrame(df, geometry=geo_series)

# buffer 불러오기
gdf_buffer = gpd.read_file("./buffer_500m_output.geojson")
if gdf_grid.crs is None:
    gdf_grid.set_crs(epsg=4326, inplace=True)
gdf_buffer = gdf_buffer.to_crs(gdf_grid.crs)

# 중심점 계산 및 포함 여부 판별
gdf_grid["center"] = gdf_grid.geometry.centroid
gdf_grid_points = gdf_grid.set_geometry("center")
gdf_grid_points["in_buffer"] = gdf_grid_points.geometry.within(gdf_buffer.unary_union)

# 합계 계산
in_elderly = gdf_grid_points[gdf_grid_points["in_buffer"]]["val"].sum()
out_elderly = gdf_grid_points[~gdf_grid_points["in_buffer"]]["val"].sum()

in_elderly, out_elderly


# -------------------------------------------------------------
# 음성통보시스템이 커버하지 못하는 부분 구하기
from shapely.geometry import shape
import geopandas as gpd
import json

# 파일 경로
grid_path = "./elderly_grid_squares.geojson"
diff_path = "./difference_area.geojson"

# GeoJSON 수동 파싱
with open(grid_path, encoding="utf-8") as f:
    geojson_data = json.load(f)

# geometry 생성
geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]
properties = [feature["properties"] for feature in geojson_data["features"]]

# GeoSeries로 geometry 구성
geometry_series = gpd.GeoSeries(geometries, crs="EPSG:4326")

# GeoDataFrame 생성
gdf_grid = gpd.GeoDataFrame(properties, geometry=geometry_series)

# difference_area.geojson 불러오기
gdf_diff = gpd.read_file(diff_path)

# 좌표계 맞추기
gdf_grid = gdf_grid.to_crs(gdf_diff.crs)

# val < 5 조건을 만족하는 사각형 필터링
gdf_grid['val']=gdf_grid["val"].fillna(0)
gdf_small_val = gdf_grid[gdf_grid["val"] < 30].copy()

# 병합된 geometry로 삭제 대상 생성
removal_union = gdf_small_val.unary_union

# 차집합 수행
gdf_diff["geometry"] = gdf_diff.geometry.difference(removal_union)

# 유효한 geometry만 남기기
gdf_diff = gdf_diff[gdf_diff.is_valid & ~gdf_diff.is_empty]

# 저장
output_path = "./difference_area_filtered24.geojson"
gdf_diff.to_file(output_path, driver="GeoJSON")

# import ace_tools as tools; tools.display_dataframe_to_user(name="Filtered Difference Area", dataframe=gdf_diff)

# output_path