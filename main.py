from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert 
from selenium import webdriver
import utils as tool
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
#Erase every file in download folder at the beginning to avoid mixed files
for file in os.listdir(download_dir):
    os.remove(download_dir+'\\'+file)

print('Download folder empty...')
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
    #Read the information of query and page
    with open("app_control.txt", "r") as file:
        first_line = file.readline()

    info=first_line.split(',')
    topic=str(info[0])
    ten=info[1]
    ten=int(ten[0])
    startPage=int(info[1])

    #class names for li: rtsLI rtsLast
    liBuscar=browser.find_elements_by_xpath("//li[contains(@class,'rtsLI rtsLast')]")[0].click()
    strSearch=topic
    txtBuscar= browser.find_elements_by_id('txtTema')[0].send_keys(strSearch)
    btnBuscaTema=browser.find_elements_by_id('btnBuscarPorTema')[0].click()
    #WAit X secs until query is loaded.
    time.sleep(40)

    if ten<=10:
        #Mechanism no failure
        SectionNextPages=browser.find_elements_by_xpath("//*[@id='grdSentencias_ctl00']/tfoot/tr/td/table/tbody/tr/td/div[2]/a[11]")[0].click()
        time.sleep(2)
        btnBuscaTema=browser.find_elements_by_id('btnBuscarPorTema')[0].click()
        time.sleep(2)
        SectionPriorPages=browser.find_elements_by_xpath("//*[@id='grdSentencias_ctl00']/tfoot/tr/td/table/tbody/tr/td/div[2]/a[1]")[0].click()
        #End of non failire mechanism
    if ten==0:
        #This means it's the page 100
        for times in range(1,11):
            if times==1:
                SectionNextPages=browser.find_elements_by_xpath("//*[@id="grdSentencias_ctl00"]/tfoot/tr/td/table/tbody/tr/td/div[2]/a[11]")[0].click()
                btnBuscaTema=browser.find_elements_by_id('btnBuscarPorTema')[0].click()
            else:
                SectionNextPages=browser.find_elements_by_xpath("//*[@id="grdSentencias_ctl00"]/tfoot/tr/td/table/tbody/tr/td/div[2]/a[12]")[0].click()
                btnBuscaTema=browser.find_elements_by_id('btnBuscarPorTema')[0].click()

    print('Start reading the page...')
    for row in range(0,20):
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
                    #I remove (') because some text got it and cassandra failed to insert it
                    summary=summary=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']')[0].text
                    str(summary).replace("'"," ")
                if col==6:
                    date=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']')[0].text                    

            else:
                #This is the xpath of the link : //*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']/a
                #This find_element method works!
                link=browser.find_element(By.XPATH,'//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']/a')
                link.click()
                #The 2nd  window should be opened, then I know
                time.sleep(20)
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
                    json_sentencia['summary']=str(summary).replace("'"," ")    


                    #Check if a pdf exists
                       
                    json_sentencia['lspdfcontent'].clear()
                    lsText=[]
                    lsWords=[]
                    for file in os.listdir(download_dir):
                        pdfDownloaded=True
                        strFile=file.split('.')[1]
                        if strFile=='PDF' or strFile=='pdf':
                            pdfFileObj = open(download_dir+'\\'+file, 'rb')
                            pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
                            pags=pdfReader.numPages
                            for x in range(0,pags):
                                pageObj = pdfReader.getPage(x)
                                lsText.append(str(pageObj.extractText().encode('utf-8')))
                                #tool.appendInfoToFile(download_dir+'\\','temp.txt',str(strContent))                             
                            pdfFileObj.close()

                        #Clean all the list of words
                        for content in lsText:
                            lsWords.append(content.split())
                            
                        lsCleanWord=[]
                        for word in lsWords:
                            lsCleanWord.append(str(word).replace("b'"," "))
                        lsCleanWord2=[]
                        for word in lsCleanWord:
                            lsCleanWord2.append(str(word).replace("\'"," "))    
                        lsCleanWord3=[]
                        for word in lsCleanWord2:
                            lsCleanWord3.append(str(word).replace("\n"," "))  
                                             
                    #When pdf is done and the record is in cassandra, delete all files in download folder
                    #If the pdf is not downloaded but the window is open, save the data without pdf
                    if pdfDownloaded==True:
                        for word in lsCleanWord3:
                            json_sentencia['lspdfcontent'].append(word)
                        for file in os.listdir(download_dir):
                            os.remove(download_dir+'\\'+file) 

                    #Insert information to cassandra
                    res=bd.cassandraBDProcess(json_sentencia)
                    if res:
                        print('Sentencia added:',str(fileNumber))
                    else:
                        print('Keep going...sentencia existed:',str(fileNumber))    

                    browser.close()
                    browser.switch_to_window(main_window)
                else:
                    print('Hold it...nothing was opened!...Search: ',strSearch)
                    browser.quit()
                    sys.exit(0)
        btnnext=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00"]/tfoot/tr/td/table/tbody/tr/td/div[3]/input[1]')[0].click()   
        #Update the info in file
        currentPage=browser.find_element_by_xpath('//*[@id="grdSentencias_ctl00"]/tfoot/tr/td/table/tbody/tr/td/div[5]/strong[1]')[0]
        with open("app_control.txt", "r") as file: 
            list_of_lines = file.readlines()
            line1=list_of_lines[0]
            info=line1.split(',')
            strTopic=info[0]
            control_page=int(currentPage)+1
            list_of_lines[0]=strTopic+','+str(control_page)

     

    browser.quit()
                           