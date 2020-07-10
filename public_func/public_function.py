# -*- coding: utf-8 -*-
"""
Proj: pyecharts
Created on:   2020/7/1 18:47
@Author: RAMSEY

"""

"""
常用的一些方法
"""
from datetime import datetime


def run_time(func):
    """
    计算程序运行时间
    常被当做类方法来使用
    Returns:

    """

    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        print(f'函数{func.__name__}花费:{end_time - start_time}')
        return result

    return wrapper
