from django.shortcuts import render, render_to_response
from pyecharts.charts.basic_charts.map import Map
from pyecharts import options as opts

# Create your views here.

# 绘制美国疫情情况
"""
    数据来源:
        Johns Hopkins University的数据源
    数据截止时间:
        截止到2020年6月4日
    主要展示面板包括:
       1. 病例总数(新增病例)总死亡病例(新增死亡)  数字
       2. 美国各州累计病例总数 地图
       3. 美国各州累计死亡总数 地图
       4. 美国每天新增病例数 折线图
       5. 美国每天死亡病例数 折线图
"""
import os

from public_func import static_param
from public_func import process_files
from public_func import conn_db
from public_func import init_covid_data
from public_func import public_function


def show_US_status(requests):
    """
    显示美国目前情况的主函数:
    :param requests:
    :return:
    """

    def load_covid_origin_data():
        """
        加载covid_19全部中美国的原始数据
        首先从本地的pkl中加载,如果不成功再从数据库中加载
        :return:
        """
        # 从本地pkl文件中加载covid_19数据
        covid_19_data_path = static_param.COVID_19_DATA_PATH
        if os.path.exists(covid_19_data_path):
            covid_19_all_origin_data = process_files.read_pickle_2_df(covid_19_data_path)
        # 若本地pkl文件不存在,则从数据库中加载数据源
        else:
            conn_covid_19_db = conn_db.ConnMysql()
            read_sql = "SELECT * FROM covid_19 where Country_Region = 'US'"
            covid_19_all_origin_data = conn_covid_19_db.read_table(read_sql)
        if covid_19_all_origin_data is None:
            raise ValueError('Cant get covid_19 origin data from local or database')
        return covid_19_all_origin_data


    # 1.加载数据源
    covid_19_origin_data = load_covid_origin_data()
    # 检查原始数据的有效性
    public_function.detect_df(covid_19_origin_data)
    # 2.初始化数据源
    init_covid_data.init_covid_19_data(covid_19_origin_data)

    # 3.得到美国数据
    covid_19_US_data = covid_19_origin_data[covid_19_origin_data['Country_Region'] == 'United States']

    # 4.计算绘制的统计量
    # 病例类型字典:分为确诊和死亡
    case_type_dict = {'Confirmed': 'Confirmed', 'Deaths': 'Deaths'}

    last_date = max(covid_19_US_data['Date'])

    # 4.1 各州每日新增确诊和死亡病例汇总
    states_timing_data = []
    for case_type in case_type_dict.values():
        states_timing_data_temp = covid_19_US_data[['Province_State', 'Cases', 'Date']][
            covid_19_US_data['Case_Type'] == case_type]
        states_timing_data_temp = states_timing_data_temp.groupby(by=['Province_State','Date']).agg({'Cases':'sum'}).reset_index()
        states_timing_data_temp.sort_values(by=['Date', 'Cases'], ascending=[False, False], inplace=True)
        states_timing_data.append(states_timing_data_temp)
    states_confirmed_timing_data = states_timing_data[0]
    states_deaths_timing_data = states_timing_data[1]

    # 4.2 美国每日新增确诊和死亡病例汇总
    US_timing_data = []
    for case_type, case_data in zip(case_type_dict.values(), states_timing_data):
        US_timing_data_temp = case_data.groupby(by=['Date']).agg({'Cases': 'sum'}).reset_index()
        US_timing_data_temp.sort_values(by=['Date'], ascending=True, inplace=True)
        US_timing_data.append(US_timing_data_temp)
    US_confirmed_timing_data = US_timing_data[0]
    US_deaths_timing_data = US_timing_data[1]

    # 4.3 现存美国各州确诊病例和死亡病例
    now_date_states_status = []
    for case_type, case_data in zip(case_type_dict.values(), states_timing_data):
        now_date_states_status_temp = case_data[case_data['Date'] == last_date]
        now_date_states_status.append(now_date_states_status_temp)

    # 4.4 目前现存确诊和死亡病例,单日确诊和死亡病例
    now_date_US_all_confirmed = sum(now_date_states_status[0]['Cases'])
    now_date_US_all_deaths = sum(now_date_states_status[1]['Cases'])
    last_date_US_all_confirmed = sum(covid_19_US_data['Difference'][(covid_19_US_data['Date'] == last_date) & (
            covid_19_US_data['Case_Type'] == case_type_dict['Confirmed'])])
    last_date_US_all_deaths = sum(covid_19_US_data['Difference'][(covid_19_US_data['Date'] == last_date) & (
            covid_19_US_data['Case_Type'] == case_type_dict['Deaths'])])

    # 绘制美国各州确诊情况图
    # 加载数据
    now_date_states_confirmed = now_date_states_status[0]
    now_date_states_confirmed_sequence = [(states, confirmed) for states, confirmed in
                                          zip(now_date_states_confirmed['Province_State'],
                                              now_date_states_confirmed['Cases'])]


    # 初始化地图
    now_date_states_confirmed_map = Map(init_opts=opts.InitOpts(width='1000px', height='800px', bg_color="#000f1a"))

    # 加载数据:其中maptype可以初始化地图类型,而geo中需要单独设置
    now_date_states_confirmed_map.add(series_name='1', data_pair=now_date_states_confirmed_sequence, maptype='US',
            label_opts=opts.LabelOpts(is_show=False))

    # 配置
    now_date_states_confirmed_map.set_global_opts(
        # 视觉配置
        visualmap_opts=opts.VisualMapOpts(
            type_='color',
        ),
        tooltip_opts=opts.TooltipOpts(is_show=True)
    )

    # 保存现存美国确诊病例地图为Html中内嵌框架
    # now_date_states_confirmed_map.render_embed()
    # 输出为html
    path = '123.html'
    now_date_states_confirmed_map.render(path)
    save_show_dashboards_name = 'covid_19_US_status.html'
    save_html_path = os.path.join(static_param.PROJECT_PATH, static_param.TEMPLATES_NAME, save_show_dashboards_name)
    return render_to_response(save_html_path, locals())
