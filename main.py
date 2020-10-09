from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert 
from selenium import webdriver
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
import json
import time
import os
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import requests 
from cassandra.query import SimpleStatement
import sys
import PyPDF2

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
browser.get('chrome://settings/clearBrowserData')
browser.find_element_by_xpath('//settings-ui').send_keys(Keys.ENTER)
print('Browser data clear...')

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
        browser.refresh()
    except TimeoutException:
        print('No alert found!')
        
    time.sleep(3)  
    #class names for li: rtsLI rtsLast
    liBuscar=browser.find_elements_by_xpath("//li[contains(@class,'rtsLI rtsLast')]")[0].click()
    strSearch='Ampara directo'
    txtBuscar= browser.find_elements_by_id('txtTema')[0].send_keys(strSearch)
    btnBuscaTema=browser.find_elements_by_id('btnBuscarPorTema')[0].click()
    #WAit X secs until query is loaded.
    time.sleep(15)
    #id de tabla :grdSentencias_ctl00
    # headers: //*[@id="grdSentencias_ctl00"]/thead/tr[2]
    #A way to iterate by rows
    #Every row is:
    # First page first row:   //*[@id="grdSentencias_ctl00__0"]
    #Second page first row: //*[@id="grdSentencias_ctl00__0"]
    #Last row of any page (paged by 20 ): //*[@id="grdSentencias_ctl00__19"]
    #First row, first column: //*[@id="grdSentencias_ctl00__0"]/td[1]
    #find_elements_by_xpath will ALWAYS return a list
    print('Start reading the page...')
    for row in range(0,20):
        for col in range(1,8):
            if col<7:
                value=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']')[0].text
            else:
                #This is the xpath of the link : //*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']/a
                #This find_element method works!
                link=browser.find_element(By.XPATH,'//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']/a')
                link.click()
                #The 2nd  window should be opened, then I know
                time.sleep(8)
                if len(browser.window_handles)>1:
                    #window_handles changes always
                    #If the pdf browser page opens, then the record should be done in Cassandra
                    main_window=browser.window_handles[0]
                    pdf_window=browser.window_handles[1]
                    browser.switch_to_window(pdf_window)
                    #Check if a pdf exists
                    for file in os.listdir(download_dir):
                        strFile=file.split('.')[1]
                        if strFile=='PDF' or strFile=='pdf':
                            pdfFileObj = open(download_dir+'\\'+file, 'rb')
                            pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
                            pags=pdfReader.numPages
                            strFile=''
                            for x in range(0,pags):
                                pageObj = pdfReader.getPage(x)
                                strContent=pageObj.extractText()
                                strFile=strFile+strContent

                            pdfFileObj.close()   
                            
                              
                    #When pdf is done and the record is in cassandra, delete all files in download folder
                    for file in os.listdir(download_dir):
                        os.remove(download_dir+'\\'+file)


                                
                    browser.close()
                    browser.switch_to_window(main_window)
                else:
                    print('Hold it...nothing was opened!...Search: ',strSearch)
                    sys.exit(0)
                        
     

    browser.quit()