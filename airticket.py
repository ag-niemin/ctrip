# -*- coding: utf-8 -*-
import time
import sys
import os
sys.path.append(os.getcwd())
import datetime
import logging
from lxml import etree
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from data import t_market_airticket_day
from OracleUtils import Oracle
import crack as crack
import importlib
importlib.reload(sys)


logging.basicConfig(level=logging.INFO,
                    # filename='selenium.log',
                    filemode='a')


class selenium_ctrip(object):

    BROWSER_PATH = os.path.dirname(__file__) + '/browser/chromedriver.exe'
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
    DATABASE = 'oracle://stg:stg123@10.6.0.94:1521/?service_name=db'

    city_dict_en = {
            'BJS': "北京",
            'SHA': "上海",
            'SZX': "深圳",
            'HGH': "杭州",
            'CTU': "成都",
            'SIA': "西安",
            'CAN': "广州"
        }
    city_dict_cn = {v: k for k, v in city_dict_en.items()}

    city_list = [
            city_dict_cn["北京"] + '-' + city_dict_cn["上海"],
            city_dict_cn["北京"] + '-' + city_dict_cn["深圳"],
            city_dict_cn["北京"] + '-' + city_dict_cn["杭州"],
            city_dict_cn["北京"] + '-' + city_dict_cn["成都"],
            city_dict_cn["上海"] + '-' + city_dict_cn["深圳"],
            city_dict_cn["上海"] + '-' + city_dict_cn["成都"],
            city_dict_cn["上海"] + '-' + city_dict_cn["西安"],
            city_dict_cn["深圳"] + '-' + city_dict_cn["杭州"],
            city_dict_cn["深圳"] + '-' + city_dict_cn["成都"],
            city_dict_cn["深圳"] + '-' + city_dict_cn["西安"],
            city_dict_cn["北京"] + '-' + city_dict_cn["广州"],
            city_dict_cn["上海"] + '-' + city_dict_cn["广州"],
            city_dict_cn["成都"] + '-' + city_dict_cn["广州"],
            city_dict_cn["杭州"] + '-' + city_dict_cn["广州"],
            city_dict_cn["西安"] + '-' + city_dict_cn["广州"],
        ]

    # 未来1天、2天、3天、4天、5天、6天、7天、8天、9天、10天、15天、20天、30天、40天、50天、60天、120天、180天
    date_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 40, 50, 60, 120, 180]

    def get_ctrip_data(self):

        scan_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        scan_hour = time.strftime('%H', time.localtime(time.time()))

        if int(scan_hour) >= 0 and int(scan_hour) <= 23:
            request_urls = []
            for city_li in self.city_list:
                for i in self.date_list:
                    today = datetime.date.today()
                    sp_date = today + datetime.timedelta(days=i)
                    st_date = str(sp_date)[0:10]
                    request_url = "https://flights.ctrip.com/itinerary/oneway/" + city_li.lower() + "?date=" + st_date
                    request_urls.append(request_url)

            browser_path = self.BROWSER_PATH
            options = Options()
            options.add_argument('--headless') # 设置Chrome不弹出界面
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')  # 禁用GPU加速
            options.add_argument("--user-agent=%s" % self.USER_AGENT)  # 设置用户代理
            options.add_argument('--log-level=3')  # python调用selenium会产生大量日志
            options.add_argument('--start-maximized')  # 最大化运行
            options.add_argument('--disable-infobars')  # 禁用浏览器正在被自动化程序控制的提示
            # options.add_argument('--blink-settings=imagesEnabled=false') # 不加载图片
            options.add_experimental_option('excludeSwitches', ['enable-logging'])

            driver = Chrome(executable_path=browser_path, chrome_options=options)


            for url in request_urls:
                items = []
                driver.get(url)
                # 判断是否弹出滑动验证码
                try:
                    if driver.find_element_by_xpath('//*[@id="J_slider_verification_qwewq"]/div[1]/div[2]'):
                        driver, url = crack.crack_slide_verification(driver, url)
                        driver, url, characters, characters_pos = crack.crack_ocr_verification(driver, url)
                        driver, url, characters, characters_pos = crack.fresh_verification(driver, url, characters, characters_pos)
                        driver = crack.click_verification(driver, url, characters, characters_pos)
                        driver = crack.check_verification(driver, url)

                        # 判断是否下拉到底部
                        s = 0
                        t = 1
                        while s < t:
                            for i in range(10):  # 下拉10次
                                driver.execute_script("var q=document.documentElement.scrollTop=10000")
                            elements = driver.find_elements_by_xpath('//div[@class="search_box search_box_tag search_box_light Label_Flight"]')
                            s = len(elements)
                            for i in range(10):  # 再下拉10次
                                driver.execute_script("var q=document.documentElement.scrollTop=10000")
                            elements = driver.find_elements_by_xpath('//div[@class="search_box search_box_tag search_box_light Label_Flight"]')
                            t = len(elements)

                except:

                    # 判断是否下拉到底部
                    s = 0
                    t = 1
                    while s < t:
                        for i in range(10):  # 下拉10次
                            driver.execute_script("var q=document.documentElement.scrollTop=10000")
                        elements = driver.find_elements_by_xpath('//div[@class="search_box search_box_tag search_box_light Label_Flight"]')
                        s = len(elements)
                        for i in range(10):  # 再下拉10次
                            driver.execute_script("var q=document.documentElement.scrollTop=10000")
                        elements = driver.find_elements_by_xpath('//div[@class="search_box search_box_tag search_box_light Label_Flight"]')
                        t = len(elements)

                driver.implicitly_wait(2)
                # driver.save_screenshot('screenshot-result.png')
                html = driver.page_source

                rbody = etree.HTML(html, parser=etree.HTMLParser(encoding='utf-8'))
                res = rbody.xpath('//div[@class="search_box search_box_tag search_box_light Label_Flight"]')
                if res:
                    # print(url + ' selenium chrome scraped %s records' % str(len(res)))
                    logging.info(url + ' selenium chrome scraped %s records' % str(len(res)))
                    for r in res:
                        st_date = url[-10:]
                        city_li = url.replace('https://flights.ctrip.com/itinerary/oneway/', '')[0:7].upper()
                        startcity = self.city_dict_en[city_li[0:city_li.index('-')]]
                        stopcity = self.city_dict_en[city_li[city_li.index('-') + 1:]]

                        startairport = r.xpath('./div[1]/div[1]/div[@class="inb right"]/div[@class="airport"]//text()')[0]
                        starttime = r.xpath('./div[1]/div[1]/div[@class="inb right"]/div[@class="time_box"]/strong[1]/text()')[0]
                        stopairport = r.xpath('./div[1]/div[1]/div[@class="inb left"]/div[@class="airport"]//text()')[0]
                        stoptime = r.xpath('./div[1]/div[1]/div[@class="inb left"]/div[@class="time_box"]/strong[1]/text()')[0]
                        airline = r.xpath('./div[1]/div[1]/div[@class="inb logo"]/div[1]/div[1]/span[1]/span[1]/strong[1]/text()')[0]
                        airtype = r.xpath('./div[1]/div[1]/div[@class="inb logo"]/div[1]/div[1]/span[1]/span[1]/span[1]/text()')[0]
                        if r.xpath('./div[1]/div[1]/div[@class="inb price child_price lowest_price"]/div[1]/span[@class="base_price02"]/text()'):
                            price = r.xpath('./div[1]/div[1]/div[@class="inb price child_price lowest_price"]/div[1]/span[@class="base_price02"]/text()')[0]
                            class_discount = r.xpath('./div[1]/div[1]/div[@class="inb price child_price lowest_price"]/div[1]/div[@class="flight_price_tips"]/div[1]/span[1]/text()')[0]
                        else:
                            price = r.xpath('./div[1]/div[1]/div[@class="inb price child_price"]/div[1]/span[@class="base_price02"]/text()')[0]
                            class_discount = r.xpath('./div[1]/div[1]/div[@class="inb price child_price"]/div[1]/div[@class="flight_price_tips"]/div[1]/span[1]/text()')[0]
                        classgrade = class_discount[0:class_discount.index(u'舱') + 1]
                        discount = class_discount.replace(classgrade, '') or u'全价'

                        item = {}
                        item['scan_date'] = datetime.datetime.strptime(str(scan_date), '%Y-%m-%d')
                        item['scan_hour'] = str(scan_hour)
                        item['start_city'] = startcity
                        item['stop_city'] = stopcity
                        item['start_airport'] = startairport
                        item['start_time'] = datetime.datetime.strptime(st_date + ' ' + starttime, '%Y-%m-%d %H:%M')
                        item['stop_airport'] = stopairport
                        if int(starttime[0:2]) <= int(stoptime[0:2]):
                            item['stop_time'] = datetime.datetime.strptime(st_date + ' ' + stoptime, '%Y-%m-%d %H:%M')
                        else:
                            item['stop_time'] = datetime.datetime.strptime(st_date + ' ' + stoptime,'%Y-%m-%d %H:%M') + datetime.timedelta(days=1)
                        item['airline'] = airline
                        item['air_type'] = airtype
                        item['source'] = url
                        item['low_price'] = price
                        item["discount"] = discount
                        item["class_grade"] = classgrade

                        # print(item)
                        items.append(item)

                else:
                    # print(url + " selenium chrome failure, failure")
                    # driver.save_screenshot('screenshot-failure.png')
                    logging.info(url + " selenium chrome failure, failure")

            driver.quit()
            res = {'scan_date': scan_date,
                   'scan_hour': scan_hour,
                   'flights' : items}
            return res


    def load_ctrip_data(self,seleres):
        table = t_market_airticket_day()
        self.table_name = table.table_name
        self.column_list = table.column_list

        orcl = Oracle()
        insertValues = []
        deleteValues = []

        scan_date = datetime.datetime.strptime(str(seleres['scan_date']), '%Y-%m-%d')
        scan_hour = seleres['scan_hour']
        deleteValues.append([scan_date,scan_hour])

        for item in seleres['flights']:
            insertValues.append([item['scan_date'],
                                 item['scan_hour'],
                                 item['start_city'],
                                 item['stop_city'],
                                 item['start_airport'],
                                 item['start_time'],
                                 item['stop_airport'],
                                 item['stop_time'],
                                 item['airline'],
                                 item['air_type'],
                                 item['class_grade'],
                                 item['low_price'],
                                 item['discount'],
                                 item['source']])

        column_nums = len(self.column_list)
        orders = list(range(1, column_nums + 1))
        value_orders = ','.join([':' + str(i) for i in orders])
        insertsql = "insert into %s(%s) values(%s)" % (self.table_name, ','.join(self.column_list), value_orders)
        deletesql = "delete from %s where scan_date=:1 and scan_hour=:2" % (self.table_name)
        orcl.batchinsert_ex(deletesql, deleteValues, insertsql, insertValues)


if __name__ == '__main__':
    ctrip = selenium_ctrip()
    res = ctrip.get_ctrip_data()
    ctrip.load_ctrip_data(res)
