from shiny import reactive
from shiny.express import input, render, ui
from plotly_streaming import render_plotly_streaming
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
import folium  #원정 추가
from folium.features import GeoJsonTooltip, DivIcon
import numpy as np
import plotly.graph_objs as go #원정추가
import matplotlib.pyplot as plt
import seaborn as sns
from htmltools import HTML
import plotly.utils
from shinyswatch import theme
from shared import geojson_data, gdf, geojson_fruit, geojson_buffer, geojson_grid, gdf_grid


#statsmodels 설치 필요

# 환경에 따른 경로 설정
if 'SHINY_SERVER' in os.environ:
    app_dir = Path('/home/shiny')  # shinyapps.io 환경
else:
    app_dir = Path(__file__).parent  # 로컬 환경

# ui.page_opts(title="2025년 제4회 영천시 공공데이터 활용 경진대회", page_fn=partial(page_navbar, id="page"), fillable=False)
# 두번째 잘 되는 네비바
ui.page_opts(title=ui.tags.div(
        ui.img(
            src = "ycs_logo2.png", 
            height="50px", style="vertical-align: middle; margin-right: 10px;"
        ),
        "2025년 제4회 영천시 공공데이터 활용 경진대회",
        style="display: flex; align-items: center;"
    ), page_fn=partial(page_navbar, id="page"), fillable=False, theme=theme.flatly)

auto_voice = pd.read_csv(app_dir / "data/경상북도 영천시_자동음성통보시스템_20241120.csv")
# app_dir = Path(__file__).parent


