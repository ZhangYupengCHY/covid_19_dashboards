from django.shortcuts import render, render_to_response
import sys
import os

import pandas as pd
from datetime import datetime
import warnings
from pyecharts.charts import Page
from pyecharts.charts import Line
from pyecharts.charts import Map
from pyecharts import options as opts
import gc

from public_func import conn_db
from public_func import public_function
from public_func import process_files
from public_func import static_param

"""
可视化全球疫情地图
"""

warnings.filterwarnings(action='ignore')


# 计算加载全球新冠疫情数据时间
@public_function.run_time
def db_download_covid_19_data_primary_country():
    """
    # 本应该从数据库中加载数据,但考虑到速度太慢,
    于是将文件保存为pkl文件,然后从pkl文件中加载数据.
    数据库中加载covid_19数据(截止到2020年6月4日)
    来源为Johns Hopkins University的数据源
    列为
    columns:
        Case_Type:string
             Confirmed cases and reported deaths
             确诊或是死亡病例
        People_Total_Tested_Count:int
             How many people have been hospitalized, cumulatively (just United States)
             检测总人数
        Cases:int
            How many people tested positive for all times
            总病例数
        Difference:int
            How many people tested positive for each day
            新增病例
        Date:date
            Jan 23, 2020 - June 4,2020
            数据日期范围
        Combined_Key:string
            Combination of Admin 2, State_Province, and Country_Region
            行政省加国家名
        Country_Region:string
            Provided for all countries
            国家名
        Province_State:string
            Provided for Australia, Canada, China,
            Denmark, France, Netherlands,
            United Kingdom, United States
            特定国家行政省
        Admin2:string
            US only - County name
            美国行政省
        iso2:string
            两位国家以及区域代码
        iso3:string
            三位国家以及区域代码
        FIPS:string
            US only - 5-digit Federal
            Information Processing Standard
            美国县区域代码
        Lat:float
            Latitude
            纬度
        Long:float
            Longitude
            经度
        Population_Count:int
            人口
        people_Hospitalized_Cumulative_Count:int
            Positive + Negative + Pending test results
            医院全病例人数
        Data_Source:string
            Where the data was sourced from
            数据来源
        Prep_Flow_Runtime:datetime
            Date when the ETL job ran
            数据获取时间
    Returns:pd.DataFrame
            数据源数据
    """
    try:
        # 从pkl文件中加载数据
        pkl_path = r"D:\pyecharts\covid_19.pkl"
        covid_19_data = process_files.read_pickle_2_df(pkl_path)

    except:
        # 连接数据库获取covid_19的数据
        conn_mysql = conn_db.ConnMysql()
        sql = "SELECT * FROM covid_19_cases"
        covid_19_data = conn_mysql.read_table(sql)
    # # 只加载一部分国家的数据
    # primary = ['Afghanistan'
    #     , 'Andorra'
    #     , 'Angola'
    #     , 'Argentina'
    #     , 'Armenia'
    #     , 'Australia'
    #     , 'Bahrain'
    #     , 'Bangladesh'
    #     , 'Barbados'
    #     , 'Belarus'
    #     , 'Belgium'
    #     , 'Belize'
    #     , 'Benin'
    #     , 'Bhutan'
    #     , 'Brazil'
    #     , 'Brunei'
    #     , 'Bulgaria'
    #     , 'Cambodia'
    #     , 'Cameroon'
    #     , 'Canada'
    #     , 'Chad'
    #     , 'Chile'
    #     , 'China'
    #     , 'Colombia'
    #     , 'Croatia'
    #     , 'Cuba'
    #     , 'Cyprus'
    #     ,'Korea'
    #     ,'Korea, South'
    #     , 'Czechia'
    #     , 'Dominica'
    #     , 'Fiji'
    #     , 'Finland'
    #     , 'France'
    #     , 'Gambia'
    #     , 'Georgia'
    #     , 'Germany'
    #     , 'Ghana'
    #     , 'Greece'
    #     , 'Grenada'
    #     , 'Guatemala'
    #     , 'Haiti'
    #     , 'Iceland'
    #     , 'India'
    #     , 'Indonesia'
    #     , 'Iran'
    #     , 'Iraq'
    #     , 'Ireland'
    #     , 'Israel'
    #     , 'Italy'
    #     , 'Jamaica'
    #     , 'Japan'
    #     , 'Liberia'
    #     , 'Libya'
    #     , 'Lithuania'
    #     , 'Mexico'
    #     , 'New Zealand'
    #     , 'Nicaragua'
    #     , 'Niger'
    #     , 'Nigeria'
    #     , 'Norway'
    #     , 'Oman'
    #     , 'Pakistan'
    #     , 'Philippines'
    #     , 'Poland'
    #     , 'Portugal'
    #     , 'Qatar'
    #     , 'Romania'
    #     , 'Russia'
    #     , 'Rwanda'
    #     , 'Singapore'
    #     , 'Slovakia'
    #     , 'Slovenia'
    #     , 'Somalia'
    #     , 'South Africa'
    #     , 'South Sudan'
    #     , 'Spain'
    #     , 'Sudan'
    #     , 'Switzerland'
    #     , 'Syria'
    #     , 'Thailand'
    #     , 'Togo'
    #     , 'Tunisia'
    #     , 'Turkey'
    #     , 'Uganda'
    #     , 'Ukraine'
    #     , 'United Kingdom'
    #     , 'Uruguay'
    #     , 'US'
    #     , 'Uzbekistan'
    #     , 'Venezuela'
    #     , 'Vietnam'
    #     , 'Yemen', 'Zambia', 'Zimbabwe']
    # covid_19_data = covid_19_data[covid_19_data['Country_Region'].isin(primary)]
    return covid_19_data


