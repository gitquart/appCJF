#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 12 13:13:25 2020

@author: quart

Importat data to develop the code:

-Link to get thesis of any period ( ID changes only):     
https://sjf.scjn.gob.mx/SJFSist/Paginas/DetalleGeneralV2.aspx?ID=#&Clase=DetalleTesisBL&Semanario=0

-10th period , last thesis found 1531. Registro No. 2 021 804
- 2,021,819 seems to be a nice limit to look for thesis


"""



import json
from selenium import webdriver
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
import time
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
#import writeFile as wf
import requests 
from cassandra.query import SimpleStatement
import os

#Global variables


pathToHere=os.getcwd()
chromedriver_autoinstaller.install()
browser=webdriver.Chrome()


"""
readUrl

Reads the url from the jury web site
"""

def readUrl(sense,l_bot,l_top,period):
    
    res=''
    #Can use noTesis as test variable too
    noTesis=0
    strField=''
    
    #Import JSON file
    print('Starting process...')
    
    if l_top==0:
        l_top=lim_top_fijo
    if l_bot==0:
        l_bot=lim_bot_fijo
    
    with open('thesis_json_base.json') as f:
        json_thesis = json.load(f)
          
    #Onwars for    
    if(sense==1):
        for x in range(l_bot,l_top):
            print('Current thesis:',str(x))
            res=prepareThesis(x,json_thesis,period)
            #wf.appendInfoToFile(pathToHere+'tests/',str(x)+'.json',json.dumps(json_thesis))
            if(res!=''):
                thesis_added=cassandraBDProcess(1,res,period) 
                #thesis_added=True 
                if thesis_added==True:
                    noTesis=noTesis+1
                    print('Thesis ready: ',noTesis, "-ID: ",x)
                    #if noTesis==3:
                    #   break
    #Backwards For             
    if(sense==2):
        for x in range(l_top,l_bot,-1): 
            print('Current thesis:',str(x))
            res=prepareThesis(x,json_thesis,period)
            #wf.appendInfoToFile(pathToHere+'tests/',str(x)+'.json',json.dumps(json_thesis))
            if(res!=''):
                #Upload thsis to Cassandra 
                thesis_added=cassandraBDProcess(1,res,period) 
                #thesis_added=True 
                if thesis_added==True:
                    noTesis=noTesis+1
                    print('Thesis ready: ',noTesis, "-ID: ",x)
                    #if noTesis==3:
                    #    break 
                                   
    browser.quit()  
    
    return 'It is all done'
              
def cassandraBDProcess(op,json_thesis,period_num):
    
    global thesis_added
    global row

    #Connect to Cassandra
    objCC=CassandraConnection()
    cloud_config= {
        'secure_connect_bundle': pathToHere+'\\secure-connect-dbquart.zip'
    }
    
    auth_provider = PlainTextAuthProvider(objCC.cc_user,objCC.cc_pwd)
    
    
        
    if period_num==9:
        strperiod='Novena Época'
    if period_num==10:
        strperiod='Décima Época'    
    
    
    if op==1:
        
        #Get values for query
        #Ejemplo : Décima Época
        thesis_added=False
        period=json_thesis['period']
        period=period.lower()
    
        cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
        session = cluster.connect()
        session.default_timeout=70
        row=''
        idThesis=json_thesis['id_thesis']
        heading=json_thesis['heading']
        #Check wheter or not the record exists
           
        querySt="select id_thesis from thesis.tbthesis where id_thesis="+str(idThesis)+" and heading='"+heading+"'"
                
        future = session.execute_async(querySt)
        row=future.result()
        
        if row: 
            thesis_added=False
            cluster.shutdown()
        else:
                
            #Insert Data as JSON
            json_thesis=json.dumps(json_thesis)
            #wf.appendInfoToFile(dirquarttest,str(idThesis)+'.json', json_thesis)                
            insertSt="INSERT INTO thesis.tbthesis JSON '"+json_thesis+"';" 
            future = session.execute_async(insertSt)
            future.result()  
            thesis_added=True
            cluster.shutdown()     
                
                
    if op==2:

        cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
        session = cluster.connect()
        session.default_timeout=70
        
        row=''
        print('Test python vs scala')
       
        querySt="select * from thesis.tbthesis where period_number>"+str(period_num)+" ALLOW FILTERING "   
        
        count=0
        statement = SimpleStatement(querySt, fetch_size=1000)
        for row in session.execute(statement):
            count=count+1
        
        print('Count',str(count))   
        cluster.shutdown() 
            
    
    if op==3:

        cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
        session = cluster.connect()
        session.default_timeout=70
        
        row=''
        count=0
        print('Deleting...')
        querySt="select id_thesis from thesis.tbthesis where period_number="+str(period_num)+"" 
        row = session.execute(querySt)
        if row:
            for r in row:
                strId=str(r[0])
                deleteSt='delete from thesis.tbthesis where id_thesis='+strId+''
                count=count+1
                session.execute(deleteSt)
                
        print('Deleted:',str(count))  
        cluster.shutdown()      
                
    if op==4:

        session = cluster.connect()
        session.default_timeout=70
        print('Updating started...')
        querySt="select id_thesis from thesis.tbthesis where period='Décima Época'"
        future = session.execute_async(querySt)
        res= future.result();
        count=0
        if res:
            for row in res:
                print('Hang on...')
                idThesis=row[0]                
                updateSt="update thesis.tbthesis set period_number=10  where id_thesis="+str(idThesis)+""
                future = session.execute_async(updateSt)
                res= future.result();    
                print(idThesis,': updated')
                count=count+1
            
                            
        print('Total of thesis updated:',count)  
        cluster.shutdown()          
                         
    return thesis_added


     

"""
prepareThesis:
    Reads the url where the service is fetching data from thesis