with ui.nav_panel('자동 음성 통보시스템이란?'):                
    with ui.layout_sidebar():
        with ui.sidebar():
        
            choices = auto_voice['행정동명'].value_counts().index.to_list() #원정추가
            with ui.accordion(open=False):
                with ui.accordion_panel("행정구역"):
                    ui.input_checkbox_group(
                    "space",
                    "행정동명",
                    #auto_voice['행정동명'].value_counts().index.to_list(),
                    selected=auto_voice['행정동명'].value_counts().index.to_list(),
                    choices = choices, #원정추가 / 체크박스 모두 표시 안되게 시작
                    # selected=[choices[0]] #원정추가)
                    )
            
                


            ui.input_action_button("go", "적용", class_="btn-success")

            @render.ui
            @reactive.event(input.go)
            async def compute():
                with ui.Progress(min=1, max=15) as p:
                    p.set(message="Calculation in progress", detail="This may take a while...")
            
            # 여기에 메세지 추가

            ui.input_action_button("show_img", "음성 통보 시스템")

            # 버튼 클릭 시 모달 표시
            @reactive.effect
            @reactive.event(input.show_img)
            def show_modal_with_image():
                m = ui.modal(
                    ui.img(
                        src="음성경보시스템.png",
                        style="width: 100%; height: auto; border: 2px solid black;",
                        alt="음성 통보시스템"
                    ),
                    title="샘플 이미지 보기",
                    easy_close=True,
                    footer=ui.modal_button("닫기")
                )
                ui.modal_show(m)


            ui.input_action_button("show_text1", "음성 통보시스템이란?")

            @reactive.effect
            @reactive.event(input.show_text1)
            def show_important_message():
                m = ui.modal(  
                    ui.markdown("""
                                **음성통보시스템(AVAS, Automated Voice Alert System)은**  
                                특히 **고령자, 시각장애인, 문자 수신이 어려운 정보 취약계층**에게  
                                보다 빠르고 효과적으로 위험 상황을 전달할 수 있어,  
                                **즉각적인 행동 유도와 인명 피해 예방**에 중요한 역할을 합니다.
                                """),
                    size='x1' , 
                    easy_close=True,  
                    footer=None,  
                )  
                ui.modal_show(m)

            ui.input_action_button("show_text2", "적용 사례")

            @reactive.effect
            @reactive.event(input.show_text2)
            def show_important_message():
                m = ui.modal(  
                    ui.markdown("""
                                - 🇫🇷 **프랑스 (2006년)**: 폭염경보시스템(HWS) 도입 후 **약 4,400명의 초과 사망자** 예방  
                                - 🇭🇰 **홍콩(65세 이상)**: 허혈성 심장질환·뇌졸중 등과 관련된 사망 **약 1,300건 감소**  
                                - 🇬🇧 **영국**: 폭염경보 운영을 통해 **117명의 생명 보호** 및 **높은 비용 효율성 입증**"""),  
                    size='x1' , 
                    easy_close=True,  
                    footer=None,  
                )  
                ui.modal_show(m)

            ui.input_action_button("show_text3", "필요성")

            @reactive.effect
            @reactive.event(input.show_text3)
            def show_important_message():
                m = ui.modal(  
                    ui.markdown("""
                                        - 국내 **65세 이상 고령자의 스마트폰 보급률은 66.5%**
                                        - 스마트폰이 아니라면 재난문자 전달율 저하"""),  
                    size='x1' , 
                    easy_close=True,  
                    footer=None,  
                )  
                ui.modal_show(m)

            

                        # for i in range(1, 15):
                        #     p.set(i, message="Computing")
                        #     await asyncio.sleep(0.1)

                return "Done computing!"
        with ui.layout_column_wrap(width=1):
            with ui.card(style="height: auto;"):
                with ui.card():
                    ui.div('경상북도 영천시 자동 음성 통보 시스템 현황', style="text-align: center; font-weight: bold; font-size: 30px;")

                with ui.layout_columns(col_widths=(9,3)):
                    with ui.card(full_screen=True):

                        @render.ui
                        @reactive.event(input.go, ignore_none=False)
                        def simple_auto_voice_map():
                            # 선택된 데이터 처리
                            selected_df = filtered_df()
                            selected_names = input.space()
                            selected_gdf = gdf[gdf['ADM_NM'].isin(selected_names)]
                            selected_geojson = json.loads(selected_gdf.to_json())
                            gdf_points = gpd.GeoDataFrame(
                                selected_df,
                                geometry=gpd.points_from_xy(selected_df['좌표정보(Y)'], selected_df['좌표정보(X)']),
                                crs="EPSG:4326"
                            ).to_crs(epsg=5181)
                            gdf_buffer = gdf_points.copy()
                            gdf_buffer["geometry"] = gdf_points.buffer(500)
                            gdf_buffer = gdf_buffer.to_crs(epsg=4326)
                            buffer_geojson = json.loads(gdf_buffer.to_json())
                        
                            # mapbox layers
                            layers = [
                                {
                                    "sourcetype": "geojson",
                                    "source": geojson_data,
                                    "type": "line",
                                    "color": "black",
                                    "line": {"width": 1},
                                    "below": "traces"
                                },
                                {
                                    "sourcetype": "geojson",
                                    "source": selected_geojson,
                                    "type": "fill",
                                    "color": "rgba(0, 100, 255, 0.2)",
                                    "below": "traces"
                                },
                                {
                                    "sourcetype": "geojson",
                                    "source": buffer_geojson,
                                    "type": "fill",
                                    "color": "rgba(0, 0, 255, 0.1)",
                                    "below": "traces"
                                }
                            ]
                        
                            # plotly figure
                            fig = px.scatter_mapbox(
                                selected_df,
                                lat='좌표정보(X)',
                                lon='좌표정보(Y)',
                                hover_name='장소명',
                                hover_data={'좌표정보(X)': True, '좌표정보(Y)': True},
                                text='장소명',
                                zoom=10,
                                height=600,
                                width=1100
                            )
                        
                            fig.update_layout(
                                mapbox_style="carto-positron",
                                mapbox_center={"lat": 35.97326, "lon": 128.938613},
                                mapbox_layers=layers,
                                margin={"r": 0, "t": 30, "l": 0, "b": 0},
                                
                            )
                        
                            fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
                        
                            # 고유 ID 만들기 (재랜더링 대비)
                            import uuid
                            unique_id = f"mapbox-plot-{uuid.uuid4().hex}"
                        
                            html_code = f"""
                            <div id="{unique_id}" style="height:600px;"></div>
                            <script>
                                (function() {{
                                    const fig = {fig_json};
                                    Plotly.newPlot("{unique_id}", fig.data, fig.layout, {{
                                        scrollZoom: true,
                                        displayModeBar: true,
                                        responsive: true
                                    }});
                                }})();
                            </script>
                            """
                            return HTML(html_code)
                        

                            


                    with ui.layout_column_wrap(width=1):
                        with ui.value_box(showcase=icon_svg("walkie-talkie")):
                            "자동음성통보시스템 수"

                            @render.text
                            @reactive.event(input.go, ignore_none=False)
                            def count():
                                return filtered_df().shape[0]
                                # return input.space()

                        with ui.value_box(showcase=icon_svg("ruler-horizontal")):
                            "행정동별 평균 수"

                            @render.text
                            @reactive.event(input.go, ignore_none=False)
                            def bill_length():
                                return round(filtered_df().groupby(['행정동명']).size().mean(), 2)

                        with ui.value_box(showcase=icon_svg("calendar")):
                            "최신신 설치년도"

                            @render.text
                            @reactive.event(input.go, ignore_none=False)
                            def bill_depth():
                                return f"{filtered_df()['설치일자'].max()}년"


                with ui.layout_columns():
                    with ui.card(full_screen=True):
                        ui.card_header("경상북도 영천시 자동 음성 통보 시스템 행정구역별")

                        @render_widget
                        @reactive.event(input.go, ignore_none=False)
                        def plot_elder_map():
                            with open(app_dir / 'data/ychsi4326.geojson', encoding='utf-8') as f:
                                geojson_data = json.load(f)
                            auto_cnt = auto_voice.groupby(['행정동명']).size().reset_index(name='설치수')
                            # ych_pop = pd.read_csv(app_dir / "data/ych_pop_clean.csv")
                            selected_names = input.space()

                            filtered_features = [
                                feature for feature in geojson_data["features"]
                                if feature["properties"]["ADM_NM"] in selected_names
                                ]
                            filtered_geojson = {
                                "type": "FeatureCollection",
                                "features": filtered_features
                            }

                            # ✅ 데이터도 선택된 것만 필터
                            auto_cnt = auto_voice.groupby(['행정동명']).size().reset_index(name='설치수')
                            auto_cnt = auto_cnt[auto_cnt["행정동명"].isin(selected_names)]

                            # ✅ choropleth 그리기
                            fig = px.choropleth_mapbox(
                                auto_cnt,
                                geojson=filtered_geojson,
                                locations="행정동명",
                                featureidkey="properties.ADM_NM",
                                color="설치수",
                                color_continuous_scale="Blues",
                                mapbox_style="carto-positron",
                                center={"lat": 35.97326, "lon": 128.938613},
                                zoom=9,
                                opacity=0.7,
                                title="경상북도 영천시 자동 음성 통보 시스템 행정구역별"
                            )

                            fig.update_layout(
                                margin={"r":0,"t":30,"l":0,"b":0},
                                title={
                                    'text': "경상북도 영천시 자동 음성 통보 시스템 행정구역별",
                                    'x': 0.5,
                                    'xanchor': 'center'
                                }
                            )

                            return fig

                    with ui.card(full_screen=True):
                        ui.card_header("행정동별 자동음성통보시스템 현황")

                        @render_widget
                        @reactive.event(input.go, ignore_none=False)
                        def admin_chart():
                            admin_counts = auto_voice['행정동명'].value_counts().reset_index()
                            admin_counts.columns = ['행정동명', '설치 수']
                            color_map = {
                                name: "#FF5733" if name in input.space() else "lightgray"
                                for name in admin_counts["행정동명"]
                            }

                            fig = px.bar(
                                admin_counts, 
                                x='행정동명', 
                                y='설치 수',
                                color='행정동명',
                                color_discrete_map=color_map,
                                title='행정동별 자동음성통보시스템 설치 현황'
                            )

                            fig.update_layout(xaxis_title='행정동명', yaxis_title='설치 수')
                            return fig
                        