def init_data(data):
    """
    初始化数据,规范数据格式:
        1.将列名中空格去除
        2.修改列的数据类型
        3.空缺值替换
        4.将Data转换成时间格式
    Args:
        data:pd.DataFrame
            原始数据
    Returns:pd.DataFrame
            替换之后的数据
    """
    data.columns = [column.strip(' ') for column in data.columns]
    int_columns = ['Cases', 'Difference', 'Population_Count']
    for column in int_columns:
        data[column].fillna(value=0, inplace=True)
        data[column] = data[column].astype(int)
    # 国家字典
    nameMap = {
        'Singapore Rep.': '新加坡',
        'Dominican Rep.': '多米尼加',
        'Palestine': '巴勒斯坦',
        'Bahamas': '巴哈马',
        'Timor-Leste': '东帝汶',
        'Afghanistan': '阿富汗',
        'Guinea-Bissau': '几内亚比绍',
        "Côte d'Ivoire": '科特迪瓦',
        'Siachen Glacier': '锡亚琴冰川',
        "Br. Indian Ocean Ter.": '英属印度洋领土',
        'Angola': '安哥拉',
        'Albania': '阿尔巴尼亚',
        'United Arab Emirates': '阿联酋',
        'Argentina': '阿根廷',
        'Armenia': '亚美尼亚',
        'French Southern and Antarctic Lands': '法属南半球和南极领地',
        'Australia': '澳大利亚',
        'Austria': '奥地利',
        'Azerbaijan': '阿塞拜疆',
        'Burundi': '布隆迪',
        'Belgium': '比利时',
        'Benin': '贝宁',
        'Burkina Faso': '布基纳法索',
        'Bangladesh': '孟加拉国',
        'Bulgaria': '保加利亚',
        'The Bahamas': '巴哈马',
        'Bosnia and Herz.': '波斯尼亚和黑塞哥维那',
        'Belarus': '白俄罗斯',
        'Belize': '伯利兹',
        'Bermuda': '百慕大',
        'Bolivia': '玻利维亚',
        'Brazil': '巴西',
        'Brunei': '文莱',
        'Bhutan': '不丹',
        'Botswana': '博茨瓦纳',
        'Central African Rep.': '中非',
        'Canada': '加拿大',
        'Switzerland': '瑞士',
        'Chile': '智利',
        'China': '中国',
        'Ivory Coast': '象牙海岸',
        'Cameroon': '喀麦隆',
        'Dem. Rep. Congo': '刚果民主共和国',
        'Congo': '刚果',
        'Colombia': '哥伦比亚',
        'Costa Rica': '哥斯达黎加',
        'Cuba': '古巴',
        'N. Cyprus': '北塞浦路斯',
        'Cyprus': '塞浦路斯',
        'Czech Rep.': '捷克',
        'Germany': '德国',
        'Djibouti': '吉布提',
        'Denmark': '丹麦',
        'Algeria': '阿尔及利亚',
        'Ecuador': '厄瓜多尔',
        'Egypt': '埃及',
        'Eritrea': '厄立特里亚',
        'Spain': '西班牙',
        'Estonia': '爱沙尼亚',
        'Ethiopia': '埃塞俄比亚',
        'Finland': '芬兰',
        'Fiji': '斐',
        'Falkland Islands': '福克兰群岛',
        'France': '法国',
        'Gabon': '加蓬',
        'United Kingdom': '英国',
        'Georgia': '格鲁吉亚',
        'Ghana': '加纳',
        'Guinea': '几内亚',
        'Gambia': '冈比亚',
        'Guinea Bissau': '几内亚比绍',
        'Eq. Guinea': '赤道几内亚',
        'Greece': '希腊',
        'Greenland': '格陵兰',
        'Guatemala': '危地马拉',
        'French Guiana': '法属圭亚那',
        'Guyana': '圭亚那',
        'Honduras': '洪都拉斯',
        'Croatia': '克罗地亚',
        'Haiti': '海地',
        'Hungary': '匈牙利',
        'Indonesia': '印度尼西亚',
        'India': '印度',
        'Ireland': '爱尔兰',
        'Iran': '伊朗',
        'Iraq': '伊拉克',
        'Iceland': '冰岛',
        'Israel': '以色列',
        'Italy': '意大利',
        'Jamaica': '牙买加',
        'Jordan': '约旦',
        'Japan': '日本',
        'Kazakhstan': '哈萨克斯坦',
        'Kenya': '肯尼亚',
        'Kyrgyzstan': '吉尔吉斯斯坦',
        'Cambodia': '柬埔寨',
        'Korea': '韩国',
        'Kosovo': '科索沃',
        'Kuwait': '科威特',
        'Lao PDR': '老挝',
        'Lebanon': '黎巴嫩',
        'Liberia': '利比里亚',
        'Libya': '利比亚',
        'Sri Lanka': '斯里兰卡',
        'Lesotho': '莱索托',
        'Lithuania': '立陶宛',
        'Luxembourg': '卢森堡',
        'Latvia': '拉脱维亚',
        'Morocco': '摩洛哥',
        'Moldova': '摩尔多瓦',
        'Madagascar': '马达加斯加',
        'Mexico': '墨西哥',
        'Macedonia': '马其顿',
        'Mali': '马里',
        'Myanmar': '缅甸',
        'Montenegro': '黑山',
        'Mongolia': '蒙古',
        'Mozambique': '莫桑比克',
        'Mauritania': '毛里塔尼亚',
        'Malawi': '马拉维',
        'Malaysia': '马来西亚',
        'Namibia': '纳米比亚',
        'New Caledonia': '新喀里多尼亚',
        'Niger': '尼日尔',
        'Nigeria': '尼日利亚',
        'Nicaragua': '尼加拉瓜',
        'Netherlands': '荷兰',
        'Norway': '挪威',
        'Nepal': '尼泊尔',
        'New Zealand': '新西兰',
        'Oman': '阿曼',
        'Pakistan': '巴基斯坦',
        'Panama': '巴拿马',
        'Peru': '秘鲁',
        'Philippines': '菲律宾',
        'Papua New Guinea': '巴布亚新几内亚',
        'Poland': '波兰',
        'Puerto Rico': '波多黎各',
        'Dem. Rep. Korea': '朝鲜',
        'Portugal': '葡萄牙',
        'Paraguay': '巴拉圭',
        'Qatar': '卡塔尔',
        'Romania': '罗马尼亚',
        'Russia': '俄罗斯',
        'Rwanda': '卢旺达',
        'W. Sahara': '西撒哈拉',
        'Saudi Arabia': '沙特阿拉伯',
        'Sudan': '苏丹',
        'S. Sudan': '南苏丹',
        'Senegal': '塞内加尔',
        'Solomon Is.': '所罗门群岛',
        'Sierra Leone': '塞拉利昂',
        'El Salvador': '萨尔瓦多',
        'Somaliland': '索马里兰',
        'Somalia': '索马里',
        'Serbia': '塞尔维亚',
        'Suriname': '苏里南',
        'Slovakia': '斯洛伐克',
        'Slovenia': '斯洛文尼亚',
        'Sweden': '瑞典',
        'Swaziland': '斯威士兰',
        'Syria': '叙利亚',
        'Chad': '乍得',
        'Togo': '多哥',
        'Thailand': '泰国',
        'Tajikistan': '塔吉克斯坦',
        'Turkmenistan': '土库曼斯坦',
        'East Timor': '东帝汶',
        'Trinidad and Tobago': '特里尼达和多巴哥',
        'Tunisia': '突尼斯',
        'Turkey': '土耳其',
        'Tanzania': '坦桑尼亚',
        'Uganda': '乌干达',
        'Ukraine': '乌克兰',
        'Uruguay': '乌拉圭',
        'United States': '美国',
        'Uzbekistan': '乌兹别克斯坦',
        'Venezuela': '委内瑞拉',
        'Vietnam': '越南',
        'Vanuatu': '瓦努阿图',
        'West Bank': '西岸',
        'Yemen': '也门',
        'South Africa': '南非',
        'Zambia': '赞比亚',
        'Zimbabwe': '津巴布韦'
    }
    en_name = nameMap.keys()
    data['Country_Region'].replace(
        {'US': 'United States', 'Singapore': 'Singapore Rep.', 'Dominica': 'Dominican Rep.', 'Korea, South': 'Korea'},
        inplace=True)
    # 无法正确识别的国家或地区(不在国家字典中)
    country = set(data['Country_Region'].values)
    wrong_name = country - set(en_name)

    # 将Data列修改成时间格式
    data['Date'] = pd.to_datetime(data['Date'], dayfirst=False, yearfirst=False)
    data['Date'] = [date.date() for date in data['Date']]


