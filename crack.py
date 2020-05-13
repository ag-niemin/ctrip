# -*- coding: utf-8 -*-
import os
import sys
import time
import logging
from selenium.webdriver.common.action_chains import ActionChains
sys.path.append(os.getcwd())
from chineseocr_lite import ocr
import importlib
importlib.reload(sys)

logging.basicConfig(level=logging.INFO,
                    # filename='selenium.log',
                    filemode='a')

# 破解携程滑块验证码
def crack_slide_verification(browser,url):
    driver = browser
    slider_btn = driver.find_element_by_xpath('//*[@id="J_slider_verification_qwewq"]/div[1]/div[2]')
    if slider_btn:
        logging.info(url + u' drag slider button')
        actions = ActionChains(driver)
        actions.click_and_hold(slider_btn).perform()
        actions.move_by_offset(280,0).release(slider_btn).perform()
        # driver.save_screenshot('screenshot-verify.png')

        return driver,url

# 破解携程中文验证码
def crack_ocr_verification(browser,url):
    driver = browser
    dest_img_url = driver.find_element_by_xpath('//*[@id="J_slider_verification_qwewq-choose"]/div[2]/div[1]/img').get_attribute('src')
    dest_img_res = ocr.resultBase64(dest_img_url)
    for dest_img_character in dest_img_res:
        # dest_img_characters = unicode(dest_img_character['word'], 'utf-8')
        dest_img_characters = dest_img_character['word']
        logging.info(url + u' dest characters: ' + dest_img_characters)
        characters = list(dest_img_characters)

    sele_img_url = driver.find_element_by_xpath('//*[@id="J_slider_verification_qwewq-choose"]/div[2]/div[3]/img').get_attribute('src')
    sele_img_res = ocr.resultBase64(sele_img_url)
    sele_characters = []
    sele_characters_pos = []
    for sele_img_character in sele_img_res:
        sele_characters.append(sele_img_character['word'])
        sele_characters_pos.append(sele_img_character['pos'])
    logging.info(url + u' candidate characters: ' + ' '.join(sele_characters))

    characters_pos = []
    for c in characters:
        for i in range(0,len(sele_characters)):
            if sele_characters[i] == c:
                characters_pos.append(sele_characters_pos[i])

    return driver,url,characters,characters_pos

# 刷新携程中文验证码
def fresh_verification(browser,url,characters,characters_pos):
    driver = browser
    if len(characters_pos) == len(characters):
        return driver,url,characters,characters_pos

    while (len(characters_pos) != len(characters)):
       cpt_choose_refresh = driver.find_element_by_xpath('//*[@id="J_slider_verification_qwewq-choose"]/div[2]/div[4]/div/a')
       cpt_choose_refresh.click()
       driver,url,characters,characters_pos = crack_ocr_verification(driver,url)

       if len(characters_pos) == len(characters):
           # driver.save_screenshot('screenshot-verify.png')
           return driver,url,characters,characters_pos

# 点选携程中文验证码
def click_verification(browser,url,characters,characters_pos):
    driver = browser

    actions = ActionChains(driver)
    while (len(characters_pos) == len(characters)):
        cpt_big_img = driver.find_element_by_class_name("cpt-big-img")
        for i in range(0,len(characters)):
            logging.info(url + u' click ' + characters[i] + u' located (' + str(characters_pos[i]['x']) + ',' + str(characters_pos[i]['y']) + ')')
            actions.move_to_element_with_offset(cpt_big_img,0,0).perform()
            actions.move_by_offset(characters_pos[i]['x'],characters_pos[i]['y']).click().perform()
            time.sleep(2)
        # driver.save_screenshot('screenshot-click.png')

        # 提交点选验证码
        cpt_choose_submit = driver.find_element_by_xpath('//*[@id="J_slider_verification_qwewq-choose"]/div[2]/div[4]/a')
        cpt_choose_submit.click()
        # driver.save_screenshot('screenshot-submit.png')

        return driver

# 检查是否点选成功
def check_verification(browser,url):
    driver = browser
    cpt_success_click = driver.find_element_by_xpath('//*[@id="J_slider_verification_qwewq"]/div[1]/div[3]/div/span')
    while (u'校验成功' not in cpt_success_click.text):
        driver,url,characters,characters_pos = crack_ocr_verification(driver,url)
        driver,url,characters,characters_pos = fresh_verification(driver, url, characters, characters_pos)
        driver = click_verification(driver, url, characters, characters_pos)
    logging.info(url + ' ' + cpt_success_click.text)

    # 点击重新搜索
    research_btn = driver.find_element_by_xpath('//*[@id="app"]/div/div[2]/div/div[2]/div/div[2]/div/button')
    research_btn.click()
    # driver.save_screenshot('screenshot-search.png')
    time.sleep(2)
    return driver