with ui.nav_panel("온열질환 위험군"):
    with ui.layout_column_wrap():
        with ui.card():
            ui.div("영천시 온열질환 관련 요약 지표(2022년)", style="text-align: center; font-weight: bold; font-size: 25px;")

            with ui.layout_column_wrap(width=1/6): 
                with ui.value_box(showcase=icon_svg("temperature-high")):
                    "최고기온"
                    @render.text
                    def max_temp():
                        return "35.6℃"

                with ui.value_box(showcase=icon_svg("users")):
                    "영천 총인구 대비 온열질환자 비율"
                    @render.text
                    def total_pop():
                        result = round((154 / 100781) * 100,2)
                        return f'{result}%'

                with ui.value_box(showcase=icon_svg("chart-line")):
                    "온열질환 발생순위(157개 시군 중)"
                    @render.text
                    def rank():
                        return "8위"
                    
                with ui.value_box(showcase=icon_svg("user-check")):
                    "65세 이상 비율"
                    @render.text
                    def senior_ratio():
                        return "30.9%"

                with ui.value_box(showcase=icon_svg("hourglass-half")):
                    "평균연령"
                    @render.text
                    def avg_age():
                        return "51.3세"

                with ui.value_box(showcase=icon_svg("leaf")):
                    "농업 종사자 비율"
                    @render.text
                    def farmer_ratio():
                        return "36.1%"

    with ui.layout_columns():
        with ui.layout_sidebar():
            with ui.sidebar():
                with ui.card():
                    ui.h4("연도 선택")
                    ui.input_radio_buttons(
                        id="year_card",
                        label=None,
                        choices=["2020", "2021", "2022", "2023", "2024"],
                        selected="2022"
                    )
                ui.input_action_button("show_img1", "영천시 고령인구 추세")

                # 버튼 클릭 시 모달 표시
                @reactive.effect
                @reactive.event(input.show_img1)
                def show_modal_with_image():
                    m = ui.modal(
                        ui.img(
                            src="ycs_population_graph.png",
                            style="width: 100%; height: auto; border: 2px solid black;",
                            alt="영천시 고령인구 추세선"
                        ),
                        title="영천시 연도별 65세 이상 인구 추세",
                        easy_close=True,
                        footer=ui.modal_button("닫기")
                    )
                    ui.modal_show(m)    
            job_hot_data = pd.read_csv(app_dir / "data/ill_loc.csv")

            with ui.card():
                ui.div('온열질환 발생 현황 분석: 장소, 직종, 연령을 중심으로', style="text-align: center; font-weight: bold; font-size: 30px;")
                ui.div('🔥온열질환: 고온 환경에서 체온 조절이 제대로 되지 않아 발생하는 질환 ➜ 여름철 장시간 실외 작업 및 체온조절 능력이 떨어지는 고령자의 경우 더 쉽게 영향을 받음  ', style="font-weight: bold; font-size: 18px;")
                with ui.layout_column_wrap(width=1 / 2):
                    with ui.card():
                        @render_widget
                        def job_hot():
                            # 데이터 정의
                            selected_year = input.year_card()
                            hit_ill = job_hot_data[selected_year]
                            hit_ill_location = job_hot_data['location']
                            # 실외/실내 분류
                            outdoor_labels = ["실외작업장", "운동장", "논/밭", "산", "강가/해변", "길가", "주거지주변", "실외기타"]
                            # DataFrame 생성 및 구분 열 추가
                            df = pd.DataFrame({"장소": hit_ill_location, "건수": hit_ill})
                            df["구분"] = df["장소"].apply(lambda x: "실외" if x in outdoor_labels else "실내")
                            # 실외/실내 정렬 및 병합
                            df_out = df[df["구분"] == "실외"].sort_values(by="건수", ascending=False)
                            df_in = df[df["구분"] == "실내"].sort_values(by="건수", ascending=False)
                            df_sorted = pd.concat([df_out, df_in])
                            # 색상 지정: 논/밭은 빨간색, 나머지는 파란색 계열
                            colors = ["red" if loc == "논/밭" else "#d3d3d3" for loc in df_sorted["장소"]]
                            # Plotly 막대 그래프 생성
                            fig = go.Figure(go.Bar(
                                x=df_sorted["장소"],
                                y=df_sorted["건수"],
                                marker_color=colors,
                                text=df_sorted["건수"],
                                textposition="outside"
                            ))
                            fig.update_layout(  
                                title="전국 장소별 온열질환 발생 건수",
                                xaxis_title="장소",
                                yaxis_title="온열질환 발생 건수",
                                xaxis_tickangle=-45,
                                template="plotly_white"
                            )
                            return fig
                        ui.card_footer("📌농민 비율은 0.2%지만 논/밭이 온열질환 발생의 2위 장소에 해당.",style="font-size: 18px;")

                    with ui.card():
                        file_path_ = app_dir / "data" / "age_hit_ill.csv"
                        hit_ill_data = pd.read_csv(file_path_)
                        @render_widget
                        def age_hot():
                            # 데이터 정의
                            selected_year = input.year_card()
                            age_groups = hit_ill_data['age_groups']
                            bar_values = hit_ill_data[f"age_{selected_year}"]
                            line_values = hit_ill_data[f"age_10_{selected_year}"]

                            red_ages = ['60-69세', '70-79세', '80세 이상']  # ← 빨간색으로 표시할 연령대 목록
                            bar_colors = ['red' if age in red_ages else '#d3d3d3' for age in age_groups]
                            bar_trace = go.Bar(
                                x=age_groups,
                                y=bar_values,
                                yaxis='y',  # 왼쪽 y축 사용
                                name='온열질환자 수',
                                marker=dict(color=bar_colors)
                            )
                            # 선 그래프 (인구 10만명당 온열질환자 수)
                            line_trace = go.Scatter(
                                x=age_groups,
                                y=line_values,
                                name='인구 10만명당 온열질환자 수(명)',
                                yaxis='y2',  # 오른쪽 y축 사용
                                mode='lines+markers+text',
                                text=line_values,
                                textposition='top center',
                                line=dict(color='red')
                            )
                            # 레이아웃 설정
                            layout = go.Layout(
                                title='전국 연령별 온열질환자 수 및 인구 10만명당 비율',
                                xaxis=dict(title='연령별'),
                                yaxis=dict(title='온열질환자수', side='left'),
                                yaxis2=dict(title='인구 10만명당 온열질환자 수', overlaying='y', side='right'),
                                legend=dict(x=0.0, y=1.0, orientation='v'),
                                bargap=0.3
                            )
                            # 그래프 생성
                            return go.Figure(data=[bar_trace, line_trace], layout=layout)
                        with ui.card_footer(style="font-size: 18px;"):
                            @render.text
                            def age_summary():
                                selected_year = input.year_card()
                                bar_values = hit_ill_data[f"age_{selected_year}"]
                                up_60 = bar_values.iloc[6:].sum() / bar_values.sum() * 100
                                return f"📌 60대 이상의 온열질환 비율: {up_60:.1f}%"

            with ui.card():
                ui.div("온열질환 위험군(농민·고령자) 맞춤 예방 중심의 선제적 알림체계 구축 필요",style="text-align: center; font-weight: bold; font-size: 20px;")