#  print(wrong_name)


def plot_covid_19_world_situation(world_data):
    """
    绘制全球新冠疫情情况:
        1. 包含新增确诊人数
        2. 新增死亡人数
        3. 累计确诊人数
        4. 累计死亡人数
        5. 累计检测人数
        6. 全病例比例
    Args:
        world_data:pd.DataFrame
            全球数据
    Returns:html
            绘制成html
    """
    last_date = max(world_data['Date'])

    # 1.全球单日新增确诊病例
    now_date_confirmed_info = world_data[['Difference', 'Country_Region']][
        (world_data[world_data.columns[0]] == 'Confirmed') & (world_data['Date'] == last_date)]
    now_date_confirmed_info = now_date_confirmed_info.groupby(['Country_Region']).agg(
        {'Difference': 'sum'}).reset_index()

    # 2.全球单日新增死亡病例
    now_date_deaths_info = world_data[['Difference', 'Country_Region']][
        (world_data[world_data.columns[0]] == 'Deaths') & (world_data['Date'] == last_date)]
    now_date_deaths_info = now_date_deaths_info.groupby(['Country_Region']).agg(
        {'Difference': 'sum'}).reset_index()

    # 3.全球总共确诊病例
    total_confirmed_info = world_data[['Difference', 'Country_Region']][
        world_data[world_data.columns[0]] == 'Confirmed']
    total_confirmed_info = total_confirmed_info.groupby(['Country_Region']).agg(
        {'Difference': 'sum'}).reset_index()

    # 4.全球总共死亡病例
    total_deaths_info = world_data[['Difference', 'Country_Region']][world_data[world_data.columns[0]] == 'Deaths']
    total_deaths_info = total_deaths_info.groupby(['Country_Region']).agg(
        {'Difference': 'sum'}).reset_index()

    # 四种指标字典
    # express_dict = {
    #     'day_confirmed':
    #         {
    #             'data': now_date_confirmed_info,
    #             'case_type': 'confirmed',
    #             'date_type': 'day',
    #         },
    #     'day_deaths':
    #         {
    #             'data': now_date_deaths_info,
    #             'case_type': 'deaths',
    #             'date_type': 'day',
    #         },
    #     'total_confirmed':
    #         {
    #             'data': total_confirmed_info,
    #             'case_type': 'confirmed',
    #             'date_type': 'total',
    #         },
    #     'total_deaths':
    #         {
    #             'data': total_deaths_info,
    #             'case_type': 'deaths',
    #             'date_type': 'total',
    #         },
    # }

    express_dict = {
        'total_confirmed':
            {
                'data': total_confirmed_info,
                'case_type': 'confirmed',
                'date_type': 'total',
            },
    }

    for name, info in express_dict.items():
        data = info['data']
        max_num = max(data['Difference'])
        total_num = sum(data['Difference'])
        data_pair = [(country, int(confirmed_num)) for country, confirmed_num in
                     zip(data['Country_Region'],
                         data['Difference'])]
        express_dict[name]['max_num'] = max_num
        express_dict[name]['total_num'] = total_num
        express_dict[name]['data_pair'] = data_pair

    # 初始化pages
    pages = Page(page_title=f'全球{last_date}情况', layout=opts.PageLayoutOpts())

    # 绘制地图
    for plot_name, plot_data in express_dict.items():
        # 初始化地图
        map = Map(init_opts=opts.InitOpts(width='1000px', height='800px', bg_color="#000f1a"))

        # 加载数据:其中maptype可以初始化地图类型,而geo中需要单独设置
        if plot_data['case_type'] == 'confirmed':
            case_name = '确诊'
        else:
            case_name = '死亡'
        if plot_data['date_type'] == 'day':
            date_type = '当日'
        else:
            date_type = '累计'
        map.add(series_name=f'全球{last_date}{date_type}{case_name}人数分布', data_pair=plot_data['data_pair'],
                maptype='world',
                label_opts=opts.LabelOpts(is_show=False, color='white'),
                # itemstyle_opts是设置每个项目中标注点的样式 area_color是设置项目的背景色,color是设置项目的点的颜色
                itemstyle_opts=opts.ItemStyleOpts(area_color='#2a2a28', color="#d3d307"))

        # 配置
        map.set_global_opts(
            title_opts=opts.TitleOpts(title=f'全球{last_date}{date_type}{case_name}人数分布',
                                      subtitle=f"全球新增确诊:{plot_data['total_num']}",
                                      title_textstyle_opts={'color': "white"}),
        )

        # 添加图形系列
        pages.add(map)

    """
    # 绘制美国和中国每日新增确诊病例趋势线
    us_day_confirmed_data = world_data[
        (world_data['Country_Region'] == 'United States') & (world_data['Case_Type'] == 'Confirmed')]
    us_day_confirmed_grouped = us_day_confirmed_data[['Date', 'Difference']].groupby(['Date']).agg(
        {'Difference': 'sum'}).reset_index()
    gc.collect()
    us_day_confirmed_grouped_x = pd.to_datetime(us_day_confirmed_grouped['Date'], dayfirst=False)
    us_day_confirmed_grouped_x = list(us_day_confirmed_grouped_x.apply(lambda x: x.date()))
    us_day_confirmed_grouped_dict = {date: confirmed for date, confirmed in
                                     zip(us_day_confirmed_grouped_x, list(us_day_confirmed_grouped['Difference']))}
    us_day_confirmed_grouped_x = sorted(us_day_confirmed_grouped_x)
    us_day_confirmed_grouped_y = [us_day_confirmed_grouped_dict[date] for date in us_day_confirmed_grouped_x]
    total_confirmed_num = sum(us_day_confirmed_grouped_y)
    # 绘制折线图
    line = Line(init_opts=opts.InitOpts())

    # 添加X,Y数据
    line.add_xaxis(xaxis_data=us_day_confirmed_grouped_x)
    line.add_yaxis(series_name='美国确诊病例趋势', y_axis=us_day_confirmed_grouped_y)

    # 添加折线图配置
    line.set_global_opts(title_opts=opts.TitleOpts(title='美国新增确诊病例趋势', subtitle=f'美国累计确诊病例{total_confirmed_num}'))

    pages.add(line)

    # 绘制美国累计确诊病例
    us_add_confirmed_grouped = us_day_confirmed_data[['Date', 'Cases']].groupby(['Date']).agg(
        {'Cases': 'sum'}).reset_index()
    us_add_confirmed_grouped_x = pd.to_datetime(us_add_confirmed_grouped['Date'], dayfirst=False)
    us_add_confirmed_grouped_x = list(us_add_confirmed_grouped_x.apply(lambda x: x.date()))
    us_add_confirmed_grouped_dict = {date: case_num for date, case_num in
                                     zip(us_add_confirmed_grouped_x, list(us_add_confirmed_grouped['Cases']))}
    us_add_confirmed_grouped_x = sorted(us_add_confirmed_grouped_x)
    us_add_confirmed_grouped_y = [us_add_confirmed_grouped_dict[date] for date in us_add_confirmed_grouped_x]
    # 绘制折线图
    line = Line(init_opts=opts.InitOpts())

    # 添加X,Y数据
    line.add_xaxis(xaxis_data=us_add_confirmed_grouped_x)
    line.add_yaxis(series_name='美国累计确诊病例趋势', y_axis=us_add_confirmed_grouped_y)

    # 添加折线图配置
    line.set_global_opts(title_opts=opts.TitleOpts(title='美国累计确诊病例趋势'))
    pages.add(line)

    """

    return pages


