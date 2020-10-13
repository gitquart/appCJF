from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert 
from selenium import webdriver
import chromedriver_autoinstaller
import json
import textract
import time
import os
import requests 
import sys
import PyPDF2
import uuid
import cassandraSent as bd

pathToHere=os.getcwd()

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
    strSearch='Amparo directo'
    txtBuscar= browser.find_elements_by_id('txtTema')[0].send_keys(strSearch)
    btnBuscaTema=browser.find_elements_by_id('btnBuscarPorTema')[0].click()
    #WAit X secs until query is loaded.
    time.sleep(20)
    #id de tabla :grdSentencias_ctl00
    # headers: //*[@id="grdSentencias_ctl00"]/thead/tr[2]
    #A way to iterate by rows
    #Every row is:
    # First page first row:   //*[@id="grdSentencias_ctl00__0"]
    #Second page first row: //*[@id="grdSentencias_ctl00__0"]
    #Last row of any page (paged by 20 ): //*[@id="grdSentencias_ctl00__19"]
    #First row, first column: //*[@id="grdSentencias_ctl00__0"]/td[1]
    #find_elements_by_xpath will ALWAYS return a list
    #Get the page value and next click button
    
    PageTotal=int(browser.find_element(By.XPATH,'//*[@id="grdSentencias_ctl00_ctl03_ctl01_PageSizeComboBox_Input"]').get_attribute('value'))
    infoPag=browser.find_element(By.XPATH,'//*[@id="grdSentencias_ctl00"]/tfoot/tr/td/table/tbody/tr/td/div[5]').text
    data=infoPag.split(' ')
    data=data[4].split(',')
    pagLimit=int(data[0])+1

    print('Start reading the page...')
    for page in range(1,pagLimit):
        #Time sleep for the click to change paging
        time.sleep(3)
        for row in range(0,PageTotal):
            pdfDownloaded=False
            for col in range(1,8):
                if col<7:
                    if col==1:
                        juris_rev=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']')[0].text
                    if col==2:
                        filetype=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']')[0].text
                    if col==3:
                        subject=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']')[0].text
                    if col==4:
                        fileNumber=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']')[0].text
                    if col==5:
                        summary=summary=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']')[0].text
                    if col==6:
                        date=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']')[0].text                    

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
                    
                        with open('json_sentencia.json') as json_file:
                            json_sentencia = json.load(json_file)

                        json_sentencia['id']=str(uuid.uuid4())
                        json_sentencia['filenumber']=fileNumber
                        json_sentencia['filetype']=filetype
                        json_sentencia['jurisdictionalreviewer']=juris_rev
                        # timestamp accepted for cassandra: yyyy-mm-dd 
                        #In web site, the date comes as day-month-year
                        dateStr=date.split('/') #0:day,1:month,2:year
                        dtDate=dateStr[2]+'-'+dateStr[1]+'-'+dateStr[0]
                        json_sentencia['publication_datetime']='1000-01-01'
                        json_sentencia['strpublicationdatetime']=dtDate
                        json_sentencia['subject']=subject
                        json_sentencia['summary']=summary    


                        #Check if a pdf exists
                        json_sentencia['lspdfcontent'].clear()
                        strContent=''
                        fileC=''
                        lsSentencia=[]
                        for file in os.listdir(download_dir):
                            pdfDownloaded=True
                            strFile=file.split('.')[1]
                            if strFile=='PDF' or strFile=='pdf':
                                text = textract.process(download_dir+'\\'+file, encoding='utf_8')
                            for text in lsSentencia:
                                json_sentencia['lspdfcontent'].append(str(text))        
                            

                        #When pdf is done and the record is in cassandra, delete all files in download folder
                        #If the pdf is not downloaded but the window is open, save the data without pdf
                        if pdfDownloaded==True:
                            #json_sentencia['lspdfcontent']=fileC
                            for file in os.listdir(download_dir):
                                os.remove(download_dir+'\\'+file) 

                        #Insert information to cassandra
                        res=bd.cassandraBDProcess(json_sentencia)
                        if res:
                            print('Sentencia added...')
                        else:
                            print('Keep going...sentencia existed')    

                        browser.close()
                        browser.switch_to_window(main_window)
                    else:
                        print('Hold it...nothing was opened!...Search: ',strSearch)
                        sys.exit(0)
        btnnext=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00"]/tfoot/tr/td/table/tbody/tr/td/div[3]/input[1]')[0].click()               
     

    browser.quit()

    """
     pdfFileObj = open(download_dir+'\\'+file, 'rb')
                                pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
                                pags=pdfReader.numPages
                                for x in range(0,pags):
                                    pageObj = pdfReader.getPage(x)
                                    strContent=pageObj.extractText().decode('UTF-8')
                                    lsSentencia.append(str(strContent))

                                pdfFileObj.close()

    """                            