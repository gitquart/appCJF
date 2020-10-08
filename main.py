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

options = webdriver.ChromeOptions()

download_dir='C:\\Users\\1098350515\\Downloads'
profile = {"plugins.plugins_list": [{"enabled": False, "name": "Chrome PDF Viewer"}], # Disable Chrome's PDF Viewer
               "download.default_directory": download_dir , 
               "download.prompt_for_download": False,
               "download.directory_upgrade": True,
               "download.extensions_to_open": "applications/pdf",
               "plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome
               }
options.add_experimental_option("prefs", profile)


chromedriver_autoinstaller.install()
browser=webdriver.Chrome(options=options)
browser.delete_all_cookies()
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
                js=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']/a')[0]
                time.sleep(10)
                browser.execute_script('arguments[0].click();',js)
                if len(browser.window_handles)>1:
                    #If the pdf browser page opens, then the record should be done in Cassandra
                    pdf_window=browser.window_handles[1]
                    pdf_window.close()
                    
                            
    browser.quit()