"""

def prepareThesis(id_thesis,json_thesis,period): 

    if period==9:
        strperiod='Novena Época'
    if period==10:
        strperiod='Décima Época'
        
      
        
    result=''
    strIdThesis=str(id_thesis) 
    url="https://sjf.scjn.gob.mx/SJFSist/Paginas/DetalleGeneralV2.aspx?ID="+strIdThesis+"&Clase=DetalleTesisBL&Semanario=0"
    response= requests.get(url)
    status= response.status_code
    if status==200:
        browser.get(url)
        time.sleep(1)
        thesis_html = BeautifulSoup(browser.page_source, 'lxml')
        title=thesis_html.find('title')
        title_text=title.text
        if title_text.strip() != msg_error:  
            #Clear Json  
            json_thesis['id_thesis']=''
            json_thesis['lst_precedents'].clear()
            json_thesis['thesis_number']=''
            json_thesis['instance']=''
            json_thesis['source']=''
            json_thesis['book_number']=''  
            json_thesis['publication_date']='' 
            json_thesis['dt_publication_date']=''
            json_thesis['period']=''
            json_thesis['page']=''
            json_thesis['jurisprudence_type']=''
            json_thesis['type_of_thesis']=''
            json_thesis['subject']=''
            json_thesis['heading']=''
            json_thesis['text_content']=''
            json_thesis['publication']=''
            
            
            json_thesis['id_thesis']=int(strIdThesis)
            #Fet values from header, and body of thesis
            for obj in thesis_id:  
                field=thesis_html.find(id=obj)
                if field.text != '':   
                    strField=field.text.strip()
                    if obj==thesis_id[0]:
                        json_thesis['thesis_number']=strField
                    if obj==thesis_id[1]:
                        json_thesis['instance']=strField
                    if obj==thesis_id[2]:
                        json_thesis['source']=strField
                    #Special Case    
                    if obj==thesis_id[3]:
                        if strField=='.':
                            json_thesis['book_number']=''  
                            json_thesis['publication_date']='' 
                            json_thesis['dt_publication_date']='1000-01-01'
                        else:
                            json_thesis['book_number']=strField  
                            json_thesis['publication_date']='' 
                            json_thesis['dt_publication_date']='1000-01-01' 
                                                
                    if obj==thesis_id[4]:
                        json_thesis['period']=strField
                        if strField=='Quinta Época':
                            json_thesis['period_number']=5
                        if strField=='Sexta Época':
                            json_thesis['period_number']=6
                        if strField=='Séptima Época':
                            json_thesis['period_number']=7
                        if strField=='Octava Época':
                            json_thesis['period_number']=8        
                        if strField=='Novena Época':
                            json_thesis['period_number']=9
                        if strField=='Décima Época':
                            json_thesis['period_number']=10       
                    if obj==thesis_id[5]:
                        json_thesis['page']=strField
                    #Special case :
                    #Type of jurispricende: pattern => (Type of thesis () )
                    if obj==thesis_id[6]:
                        strField=strField.replace(')','')
                        chunks=strField.split('(')
                        count=len(chunks)
                        if count==2: 
                            json_thesis['type_of_thesis']=chunks[0]
                            json_thesis['subject']=chunks[1]
                        
                        if count==3:
                            json_thesis['jurisprudence_type']=chunks[0]
                            json_thesis['type_of_thesis']=chunks[1]
                            json_thesis['subject']=chunks[2] 

                    if obj==thesis_id[7]:
                        json_thesis['heading']=strField.replace("'",',')
                    if obj==thesis_id[8]:
                        json_thesis['text_content']=strField.replace("'",',') 
                    if obj==thesis_id[9]:  
                        children=thesis_html.find_all(id=obj)
                        for child in children:
                            for p in precedentes_list:   
                                preced=child.find_all(class_=p)
                                for ele in preced:
                                    if ele.text!='':
                                        strValue=ele.text.strip()
                                        json_thesis['lst_precedents'].append(strValue.replace("'",','))

                
            for obj in thesis_class:
                field=thesis_html.find(class_=obj)
                if field.text != '':   
                    strField=field.text.strip()
                    if obj==thesis_class[0]:
                        json_thesis['publication']=strField
   
        thesis_html=''
        result=json_thesis
        
        if title_text.strip() == msg_error:
            result=''
            
            
    else:
        print('Custom error ID:',strIdThesis)
        result=''
        
    return  result


    
class CassandraConnection():
    cc_user='quartadmin'
    cc_keyspace='thesis'
    cc_pwd='P@ssw0rd33'
    cc_databaseID='9de16523-0e36-4ff0-b388-44e8d0b1581f'
        

