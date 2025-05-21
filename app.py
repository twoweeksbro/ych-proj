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

import plotly.graph_objs as go #원정추가
import matplotlib.pyplot as plt
import seaborn as sns

import asyncio

from shared import geojson_data, gdf, geojson_fruit, geojson_buffer, geojson_grid, gdf_grid, geojson_green_single


#statsmodels 설치 필요

# 환경에 따른 경로 설정
if 'SHINY_SERVER' in os.environ:
    app_dir = Path('/home/shiny')  # shinyapps.io 환경
else:
    app_dir = Path(__file__).parent  # 로컬 환경

# app_dir = Path(__file__).parent

# ui.page_opts(title="2025년 제4회 영천시 공공데이터 활용 경진대회", page_fn=partial(page_navbar, id="page"), fillable=False)
# 두번째 잘 되는 네비바
ui.page_opts(title=ui.tags.div(
        ui.img(
            src = "auto-voice-logo.png", 
            height="50px", style="vertical-align: middle; margin-right: 10px;"
        ),
        "2025년 제4회 영천시 공공데이터 활용 경진대회",
        style="display: flex; align-items: center;"
    ), page_fn=partial(page_navbar, id="page"), fillable=False)

auto_voice = pd.read_csv(app_dir / "data/경상북도 영천시_자동음성통보시스템_20241120.csv")

