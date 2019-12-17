###################################################################################
# Environment: python3X
# This program or module is a software: 
# Name: ipatrans
# Version: 1.24
# Function:#
#          1. Support IPA tranning and practice
# New Add:
#       GUI support  
# Fix:
#          1.
# Author: Pei-Tai
########
#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
# import json
import time
from bs4 import BeautifulSoup
import requests
import _thread
import struct
from ftplib import FTP 
import io
import simpleaudio as sa 

from PyQt5.QtWidgets import QMainWindow,QMessageBox,QApplication,QFileDialog,QWidget,QInputDialog,QLineEdit
import mainwindow
from PyQt5.QtCore import QThread,QObject, pyqtSignal, QEvent, QTimer,QElapsedTimer
from PyQt5 import QtWidgets,QtGui,QtCore
import configparser


music_url ='' # we remove the link site for license issue 

Default_Dict={'IP1':music_url,'IP2':'','build':'','save_directory':'','url':'','list':'',\
    'practice':'/audio','test':'/test'}           

TVersion='1.24'
 

class HANDLE_FILE:
    def __init__(self):  
        self.req=requests.session()   


    def query_get(self,go_url):
        headervalue={
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'}
 
        for _ in range(4):
            try:
                content = self.req.get(go_url,timeout=3,headers=headervalue)               
                if content.status_code != requests.codes.ok:
                    # print("Query Web GET failed")
                    return False,-1
                return True,content    
            except Exception as err:
                time.sleep(0.5)
                if _ >= 3:
                    # print(err)
                    return False, -1  
   

class AudioHandler(QObject):
    update = pyqtSignal(int)
    item=pyqtSignal(str)
    errtag=pyqtSignal(str)
    timeup=pyqtSignal()
    def __init__(self,parent=None):
        QObject.__init__(self, parent=parent)
        self.handleUrl=HANDLE_FILE()        
        self.soundarray={}
        self.audioanswer={}
        self.editanswer={}
        self._download_flag=False
        self._TimeCount=0 
        self._stop=False
        self._end=False       

    def query_file(self):
        self.update.emit(5)   
        status, content=self.handleUrl.query_get(Default_Dict['url']+Default_Dict['list'])
        if status ==False:
            self.errtag.emit("Download Failed!!")
            return        
        data=content.text 
        itemNum=0            
        soup = BeautifulSoup(data,"lxml")
        self.soundarray.clear()
        self.audioanswer.clear()
        self.editanswer.clear()
        for row in soup.find_all('a'):  
            self.soundarray[row.string]=[]
            self.audioanswer[row.string]=[]
            self.editanswer[row.string]=[]
        if len(self.soundarray)==0:
            return
        itemNum=int(100/len(self.soundarray))
        j=1     
        for key in self.soundarray.keys():
            try:                  
                value=j * int(itemNum)                                                     
                j += 1 
                audiostring=bytearray()    
                queryUrl=Default_Dict['url']+Default_Dict['list']+"/"+key                
                
                status, content=self.handleUrl.query_get(queryUrl)
                if status ==False:
                    self.errtag.emit("Download Failed!!")
                    return        
                audioData=content.content           
                Head=audioData[0:8]             
                if Head !=b"IPA-GOGO":                 
                    continue 
                head_length=struct.unpack("<7H",audioData[8:8+14])
                self.audioanswer[key]=audioData[8:8+14+sum(head_length)]                                     
                for i in range(20): #(len(audioData)):
                    audiostring.append(audioData[i+8+14+sum(head_length)] ^ 0xFF) 
                audiostring= audiostring + (audioData[8+14+sum(head_length)+20:])                   
                self.soundarray[key]=audiostring    
                self.update.emit(value)
                self.item.emit(key)                                   
            except Exception as err:
                # print(str(err))
                pass
        self.update.emit(100)         




    def GoTimer(self,value):
        Count=0
        while Count<value:
            if self._stop:
               self.update.emit(0)
               self._stop=False
               return 
            if self._end:   
                break
            QThread.sleep(1)
            Count +=1              
            self.update.emit(Count)    
        self.update.emit(value)    
        self.timeup.emit()
        self._end=False    
        
             
        
    def run(self):
        while True:
            self._stop=False
            self._end=False
            QThread.sleep(1)
            if self._download_flag:                
                self.query_file()
                self._download_flag=False                
            if self._TimeCount:
                value=self._TimeCount
                self._TimeCount=0
                self.GoTimer(value-1)
           
                           

    @property
    def download(self):
        return self._download_flag

    @download.setter
    def download(self,value):
        self._download_flag=value

    @property
    def timeCount(self):
        return self._TimeCount

    @timeCount.setter
    def timeCount(self,value):
        self._TimeCount=value

    @property
    def stop(self):
        return self._stop

    @stop.setter
    def stop(self,value):
        self._stop=value     

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self,value):
        self._end=value              