def show(requests):
    """
    绘制新冠疫情数据
    绘制全球新冠疫情情况:
        1. 包含新增确诊人数
        2. 新增死亡人数
        3. 累计确诊人数
        4. 累计死亡人数
        5. 累计检测人数
        6. 全病例比例
    左侧概览:
        1.当前全球疫情情况汇总 (数字)
        2.当前全球疫情国家情况    (数字)
        3.当前全球最严重国家(可选)省份与城市疫情情况 (数字)
        4.数据更新时间
    中间部位:
        全球城市疫情地图(确诊病例、死亡病例、疑似病例、测试人数比例、感染比例) (图形)
    右侧:
        每个国家的(确诊人数、死亡人数、康复人数) (数字)
        特定国家每个省份死亡和康复人数 (数字)
        特定国家的(确诊人数、死亡人数、康复人数)时间图 (图形)
    Returns:

    """
    # 加载数据
    world_data = db_download_covid_19_data_primary_country()
    # 初始化数据
    init_data(world_data)
    # 绘制地图
    last_date = max(world_data['Date'])

    # 1.全球单日新增确诊病例
    now_date_confirmed_info = world_data[['Difference', 'Country_Region']][
        (world_data[world_data.columns[0]] == 'Confirmed') & (world_data['Date'] == last_date)]
    now_date_confirmed_info = now_date_confirmed_info.groupby(['Country_Region']).agg(
        {'Difference': 'sum'}).reset_index()

    # 2.全球单日新增死亡病例
    now_date_deaths_info = world_data[['Difference', 'Country_Region']][
        (world_data[world_data.columns[0]] == 'Deaths') & (world_data['Date'] == last_date)]
    now_date_deaths_info = now_date_deaths_info.groupby(['Country_Region']).agg(
        {'Difference': 'sum'}).reset_index()

    # 3.全球总共确诊病例
    total_confirmed_info = world_data[['Difference', 'Country_Region']][
        world_data[world_data.columns[0]] == 'Confirmed']
    total_confirmed_info = total_confirmed_info.groupby(['Country_Region']).agg(
        {'Difference': 'sum'}).reset_index()

    # 4.全球总共死亡病例
    total_deaths_info = world_data[['Difference', 'Country_Region']][world_data[world_data.columns[0]] == 'Deaths']
    total_deaths_info = total_deaths_info.groupby(['Country_Region']).agg(
        {'Difference': 'sum'}).reset_index()
    total_deaths_info.sort_values(by=['Difference'], ascending=False, inplace=True)

    # 四种指标字典
    # express_dict = {
    #     'day_confirmed':
    #         {
    #             'data': now_date_confirmed_info,
    #             'case_type': 'confirmed',
    #             'date_type': 'day',
    #         },
    #     'day_deaths':
    #         {
    #             'data': now_date_deaths_info,
    #             'case_type': 'deaths',
    #             'date_type': 'day',
    #         },
    #     'total_confirmed':
    #         {
    #             'data': total_confirmed_info,
    #             'case_type': 'confirmed',
    #             'date_type': 'total',
    #         },
    #     'total_deaths':
    #         {
    #             'data': total_deaths_info,
    #             'case_type': 'deaths',
    #             'date_type': 'total',
    #         },
    # }

    express_dict = {
        'total_confirmed':
            {
                'data': total_confirmed_info,
                'case_type': 'confirmed',
                'date_type': 'total',
            },
    }

    for name, info in express_dict.items():
        data = info['data']
        max_num = max(data['Difference'])
        total_num = sum(data['Difference'])
        data_pair = [(country, int(confirmed_num)) for country, confirmed_num in
                     zip(data['Country_Region'],
                         data['Difference'])]
        express_dict[name]['max_num'] = max_num
        express_dict[name]['total_num'] = total_num
        express_dict[name]['data_pair'] = data_pair

    # 初始化pages
    pages = Page(page_title=f'全球{last_date}情况', layout=opts.PageLayoutOpts())

    # 绘制地图
    for plot_name, plot_data in express_dict.items():
        # 初始化地图
        map = Map(init_opts=opts.InitOpts(width='1000px', height='800px', bg_color="#000f1a"))

        # 加载数据:其中maptype可以初始化地图类型,而geo中需要单独设置
        if plot_data['case_type'] == 'confirmed':
            case_name = '确诊'
        else:
            case_name = '死亡'
        if plot_data['date_type'] == 'day':
            date_type = '当日'
        else:
            date_type = '累计'
        map.add(series_name=f'全球{last_date}{date_type}{case_name}人数分布', data_pair=plot_data['data_pair'],
                maptype='world',
                label_opts=opts.LabelOpts(is_show=False, color='white'),
                # itemstyle_opts是设置每个项目中标注点的样式 area_color是设置项目的背景色,color是设置项目的点的颜色
                itemstyle_opts=opts.ItemStyleOpts(area_color='#2a2a28', color="#d3d307"))

        # 配置
        map.set_global_opts(
            title_opts=opts.TitleOpts(title=f'全球{last_date}{date_type}{case_name}人数分布',
                                      subtitle=f"全球新增确诊:{plot_data['total_num']}",
                                      title_textstyle_opts={'color': "white"}),
        )

        # 添加图形系列
        pages.add(map)
    # msg1:中间部位地图
    plot_map = pages.render_embed()
    save_show_dashboards_name = 'covid_19_world_map.html'
    save_html_path = os.path.join(static_param.PROJECT_PATH, static_param.TEMPLATES_NAME, save_show_dashboards_name)
    # msg2:用于绘制地图左侧中间部位的数据:
    # 包括国家以及国家对应的确诊人数
    total_confirmed_info.sort_values(by=['Difference'], ascending=False, inplace=True)
    total_confirmed_info = total_confirmed_info
    gc.collect()
    now_datetime = datetime.now().strftime('%m/%d/%Y %H:%M:%S %p')
    # 一共的国家个数
    country_num = total_confirmed_info.shape[0]
    global_death = sum(total_deaths_info['Difference'].values)

    # 美国确诊死亡人数
    us_city_deaths_days = world_data[['Combined_Key', 'Difference']][
        (world_data['Country_Region'] == 'United States') & (world_data['Case_Type'] == 'Deaths')]
    us_city_deaths_total = us_city_deaths_days.groupby(by=['Combined_Key']).agg({'Difference': 'sum'}).reset_index()
    us_city_deaths_total['Combined_Key'] = us_city_deaths_total['Combined_Key'].apply(
        lambda x: x.split(',')[0] if ',' in x else x)
    us_city_deaths_total.sort_values(by=['Difference'], ascending=False, inplace=True)

    # 全球确诊病例随时间变化的曲线图
    world_confirmed_timing = world_data[['Date', 'Cases']][world_data['Case_Type'] == 'Confirmed']
    world_confirmed_timing = world_confirmed_timing.groupby(by=['Date']).agg({'Cases': 'sum'}).reset_index()
    world_confirmed_timing.sort_values(by=['Cases'], ascending=True, inplace=True)
    # 绘制折线图
    line = Line(init_opts=opts.InitOpts(width='400px', height='250px'))
    # x轴数据
    line.add_xaxis(xaxis_data=list(world_confirmed_timing['Date']))

    # y轴数据
    world_confirmed_timing['show_Cases'] = [round(case/10000,2) for case in world_confirmed_timing['Cases']]
    line.add_yaxis(series_name='', y_axis=list(world_confirmed_timing['show_Cases']), is_smooth=True,linestyle_opts=opts.LineStyleOpts(width=6,color='red'))

    # 设置折线的全局变量
    line.set_global_opts(title_opts=opts.TitleOpts(title="world confirmed changed",title_textstyle_opts={'color':'white','font_size':'10px'}),
                         yaxis_opts=opts.AxisOpts(max_=800, interval=200,name='单位:million',axislabel_opts={'color':'white','font-size':'5px'},axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(width=2,color='white'))),
                         xaxis_opts=opts.AxisOpts(axislabel_opts={'color':'white','font-size':'5px'},axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(width=2,color='white'))))

    # 生成折线图
    plot_world_confirmed_timing = line.render_embed()

    return render_to_response(save_html_path, locals())
