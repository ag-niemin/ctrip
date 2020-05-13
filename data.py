# -*- coding: utf-8 -*-
import sys
import os
import importlib
importlib.reload(sys)
sys.path.append(os.getcwd())


class t_market_airticket_day(object):
    def __init__(self):
        self.table_name = 'test_market_airticket_day'
        self.column_list = ['scan_date',
                            'scan_hour',
                            'start_city',
                            'stop_city',
                            'start_airport',
                            'start_time',
                            'stop_airport',
                            'stop_time',
                            'airline',
                            'air_type',
                            'class_grade',
                            'low_price',
                            'discount',
                            'source']