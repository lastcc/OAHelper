# -*- coding: utf-8 -*-
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC

import cookielib
from tinyhttp import Firefox64 as Firefox
from tinyhttp import ua

import urllib
import urllib2

from log_config import log

def convert_cookie(cookie):
    #converts cookie from one type to another
    #chromedriver cookie to cookielib cookie
    override={}
    for key in cookie:
        value=cookie[key]
        if isinstance(key,unicode):
            key=str(key)
        if isinstance(value, unicode):
            value=str(value)

        if key=='expiry':
            key='expires'
            print(value)

        override[key]=value


    defaults=dict(version=0,
                  name=None,
                  value=None,
                  port=None,
                  port_specified=None,
                  domain=None,
                  domain_specified=True,
                  domain_initial_dot=False,
                  path='/',
                  path_specified=None,
                  secure=False,
                  expires=None,
                  discard=None,
                  comment=None,
                  comment_url=None,
                  rest=None,
                  rfc2109=False) 

    for key in override:
        if defaults.has_key(key):
            defaults[key]=override[key]

    new_cookie=cookielib.Cookie(**defaults)

    return new_cookie


def get_eBay_cookiejar(username, password,login_url,use_which='Chrome', wait=False):

    options = webdriver.ChromeOptions()
    options.add_argument('--user-agent=%s'%ua)

    profile = webdriver.FirefoxProfile()
    profile.set_preference("general.useragent.override", ua)

    if use_which=='Chrome':
        driver = webdriver.Chrome(chrome_options=options)
    elif use_which=='Firefox':
        driver = webdriver.Firefox(profile)

    driver.get(login_url)
    time.sleep(1)

    driver.find_element_by_id("userid").send_keys(username)
    time.sleep(2)
    driver.find_element_by_id("pass").send_keys(password)
    time.sleep(2)
    driver.find_element_by_id("sgnBt").click()
    time.sleep(1)
    
    if wait:
        x = raw_input('Waiting...')

    cookie_jar=cookielib.CookieJar()

    cookies=driver.get_cookies()

    driver.close()
    for each_cookie in cookies:
        converted_cookie=convert_cookie(each_cookie)
        cookie_jar.set_cookie(converted_cookie)    

    return cookie_jar

def get_eBay_opener(username=None, password=None,login_url=None,use_which='Chrome', wait=False):
    if not use_which in ['Chrome','Firefox']:
        raise NotImplementedError('Given browser func not implemented. %r'%use_which)
    
    if username==None:
        username='homesale_estore'
    if password==None:
        password='@flytstar3651s'
    if login_url==None:
        login_url='https://signin.ebay.com.hk/ws/eBayISAPI.dll?SignIn'
    
    max_try_times=3
    
    while max_try_times:
        max_try_times-=1
        try:
            cookie_jar=get_eBay_cookiejar(username, password,login_url, wait=wait)
            break
        except:
            log.exception('[Login]')
            
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
    return opener


def get_oa_opener():
    url='http://banggood.sellercube.com/Start/Login'
    data='email=610591830%40qq.com&password=topsecrett1&rememberMe=true'

    cookie_jar=cookielib.CookieJar()
    opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar)) 

    headers={'User-Agent':ua}

    response=Firefox(opener).post(url=url,form=data,headers=headers, encode_to='gbk')
    print(response)

    return opener


def get_oa_opener2():

    use_which='Firefox'

    options = webdriver.ChromeOptions()
    options.add_argument('--user-agent=%s'%ua)

    #profile = webdriver.FirefoxProfile()
    #profile.set_preference("general.useragent.override", ua)

    if use_which=='Chrome':
        driver = webdriver.Chrome(chrome_options=options)
    elif use_which=='Firefox':
        driver = webdriver.Firefox()

    driver.get('http://banggood.sellercube.com/Start/html/cn/login.html')
    time.sleep(1)

    driver.find_element_by_id("email").send_keys('610591830@qq.com')
    time.sleep(2)
    driver.find_element_by_id("password").send_keys('topsecrett1')
    time.sleep(2)
    driver.find_element_by_tag_name('button').click()
    time.sleep(1)

    cookie_jar=cookielib.CookieJar()

    cookies=driver.get_cookies()

    driver.close()
    for each_cookie in cookies:
        converted_cookie=convert_cookie(each_cookie)
        cookie_jar.set_cookie(converted_cookie)    

    opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar)) 
    
    return opener

if __name__=='__main__':
    get_oa_opener()
