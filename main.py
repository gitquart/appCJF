from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.alert import Alert 
import json
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
import time
import os
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import requests 
from cassandra.query import SimpleStatement



chromedriver_autoinstaller.install()
browser=webdriver.Chrome()
url="https://sise.cjf.gob.mx/consultasvp/default.aspx"

response= requests.get(url)
status= response.status_code
if status==200:
    browser.get(url)
    try:
        WebDriverWait(browser, 5).until (EC.alert_is_present())
        #switch_to.alert for switching to alert and accept
        alert = browser.switch_to.alert
        alert.dismiss()
    except TimeoutException:
        print('No alert found!')
        
    #class names for li: rtsLI rtsLast
    liBuscar=browser.find_elements_by_xpath("//li[contains(@class,'rtsLI rtsLast')]")[0].click()
    txtBuscar= browser.find_elements_by_id('txtTema')[0].send_keys('Amparo directo')
    btnBuscaTema=browser.find_elements_by_id('btnBuscarPorTema')[0].click()
    time.sleep(100)
    #page = BeautifulSoup(browser.page_source, 'lxml')
    browser.quit()

