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
    #WAit 20 secs until query is loaded.
    time.sleep(20)
    #id de tabla :grdSentencias_ctl00
    # headers: //*[@id="grdSentencias_ctl00"]/thead/tr[2]
    #A way to iterate by rows
    #Every row is:
    # First page first row:   //*[@id="grdSentencias_ctl00__0"]
    #Second page first row: //*[@id="grdSentencias_ctl00__0"]
    #Last row of any page (paged by 20 ): //*[@id="grdSentencias_ctl00__19"]
    #First row, first column: //*[@id="grdSentencias_ctl00__0"]/td[1]

    for row in range(0,20):
        for col in range(1,8):
            if col<7:
                value=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']')[0].text
            else:
                browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']/a')[0].click()

            
            

    browser.quit()

