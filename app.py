import seaborn as sns
from faicons import icon_svg

# Import data from shared.py
from shared import app_dir, df

from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_widget
from pathlib import Path

import pandas as pd

app_dir = Path(__file__).parent
df = pd.read_csv(app_dir / "penguins.csv")




ui.page_opts(title="2025년 제4회 영천시 공공데이터 활용 경진대회", fillable=True)
auto_voice = pd.read_csv("./data/경상북도 영천시_자동음성통보시스템_20241120.csv")

with ui.sidebar(title="Filter controls"):
    ui.input_slider("mass", "Mass", 2000, 6000, 6000)
    ui.input_checkbox_group(
        "space",
        "장소명",
        auto_voice['장소명'].value_counts().index.to_list(),
        selected=auto_voice['장소명'].value_counts().index.to_list(),
    )


with ui.layout_column_wrap(fill=False):
    with ui.value_box(showcase=icon_svg("earlybirds")):
        "자동음성통보시스템 수"

        @render.text
        def count():
            return filtered_df().shape[0]

    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Average bill length"

        @render.text
        def bill_length():
            return f"{filtered_df()['bill_length_mm'].mean():.1f} mm"

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Average bill depth"

        @render.text
        def bill_depth():
            return f"{filtered_df()['bill_depth_mm'].mean():.1f} mm"

import plotly.express as px
import pandas as pd
import geopandas as gpd
import json



with ui.layout_columns():
    with ui.card(full_screen=True):
        ui.card_header("경상북도 영천시 자동음성통보시스템")
        shapefile_path = 'data/ych-map/sig.shp'
        gdf = gpd.read_file(shapefile_path, encoding='euc-kr')

        
        # gdf = gdf.to_crs(epsg=4623)
        gdf.to_file("data/korea_districts.geojson", driver="GeoJSON")
        with open('data/korea_districts.geojson', encoding='utf-8') as f:
            geojson_data = json.load(f)
        

        


        @render_widget
        def auto_voice_map():
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
                title='경상북도 영천시 자동 음성통보시스템'
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


@reactive.calc
def filtered_df():
    filt_df = auto_voice[auto_voice["행정동명"].isin(input.space())]
    # filt_df = filt_df.loc[filt_df["body_mass_g"] < input.mass()]
    return filt_df
