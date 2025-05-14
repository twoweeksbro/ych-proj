import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt

# 예시: 좌표 데이터 프레임
data = {
    '지역X좌표': [
        396854, 398156, 398142, 398130, 396585, 396785, 396787, 396606,
        396826, 396613, 397822, 397823, 396597, 396815, 396820, 396573,
        396596, 396816, 396821, 396600, 396836, 396842, 396837, 396842
    ],
    '지역Y좌표': [
        394031, 395903, 395931, 395930, 394393, 393993, 393995, 394432,
        394000, 394420, 396001, 396002, 394409, 394081, 394081, 394445,
        394460, 394057, 394054, 394436, 394063, 394051, 394054, 394054
    ]
}
df = pd.DataFrame(data)

# Point geometry 생성
geometry = [Point(xy) for xy in zip(df['지역X좌표'], df['지역Y좌표'])]

# GeoDataFrame으로 변환
gdf = gpd.GeoDataFrame(df, geometry=geometry)

# 좌표계 설정 (예: 중부원점 TM = EPSG:5181 또는 EPSG:5174 사용 가능)
gdf.set_crs(epsg=5174, inplace=True)

# 지도 시각화
gdf.plot(markersize=30, color='red', figsize=(10, 8))
plt.title("지역 좌표 시각화")
plt.show()