class Main(QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)             
        
        self.handleUrl=HANDLE_FILE()
        self.elapstimer=QElapsedTimer()
        palette = self.lcdNumber.palette()
        self.lcdNumber.setSegmentStyle(QtWidgets.QLCDNumber.Flat)
        palette.setColor(palette.WindowText, QtGui.QColor(85, 85, 255))
        # background color
        palette.setColor(palette.Background, QtGui.QColor(0, 170, 255))
        self.lcdNumber.setPalette(palette)
        self.error_dialog = QtWidgets.QErrorMessage()
        self.Edit_object=[self.Edit_Chinese,self.Edit_11,self.Edit_12,self.Edit_21,self.Edit_22,\
            self.Edit_31,self.Edit_32]
        self.Label_object=[self.label_IPA,self.label_11,self.label_12,self.label_21,self.label_22,\
            self.label_31,self.label_32]

        self.thread = QThread()        
        self.audiohandler=AudioHandler()  
        self.audiohandler.moveToThread(self.thread)            
        self.audiohandler.update.connect(self.set_progress)   
        self.audiohandler.item.connect(self.update_item)
        self.audiohandler.errtag.connect(self.get_err)  
        self.audiohandler.timeup.connect(self.timeout)
        self.thread.started.connect(self.audiohandler.run)  
        self.thread.start()                
        self.timer = QTimer()
        self.go_continue=False
        self.hold_flag=False
        self.timer_Flag=False
        self.build_flag=False
        self.test_Flag=False
        self.newVersion=False
        self.formaltest=False
        self.elapsemin=0  
        self.elapseminPer=60  
        self.fileName=''
        self.formalTime=120
        self.runAmount=0
        self.runItem=[]   
        self.CountNo=0
        self.currentIndex=-1
        self.path=".\\wav_SIL" 
        self.soundarray=self.audiohandler.soundarray
        self.audioanswer=self.audiohandler.audioanswer
        self.editanswer=self.audiohandler.editanswer          
        self.center()
        '''
          for infocus to get the object 
        '''
        self.object = None #QObject
        self.gotsender=None
        self.Edit_12.installEventFilter(self)
        self.Edit_22.installEventFilter(self)
        self.Edit_32.installEventFilter(self)
        self.Edit_11.installEventFilter(self)
        self.Edit_21.installEventFilter(self)
        self.Edit_31.installEventFilter(self)
        self.listWidget.installEventFilter(self) 
        self.lineEdit_ID.installEventFilter(self)
        self.lineEdit_Name.installEventFilter(self)
        self.spinBox.installEventFilter(self)
        self.spinBox_countNo.installEventFilter(self)       
        self.setTabOrder(self.Edit_11,self.Edit_12)
        self.setTabOrder(self.Edit_12,self.Edit_21)
        self.setTabOrder(self.Edit_21,self.Edit_22)
        self.setTabOrder(self.Edit_22,self.Edit_31)
        self.setTabOrder(self.Edit_31,self.Edit_32)
        
        '''
          start to create the connect
        '''
        self.object_conenct() 
        _thread.start_new_thread(self.set_interval, ())       
    
    def center(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())


    def eventFilter(self, obj, event):        
        if event.type() == QEvent.FocusIn:
            if obj in [self.Edit_12,self.Edit_22,self.Edit_32]:
                self.object=obj
            else:
                self.object=None     
        return super(Main, self).eventFilter(obj, event)

  
    def object_conenct(self):
        Button_E=[self.Button_E1,self.Button_E2,self.Button_E3,self.Button_E4,self.Button_E5,\
                   self.Button_E6,self.Button_E7,self.Button_E8,self.Button_E9,self.Button_E10,\
                   self.Button_E11,self.Button_E12,self.Button_E13,self.Button_E14,self.Button_E15,\
                   self.Button_E16,self.Button_E17,self.Button_E18,self.Button_E19,self.Button_E20,\
                   self.Button_E21,self.Button_E22,self.Button_E23,self.Button_E24,self.Button_E25,\
                   self.Button_E26,self.Button_E27,self.Button_E28,self.Button_E29,self.Button_E30,\
                   self.Button_E31,self.Button_E32,self.Button_E33,self.Button_E34,self.Button_E35,\
                   self.Button_E36,self.Button_E37,self.Button_E38,self.Button_E39,self.Button_E40,\
                   self.Button_E41,self.Button_E42,self.Button_E43,self.Button_E44,self.Button_E45,\
                   self.Button_E46,self.Button_E47,self.Button_E48,self.Button_E49,self.Button_E50,\
                   self.Button_E51,self.Button_E52,self.Button_E53]  
        Button_T=[self.Button_T1,self.Button_T2,self.Button_T3,self.Button_T4,self.Button_T5,\
                   self.Button_T6,self.Button_T7,self.Button_T8,self.Button_T9,self.Button_T10,\
                   self.Button_T11,self.Button_T12,self.Button_T13,self.Button_T14,self.Button_T15,\
                   self.Button_T16,self.Button_T17,self.Button_T18,self.Button_T19,self.Button_T20,\
                   self.Button_T21,self.Button_T22,self.Button_T23,self.Button_T24,self.Button_T25,\
                   self.Button_T26,self.Button_T27,self.Button_T28,self.Button_T29,self.Button_T30,\
                   self.Button_T31,self.Button_T32,self.Button_T33,self.Button_T34,self.Button_T35,\
                   self.Button_T36,self.Button_T37,self.Button_T38,self.Button_T39,self.Button_T40,\
                   self.Button_T91,self.Button_T92]
        Combox_=[self.comboBox_1,self.comboBox_2,self.comboBox_3]                                            
        for x in Button_E:
            x.clicked.connect(self.On_button_shot)
        for x in Button_T:
            x.clicked.connect(self.On_button_shot)   
        for x in Combox_:
            x.activated['QString'].connect(self.on_type)
        self.action_download.triggered.connect(self.listFiles)
        self.action_loadTest.triggered.connect(self.listTestFiles)
        self.action_select.triggered.connect(self.selectFiles)
        self.action_build.triggered.connect(self.active_build)
        self.action_compare.triggered.connect(self.active_compare)
        self.action_answerfile.triggered.connect(self.active_answerfile) 
        self.action_sound_comp.triggered.connect(self.active_sound_comp)
        self.action_test.triggered.connect(self.active_test)
        self.action_exam.triggered.connect(self.active_exam)
        self.action_resend.triggered.connect(self.active_resend)
        self.actionExit.triggered.connect(sys.exit)
        self.actionAbout.triggered.connect(self.active_about)
        self.action_SaveFile.triggered.connect(self.active_save)
        self.action_open.triggered.connect(self.active_open)
        self.action_Note.triggered.connect(self.active_note)
        self.action_faketest.triggered.connect(self.active_faketest)
        self.Button_start.clicked.connect(self.on_start_shot) 
        self.Button_next.clicked.connect(self.on_next_shot) 
        self.Button_compare.clicked.connect(self.on_compare_shot)
        self.listWidget.currentRowChanged['int'].connect(self.on_changeitem)
  

        if Default_Dict['build']=='yes':
            self.action_build.setEnabled(True) 
            self.action_compare.setEnabled(True)  
            self.action_answerfile.setEnabled(True)
             
    
        
    def active_about(self):
        Message='版本: ' + TVersion + '.\n' \
                +'License: ' +'Free for none commercial purpose.'
        if self.newVersion:
            Message = Message +'\n' + 'Note: New version is released.'                        
        QMessageBox.information(self, "Version", Message)

    def active_note(self):        
        Message='1.23版:\n\t1. 修正Build選項。\n'\
                '1.22版:\n\t1. 新增結構/類型欄位可插入修改。\n\t2. 修改部分IPA 字體大小。\n\t3. 增加課堂測驗選項。\n'\
                '1.21版:\n\t1. 提升下載題目速度。\n1.20版:\n\t1. 新增開啟存檔答案功能。\n\t2. 新增剩餘測驗時間於右上角。\n\t'+\
                '3. 新增模擬測驗功能。\n\t'+\
                '4. 修正IPA Table和Extentions to IPA Table。\n\t5. 修正字體大小。\n\t'+\
                '6. 修正答案存檔功能。\n\t7. 修正正式測驗功能。\n'
                                        
  
        QMessageBox.information(self, "Release Note", Message)
    
    def active_faketest(self):
        if self.listWidget.count()==0:
            self.action_faketest.setChecked(False)
            self.get_err("請先下載題目!")
            return
        if self.action_faketest.isChecked()==True:                   
            Message='使用說明:\n1. 先下載練習題或測驗題。\n'+\
                    '2. 此測驗將限制總測驗時間和每題作答時間。\n'+\
                    '3. 此測驗會存檔，但不會比對答案也不會傳送答案。\n'+\
                    '4. 只作為正式測驗前的練習，可藉由開啟存檔答案來驗證答題能力。'        

            buttonReply = QMessageBox.question(self,"" ,Message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if buttonReply == QMessageBox.Yes:                                                                     
                self.spinBox_countNo.setValue(0)
                self.spinBox_countNo.setEnabled(False)
                self.spinBox_comp.setValue(1)
                self.groupBox_Comp.setEnabled(False)
                for object in self.Edit_object:
                        object.clear()                  
                self.progressBar.setValue(0)                  
                self.spinBox.setValue(self.formalTime) 
                self.formal_test() 
                self.elapsemin=self.elapseminPer*self.listWidget.count()
                self.action_test.setChecked(True) 
                self.action_faketest.setEnabled(False)
                self.action_test.setEnabled(False)                   
            else:
                self.action_faketest.setChecked(False)
 
   
    def formal_test(self):
        self.groupBox_Test.setEnabled(True)
        self.spinBox.setEnabled(False)        
        self.listWidget.setEnabled(False)          
        self.Button_start.setText("測驗開始")   



    def update_item(self,item):
        if item !="":
            self.listWidget.addItem(item)
        


    def set_progress(self,value):       
        # print(value)       
        self.progressBar.setValue(value)

    def get_err(self,err):
        self.statusBar().showMessage(str(err)) 
        self.error_dialog.showMessage(str(err))
        self.error_dialog.show()  
        if self.action_exam.isChecked() and self.listWidget.count()==0:
            self.action_exam.setChecked(False)   
            self.action_test.setChecked(False)                                            
        

    def listFiles(self): 
        self.listWidget.clear()
        for object in self.Edit_object:
                object.clear()
        for object in self.Label_object:
                object.clear()
        Default_Dict['list'] = Default_Dict['practice'] #'/audio'   
        self.progressBar.setMaximum(100)     
        self.audiohandler.download=True
        if not self.action_build.isChecked(): 
            self.Edit_Chinese.setReadOnly(True)
        self.test_Flag=False    
        self.groupBox_Test.setEnabled(True) 
        self.Button_compare.setEnabled(True) 
        self.spinBox.setValue(0)
        self.spinBox_countNo.setValue(0)
        self.listWidget.setEnabled(True)         

        
    def set_interval(self):     
        status, r=self.handleUrl.query_get(Default_Dict['url']+"/formal")
        if status ==False:
            self.statusBar().showMessage("Initial Failed! Server or netwrok Error!")
            return                    
        content=r.json()       
        if 'practice' in content.keys():
            Default_Dict['practice'] = content['practice']  
        if 'test' in content.keys():
            Default_Dict['test'] = content['test']
        if 'exam' in content.keys():
            Default_Dict['exam'] = content['exam']    
        if 'interval' in content.keys():
            self.formalTime=content['interval']          
        if 'version' in content.keys():
            if content['version'] != TVersion:
                self.newVersion=True
        if 'formaltest' in content.keys():
            if content['formaltest'] == 'on':
                self.formaltest=True                 
                self.action_faketest.setEnabled(False)                 
            else:
                self.formaltest=False                 
                self.action_exam.setChecked(False)   
                self.action_test.setChecked(False)
        if 'elapsemin' in content.keys():                
            self.elapseminPer=content['elapsemin']        
        if 'web' in content.keys():
            if content['web'] !='':
                Default_Dict['url'] =content['web']                                   
        if self.action_test.isChecked():               
            while True:
                time.sleep(1)                
                if self.audiohandler.download==False:
                    self.progressBar.setValue(0)    
                    self.spinBox.setValue(self.formalTime)
                    self.elapsemin=self.elapseminPer*self.listWidget.count()                    
                    return
               
                  

    def listTestFiles(self): 
        if self.action_test.isChecked():                 
            _thread.start_new_thread(self.set_interval, ())
        self.progressBar.setMaximum(100)     
        self.listWidget.clear()
        for object in self.Edit_object:
                object.clear()
        for object in self.Label_object:
                object.clear()
        Default_Dict['list'] = Default_Dict['test']       
        self.audiohandler.download=True
        if not self.action_build.isChecked(): 
            self.Edit_Chinese.setReadOnly(True)  
        self.test_Flag=True    
        self.groupBox_Test.setEnabled(True)
        if not self.action_build.isChecked:
            self.Button_compare.setEnabled(False)  
        self.spinBox.setValue(0)
        self.spinBox_countNo.setValue(0)
        self.listWidget.setEnabled(True)      
       
   
    

    def selectFiles(self):      
        file=QFileDialog.getExistingDirectory(self, 'Select directory')
        if file=="":
            return
        self.progressBar.setMaximum(100)      
        self.listWidget.clear()
        self.progressBar.setValue(0)
        for r, d, f in os.walk(file):
            for file in f:
                if '.wav' in file:
                    self.listWidget.addItem(file)
                    filename=os.path.join(r, file)
                    if os.path.exists(filename):
                        with open(filename, 'rb') as file_t:
                            self.audioanswer[file]=bytearray(0)
                            self.soundarray[file] = bytearray(file_t.read())                         
        self.progressBar.setValue(100)
        if self.listWidget.count()>0:
            self.spinBox_countNo.setMaximum(self.listWidget.count())


    def on_interval(self):
        time_out=self.spinBox.value()
        # print(time_out)
        if time_out!=0:
            self.progressBar.setMaximum(time_out)        
        if time_out!=0:
            if self.test_Flag:
                self.Button_start.setText("測驗開始")
            else:    
                self.Button_start.setText("連續作答")

            self.Button_start.setEnabled(True)
        else:
            self.Button_start.setEnabled(False)             
            self.timer_Flag=False   

    def on_do(self): 
        if self.checkBox_continue.isChecked():
            self.listWidget.setCurrentRow(self.spinBox_comp.value()-1)
            if self.listWidget.currentItem()==None:
                return
            self.show_listanswer()

    def final_one(self):
        if not self.timer_Flag:
            self.spinBox.setEnabled(True)
            if self.test_Flag:
                self.Button_start.setText("測驗開始")
            else:     
                self.Button_start.setText("連續作答")
            if not self.test_Flag:    
                self.Button_compare.setEnabled(True) 
            return           
        self.save_answer()      
        self.spinBox.setEnabled(True)
        if self.test_Flag:
            self.Button_start.setText("測驗開始")
        else:    
            self.Button_start.setText("連續作答")
        self.CountNo=0
        self.spinBox_countNo.setValue(0)
        self.compare_all()
        if not self.test_Flag:
            self.Button_compare.setEnabled(True) 
        self.timer_Flag=False
        self.listWidget.setCurrentRow(-1) 
        self.Button_next.setEnabled(False)  
 

    def active_save(self):
        if len(self.lineEdit_ID.text())==0 or len(self.lineEdit_Name.text())==0:
            Message="請輸入姓名和學生證ID。"
            QMessageBox.critical(self, "正式測驗", Message)
            return              
        fileName=self.lineEdit_ID.text()+time.strftime("%m%d", time.localtime())+'.ipa'
        fname = QFileDialog.getSaveFileName(self, 'Save File',fileName,("*.ipa"))
        if fname[0]=="":
            return
        self.save_all(fname[0])
 

    def save_all(self, fileName=''):
        try:
            if fileName=='':
                self.fileName=self.lineEdit_ID.text()+time.strftime("%m%d", time.localtime())+'.ipa'
            else:
                self.fileName=fileName        
 
            Iname=bytearray(20)
            ID=bytearray(12)               
            Iname[0:len(self.lineEdit_Name.text().encode('utf-8'))]=self.lineEdit_Name.text().encode('utf-8')
            ID[:len(self.lineEdit_ID.text().encode('utf-8'))]=self.lineEdit_ID.text().encode('utf-8')

            for i in range(12):
                 ID[i]=ID[i] ^ 0xFF
            Iname[16]=0xAA
            Iname[17]=0x55     
            checksum=sum(Iname[0:12])
            Iname[18]=checksum & 0xFF 
            Iname[19]=(checksum & 0xFF00) >>8  
            with open(self.fileName, 'wb') as file:                  
                file.write(Iname)
                file.write(ID) 
                length=struct.pack("<H",len( self.editanswer.keys()))
                file.write(length)           
                for key in self.editanswer.keys():                             
                    Item=bytearray(20)
                    Item[0:len(key.encode('utf-8'))]=key.encode('utf-8')
                    file.write(Item)                  
                    # print(object_length) 
                    length=struct.pack("<H",len(self.editanswer[key])) 
                    file.write(length)                
                for key in self.editanswer.keys():   
                    if len(self.editanswer[key])!=0:    
                        file.write(self.editanswer[key])
        except Exception as err:
            self.get_err(str(err))                       

    def active_open(self):
        # try:
            fname = QFileDialog.getOpenFileName(self, 'Open File',("*.ipa"))
            if fname[0]=="":
                return
            key_length=[]
            listItem=[]        
            with open(fname[0], 'rb') as file: 
                Iname=file.read(20)
                checksum=sum(Iname[0:12])  
                self.lineEdit_Name.setText((Iname[0:16].decode('utf-8')).rstrip('\0'))
                ID=file.read(12)
                ID1=bytearray(12)
                if Iname[16:20] != b'\x00\x00\x00\x00':
                    for i in range(12):
                        ID1[i]=ID[i] ^ 0xFF                       
                    if Iname[16] != 0xAA and Iname[17] !=0x55:   
                        self.get_err("ID or Name error")
                        return
                    if Iname[18] != (checksum & 0xFF) or Iname[19]!= ((checksum & 0xFF00)>>8) :
                        self.get_err("ID or Name error")
                        return     
                    self.lineEdit_ID.setText(ID1.decode('utf-8').rstrip('\0'))
                else:
                    self.lineEdit_ID.setText(ID.decode('utf-8').rstrip('\0'))           
 
                templength=file.read(2)            
                length=struct.unpack("<H",templength)           
                for i in range(length[0]):
                    listItem.append((file.read(20).decode('utf-8')).rstrip('\0'))
                    temp=file.read(2)
                    key_length.append(struct.unpack("<H",temp)[0])
                for index,key in enumerate(listItem):
                    self.editanswer[key]=file.read(key_length[index])
                    item=self.listWidget.findItems(key, QtCore.Qt.MatchExactly)
                    if len(item)>0:                    
                        item[0].setForeground(QtGui.QColor("blue"))
                    else:
                        self.listWidget.addItem(key)   
                        self.listWidget.item(self.listWidget.count()-1).setForeground(QtGui.QColor("blue"))
                self.groupBox_Test.setEnabled(False)
 
                 
    def active_answerfile(self):
        try:
            fname = QFileDialog.getOpenFileName(self, 'Open Answer File',("*.ipa"))
            if fname[0]=="":
                return
            key_length=[]
            listItem=[]        
            with open(fname[0], 'rb') as file: 
                Iname=file.read(16).decode('utf-8').rstrip('\0')
                file.read(4)    
                ID1=file.read(12)    
                ID=bytearray(12)                
                for i in range(12):
                    ID[i]=ID1[i] ^ 0xFF       

                if Iname!="Answer":
                    self.get_err("非標準答案檔!!")
                    return
                self.lineEdit_Name.setText(Iname)
                self.lineEdit_ID.setText(ID.decode('utf-8').rstrip('\0'))
                templength=file.read(2)            
                length=struct.unpack("<H",templength)           
                for i in range(length[0]): 
                    listItem.append((file.read(20).decode('utf-8')).rstrip('\0'))
                    temp=file.read(2)
                    key_length.append(struct.unpack("<H",temp)[0])
                self.listWidget.clear()    
                for index,key in enumerate(listItem):
                    self.audioanswer[key]=file.read(key_length[index])
                    self.listWidget.addItem(key)   
                    self.listWidget.item(self.listWidget.count()-1).setForeground(QtGui.QColor("red"))

        except Exception as err:
            self.get_err(str(err))

    def active_compare(self):      
        file=QFileDialog.getExistingDirectory(self, 'Select directory')
        if file=="":
            return                         
        row=[]         
        answer={}
        for key in self.audioanswer.keys():
            answer[key]=[]
        Field = list(["ID","Name"])+list(self.audioanswer.keys())
        Field.append("Correct")
        Column = list(["ID","Name","中文","結構/類型","音節","結構/類型","音節","結構/類型","音節"])        
               
        for key in self.audioanswer.keys():                         
            length=struct.unpack('<7H',self.audioanswer[key][0:14])
            item=[]
            item.append(self.lineEdit_Name.text())
            item.append(self.lineEdit_ID.text())
            for i in range(7):
                if length[i]!=0:
                    item.append(self.audioanswer[key][14+sum(length[0:i]):14+sum(length[0:i+1])].decode('UTF-8'))   
                else:    
                    item.append("")
            answer[key].append(item)       
        self.progressBar.setValue(0)
        for r, d, f in os.walk(file):
            for file in f:
                if '.ipa' in file:                    
                    filename=os.path.join(r, file)
                    try:
                        if os.path.exists(filename):                        
                            listItem=[]  
                            key_length=[]   
                            self.editanswer.clear()                                              
                            with open(filename, 'rb') as file:
                                Tname=file.read(20)                                
                                checksum=sum(Tname[0:12])  
                                if Tname[16] != 0xAA and Tname[17] !=0x55:   
                                    self.get_err("ID or Name error :" + filename)
                                    return
                                if Tname[18] != (checksum & 0xFF) or Tname[19]!= ((checksum & 0xFF00)>>8) :
                                    self.get_err("ID or Name error :" + filename)
                                    return 
                                ID=file.read(12)
                                ID1=bytearray(12)
                                for i in range(12):
                                    ID1[i]= ID[i] ^ 0xFF                            
                                Iname=Tname[0:16].decode('utf-8').rstrip('\0')
                                ID=ID1.decode('utf-8').rstrip('\0')
                                templength=file.read(2)            
                                length=struct.unpack("<H",templength)           
                                for i in range(length[0]):
                                    listItem.append((file.read(20).decode('utf-8')).rstrip('\0'))
                                    temp=file.read(2)
                                    key_length.append(struct.unpack("<H",temp)[0])                                                                                       
                                for index,key in enumerate(listItem):
                                    self.editanswer[key]=file.read(key_length[index])                            
                            answerList=[]
                            answerList.append(ID)
                            answerList.append(Iname)                       
                            for key in self.audioanswer.keys(): 
                                if key in self.editanswer.keys():                                   
                                    if self.audioanswer[key]==self.editanswer[key]:
                                        answerList.append(1)
                                    else:                        
                                        answerList.append(0)
                                else:                            
                                    answerList.append(0)                                        
                            answerList.append(sum(answerList[2:]))                                        
                            row.append(answerList) 
                            for key in self.editanswer.keys(): 
                                if key not in self.audioanswer.keys():                          
                                    continue                            
                                length=struct.unpack('<7H',self.editanswer[key][0:14])
                                item=[]                           
                                item.append(Iname)
                                item.append(ID)
                                for i in range(7):
                                    if length[i]!=0:
                                        item.append(self.editanswer[key][14+sum(length[0:i]):14+sum(length[0:i+1])].decode('UTF-8'))   
                                    else:    
                                        item.append("")
                                answer[key].append(item)                 
                    except Exception as err:
                        self.get_err(filename +" : " + str(err))
                    self.progressBar.setValue(30)        
        try:                        
            filename=self.lineEdit_ID.text()+".xlsx" 
            writer = ExcelWriter(filename, engine='xlsxwriter')
            df = DataFrame(row,columns=Field)                
            df.to_excel(writer,sheet_name='List',na_rep=False,index=False,encoding='utf-8')
            for key in answer.keys():
                df2 = DataFrame(answer[key],columns=Column)  
                df2.to_excel(writer,sheet_name=key,na_rep=False,index=False,encoding='utf-8')          
        except Exception as err:
            self.get_err(err)        
        self.progressBar.setValue(100)    



    def active_resend(self):
        self.send_file()

    def send_file(self):
        # self.filename
        try:
            ftp = FTP(Default_Dict['IP2'])  
            ftp.login('ipa', '1234')  
            with open(self.fileName, 'rb') as f:  
                ftp.storbinary('STOR %s' % self.fileName, f)  
            ftp.quit()
            return True
        except Exception as err:
            self.get_err(str(err))    
            return False


    def compare_all(self): 
        try:      
            wrong=[]
            wrongIndex=[]
            if self.CountNo!=0:
                return
            if self.action_faketest.isChecked() or self.action_exam.isChecked(): 
                self.save_all()       
                Message="很好! 你已完成本次測驗。"
                QMessageBox.warning(self, "IPA 轉錄測試", Message)
                self.listWidget.clear() 
                if self.elapstimer.isValid:         
                    self.elapstimer.invalidate()
                self.action_faketest.setChecked(False)
                self.action_exam.setChecked(False)
                self.action_test.setChecked(False) 
                self.groupBox_Comp.setEnabled(True)
                self.action_faketest.setEnabled(True)
                self.action_test.setEnabled(True)
                self.spinBox.setValue(0)      
                return 
            if self.action_test.isChecked()==True:
                self.save_all()                       
                if not self.send_file():
                    return
                Message="很好! 你已完成本次測驗。"
                QMessageBox.warning(self, "IPA 轉錄測試", Message)
                self.listWidget.clear() 
                Default_Dict['url']="" 
                if self.elapstimer.isValid:         
                    self.elapstimer.invalidate()
                return
            if self.test_Flag==True:
                return    

            for row in self.runItem:
                key=self.listWidget.item(row).text() 
                if self.action_type_comp.isChecked() and self.action_sound_comp.isChecked():   
                    if self.audioanswer[key]!=self.editanswer[key]:
                        wrong.append(key)
                        wrongIndex.append(row+1)
                elif self.action_type_comp.isChecked():               
                        length=struct.unpack('<7H',self.audioanswer[key][0:14]) 
                        j=0                        
                        for i in length:
                            if j in (0,2,4):
                                j +=1
                                continue
                            if self.audioanswer[key][14+sum(length[0:i]):14+sum(length[0:i+1])].decode('UTF-8') \
                                != self.editanswer[key][14+sum(length[0:i]):14+sum(length[0:i+1])].decode('UTF-8'):
                                wrong.append(key)
                                wrongIndex.append(row+1)                    
                            j += 1    

            all=self.runAmount #len(self.runItem)
            wrongNo=len(wrong)
            if wrongNo ==0 :
                Message='優秀啊!! 全答對了!!\n'
            elif wrongNo==1: 
                Message="Good Job!! 只差一題。\n"
            elif 2 <= wrongNo <4 and all != wrongNo:
                Message="還差一些，加油!!\n"
            else:
                Message="要多練習，加油 加油!!\n"               
            Message= Message+'總共測試'+ str(all)+'題，答錯'+str(wrongNo)+'題。  \n'
            i=0    
            for i in range(len(wrong)):
                if i%2: 
                    Message = Message + '答錯: '+ wrong[i] + '         \n' 
                else:
                    Message = Message + '答錯: '+ wrong[i] +',   '
            QMessageBox.warning(self, "IPA 轉錄測試", Message)
            if len(wrongIndex)!=0:
                self.statusBar().showMessage("答錯題: "+ str(wrongIndex))
            else:
                self.statusBar().clearMessage() #showMessage("")
        except Exception as err:
            self.get_err(str(err))                   

    def timeout(self):
        try:           
            if self.timer_Flag:
                self.save_answer()                 
                self.CountNo -=1   
            else:                                                          
                return          
            if self.CountNo>0: #self.currentIndex +1  < self.listWidget.count():
                self.goNextOne()        
            else:
                self.final_one()              
        except Exception as err:
            self.get_err(str(err))

    def moveItem(self):
        currentIndex = self.listWidget.currentRow()
        currentItem = self.listWidget.takeItem(currentIndex)
        self.listWidget.insertItem(currentIndex+1, currentItem)
        self.listWidget.setCurrentRow(currentIndex+1)   

    def play_build(self):
        try:        
            if self.listWidget.currentItem()==None:
                return
            soundName=self.listWidget.currentItem().text() 
            soundName=os.path.join(Default_Dict['save_directory'], soundName)
            if not os.path.exists(soundName):            
                self.get_err(soundName + "測試題不存在!。")
                return 
            with open(soundName, 'rb') as file:
                Head=(file.read(8))
                if Head !=b"IPA-GOGO":
                    return
                dataHead=file.read(2*len(self.Edit_object))
                head_length=struct.unpack("<7H",dataHead)
                for i in range(len(self.Edit_object)):
                    self.Edit_object[i].setText(file.read(head_length[i]).decode("utf-8"))
                sound=file.read()
                audiostring=bytearray()
                for i in range(20): #(len(audioData)):
                    audiostring.append(sound[i] ^ 0xFF) 
                audiostring= audiostring + (sound[20:])  
                filestream=io.BytesIO(audiostring) #self.soundarray[file])
                wave_obj = sa.WaveObject.from_wave_file(filestream)
                play_obj = wave_obj.play()
        except Exception as err:
            self.get_err("音檔錯誤!")        

    def on_spinComp(self):
        if self.listWidget.count()==0:
            return
        self.spinBox_comp.setMaximum(self.listWidget.count())
        self.listWidget.setCurrentRow(self.spinBox_comp.value()-1)
        self.on_do()

    def on_changeitem(self, value):        
        self.spinBox_comp.setValue(value+1)

    def show_listanswer(self):
        try:
            soundName=self.listWidget.currentItem().text()
            for object in self.Edit_object:
                    object.clear() 
            if len(self.editanswer[soundName])==0:
                return 
 
            length=struct.unpack('<7H',self.editanswer[soundName][0:14])
            for i in range(len(self.Edit_object)):
                if length[i]!=0:
                    self.Edit_object[i].setText(self.editanswer[soundName][14+sum(length[0:i]):14+sum(length[0:i+1])].decode('UTF-8'))   
        except Exception as err:
            self.get_err(str(err))        

    def on_compare_shot(self):
        QTimer.singleShot(0, self.on_compare)  

    def on_compare(self):
        try:
            if self.build_flag:
                self.on_done()            
                return
            if self.listWidget.currentItem()==None:
                return
            if self.test_Flag:
                return    
            for object in self.Label_object:
                object.clear()     
            soundName=self.listWidget.currentItem().text() 
            length=struct.unpack('<7H',self.audioanswer[soundName][0:14])      
            for i in range(1,len(self.Edit_object)):
                if self.Edit_object[i].text() != self.audioanswer[soundName][14+sum(length[0:i]):14+sum(length[0:i+1])].decode('UTF-8'):
                    if (i%2!=0 and self.action_type_comp.isChecked()==True) or (i%2==0 and self.action_sound_comp.isChecked()==True):
                        self.Label_object[i].setText("( "+ str(self.audioanswer[soundName][14+sum(length[0:i]):14+sum(length[0:i+1])].decode('UTF-8'))+" )")                
        except Exception as err:
            self.get_err("音檔錯誤! 請重新下載。")

    def on_calculatetime(self):
        if self.elapsemin==0:
            self.elapstimer.invalidate()
            return
        timerup=self.elapsemin *1000        
        if not self.elapstimer.hasExpired(timerup):
            total=(timerup-self.elapstimer.elapsed())/1000
            min=total/60
            sec=total%60
            tick=str(int(min))+":"+str(int(sec))
            QTimer.singleShot(1000, self.on_calculatetime)
            self.lcdNumber.display(tick)
        else:
            self.elapstimer.invalidate()
            self.CountNo=1
            self.audiohandler.end=True
    


    def on_next_shot(self):
        QTimer.singleShot(0, self.on_next)  

    def on_next(self):
        self.audiohandler.end=True

    def on_start_shot(self):
        QTimer.singleShot(0, self.on_start)  

    def on_start(self): 
        if self.Button_start.text()=="停 止":
            self.audiohandler.stop=True
            self.timer_Flag=False
            self.spinBox.setEnabled(True) 
            if self.test_Flag:
                self.Button_start.setText("測驗開始")
            else:    
                self.Button_start.setText("連續作答") 
            if not self.test_Flag:  
                self.Button_compare.setEnabled(True)
            self.Button_next.setEnabled(False) 

        elif self.Button_start.text()=="連續作答" or self.Button_start.text()=="測驗開始":
            if self.listWidget.count()==0:
                self.get_err("題目不存在!\n請下載題目。")
                return
            if self.action_test.isChecked()==True:                  
                if len(self.lineEdit_ID.text())==0 or len(self.lineEdit_Name.text())==0:
                    Message="請輸入姓名和學生證ID。"
                    QMessageBox.critical(self, "正式測驗", Message)
                    return                
                else:
                    self.listWidget.setEnabled(True)
                    self.Button_start.setEnabled(False) 
                    if self.elapsemin!=0:
                        self.elapstimer.start() 
                        QTimer.singleShot(1000, self.on_calculatetime)                                         
            self.checkBox_continue.setChecked(False)                
            self.spinBox.setEnabled(False)
            self.timer_Flag=True
            
            self.Button_next.setEnabled(True)
            self.Button_start.setText("停 止")  
            self.Button_compare.setEnabled(False)  
            if self.listWidget.currentRow()==-1:             
                self.currentIndex=-1
            else:
                self.currentIndex=self.listWidget.currentRow()-1
            if self.spinBox_countNo.value()==0:
                self.CountNo=(self.listWidget.count()-(self.currentIndex+1))
            else:    
                self.CountNo=self.spinBox_countNo.value()
            if (self.CountNo > self.listWidget.count()) or (self.CountNo > (self.listWidget.count()-(self.currentIndex+1))):
                self.CountNo=(self.listWidget.count()-(self.currentIndex+1))
            self.runAmount=self.CountNo 
            self.runItem.clear()           
            self.goNextOne()
          
        elif self.build_flag: 
                self.play_build()
                                                     

    def goNextOne(self):
        currentIndex = self.listWidget.currentRow()
        self.spinBox_countNo.setValue(self.CountNo)
        self.currentIndex +=1
    
        if self.currentIndex < self.listWidget.count():
            self.audiohandler.timeCount=self.spinBox.value()+1            
            self.listWidget.setCurrentRow(self.currentIndex)
            self.runItem.append(self.currentIndex)  
            for object in self.Edit_object:
                object.clear()
            for object in self.Label_object:
                object.clear()
            self.Edit_11.setFocus()    
 
            _thread.start_new_thread(self.on_change, ())
  
    def active_sound_comp(self):
        if self.action_sound_comp.isChecked()==True:
            self.action_type_comp.setChecked(True)      

    def active_exam(self):
        self.set_interval()
        if not self.formaltest:   
            Message="課堂測驗尚未開啟。"
            QMessageBox.warning(self, "IPA 課堂測驗", Message)
            self.action_exam.setChecked(False)             
        if self.action_exam.isChecked()==True:         
            self.action_test.setChecked(True)    
            Default_Dict['test'] = Default_Dict['exam']
            self.listWidget.clear()
            self.listTestFiles()
            self.formal_test()                                
            self.spinBox_countNo.setValue(0)
            self.spinBox_countNo.setEnabled(False)
            self.spinBox_comp.setValue(1)
            self.groupBox_Comp.setEnabled(False)
            for object in self.Edit_object:
                    object.clear()
            self.action_resend.setEnabled(True)                        
  
        else:
            if not self.test_Flag:
                self.Button_compare.setEnabled(True)
            self.groupBox_Test.setEnabled(False)
            self.spinBox.setValue(0)
            self.spinBox.setEnabled(True)
            self.spinBox_comp.setEnabled(True) 
            self.spinBox_countNo.setEnabled(True) 
            self.groupBox_Comp.setEnabled(True) 
            self.action_resend.setEnabled(False)  

    def active_test(self):
        # self.set_interval()
        if not self.formaltest:   
            Message="正式測驗尚未開啟。"
            QMessageBox.warning(self, "IPA 正式測驗", Message)
            self.action_test.setChecked(False)             
        if self.action_test.isChecked()==True:         
            text, okPressed = QInputDialog.getText(self,"IPA 轉錄測驗","IP Address:", QLineEdit.Normal,"")
            if okPressed and text != '':
                Default_Dict['IP2']=text
                Default_Dict["url"]="http://"+text
                self.listWidget.clear()
                self.listTestFiles()
                self.formal_test()                                
                self.spinBox_countNo.setValue(0)
                self.spinBox_countNo.setEnabled(False)
                self.spinBox_comp.setValue(1)
                self.groupBox_Comp.setEnabled(False)
                for object in self.Edit_object:
                        object.clear()
                self.action_resend.setEnabled(True)                        
            else:
                self.action_test.setChecked(False)        
        else:
            if not self.test_Flag:
                self.Button_compare.setEnabled(True)
            self.groupBox_Test.setEnabled(False)
            self.spinBox.setValue(0)
            self.spinBox.setEnabled(True)
            self.spinBox_comp.setEnabled(True) 
            self.spinBox_countNo.setEnabled(True) 
            self.groupBox_Comp.setEnabled(True) 
            self.action_resend.setEnabled(False)  

    def active_build(self): 
        if self.action_build.isChecked()==True:         
            self.spinBox.setValue(0)
            self.action_select.setEnabled(True)            
            self.checkBox_continue.setEnabled(False)
            self.build_flag=True
            self.Button_start.setText("測試音檔")
            self.Button_compare.setText("建立測試題")
            self.Button_start.setEnabled(True)
            self.Edit_Chinese.setReadOnly(False)            
        else:
            self.spinBox.setEnabled(True)
            self.checkBox_continue.setEnabled(True)
            self.action_select.setEnabled(False)
            self.build_flag=False
            self.audiohandler.build_flag=False
            if self.test_Flag:
                self.Button_start.setText("測驗開始")
            else:    
                self.Button_start.setText("連續作答")
            self.Button_compare.setText("音節比對")
            self.Button_start.setEnabled(False)
            self.Edit_Chinese.setReadOnly(True) 
  

    def save_answer(self): 
        try:              
            object_length=[]    
            fileHead=b'IPA-GOGO'
            if self.listWidget.currentItem()==None:
                return
            soundName=self.listWidget.currentItem().text() 
            if soundName =="":
                return                                       
            for object in self.Edit_object:
                object_length.append(len(object.text().encode('utf-8')))
 
            data=struct.pack("<7H",object_length[0],object_length[1],object_length[2],\
                object_length[3],object_length[4],object_length[5],object_length[6]) 
 
            answerdata=bytearray()
            for object in self.Edit_object:
                answerdata.extend(object.text().encode('utf-8'))
            self.editanswer[soundName]=data+answerdata
        except Exception as err: 
            self.get_err(str(err))
            
                  

    def on_done(self):
        try:                
            object_length=[]    
            fileHead=b'IPA-GOGO'
            if self.listWidget.currentItem()==None:
                return
            soundName=self.listWidget.currentItem().text() 
            if soundName =="":
                return
            fileName=os.path.join(Default_Dict['save_directory'], soundName)
            with open(fileName, 'wb') as file:
                file.write(fileHead)                        
                for object in self.Edit_object:
                    object_length.append(len(object.text().encode('utf-8')))
                head=struct.pack("<7H",object_length[0],object_length[1],object_length[2],\
                    object_length[3],object_length[4],object_length[5],object_length[6]) 
                file.write(head)
                for object in self.Edit_object:
                    file.write(object.text().encode('utf-8'))
                audiostring=bytearray()                
                for i in range(20): #(len(audioData)):
                    audiostring.append(self.soundarray[soundName][i] ^ 0xFF) 
                audiostring= audiostring + (self.soundarray[soundName][20:])       
                file.write(audiostring)
                for object in self.Edit_object:
                    object.clear()
                for object in self.Label_object:
                    object.clear()    
        except Exception as err: 
            self.get_err(str(err))
       

    def on_download(self):
        return

    def On_button_shot(self):
        if self.object==None:
            return  
        self.gotsender = self.sender()   
        QTimer.singleShot(0, self.On_button)    
        return
 


    def On_button(self): 
        try:      
            sender = self.gotsender    
            object = self.object                     
            if object.cursorPosition()< len(object.text()):
                tMessage=object.text()[0:object.cursorPosition()]+sender.text()+\
                    object.text()[object.cursorPosition():]
                tempP=object.cursorPosition()+len(sender.text())   
            else:    
                tMessage= (object.text()) + sender.text()
                tempP=len(tMessage)+1                           
            object.setText(tMessage)
            object.setCursorPosition(tempP)
            object.setFocus()
        except Exception as err:
            self.get_err(str(err))

    def on_change(self):
        try:            
            self.object=None
            if (self.listWidget.currentRow() != self.currentIndex) \
                and (self.timer_Flag) :
                self.listWidget.setCurrentRow(self.currentIndex)               
                return
            elif self.listWidget.currentRow() != self.currentIndex:
                for object in self.Edit_object:
                    object.clear()
                for object in self.Label_object:
                    object.clear()            
            file=self.listWidget.currentItem().text()
            if file not in self.soundarray.keys():
                self.get_err("無音檔!")
                return                 
            if not self.build_flag:          
                length=struct.unpack("<H",self.audioanswer[file][0:2]) 
                self.Edit_Chinese.setText(self.audioanswer[file][14:14+length[0]].decode('UTF-8'))
            else:
                if len(self.audioanswer[file])!=0:
                   length=struct.unpack("<H",self.audioanswer[file][0:2]) 
                   self.Edit_Chinese.setText(self.audioanswer[file][14:14+length[0]].decode('UTF-8'))                            
                     
            filestream=io.BytesIO(self.soundarray[file])
            wave_obj = sa.WaveObject.from_wave_file(filestream)
            play_obj = wave_obj.play()            
            if not self.timer_Flag:
                self.currentIndex=self.listWidget.currentRow() 
            return
        except Exception as err:
            self.get_err("音檔錯誤!")
   

    def on_type(self):
        temp={self.comboBox_1:self.Edit_11,self.comboBox_2:self.Edit_21,self.comboBox_3:self.Edit_31}
        sender = self.sender()
        object=temp[sender]
        if object.cursorPosition()< len(object.text()):
            if sender.currentIndex()  >2 and object.text()[0:object.cursorPosition()].find(sender.currentText()[0])==-1\
            and object.text()[0:object.cursorPosition()].find('/')==-1:
                middle='/'
                if object.text()[object.cursorPosition()-1:].find(middle): 
                    newone=object.text()[object.cursorPosition():].replace(middle,"")
                else:
                    newone=object.text()[object.cursorPosition():]
            else:
                middle=""  
                newone= object.text()[object.cursorPosition():]   
            tMessage=object.text()[0:object.cursorPosition()]+middle+sender.currentText()[0] \
                + newone #object.text()[object.cursorPosition():]
            tempP=object.cursorPosition()+len(sender.currentText()[0])                 
            object.setText(tMessage)
            object.setCursorPosition(tempP) 
        else:
            if sender.currentIndex()  >2 and object.text().find(sender.currentText()[0])==-1\
                and object.text().find('/')==-1:
                # if (sender.currentText()[0] in x for x in temp[sender].text()):
                middle='/'
            else:
                middle=""     
            eMessage=object.text()+middle+sender.currentText()[0]        
            object.setText(eMessage)
        object.setFocus()      

def Handle_Parse():
    try:
        config = configparser.ConfigParser()        
        if not os.path.exists('ipatrans.ini'):
            Default_Dict['url'] = 'https://'+ Default_Dict['IP1']
            return False
        config.read('ipatrans.ini')
        default=config['DEFAULT']        
        if Default_Dict['build']!='yes':
            Default_Dict['build']=default.get('build')
        if Default_Dict['build']=='yes':
            Default_Dict['save_directory']='.\\target'        
            if not os.path.exists(Default_Dict['save_directory']):
                os.makedirs(Default_Dict['save_directory'])                 
        Default_Dict['IP1']=default.get('ip_address1')
        Default_Dict['IP2']=default.get('ip_address2')
        if Default_Dict['IP1']=='':
            Default_Dict['IP1']=music_url             
        Default_Dict['url'] = 'https://'+ Default_Dict['IP1']
        if Default_Dict['IP2']!='' and Default_Dict['IP2']!=None:
             Default_Dict['url'] = 'http://' + Default_Dict['IP2']    
        return True
    except Exception as err:        
    #    print("configure error: " + str(err))
        return False
  

# BUILD=False
if __name__ == '__main__':                  
    if len(sys.argv)>1 and sys.argv[1]=='BUILD':
        Default_Dict['build']='yes'     
    Handle_Parse()    
    app = QApplication(sys.argv)
    MainWindow = Main()
    MainWindow.show()           
    sys.exit(app.exec_())   

   
        
