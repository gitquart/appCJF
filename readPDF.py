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

download_dir='C:\\Users\\1098350515\\Downloads'
 
with open('json_sentencia.json') as json_file:
    json_sentencia = json.load(json_file)

#Check if a pdf exists
json_sentencia['lspdfcontent'].clear()
strContent=''
fileC=''
lsSentencia=[]
for file in os.listdir(download_dir):
    pdfDownloaded=True
    strFile=file.split('.')[1]
    if strFile=='PDF' or strFile=='pdf':
        pdfFileObj = open(download_dir+'\\'+file, 'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
        pags=pdfReader.numPages
        for x in range(0,pags):
            pageObj = pdfReader.getPage(x)
            strContent=pageObj.extractText()
            fileC=fileC+strContent

        pdfFileObj.close()


  