with ui.nav_panel('농업 지역 및 인구 격자'):
    with ui.layout_sidebar():
        with ui.sidebar():
            @render.ui
            @reactive.event(input.go2)
            async def compute2():
                with ui.Progress(min=1, max=15) as p:
                    p.set(message="Calculation in progress", detail="This may take a while...")



                return "Done computing!"
            
            ui.input_action_button("show_text4", "설명")
            @reactive.effect
            @reactive.event(input.show_text4)
            def show_important_message():
                m = ui.modal(  
                    ui.markdown("""
                                -  **영천시 농경지 분포와 ATMS 위치 비교**  
                                    → 농업 활동 밀집 지역 중 **ATMS가 미설치된 사각지대**를 확인할 수 있으며,  
                                        **폭염 시 야외작업 중인 농민 보호**를 위한 우선 설치 지역을 파악

                                -  **영천시 고령인구 분포(500m 격자)와 ATMS 위치 비교**  
                                    → **고령인구 밀집 지역** 중 자동 알림이 어려운 지역을 확인하여,  
                                        **취약계층 보호를 위한 맞춤형 경보 인프라 확충**에 활용 \n
                                
                                ATMS 마커는 재해·기상 특보 발생 시 신속한 경보 전달을 담당하는 시스템의 실제 위치를 나타냅니다.
                                """),
                    size='x1' , 
                    easy_close=True,  
                    footer=None,  
                )  
                ui.modal_show(m)

            ui.input_action_button("show_text5", "활용예시")
            @reactive.effect
            @reactive.event(input.show_text5)
            def show_important_message():
                m = ui.modal(  
                    ui.markdown("""
                                폭염 시 **선제적 알림 및 반복 방송**을 통해 온열질환 예방과 **취약계층 보호**에 기여 \n
                                - **행정기관**: 농경지/고령인구/ATMS 위치를 종합적으로 고려해  **폭염 대응 취약 지역에 대한 우선 설치 계획**을 수립 \n
                                - **정책 결정자 및 재난 대응 부서**: **효율적인 예산 배분**, **경보 사각지대 해소**에 근거 자료로 활용 \n
                                - **지역 주민(농민 및 고령층)**:  **자신의 거주지 주변 ATMS 설치 여부**와 **폭염 정보 수신 가능성**을 직접 확인함으로써, **위험 상황에 대한 대비와 행동 요령 습득에 도움**을 받을 수 있음
                                """),
                    size='x1' , 
                    easy_close=True,  
                    footer=None,  
                )  
                ui.modal_show(m)

        with ui.navset_card_tab(id="tab2"):  
            with ui.nav_panel("영천시 논, 과수, 시설, 마을 재배"):
                with ui.layout_columns(col_widths=(9,3)):
                    with ui.card(full_screen=True):
                        ui.card_header("경상북도 영천시 논,과수,시설 재배 맵 및 자동 음성 통보 시스템")
                        
                        @render.ui()
                        def green_auto_map():  
                            data_geojson = geojson_data
                            fruit_geojson = geojson_fruit
                            buffer_geojson = geojson_buffer  # GeoJSON 변환  #원정추가
                            
                            
                            #### layers
                            layers = [
                                {
                                    "sourcetype": "geojson",
                                    "source": data_geojson,
                                    "type": "line",
                                    "color": "black",
                                    "line": {"width": 1},
                                    "below": "traces"
                                },
                                
                                # ✅ [추가] 각 점의 반경 500m 원 표시
                                {
                                    "sourcetype": "geojson",
                                    "source": buffer_geojson,
                                    "type": "fill",
                                    "color": "rgba(0, 0, 255, 0.4)",
                                    "below": "traces"
                                },
                                # {
                                #     "sourcetype": "geojson",
                                #     "source": buffer_geojson,
                                #     "type": "line",
                                #     "color": "blue",
                                #     "line": {"width": 1},
                                #     "below": "traces"  # 원정추가
                                # }
                            ]
                            
                            # 로딩 때문에 꺼놓음 켜야함
                            layers.append({
                                    "sourcetype": "geojson",  # 과수
                                    "source": geojson_fruit,
                                    "type": "fill",
                                    "color": "rgba(0, 180, 100, 0.5)",  # 진한 청록 (투명도 0.5)
                                    "below": "traces"
                                })
                            
                            fig = px.scatter_mapbox(
                                auto_voice,
                                lat='좌표정보(X)',
                                lon='좌표정보(Y)',
                                # color='색상',
                                hover_name='장소명',
                                hover_data={'좌표정보(X)': True, '좌표정보(Y)': True},
                                text='장소명',
                                zoom=10,
                                height=600,
                                width=1100,
                                title = '경상북도 영천시 자동 음성통보시스템'
                                
                            )
                            fig.update_layout(
                                mapbox_style="carto-positron",
                                mapbox_layers=layers,
                                mapbox_center={"lat": 35.97326, "lon": 128.938613},
                                margin={"r": 0, "t": 30, "l": 0, "b": 0},
                            )
                            
                            html = fig.to_html(include_plotlyjs='cdn',full_html=False, config={"scrollZoom": True})  # ✅ HTML 문자열로 변환
                            return ui.HTML(html)
                           

                        ui.card_footer("< 경상북도_팜맵과 드론 활용 경상북도 영천시 논, 과수, 마을, 시설 재배현황_20210105 >")
                    with ui.card():
                        with ui.value_box(showcase=icon_svg("street-view")):
                            "자동음성통보 경계 밖 노인인구 비율"
                            @render.text
                            def older_out():
                                return "64.6%"
                        with ui.value_box(showcase=icon_svg("mountain-sun")):
                            "자동음성통보 경계 밖 농지면적 비율"
                            @render.text
                            def ground_out():
                                return "73.5%"

                   
            
            with ui.nav_panel("고령 인구 격자 500M"):
                with ui.layout_columns(col_widths=(9,3)):
                    with ui.card(full_screen=True):
                        ui.card_header("경상북도 영천시 고령인구 인구 격자 및 자동 음성 통보 시스템")
                        @render.ui
                        def grid_auto_map():  
                            data_geojson = geojson_data
                            buffer_geojson = geojson_buffer  # GeoJSON 변환  #원정추가


                            #### layers
                            layers = [
                                {
                                    "sourcetype": "geojson",
                                    "source": data_geojson,
                                    "type": "line",
                                    "color": "black",
                                    "line": {"width": 1},
                                    "below": "traces"
                                },

                                # ✅ [추가] 각 점의 반경 500m 원 표시
                                {
                                    "sourcetype": "geojson",
                                    "source": buffer_geojson,
                                    "type": "fill",
                                    "color": "rgba(0, 0, 255, 0.4)",
                                    "below": "traces"
                                },
    
                            ]



                            fig = px.scatter_mapbox(
                                auto_voice,
                                lat='좌표정보(X)',
                                lon='좌표정보(Y)',
                                # color='색상',
                                hover_name='장소명',
                                hover_data={'좌표정보(X)': True, '좌표정보(Y)': True},
                                text='장소명',
                                zoom=10,
                                height=600,
                                width=1100,
                                title='경상북도 영천시 자동 음성통보시스템'
                            )
                            fig.update_layout(
                                mapbox_style="carto-positron",
                                mapbox_layers=layers,
                                mapbox_center={"lat": 35.97326, "lon": 128.938613},
                                margin={"r": 0, "t": 30, "l": 0, "b": 0}
                            )

                            choropleth = go.Choroplethmapbox(
                                            geojson=geojson_grid,            # 격자 geojson
                                            locations=gdf_grid.index,           # 고유 id (index, 혹은 gid)
                                            z=gdf_grid['jenks_class'],          # 구간(색상 기준)
                                            colorscale='Reds',
                                            marker_opacity=0.6,
                                            marker_line_width=0,
                                            customdata=gdf_grid[['val']],       # hover에 보여줄 값 추가
                                            hovertemplate='<b>인구수:</b> %{customdata[0]}<br><b>클래스:</b> %{z}<extra></extra>'
                                        )
                            fig.add_trace(choropleth)
                            html = fig.to_html(include_plotlyjs='cdn',full_html=False, config={"scrollZoom": True})  # ✅ HTML 문자열로 변환
                            return ui.HTML(html)

                        ui.card_footer("< 영천시 500m 고령인구 격자 데이터 >")
           
                    with ui.card():
                        with ui.value_box(showcase=icon_svg("street-view")):
                            ui.markdown("자동음성통보 경계 밖 노인인구 비율")
                            @render.text
                            def older_out2():
                                return "64.6%"
                        with ui.card():
                            ui.markdown("""
                                        <div style="font-size:16px; font-weight:bold; margin-bottom:8px;">🔴 색상 범례</div>
                                        <table>
                                        <thead>
                                        <tr><th>색상</th><th>그룹</th><th>고령 인구수 범위(명)</th></tr>
                                        </thead>
                                        <tbody>
                                        <td><div style="width: 30px; height: 20px; background-color: #fff5f0; border: 1px solid #ccc;"></div></td>
                                        <td>0</td><td>0 - 18</td>
                                        </tr>
                                        <tr>
                                        <td><div style="width: 30px; height: 20px; background-color: #fcbba1; border: 1px solid #ccc;"></div></td>
                                        <td>1</td><td>19 - 113</td>
                                        </tr>
                                        <tr>
                                        <td><div style="width: 30px; height: 20px; background-color: #fb6a4a; border: 1px solid #ccc;"></div></td>
                                        <td>2</td><td>114 - 297</td>
                                        </tr>
                                        <tr>
                                        <td><div style="width: 30px; height: 20px; background-color: #de2d26; border: 1px solid #ccc;"></div></td>
                                        <td>3</td><td>298 - 619</td>
                                        </tr>
                                        <tr>
                                        <td><div style="width: 30px; height: 20px; background-color: #a50f15; border: 1px solid #ccc;"></div></td>
                                        <td>4</td><td>620 - 1110</td>
                                        </tr>
                                        </tbody>
                                        </table>
                                        """)

               

        

    @reactive.calc
    def filtered_df():
        filt_df = auto_voice[auto_voice["행정동명"].isin(input.space())]
        return filt_df


