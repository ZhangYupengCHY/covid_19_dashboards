# -*- coding: utf-8 -*-
"""
Proj: pyecharts
Created on:   2020/7/1 18:32
@Author: RAMSEY

"""

import pandas as pd
from sqlalchemy import create_engine
from retry import retry

"""
连接数据库mysql和redis数据库的方法
"""


class ConnMysql(object):
    """
    连接mysql数据库
    """

    def __init__(self, host='localhost', port=3306, username='root', password='', database='covid-19'):
        """
        初始化连接MySQL数据
        """

        # 建立连接
        engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}?charset={}".format(
            username, password, host, port, database, 'utf8'))

        self.con = engine.connect()

    @retry(tries=3, delay=2)
    def read_table(self, sql):
        """
        读取数据库中的内容
        :param sql:string
                sql语言
        :return:pd.DataFrame
                查询结果
        """
        # 连接数据库
        # 读取MySQL数据
        df_data = pd.read_sql(sql, self.con)
        self.con.close()

        return df_data
