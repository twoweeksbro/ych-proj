from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_widget
from pathlib import Path
import plotly.express as px
import pandas as pd
import geopandas as gpd
import json
from functools import partial
from shiny.ui import page_navbar
from faicons import icon_svg
import os

# 환경에 따른 경로 설정
if 'SHINY_SERVER' in os.environ:
    app_dir = Path('/home/shiny')  # shinyapps.io 환경
else:
    app_dir = Path(__file__).parent  # 로컬 환경

# app_dir = Path(__file__).parent

ui.page_opts(title="2025년 제4회 영천시 공공데이터 활용 경진대회", page_fn=partial(page_navbar, id="page"), fillable=False)
auto_voice = pd.read_csv(app_dir / "data/경상북도 영천시_자동음성통보시스템_20241120.csv")

with ui.nav_panel("첫번째 탭"):  
    "Page A content"

with ui.nav_panel('두번째 탭'):
    with ui.layout_sidebar():
        with ui.sidebar():
            ui.input_checkbox_group(
                "space",
                "행정동명",
                auto_voice['행정동명'].value_counts().index.to_list(),
                selected=auto_voice['행정동명'].value_counts().index.to_list(),
            )
    
        with ui.layout_column_wrap(fill=False):
            with ui.value_box(showcase=icon_svg("earlybirds")):
                "자동음성통보시스템 수"

                @render.text
                def count():
                    return filtered_df().shape[0]

            with ui.value_box(showcase=icon_svg("ruler-horizontal")):
                "행정동별 평균 수"

                @render.text
                def bill_length():
                    return round(filtered_df().groupby(['행정동명']).size().mean(), 3)

            with ui.value_box(showcase=icon_svg("ruler-vertical")):
                "평균 설치년도"

                @render.text
                def bill_depth():
                    return f"{filtered_df()['설치일자'].mean():.1f}년"

        with ui.layout_columns():
            with ui.card(full_screen=True):
                ui.card_header("경상북도 영천시 자동음성통보시스템")
                
                @render_widget
                def auto_voice_map():
                    shapefile_path = app_dir / 'data/ychsi-map/ychsi.shp'
                    gdf = gpd.read_file(shapefile_path)
                    
                    gdf.to_file(app_dir / "data/ychsi.geojson", driver="GeoJSON")
                    with open(app_dir / 'data/ychsi.geojson', encoding='utf-8') as f:
                        geojson_data = json.load(f)

                    fig = px.scatter_mapbox(
                        filtered_df(),
                        lat='좌표정보(X)',
                        lon='좌표정보(Y)',
                        color='행정동명',
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
                                "sourcetype": "geojson",
                                "source": geojson_data,
                                "type": "line", 
                                "color": "black", 
                                "line": {"width": 1}
                            }
                        ],
                        mapbox_center={"lat": 35.97326, "lon": 128.938613},
                        margin={"r":0,"t":30,"l":0,"b":0}
                    )

                    return fig

            with ui.card(full_screen=True):
                ui.card_header("자동음성통보시스템")

                @render.data_frame
                def summary_statistics():
                    cols = [
                        "연번",
                        "행정동명",
                        "도로명주소",
                        "장소명",
                        "좌표정보(X)",
                        "좌표정보(Y)"
                    ]
                    return render.DataGrid(filtered_df()[cols], filters=True)

        ui.include_css(app_dir / "styles.css")

        with ui.layout_columns():
            with ui.card(full_screen=True):
                ui.card_header("경상북도 영천시 자치구별 65세 이상 고령 인구수")

                @render_widget
                def plot_elder_map():
                    with open(app_dir / 'data/ychsi4326.geojson', encoding='utf-8') as f:
                        geojson_data = json.load(f)

                    ych_pop = pd.read_csv(app_dir / "data/ych_pop_clean.csv")

                    fig = px.choropleth_mapbox(
                        ych_pop,
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
                    return fig

            with ui.card(full_screen=True):
                ui.card_header("행정동별 자동음성통보시스템 현황")

                @render_widget
                def admin_chart():
                    admin_counts = filtered_df()['행정동명'].value_counts().reset_index()
                    admin_counts.columns = ['행정동명', '설치 수']
                    
                    fig = px.bar(
                        admin_counts, 
                        x='행정동명', 
                        y='설치 수',
                        color='행정동명',
                        title='행정동별 자동음성통보시스템 설치 현황'
                    )
                    
                    fig.update_layout(xaxis_title='행정동명', yaxis_title='설치 수')
                    return fig

    @reactive.calc
    def filtered_df():
        filt_df = auto_voice[auto_voice["행정동명"].isin(input.space())]
        return filt_df