# 4번째 페이지. . . .. . . . .. . . . . . .. 


with ui.nav_panel('자동 음성통보시스템 위치 제안'):
    ui.tags.style("""
    .panel-absolute, .panel-well {
        z-index: 9999 !important;
        position: absolute !important;
        background-color: white !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }
    
    .shiny-card-full-screen {
        z-index: 1000 !important;
    }
    """)
    with ui.panel_absolute(  
    width="300px",  
    right="50px",  
    top="50px",  
    draggable=True,  
    class_="panel-absolute",  # Add class for targeting with CSS

    ):  
        with ui.panel_well(class_="panel-well"):
            ui.h2("지도 레이어 설정")
            ui.input_checkbox_group(
                "option",
                "옵션",
                #auto_voice['행정동명'].value_counts().index.to_list(),
                selected=[],
                choices = ['농경지','인구격자', '고령인구 수 기반 위치 추천','추천 예시'], #원정추가 / 체크박스 모두 표시 안되게 시작
                # selected=[choices[0]] #원정추가
            )
            ui.input_action_button("go2", "적용", class_="btn-success")
            
            ui.markdown('\n')
            ui.br()
            
            
            ui.input_checkbox_group(
                "option2",
                "추천",
                #auto_voice['행정동명'].value_counts().index.to_list(),
                selected=[],
                choices = ['고령인구 수 기반 위치 추천', '추천 예시'], #원정추가 / 체크박스 모두 표시 안되게 시작
                # selected=[choices[0]] #원정추가
            )
            ui.input_action_button("go3", "적용", class_="btn-success")
            
            ui.input_slider("n", "인구수 설정", 0, 100, 10)

            
            @render.ui
            @reactive.event(input.go2)
            @reactive.event(input.go3)
            async def compute3():
                with ui.Progress(min=1, max=15) as p:
                    p.set(message="Calculation in progress", detail="This may take a while...")

                    # for i in range(1, 15):
                    #     p.set(i, message="Computing")
                    #     await asyncio.sleep(0.1)

                return
            
   
    with ui.card(full_screen=True):
        ui.card_header("경상북도 영천시 자동음성통보시스템")

        # @render_plotly_streaming()
        # @render_widget
        @render.ui
        @reactive.event(input.go2, ignore_none=False)
        async def auto_voice_map():
            with ui.Progress(min=0, max=2) as p:
                p.set(0, message='loading map....')

                data_geojson = geojson_data
                

                fruit_geojson = geojson_fruit
                
                selected_names = input.space()  # 원정추가
                selected_gdf = gdf[gdf['ADM_NM'].isin(selected_names)]

                df = filtered_df().copy()
                df['색상'] = df['행정동명'].apply(
                    lambda x: x if x in selected_names else '기타'
                )  # 원정추가


                buffer_geojson = geojson_buffer  # GeoJSON 변환  #원정추가
                

                
                
                

                #### layers
                layers = [
                    {
                        "sourcetype": "geojson",
                        "source": data_geojson,
                        "type": "line",
                        "color": "black",
                        "line": {"width": 1},
                        "below": "traces"
                    },
                    # {
                    #     "sourcetype": "geojson",    # 원정추가가
                    #     "source": data_geojson,
                    #     "type": "fill",
                    #     "color": "rgba(0, 100, 255, 0.2)",  # ✅ 연한 파란색 채움
                    #     "below": "traces"
                    # },
                    # ✅ 선택된 읍면동 테두리 강조
                    # {
                    #     "sourcetype": "geojson",
                    #     "source": selected_geojson,
                    #     "type": "line",
                    #     "color": "blue",
                    #     "line": {"width": 2},
                    #     "below": "traces"
                    # },
                    # ✅ [추가] 각 점의 반경 500m 원 표시
                    {
                        "sourcetype": "geojson",
                        "source": buffer_geojson,
                        "type": "fill",
                        "color": "rgba(100, 149, 237, 0.6)",
                        "below": "traces"
                    },
                    # {
                    #     "sourcetype": "geojson",
                    #     "source": buffer_geojson,
                    #     "type": "line",
                    #     "color": "blue",
                    #     "line": {"width": 1},
                    #     "below": "traces"  # 원정추가
                    # }
                ]

                if "농경지" in input.option():
                    layers.append({
                        "sourcetype": "geojson",  # 과수
                        "source": fruit_geojson,
                        "type": "fill",
                        "color": "rgba(198, 156, 109, 0.8)",  # 연한 초록
                        "below": "traces"
                    })
                
                
                fig = px.scatter_mapbox(
                    df,
                    lat='좌표정보(X)',
                    lon='좌표정보(Y)',
                    color='색상',
                    hover_name='장소명',
                    hover_data={'좌표정보(X)': True, '좌표정보(Y)': True},
                    text='장소명',
                    zoom=10,
                    height=800,
                    width=1600,
                    title='경상북도 영천시 자동 음성통보시스템'
                )
                
                
                
                
                recd_df = pd.DataFrame({
                        "name": ["A", "B", "C"],
                        "위도": [36.00875, 35.98994, 36.0012],
                        "경도": [128.98943, 128.96914, 129.02328]
                    })
                    
                recommend = px.scatter_mapbox(
                    recd_df,
                    lat="위도",
                    lon="경도",
                    hover_name="name",  # 마우스 오버시 이름 표시
                    zoom=10,
                    height=600,
                    mapbox_style="carto-positron"  # 기본 지도 스타일
                )
                
                
                if '추천 예시' in input.option():
                
                    # df_points는 이미 있음
                    recd_points = gpd.GeoDataFrame(
                        recd_df,
                        geometry=gpd.points_from_xy(recd_df["경도"], recd_df["위도"]),  # 경도, 위도 순!
                        crs="EPSG:4326"
                    ).to_crs(epsg=5181)  # 미터 좌표계

                    recd_buffer = recd_points.copy()
                    recd_buffer["geometry"] = recd_points.buffer(500)  # 500m 원

                    recd_buffer = recd_buffer.to_crs(epsg=4326)  # 다시 위경도로
                    geojson_recd = json.loads(recd_buffer.to_json())
                    
                
                    for trace in recommend.data:
                        fig.add_trace(trace)
                    
                    layers.append({
                        "sourcetype": "geojson",
                        "source": geojson_recd,
                        "type": "fill",
                        "color": "rgba(0, 128, 0, 0.6)",  # 초록색, 원 색상 원하는대로 변경
                        "below": "traces"
                    })
                    
                    
                

                if "인구격자" in input.option():
                    choropleth = go.Choroplethmapbox(
                                    geojson=geojson_grid,            # 격자 geojson
                                    locations=gdf_grid.index,           # 고유 id (index, 혹은 gid)
                                    z=gdf_grid['jenks_class'],          # 구간(색상 기준)
                                    colorscale='Reds',
                                    marker_opacity=0.6,
                                    showscale=False,
                                    marker_line_width=0,
                                    customdata=gdf_grid[['val']],       # hover에 보여줄 값 추가
                                    hovertemplate='<b>인구수:</b> %{customdata[0]}<br><b>클래스:</b> %{z}<extra></extra>'
                                )
                    fig.add_trace(choropleth)
                    
                if "고령인구 수 기반 위치 추천" in input.option():
                    from shapely.geometry import shape

                    # 파일 경로
                    grid_path = app_dir / "data/elderly_grid_squares.geojson"
                    diff_path = app_dir / "data/difference_area.geojson"

                    # GeoJSON 수동 파싱
                    with open(grid_path, encoding="utf-8") as f:
                        geojson_elderly = json.load(f)
                    
                    # geometry 생성
                    geometries = [shape(feature["geometry"]) for feature in geojson_elderly["features"]]
                    properties = [feature["properties"] for feature in geojson_elderly["features"]]

                    # GeoSeries로 geometry 구성
                    geometry_series = gpd.GeoSeries(geometries, crs="EPSG:4326")

                    # GeoDataFrame 생성
                    gdf_grid_rec = gpd.GeoDataFrame(properties, geometry=geometry_series)

                    # difference_area.geojson 불러오기
                    gdf_diff = gpd.read_file(diff_path)

                    # 좌표계 맞추기
                    gdf_grid_rec = gdf_grid_rec.to_crs(gdf_diff.crs)

                    # val < 5 조건을 만족하는 사각형 필터링
                    gdf_small_val = gdf_grid_rec[gdf_grid_rec["val"] < input.n()].copy()

                    # 병합된 geometry로 삭제 대상 생성
                    removal_union = gdf_small_val.unary_union

                    # 차집합 수행
                    gdf_diff["geometry"] = gdf_diff.geometry.difference(removal_union)

                    # 유효한 geometry만 남기기
                    gdf_diff = gdf_diff[gdf_diff.is_valid & ~gdf_diff.is_empty]
                    gdf_diff = gdf_diff.to_crs("EPSG:4326")
                    # # 저장
                    output_path = app_dir / "data/difference_area_filtered21.geojson"
                    gdf_diff.to_file(output_path, driver="GeoJSON")
                    
                    
                    # GeoJSON 수동 파싱
                    # with open(output_path, encoding="utf-8") as f:
                    #     geojson_diff = json.load(f)
                    
                    
                    
                    geojson_diff = json.loads(gdf_diff.to_json())
                    
                    layers.append({
                        "sourcetype": "geojson",  # 
                        "source": geojson_diff,
                        "type": "fill",
                        "color": "rgba(0, 210, 0, 0.8)",  # 연한 초록
                        "below": "traces"
                    })
                    
               
                fig.update_layout(
                    mapbox_style="carto-positron",
                    mapbox_layers=layers,
                    mapbox_center={"lat": 35.97326, "lon": 128.938613},
                    margin={"r": 0, "t": 30, "l": 0, "b": 0}
                )
                    


                p.set(2, message="complete")
                
               
                fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
                        
                # 고유 ID 만들기 (재랜더링 대비)
                import uuid
                unique_id = f"mapbox-plot-{uuid.uuid4().hex}"
            
                html_code = f"""
                <div id="{unique_id}" style="height:600px;"></div>
                <script>
                    (function() {{
                        const fig = {fig_json};
                        Plotly.newPlot("{unique_id}", fig.data, fig.layout, {{
                            scrollZoom: true,
                            displayModeBar: true,
                            responsive: true
                        }});
                    }})();
                </script>
                """
                return HTML(html_code)


                    # with ui.card(full_screen=True):
                    #     ui.card_header("자동음성통보시스템")

                    #     @render.data_frame
                    #     @reactive.event(input.go, ignore_none=False)
                    #     def summary_statistics():
                    #         cols = [
                    #             "연번",
                    #             "행정동명",
                    #             "도로명주소",
                    #             "장소명",
                    #             "좌표정보(X)",
                    #             "좌표정보(Y)"
                    #         ]
                    #         return render.DataGrid(filtered_df()[cols], filters=True)

                # ui.include_css(app_dir / "styles.css")

