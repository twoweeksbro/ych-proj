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

import asyncio

from shared import geojson_data, gdf, geojson_fruit, geojson_buffer, geojson_grid, gdf_grid, geojson_green_single


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
            src = "auto-voice-logo.png", 
            height="50px", style="vertical-align: middle; margin-right: 10px;"
        ),
        "2025년 제4회 영천시 공공데이터 활용 경진대회",
        style="display: flex; align-items: center;"
    ), page_fn=partial(page_navbar, id="page"), fillable=False)

auto_voice = pd.read_csv(app_dir / "data/경상북도 영천시_자동음성통보시스템_20241120.csv")
# app_dir = Path(__file__).parent

with ui.nav_panel("온열질환 위험성"):
    with ui.layout_column_wrap():
        with ui.card():
            ui.h4("10만명당 온열질환자 수")

            @render_widget
            def choropleth_map_plotly():
                csv_path = app_dir / "data/온열질환자_지도용.csv"
                geo_path = app_dir / "data/TL_SCCO_CTPRVN.json"

                # 데이터 로딩
                df = pd.read_csv(csv_path)
                with open(geo_path, encoding="utf-8") as f:
                    geojson = json.load(f)

                fig = px.choropleth(
                    df,
                    geojson=geojson,
                    featureidkey="properties.CTP_KOR_NM",
                    locations="지역",
                    color="10만명당 온열질환자수",
                    color_continuous_scale="YlOrRd",
                    # range_color=(30, 150),
                    labels={"10만명당 온열질환자수": "10만명당 발생수"},
                )

                fig.update_geos(
                    fitbounds="locations",
                    visible=False,
                    projection_scale=7,
                    center={"lat": 36.5, "lon": 127.8}
                )

                fig.update_layout(
                    margin={"r": 0, "t": 30, "l": 0, "b": 0},
                    height=400,
                    title="도별 10만명당 온열질환자수"
                )

                return fig
            
        with ui.card():
            ui.h4("영천시 온열질환 관련 요약 지표")

            with ui.layout_column_wrap(width=1/3):  # 3열로 자동 래핑
            
                # 1행
                with ui.value_box(showcase=icon_svg("calendar")):
                    "연도"
                    @render.text
                    def year_text():
                        return "2022"

                with ui.value_box(showcase=icon_svg("temperature-high")):
                    "최고기온"
                    @render.text
                    def max_temp():
                        return "35.6℃"

                with ui.value_box(showcase=icon_svg("sun")):
                    "폭염일수"
                    @render.text
                    def heat_days():
                        return "15일"

                # 2행
                with ui.value_box(showcase=icon_svg("users")):
                    "영천 총인구"
                    @render.text
                    def total_pop():
                        return "100781명"

                with ui.value_box(showcase=icon_svg("briefcase-medical")):
                    "온열질환자 수"
                    @render.text
                    def patient_count():
                        return "154명"

                with ui.value_box(showcase=icon_svg("chart-line")):
                    "온열질환 발생순위(시군기준)"
                    @render.text
                    def rank():
                        return "8위"

                # 3행
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
            job_hot_data = pd.read_csv(app_dir / "data/ill_loc.csv")

            with ui.card():
                ui.div('온열질환 발생 현황 분석: 장소, 직종, 연령을 중심으로', style="text-align: center; font-weight: bold; font-size: 30px;")
                ui.div('⚠️ 온열질환: 고온 환경에서 체온 조절이 제대로 되지 않아 발생하는 질환 ➡️ 여름철 장시간 실외 작업 및 체온조절 능력이 떨어지는 고령자의 경우 더 쉽게 영향을 받음  ', style="font-weight: bold; font-size: 18px;")
            with ui.navset_card_tab(id="tab"):
                with ui.nav_panel("직종"):
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
                            file_path_ = app_dir / "data" / "직업분포_비율.csv"
                            df = pd.read_csv(file_path_)
                            @render_widget
                            def job():
                                selected_year = input.year_card()
                        
                                values = df[selected_year].iloc[1:].tolist()
                                labels = df["직종별"].iloc[1:].tolist()
                        
                                # 🔸 텍스트 조건: 0.5% 미만만 외부에 이름 표시 (중복 방지용)
                                custom_text = [l if v < 0.5 else "" for l, v in zip(labels, values)]
                                custom_position = ["outside" if v < 0.5 else "inside" for v in values]
                                text_colors = ["red" if v < 1 else "black" for v in values]
                                text_sizes = [16 if v < 1 else 12 for v in values]
                        
                                # 🔸 색상 분류
                                def classify_color(label):
                                    if label == "농림·어업 숙련 종사자":
                                        return "green"  # 1분류
                                    elif label in ["단순노무 종사자"]:
                                        return "steelblue"  # 2분류
                                    else:
                                        return "lightgray"  # 3분류
                        
                                colors = [classify_color(l) for l in labels]
                        
                                fig_donut = go.Figure(data=[go.Pie(
                                    labels=labels,
                                    values=values,
                                    hole=0.4,
                                    text=custom_text,                        # 외부 텍스트 제한
                                    textinfo="label+percent",                # ✅ 내부에 label + percent 표시
                                    textposition=custom_position,
                                    textfont=dict(color=text_colors, size=text_sizes),
                                    marker=dict(colors=colors),              # ✅ 색상 지정
                                    insidetextorientation="radial",
                                    hoverinfo="label+value+percent",
                                    sort=False
                                )])
                        
                                fig_donut.update_layout(title=f"{selected_year}년 직종비율")
                                return fig_donut
                            with ui.card_footer(style="font-size: 18px;"):
                                @render.text
                                def job_summaray():
                                    selected_year = input.year_card()
                                    year_col = str(selected_year)
                                    target_jobs = [
                                        '단순노무 종사자',
                                        '농림·어업 숙련 종사자'
                                    ]
                                    filtered_df = df[df['직종별'].isin(target_jobs)]
                                    total_value = filtered_df[year_col].sum()

                                    return f"🧾 야외 직종 비율 합계: {total_value:.1f}%"

                with ui.nav_panel("나이"):
                    with ui.layout_column_wrap(width=1 / 2):
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
                            file_path_ = app_dir / "data" / "연도별_연령.csv"
                            age = pd.read_csv(file_path_)
                            @render_widget
                            def ycs_age():
                                selected_year = input.year_card()
                                labels = age["연령별"].tolist()
                                values = age[selected_year].tolist() 
                                highlight_ages = ['60대', '70대', '80대이상']
                                colors = ['steelblue' if age in highlight_ages else '#d3d3d3' for age in labels]
                                labels
                                fig_donut = go.Figure(
                                    data=[go.Pie(labels=labels, values=values, hole=0.4, sort=False,marker=dict(colors=colors),
                                                 textinfo='label+percent',
                                                textposition='inside')]
                                )
                                return fig_donut.update_layout(title=f"{selected_year}년 전국 연령대 비율")
                            with ui.card_footer(style="font-size: 18px;"):
                               @render.text
                               def age_summary2():
                                selected_year = input.year_card()
                                year_col = str(selected_year)
                                target_jobs = ['60대','70대','80대이상']
                                filtered_df = age[age['연령별'].isin(target_jobs)]
                                total_value = filtered_df[year_col].sum()
                                return f"🧾 전국 60대 이상 비율 합계: {total_value:.1f}%"
                               

            with ui.card():
                ui.div("✅ 온열질환 위험군(농민·고령자) 맞춤 예방 중심의 선제적 알림체계 구축 필요",style="text-align: center; font-weight: bold; font-size: 20px;")



    with ui.card():
        ui.div("영천시 직종 및 연령 분포", style="text-align: center; font-weight: bold; font-size: 30px;")

    with ui.layout_column_wrap(width=1 / 2):
        with ui.card():
            @render_widget
            def job_yc():
                file_path_ = app_dir / "data" / "job.csv"
                df = pd.read_csv(file_path_)
                labels = ['농어업종사자', '관리자', '사무종사자', '서비스업종사자', '기계종사자', '단순노무종사자']
                years = sorted(df['연도'].unique())
                color_map = {
                    '농어업종사자': 'red',
                    '관리자': '#d3d3d3',
                    '사무종사자': '#d3d3d3',
                    '서비스업종사자': '#d3d3d3',
                    '기계종사자': '#d3d3d3',
                    '단순노무종사자': '#d3d3d3'
                    }
                fig = go.Figure()
                for label in labels:
                    fig.add_trace(go.Bar(
                        x=years,
                        y=[df[df['연도'] == y][label].values[0] for y in years],
                        name=label,
                        marker_color=color_map[label]
                    ))

                fig.update_layout(
                    barmode='stack',  
                    title='연도별 영천시 직종별 취업비율 누적 막대그래프',
                    xaxis_title='연도',
                    yaxis_title='취업 비율',
                    height=500,
                )

                return fig
            ui.card_footer("✅ 타직종에 비해 연도별 가장 많은 비율을 차지하는 농어업 종사자", style="font-size: 18px;")

        with ui.card():
            @render_widget
            def ycs_age2():
                file_path_ = app_dir / "data" / "age1.csv"
                age = pd.read_csv(file_path_)
                df_transposed = age.set_index('나이대').T.reset_index()
                df_melted = df_transposed.melt(id_vars='index', var_name='나이대', value_name='인구비율')
                df_melted.rename(columns={'index': '연도'}, inplace=True)
                custom_order = ['65세 이상', '65세 미만', '50대', '40대', '30대', '20대', '10대', '0대']
                df_melted['나이대'] = pd.Categorical(df_melted['나이대'], categories=custom_order, ordered=True)
                df_melted = df_melted.sort_values(['연도', '나이대'])

                color_map = {age: '#d3d3d3' for age in custom_order}
                color_map['65세 이상'] = 'blue'

                fig = px.bar(
                    df_melted,
                    x="연도",
                    y="인구비율",
                    color="나이대",
                    title="영천시 연도별 연령대 누적 막대 그래프",
                    barmode="stack",
                    category_orders={"나이대": custom_order},
                    color_discrete_map=color_map
                )

                return fig
            ui.card_footer("✅ 다른 연령대에 비해 연도별 가장 많은 비율을 차지하는 65세 이상 인구 비율", style="font-size: 18px;")
    with ui.layout_column_wrap(width=1 / 2):
        with ui.card():
            @render_widget()
            def population():
                file_path = app_dir / "data" / "population_update.xlsx"
                df = pd.read_excel(file_path)

                target_col = '65세 이상 고령자 (명)'
                year_col = '연도'

                df1 = df.copy()
                # 연도 기준 정렬 및 인덱스 리셋
                df1 = df1.sort_values(by=year_col).reset_index(drop=True)

                # 예측 연도와 학습 윈도우
                last_year = df1[year_col].max()
                predict_years = list(range(last_year + 1, last_year + 11))
                window_size = 5

                for predict_year in predict_years:
                    # 예측 대상 연도 이전의 데이터 중 마지막 window_size 개
                    train_df = df1[df1[year_col] < predict_year].tail(window_size)

                    # 선형 회귀 계수 계산
                    coeff = np.polyfit(train_df[year_col], train_df[target_col], 1)   #앞에값: 기울기, 뒤에값: 절편편
                    trend_func = np.poly1d(coeff)

                    # 예측값 계산
                    pred_value = trend_func(predict_year)


                    df1 = pd.concat([
                        df1,
                        pd.DataFrame({year_col: [predict_year], target_col: [pred_value]})
                    ], ignore_index=True)


                fig = go.Figure()

                # 라인 추가
                fig.add_trace(go.Scatter(
                    x=df1[year_col],
                    y=df1[target_col],
                    mode='lines+markers',
                    name='고령자 수'
                ))

                fig.add_vline(x=2022, line_dash="dot", line_color="red", annotation_text="2022")

                fig.update_layout(
                    title="영천시 연도별 65세 이상 인구의 추세선",
                    xaxis_title="연도",
                    yaxis_title="고령자 수 (명)",
                    xaxis=dict(dtick=2),
                    font=dict(family="Malgun Gothic", size=14),
                    margin=dict(l=40, r=40, t=60, b=40),
                    height=500
                )

                return fig
            with ui.card_footer(style="font-size: 18px;"):
                ui.markdown("📌 65세 이상 인구는 매년 증가하고 있음. (경북도 추가해서 비교?)")
                ui.markdown("📈 최근 5년 데이터를 이용해 매년 65세 이상 인구 예측.")
        with ui.card():
            ui.markdown('☀️ **폭염, 예방 가능한 유일한 재난**')
            ui.markdown('즉시성은 낮지만 치명적')
            ui.markdown('폭염은 눈에 띄는 외부 피해 없이 장시간 노출 시 발생하는 재난으로,')
            ui.markdown('‘위험 인지 → 행동 전환’ 사이에 큰 간극이 존재합니다.')
            ui.markdown('하지만 그렇기에 미리 알리고, 예방할 수 있는 재난입니다.')
            ui.markdown('👉 지속적 알림 체계를 통해 시민의 인지와 행동을 유도해야 합니다.')
            ui.br()
            ui.markdown('📊 **온열질환, 경북과 영천의 현황**')
            ui.markdown('✅ 경상북도: 10만 명당 온열질환자 수 17개 시도 중 5위')
            ui.markdown('✅ 영천시: 온열질환 발생 비율 전국 157개 시군 중 8위')

            ui.markdown('👥 **주요 위험군**')
            ui.markdown('농어업 종사자 <br>'
                           '⤷ 전체 직종의 0.2%지만 <br>'
                                '⤷ 온열질환 발생 장소 2위는 논·밭')
            ui.markdown('60세 이상 고령자 <br>' 
                            '⤷ 전체의 약 30% 차지 <br>'
                                '⤷ 타 연령 대비 취약성 매우 높음')

            ui.markdown('📍 영천시 특징')
            ui.markdown('농어업 종사자 비중: 연도별 약 30% <br>'
                        '고령 인구 비중: 연도별 약 30%, 지속 증가 중')


            ui.markdown('✅ 결론')
            ui.markdown('🎯 고위험군(농민·고령자) 중심의 맞춤형·선제적 폭염 알림체계 구축 필요')









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