with ui.nav_panel("온열질환 위험성"):
    with ui.layout_columns(col_widths=(4,8)):
        with ui.layout_column_wrap(width=1):
            with ui.card():
                # 시각화
                @render_widget
                def year_hot():
                    file_path = app_dir / "data" / "heat_ill.csv"
                    merged_df = pd.read_csv(file_path)
                    bar_trace = go.Bar(
                        x=merged_df["연도"],
                        y=merged_df["온열질환자 수"],
                        yaxis='y',
                        name='온열질환자 수',
                    )
                    line_trace = go.Scatter(
                        x=merged_df["연도"],
                        y=merged_df["폭염일수"],
                        name='폭염 일수',
                        yaxis='y2',
                        mode='lines+markers+text',
                        text=merged_df["폭염일수"],
                        textposition='top center',
                        line=dict(color='red')
                    )
                    layout = go.Layout(
                        title='영천시 연도별 온열질환자 수 및 폭염 일수',
                        xaxis=dict(title='연도',type='category'),
                        yaxis=dict(title='온열질환자 수', side='left'),
                        yaxis2=dict(title='폭염일수', overlaying='y', side='right'),
                        legend=dict(x=0.0, y=1.0, orientation='v'),
                        bargap=0.3
                    )
                    return go.Figure(data=[bar_trace, line_trace], layout=layout)
            with ui.card():
                @render_widget
                def year_hot_corr():
                    file_path = app_dir / "data" / "heat_ill.csv"
                    df = pd.read_csv(file_path)
                    from scipy.stats import pearsonr
                    # 상관계수 계산
                    correlation, p_value = pearsonr(df['폭염일수'], df['온열질환자 수'])
                    # Plotly 회귀선 산점도 생성
                    fig = px.scatter(
                        df,
                        x="폭염일수",
                        y="온열질환자 수",
                        trendline="ols",  # 회귀선 추가
                        title=f"폭염일수와 온열질환자수의 상관관계 (r={correlation:.2f}, p={p_value:.3f})",
                        labels={"폭염일수": "폭염일수", "온열질환자 수": "온열질환자수"},
                    )
                    fig.update_layout(
                        xaxis_title="폭염일수",
                        yaxis_title="온열질환자수",
                        template="plotly_white",
                        height=500
                    )
                    return fig
    
        with ui.navset_card_tab(id="tab"):  
            with ui.nav_panel("직종"):
                with ui.layout_column_wrap(width=1 / 2):
                    with ui.card():
                        @render_widget
                        def job_hot():
                            # 데이터 정의
                            hit_ill = [581, 95, 230, 41, 17, 161, 57, 103, 66, 36, 127, 22, 28]
                            hit_ill_location = [
                                "실외작업장", "운동장", "논/밭", "산", "강가/해변", "길가", "주거지주변", "실외기타",
                                "집", "건물", "실내작업장", "비닐하우스", "실내기타"
                            ]

                            # 실외/실내 분류
                            outdoor_labels = ["실외작업장", "운동장", "논/밭", "산", "강가/해변", "길가", "주거지주변", "실외기타"]
                            indoor_labels = ["집", "건물", "실내작업장", "비닐하우스", "실내기타"]

                            # DataFrame 생성 및 구분 열 추가
                            df = pd.DataFrame({"장소": hit_ill_location, "건수": hit_ill})
                            df["구분"] = df["장소"].apply(lambda x: "실외" if x in outdoor_labels else "실내")

                            # 실외/실내 정렬 및 병합
                            df_out = df[df["구분"] == "실외"].sort_values(by="건수", ascending=False)
                            df_in = df[df["구분"] == "실내"].sort_values(by="건수", ascending=False)
                            df_sorted = pd.concat([df_out, df_in])

                            # 색상 지정: 논/밭은 빨간색, 나머지는 파란색 계열
                            colors = ["red" if loc == "논/밭" else "#1f77b4" for loc in df_sorted["장소"]]

                            # Plotly 막대 그래프 생성
                            fig = go.Figure(go.Bar(
                                x=df_sorted["장소"],
                                y=df_sorted["건수"],
                                marker_color=colors,
                                text=df_sorted["건수"],
                                textposition="outside"
                            ))

                            fig.update_layout(  
                                title="폭염 관련 장소별 온열질환 발생 건수",
                                xaxis_title="장소",
                                yaxis_title="온열질환 발생 건수",
                                xaxis_tickangle=-45,
                                template="plotly_white"
                            )

                            return fig

                    with ui.card():
                        @render_widget
                        def job():
                            file_path_ = app_dir / "data" / "job.csv"
                            df = pd.read_csv(file_path_)
                            data_2022 = df[df["연도"] == 2022].iloc[0]
                            labels = ['관리자', '사무종사자', '서비스업종사자', '농어업종사자', '기계종사자', '단순노무종사자']
                            values = data_2022[labels].tolist()
                            fig_donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4)])
                            return fig_donut.update_layout(title='2022년 연도별 영천시 직종비율')
            with ui.nav_panel("나이"):
                with ui.layout_column_wrap(width=1 / 2):
                    with ui.card():
                        @render_widget
                        def age_hot():
                            # 데이터 정의
                            age_groups = ['0-9세', '10-19세', '20-29세', '30-39세', '40-49세', '50-59세', '60-69세', '70-79세', '80세 이상']
                            bar_values = [12, 103, 372, 478, 538, 716, 678, 434, 373]
                            line_values = [0.4, 2.2, 6.2, 7.2, 6.9, 8.2, 8.7, 10.6, 15.4]
                            # 막대 그래프 (온열질환자 수)
                            bar_trace = go.Bar(
                                x=age_groups,
                                y=bar_values,
                                yaxis='y',  # 왼쪽 y축 사용
                                name='온열질환자 수',
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
                                title='연령별 온열질환자 수 및 인구 10만명당 비율',
                                xaxis=dict(title='연령별'),
                                yaxis=dict(title='온열질환자수', side='left'),
                                yaxis2=dict(title='인구 10만명당 온열질환자 수', overlaying='y', side='right'),
                                legend=dict(x=0.0, y=1.0, orientation='v'),
                                bargap=0.3
                            )
                            # 그래프 생성
                            return go.Figure(data=[bar_trace, line_trace], layout=layout)
                    with ui.card():
                        @render_widget
                        def ycs_age():
                            file_path_ = app_dir / "data" / "age1.csv"
                            age = pd.read_csv(file_path_)
                            labels = age["나이대"].tolist()
                            values = age["2022"].tolist()  # 2022년 열 값 사용
                            labels
                            fig_donut = go.Figure(
                                data=[go.Pie(labels=labels, values=values, hole=0.4, sort=False)]
                            )
                            return fig_donut.update_layout(title="2022년 연도별 영천시 나이대 비율 (도넛차트)")

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

                    # for i in range(1, 15):
                    #     p.set(i, message="Computing")
                    #     await asyncio.sleep(0.1)

                return "Done computing!"
            
        with ui.layout_column_wrap(width=1):
            with ui.card():
                with ui.card():
                    ui.div('🔥 폭염 피해 예방의 핵심: 음성경보시스템', style="text-align: center; font-weight: bold; font-size: 30px;")
                with ui.layout_column_wrap():
                    with ui.card():
                        ui.h4("✅ 음성경보시스템(AVAS)의 온열질환 예방 효과")
                        with ui.layout_column_wrap(width=1):
                            with ui.card(style="max-height: 250px;"):
                                ui.markdown("""
                                    ### **1. 사망자 수 감소 효과 (Heat-related Mortality 감소)** 
                                    - 🇫🇷 **프랑스 (2006년)**: 폭염경보시스템(HWS) 도입 후 **약 4,400명의 초과 사망자** 예방  
                                    - 🇭🇰 **홍콩(65세 이상)**: 허혈성 심장질환·뇌졸중 등과 관련된 사망 **약 1,300건 감소**  
                                    - 🇬🇧 **영국**: 폭염경보 운영을 통해 **117명의 생명 보호** 및 **높은 비용 효율성 입증**""")
                            with ui.card(style="max-height: 250px;"):
                                ui.markdown("""
                                            ### **2. 문자 기반 재난경보의 한계 보완** 
                                            - 국내 **65세 이상 고령자의 스마트폰 보급률은 66.5%
                                            - 스마트폰이 아니라면 재난문자 전달율 저하""")

                    with ui.card():
                        ui.h4("✅ 음성경보시스템의 정의")
                        with ui.layout_column_wrap(width=1):
                            with ui.card(style="max-height: 250px;"):
                                ui.markdown("""
                                    ### **음성경보시스템이란?**  

                                    **음성경보시스템(AVAS, Automated Voice Alert System)은**  
                                    특히 **고령자, 시각장애인, 문자 수신이 어려운 정보 취약계층**에게  
                                    보다 빠르고 효과적으로 위험 상황을 전달할 수 있어,  
                                    **즉각적인 행동 유도와 인명 피해 예방**에 중요한 역할을 합니다.
                                    """)
                            with ui.card(style="max-height: 250px;"):
                                ui.h4("🔥 폭염 단계별 대응 수칙")

                                ui.markdown("""
                            | 구분   | 체감온도 기준 | 휴식 기준           | 야외 작업 기준           | 비고              |
                            |--------|----------------|----------------------|----------------------------|-------------------|
                            | 주의   | 33도           | 매 시간 10분 휴식    | 14~17시 야외 작업 조정     | -                 |
                            | 경고   | 35도           | 매 시간 15분 휴식    | 14~17시 야외 작업 중지     | -                 |
                            | 위험   | 38도           | 매 시간 15분 휴식    | 14~17시 야외 작업 중지     | 업무담당자 파견    |
                                """)
                    with ui.card():
                        ui.img(
                            src="음성경보시스템.png",
                            alt="온열질환 예방 안내 이미지",
                            style="height:600px; width:auto; display:block; margin:auto;"
                        )
                
            
        
        with ui.layout_columns(col_widths=(9,3)):
            with ui.card(full_screen=True):
                ui.card_header("경상북도 영천시 자동 음성 통보 시스템 현황")
                @render_widget
                @reactive.event(input.go, ignore_none=False)
                def simple_auto_voice_map():  
                    data_geojson = geojson_data
                    selected_df = filtered_df()
                    gdf_points = gpd.GeoDataFrame(
                        selected_df,
                        geometry=gpd.points_from_xy(selected_df['좌표정보(Y)'], selected_df['좌표정보(X)']),
                        crs="EPSG:4326"
                    ).to_crs(epsg=5181)
                    gdf_buffer = gdf_points.copy()
                    gdf_buffer["geometry"] = gdf_points.buffer(500)
                    gdf_buffer = gdf_buffer.to_crs(epsg=4326)
                    buffer_geojson = json.loads(gdf_buffer.to_json())
                    
                    
                                
                    selected_names = input.space()  # 원정추가
                    selected_gdf = gdf[gdf['ADM_NM'].isin(selected_names)]
                    selected_geojson = json.loads(selected_gdf.to_json())
                    
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
                        {
                                "sourcetype": "geojson",    # 원정추가가
                                "source": selected_geojson,
                                "type": "fill",
                                "color": "rgba(0, 100, 255, 0.2)",  # ✅ 연한 파란색 채움
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
                        # {
                        #     "sourcetype": "geojson",
                        #     "source": buffer_geojson,
                        #     "type": "line",
                        #     "color": "blue",
                        #     "line": {"width": 1},
                        #     "below": "traces"  # 원정추가
                        # }
                    ]
                    
                    
                    fig = px.scatter_mapbox(
                        selected_df,
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
                    
                    
                    return fig
                
                            
             
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
                    "평균 설치년도"

                    @render.text
                    @reactive.event(input.go, ignore_none=False)
                    def bill_depth():
                        return f"{filtered_df()['설치일자'].mean():.1f}년"

        
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

                    fig = px.choropleth_mapbox(
                        auto_cnt,
                        geojson=geojson_data,
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

                    fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
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


with ui.nav_panel('농업 지역 및 인구 격자'):
    with ui.layout_sidebar():
        with ui.sidebar():
            # choices = auto_voice['행정동명'].value_counts().index.to_list() #원정추가
            # ui.input_checkbox_group(
            #     "space2",
            #     "행정동명",
            #     #auto_voice['행정동명'].value_counts().index.to_list(),
            #     selected=auto_voice['행정동명'].value_counts().index.to_list(),
            #     choices = choices, #원정추가 / 체크박스 모두 표시 안되게 시작
            #     # selected=[choices[0]] #원정추가
            # )

            # ui.input_action_button("go", "적용", class_="btn-success")

            ui.input_checkbox_group(
                "option",
                "옵션",
                #auto_voice['행정동명'].value_counts().index.to_list(),
                selected=[],
                choices = ['농경지','인구격자'], #원정추가 / 체크박스 모두 표시 안되게 시작
                # selected=[choices[0]] #원정추가
            )
            ui.input_radio_buttons(
                "radio",
                "옵션",
                {"grid": "노령 인구 격자 500M", "green" : "농업 지역"}
                
            )

            ui.input_action_button("go2", "적용", class_="btn-success")

            @render.ui
            @reactive.event(input.go2)
            async def compute2():
                with ui.Progress(min=1, max=15) as p:
                    p.set(message="Calculation in progress", detail="This may take a while...")

                    # for i in range(1, 15):
                    #     p.set(i, message="Computing")
                    #     await asyncio.sleep(0.1)

                return "Done computing!"
            
       
        # with ui.layout_columns():
        with ui.navset_card_tab(id="tab2"):  
            with ui.nav_panel("영천시 논, 과수, 시설, 마을 재배"):
                with ui.layout_columns(col_widths=(9,3)):
                    with ui.card(full_screen=True):
                        ui.card_header("경상북도 영천시 논,과수,시설 재배 맵 및 자동 음성 통보 시스템")
                        
                        @render_widget
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
                                    "color": "rgba(0, 0, 255, 0.1)",
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
                            # layers.append({
                            #         "sourcetype": "geojson",  # 과수
                            #         "source": geojson_fruit,
                            #         "type": "fill",
                            #         "color": "rgba(189, 215, 231, 0.2)",  # 연한 초록
                            #         "below": "traces"
                            #     })
                            
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
                            
                            
                            return fig

                        ui.card_footer("< 경상북도_팜맵과 드론 활용 경상북도 영천시 논, 과수, 마을, 시설 재배현황_20210105 >")

                    
                    
                    with ui.card(full_screen=True):
                        # ui.card_header("")

                        "- 농업 지역:"
                        ui.br()
                        "논 재배현황 시각화."
                        ui.br()
                        "과수 재배현황 시각화."
                        ui.br()
                        "마을 재배현황 시각화."
                        ui.br()
                        "시설 재배현황 시각화."
                        # ui.card_footer("<경상북도_팜맵과 드론 활용 경상북도 영천시 논, 과수, 마을, 시설 재배현황_20210105>")
                        
                    with ui.card(full_screen=True):
                        "text"
                        
                            
            
            with ui.nav_panel("노령 인구 격자 500M"):
                with ui.card(full_screen=True):
                    ui.card_header("경상북도 영천시 고령인구 인구 격자 및 자동 음성 통보 시스템")
                    @render_widget
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
                                "color": "rgba(0, 0, 255, 0.1)",
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
                        
                        return fig
                    
            
    
        
        

    @reactive.calc
    def filtered_df():
        filt_df = auto_voice[auto_voice["행정동명"].isin(input.space())]
        return filt_df
    
with ui.nav_panel('자동 음성통보시스템 위치 제안'):
    with ui.card(full_screen=True):
        ui.card_header("This is the header")
    #     with ui.layout_columns():
    #         with ui.card(full_screen=True):
    #             ui.card_header("경상북도 영천시 자동음성통보시스템")

    #             # @render_plotly_streaming()
    #             # @render_widget
    #             @render.ui
    #             @reactive.event(input.go, ignore_none=False)
    #             async def auto_voice_map():
    #                 with ui.Progress(min=0, max=2) as p:
    #                     p.set(0, message='loading map....')

    #                     # shapefile_path = app_dir / 'data/ychsi-map/ychsi.shp'
    #                     # gdf = gpd.read_file(shapefile_path)

    #                     # gdf = gdf.to_crs(epsg=4326)  # 원정추가
    #                     # gdf_boundary = gdf.copy()
    #                     # gdf_boundary["geometry"] = gdf_boundary["geometry"].boundary
    #                     # geojson_path = app_dir / "data/ychsi.geojson"  # 원정추가

    #                     # gdf_boundary.to_file(geojson_path, driver="GeoJSON")

    #                     # with open(geojson_path, encoding='utf-8') as f:
    #                     #     geojson_data = json.load(f)
    #                     data_geojson = geojson_data
                        
    #                     # fruit_path = app_dir / "data/green.geojson"
    #                     # with open(fruit_path, encoding='utf-8') as f:
    #                     #     fruit_geojson = json.load(f)
    #                     fruit_geojson = geojson_fruit
                        
    #                     selected_names = input.space()  # 원정추가
    #                     selected_gdf = gdf[gdf['ADM_NM'].isin(selected_names)]
    #                     selected_geojson = json.loads(selected_gdf.to_json())

    #                     df = filtered_df().copy()
    #                     df['색상'] = df['행정동명'].apply(
    #                         lambda x: x if x in selected_names else '기타'
    #                     )  # 원정추가

    #                     # ✅ [추가] 점 → 500m 버퍼 (원) 생성   원정추가
    #                     # gdf_points = gpd.GeoDataFrame(
    #                     #     df,
    #                     #     geometry=gpd.points_from_xy(df['좌표정보(Y)'], df['좌표정보(X)']),
    #                     #     crs="EPSG:4326"
    #                     # ).to_crs(epsg=5181)  # 미터 단위 좌표계

    #                     # gdf_buffer = gdf_points.copy()
    #                     # gdf_buffer["geometry"] = gdf_points.buffer(500)  # 500m 원

    #                     # gdf_buffer = gdf_buffer.to_crs(epsg=4326)  # 다시 위경도로
    #                     # buffer_geojson = json.loads(gdf_buffer.to_json())  # GeoJSON 변환  #원정추가
    #                     buffer_geojson = geojson_buffer  # GeoJSON 변환  #원정추가
                        
                        
    #                     recd_df = pd.DataFrame({
    #                             "name": ["A", "B", "C"],
    #                             "위도": [36.00875, 35.98994, 36.0012],
    #                             "경도": [128.98943, 128.96914, 129.02328]
    #                         })
                            
    #                     recommend = px.scatter_mapbox(
    #                         recd_df,
    #                         lat="위도",
    #                         lon="경도",
    #                         hover_name="name",  # 마우스 오버시 이름 표시
    #                         zoom=10,
    #                         height=600,
    #                         mapbox_style="carto-positron"  # 기본 지도 스타일
    #                     )
                        
                        
                            
                        
    #                     # df_points는 이미 있음
    #                     recd_points = gpd.GeoDataFrame(
    #                         recd_df,
    #                         geometry=gpd.points_from_xy(recd_df["경도"], recd_df["위도"]),  # 경도, 위도 순!
    #                         crs="EPSG:4326"
    #                     ).to_crs(epsg=5181)  # 미터 좌표계

    #                     recd_buffer = recd_points.copy()
    #                     recd_buffer["geometry"] = recd_points.buffer(500)  # 500m 원

    #                     recd_buffer = recd_buffer.to_crs(epsg=4326)  # 다시 위경도로
    #                     geojson_recd = json.loads(recd_buffer.to_json())
                        

    #                     #### layers
    #                     layers = [
    #                         {
    #                             "sourcetype": "geojson",
    #                             "source": data_geojson,
    #                             "type": "line",
    #                             "color": "black",
    #                             "line": {"width": 1},
    #                             "below": "traces"
    #                         },
    #                         # {
    #                         #     "sourcetype": "geojson",    # 원정추가가
    #                         #     "source": selected_geojson,
    #                         #     "type": "fill",
    #                         #     "color": "rgba(0, 100, 255, 0.2)",  # ✅ 연한 파란색 채움
    #                         #     "below": "traces"
    #                         # },
    #                         # ✅ 선택된 읍면동 테두리 강조
    #                         {
    #                             "sourcetype": "geojson",
    #                             "source": selected_geojson,
    #                             "type": "line",
    #                             "color": "blue",
    #                             "line": {"width": 3},
    #                             "below": "traces"
    #                         },
    #                         # ✅ [추가] 각 점의 반경 500m 원 표시
    #                         {
    #                             "sourcetype": "geojson",
    #                             "source": buffer_geojson,
    #                             "type": "fill",
    #                             "color": "rgba(0, 0, 255, 0.1)",
    #                             "below": "traces"
    #                         },
    #                         # {
    #                         #     "sourcetype": "geojson",
    #                         #     "source": buffer_geojson,
    #                         #     "type": "line",
    #                         #     "color": "blue",
    #                         #     "line": {"width": 1},
    #                         #     "below": "traces"  # 원정추가
    #                         # }
    #                         {
    #                             "sourcetype": "geojson",
    #                             "source": geojson_recd,
    #                             "type": "fill",
    #                             "color": "rgba(255, 0, 0, 0.2)",  # 연한 빨강색, 원 색상 원하는대로 변경
    #                             "below": "traces"
    #                         }
    #                     ]

    #                     if "농경지" in input.option():
    #                         layers.append({
    #                             "sourcetype": "geojson",  # 과수
    #                             "source": fruit_geojson,
    #                             "type": "fill",
    #                             "color": "rgba(0, 255, 0, 0.2)",  # 연한 초록
    #                             "below": "traces"
    #                         })
                        
                        
    #                     fig = px.scatter_mapbox(
    #                         df,
    #                         lat='좌표정보(X)',
    #                         lon='좌표정보(Y)',
    #                         color='색상',
    #                         hover_name='장소명',
    #                         hover_data={'좌표정보(X)': True, '좌표정보(Y)': True},
    #                         text='장소명',
    #                         zoom=10,
    #                         height=800,
    #                         width=1300,
    #                         title='경상북도 영천시 자동 음성통보시스템'
    #                     )
    #                     fig.update_layout(
    #                         mapbox_style="carto-positron",
    #                         mapbox_layers=layers,
    #                         mapbox_center={"lat": 35.97326, "lon": 128.938613},
    #                         margin={"r": 0, "t": 30, "l": 0, "b": 0}
    #                     )
                        
    #                     for trace in recommend.data:
    #                         fig.add_trace(trace)
                        

    #                     if "인구격자" in input.option():
    #                         choropleth = go.Choroplethmapbox(
    #                                         geojson=geojson_grid,            # 격자 geojson
    #                                         locations=gdf_grid.index,           # 고유 id (index, 혹은 gid)
    #                                         z=gdf_grid['jenks_class'],          # 구간(색상 기준)
    #                                         colorscale='Blues',
    #                                         marker_opacity=0.6,
    #                                         marker_line_width=0,
    #                                         customdata=gdf_grid[['val']],       # hover에 보여줄 값 추가
    #                                         hovertemplate='<b>인구수:</b> %{customdata[0]}<br><b>클래스:</b> %{z}<extra></extra>'
    #                                     )
    #                         fig.add_trace(choropleth)
                            


    #                     p.set(2, message="complete")
                        
    #                     return fig


    #             # with ui.card(full_screen=True):
    #             #     ui.card_header("자동음성통보시스템")

    #             #     @render.data_frame
    #             #     @reactive.event(input.go, ignore_none=False)
    #             #     def summary_statistics():
    #             #         cols = [
    #             #             "연번",
    #             #             "행정동명",
    #             #             "도로명주소",
    #             #             "장소명",
    #             #             "좌표정보(X)",
    #             #             "좌표정보(Y)"
    #             #         ]
    #             #         return render.DataGrid(filtered_df()[cols], filters=True)

    #         # ui.include_css(app_dir / "styles.css")

        
    #     ui.p("This is the body.")
    #     ui.p("This is still the body.")
    #     ui.card_footer("This is the footer")
        
    # with ui.card():
    #     @render_widget
    #     def test_map():
    #         df = pd.DataFrame({
    #                             "name": ["A", "B", "C"],
    #                             "위도": [36.00875, 35.98994, 36.0012],
    #                             "경도": [128.98943, 128.96914, 129.02328]
    #                         })
                            
    #         recommend = px.scatter_mapbox(
    #             df,
    #             lat="위도",
    #             lon="경도",
    #             hover_name="name",  # 마우스 오버시 이름 표시
    #             color='red',
    #             zoom=10,
    #             height=600,
    #             mapbox_style="carto-positron"  # 기본 지도 스타일
    #         )
            
    #         return recommend
    
    
# ui.nav_spacer()
# with ui.nav_panel(ui.img(
#             src = "auto-voice-logo.png", 
#             height="50px", style="vertical-align: middle; margin-right: 10px;"
#         )):
#     with ui.card():
#         ui.card_header("Hello World!")
